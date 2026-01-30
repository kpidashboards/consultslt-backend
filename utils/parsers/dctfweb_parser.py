"""
Parser de PDFs da DCTFWeb
Extrai dados estruturados de recibos e declarações DCTFWeb

Dados extraídos:
- CNPJ do contribuinte
- Período de apuração
- Valor total devido
- Data de vencimento
- Número do recibo
- Situação da declaração
"""

import pdfplumber
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import io

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    """Exceção para erros de parsing de PDF"""
    pass


@dataclass
class DCTFWebData:
    """Dados extraídos de um PDF DCTFWeb"""
    # Identificação
    cnpj: str
    razao_social: Optional[str] = None
    
    # Período
    periodo_apuracao: str = ""  # formato: "MM/YYYY"
    ano: Optional[int] = None
    mes: Optional[int] = None
    
    # Valores
    valor_total: float = 0.0
    valor_principal: float = 0.0
    valor_multa: float = 0.0
    valor_juros: float = 0.0
    
    # Datas
    data_vencimento: Optional[date] = None
    data_transmissao: Optional[datetime] = None
    
    # Identificação do documento
    numero_recibo: Optional[str] = None
    situacao: str = ""  # "Transmitida", "Em Processamento", etc.
    tipo_declaracao: str = "DCTFWeb"  # "DCTFWeb", "DCTFWeb Anual", etc.
    
    # Metadados
    raw_text: str = ""
    extraction_confidence: float = 0.0
    extraction_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "periodo_apuracao": self.periodo_apuracao,
            "ano": self.ano,
            "mes": self.mes,
            "valor_total": self.valor_total,
            "valor_principal": self.valor_principal,
            "valor_multa": self.valor_multa,
            "valor_juros": self.valor_juros,
            "data_vencimento": self.data_vencimento.isoformat() if self.data_vencimento else None,
            "data_transmissao": self.data_transmissao.isoformat() if self.data_transmissao else None,
            "numero_recibo": self.numero_recibo,
            "situacao": self.situacao,
            "tipo_declaracao": self.tipo_declaracao,
            "extraction_confidence": self.extraction_confidence,
            "extraction_errors": self.extraction_errors
        }


class DCTFWebParser:
    """
    Parser para extração de dados de PDFs DCTFWeb
    
    Suporta:
    - Recibos de transmissão
    - Declarações completas
    - DARF numerados
    """
    
    # Padrões regex para extração
    PATTERNS = {
        "cnpj": [
            r"CNPJ[:\s]+([0-9]{2}[.][0-9]{3}[.][0-9]{3}[/][0-9]{4}[-][0-9]{2})",
            r"([0-9]{2}[.][0-9]{3}[.][0-9]{3}[/][0-9]{4}[-][0-9]{2})",
            r"([0-9]{14})",  # CNPJ sem formatação
        ],
        "periodo": [
            r"Per[íí]odo\s*(?:de\s*)?Apura[çc][ãa]o[:\s]*([0-9]{2}[/][0-9]{4})",
            r"Compet[êe]ncia[:\s]*([0-9]{2}[/][0-9]{4})",
            r"([0-9]{2}[/][0-9]{4})",
        ],
        "valor_total": [
            r"Valor\s*Total[:\s]*R?\$?\s*([0-9.,]+)",
            r"Total\s*(?:a\s*)?(?:Recolher|Pagar)[:\s]*R?\$?\s*([0-9.,]+)",
            r"TOTAL[:\s]*R?\$?\s*([0-9.,]+)",
        ],
        "vencimento": [
            r"Vencimento[:\s]*([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
            r"Data\s*(?:de\s*)?Vencimento[:\s]*([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
            r"Vence\s*em[:\s]*([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
        ],
        "recibo": [
            r"N[úu]mero\s*(?:do\s*)?Recibo[:\s]*([A-Z0-9.-]+)",
            r"Recibo[:\s]*([A-Z0-9.-]+)",
            r"Protocolo[:\s]*([A-Z0-9.-]+)",
        ],
        "razao_social": [
            r"Raz[ãa]o\s*Social[:\s]*([^\n]+)",
            r"Nome\s*Empresarial[:\s]*([^\n]+)",
            r"Contribuinte[:\s]*([^\n]+)",
        ],
        "situacao": [
            r"Situa[çc][ãa]o[:\s]*(Transmitida|Em Processamento|Aceita|Rejeitada|Retificadora)",
            r"Status[:\s]*(Transmitida|Em Processamento|Aceita|Rejeitada|Retificadora)",
        ]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_file(self, file_path: Path) -> DCTFWebData:
        """
        Extrai dados de um arquivo PDF DCTFWeb
        
        Args:
            file_path: Caminho para o arquivo PDF
            
        Returns:
            DCTFWebData com os dados extraídos
        """
        self.logger.info(f"Iniciando parsing de: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                text = self._extract_text(pdf)
                return self._parse_text(text)
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF {file_path}: {e}")
            raise PDFParsingError(f"Falha ao processar PDF: {e}")
    
    def parse_bytes(self, pdf_bytes: bytes) -> DCTFWebData:
        """
        Extrai dados de bytes de um PDF DCTFWeb
        
        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            
        Returns:
            DCTFWebData com os dados extraídos
        """
        self.logger.info("Iniciando parsing de PDF (bytes)")
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = self._extract_text(pdf)
                return self._parse_text(text)
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF: {e}")
            raise PDFParsingError(f"Falha ao processar PDF: {e}")
    
    def _extract_text(self, pdf) -> str:
        """
        Extrai texto de todas as páginas do PDF
        """
        text_parts = []
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        
        return "\n".join(text_parts)
    
    def _parse_text(self, text: str) -> DCTFWebData:
        """
        Processa o texto extraído e identifica os campos
        """
        data = DCTFWebData(
            cnpj="",
            raw_text=text[:5000]  # Limitar tamanho do texto armazenado
        )
        
        extraction_success = 0
        total_fields = 6  # Campos principais
        
        # Extrair CNPJ
        cnpj = self._extract_field(text, self.PATTERNS["cnpj"])
        if cnpj:
            data.cnpj = self._normalize_cnpj(cnpj)
            extraction_success += 1
        else:
            data.extraction_errors.append("CNPJ não encontrado")
        
        # Extrair período de apuração
        periodo = self._extract_field(text, self.PATTERNS["periodo"])
        if periodo:
            data.periodo_apuracao = periodo
            try:
                mes, ano = periodo.split("/")
                data.mes = int(mes)
                data.ano = int(ano)
                extraction_success += 1
            except:
                data.extraction_errors.append("Período em formato inválido")
        else:
            data.extraction_errors.append("Período de apuração não encontrado")
        
        # Extrair valor total
        valor = self._extract_field(text, self.PATTERNS["valor_total"])
        if valor:
            data.valor_total = self._parse_valor(valor)
            extraction_success += 1
        else:
            data.extraction_errors.append("Valor total não encontrado")
        
        # Extrair data de vencimento
        vencimento = self._extract_field(text, self.PATTERNS["vencimento"])
        if vencimento:
            try:
                data.data_vencimento = datetime.strptime(vencimento, "%d/%m/%Y").date()
                extraction_success += 1
            except ValueError:
                data.extraction_errors.append("Data de vencimento em formato inválido")
        else:
            data.extraction_errors.append("Data de vencimento não encontrada")
        
        # Extrair número do recibo
        recibo = self._extract_field(text, self.PATTERNS["recibo"])
        if recibo:
            data.numero_recibo = recibo.strip()
            extraction_success += 1
        
        # Extrair razão social
        razao = self._extract_field(text, self.PATTERNS["razao_social"])
        if razao:
            data.razao_social = razao.strip()[:200]  # Limitar tamanho
            extraction_success += 1
        
        # Extrair situação
        situacao = self._extract_field(text, self.PATTERNS["situacao"])
        if situacao:
            data.situacao = situacao
        
        # Identificar tipo de declaração
        data.tipo_declaracao = self._identify_tipo(text)
        
        # Calcular confiança da extração
        data.extraction_confidence = (extraction_success / total_fields) * 100
        
        self.logger.info(
            f"Parsing concluído: CNPJ={data.cnpj}, Período={data.periodo_apuracao}, "
            f"Valor={data.valor_total}, Confiança={data.extraction_confidence:.1f}%"
        )
        
        return data
    
    def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Tenta extrair um campo usando múltiplos padrões
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _normalize_cnpj(self, cnpj: str) -> str:
        """
        Normaliza CNPJ para formato XX.XXX.XXX/XXXX-XX
        """
        # Remover caracteres não numéricos
        digits = re.sub(r"[^0-9]", "", cnpj)
        
        if len(digits) != 14:
            return cnpj  # Retornar original se não tiver 14 dígitos
        
        # Formatar
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    
    def _parse_valor(self, valor_str: str) -> float:
        """
        Converte string de valor monetário para float
        """
        # Remover R$ e espaços
        valor = valor_str.replace("R$", "").strip()
        
        # Lidar com formato brasileiro (1.234,56)
        if "," in valor and "." in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif "," in valor:
            valor = valor.replace(",", ".")
        
        try:
            return float(valor)
        except ValueError:
            return 0.0
    
    def _identify_tipo(self, text: str) -> str:
        """
        Identifica o tipo de declaração DCTFWeb
        """
        text_lower = text.lower()
        
        if "anual" in text_lower:
            return "DCTFWeb Anual"
        elif "13" in text_lower or "décimo terceiro" in text_lower:
            return "DCTFWeb 13º"
        elif "retificadora" in text_lower:
            return "DCTFWeb Retificadora"
        else:
            return "DCTFWeb Mensal"
