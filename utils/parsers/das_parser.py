"""
Parser de PDFs do DAS (Documento de Arrecadação do Simples Nacional)
Extrai dados estruturados de guias DAS

Dados extraídos:
- CNPJ do contribuinte
- Período de apuração
- Valor total
- Data de vencimento
- Código de barras/linha digitável
"""

import pdfplumber
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import io

from .dctfweb_parser import PDFParsingError

logger = logging.getLogger(__name__)


@dataclass
class DASData:
    """Dados extraídos de um PDF DAS"""
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
    data_emissao: Optional[datetime] = None
    
    # Código de pagamento
    linha_digitavel: Optional[str] = None
    codigo_barras: Optional[str] = None
    
    # Anexo do Simples (I, II, III, IV, V)
    anexo_simples: Optional[str] = None
    
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
            "data_emissao": self.data_emissao.isoformat() if self.data_emissao else None,
            "linha_digitavel": self.linha_digitavel,
            "codigo_barras": self.codigo_barras,
            "anexo_simples": self.anexo_simples,
            "extraction_confidence": self.extraction_confidence,
            "extraction_errors": self.extraction_errors
        }


class DASParser:
    """
    Parser para extração de dados de PDFs do DAS
    """
    
    PATTERNS = {
        "cnpj": [
            r"CNPJ[:\s]+([0-9]{2}[.][0-9]{3}[.][0-9]{3}[/][0-9]{4}[-][0-9]{2})",
            r"([0-9]{2}[.][0-9]{3}[.][0-9]{3}[/][0-9]{4}[-][0-9]{2})",
        ],
        "periodo": [
            r"Per[íí]odo\s*(?:de\s*)?Apura[çc][ãa]o[:\s]*([0-9]{2}[/][0-9]{4})",
            r"Compet[êe]ncia[:\s]*([0-9]{2}[/][0-9]{4})",
            r"PA[:\s]*([0-9]{2}[/][0-9]{4})",
        ],
        "valor_total": [
            r"Valor\s*(?:Total|do\s*Documento)[:\s]*R?\$?\s*([0-9.,]+)",
            r"TOTAL[:\s]*R?\$?\s*([0-9.,]+)",
        ],
        "vencimento": [
            r"Vencimento[:\s]*([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
            r"Data\s*(?:de\s*)?Vencimento[:\s]*([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
        ],
        "linha_digitavel": [
            r"([0-9]{5}[.][0-9]{5}\s*[0-9]{5}[.][0-9]{6}\s*[0-9]{5}[.][0-9]{6}\s*[0-9]\s*[0-9]{14})",
            r"([0-9]{47,48})",
        ],
        "anexo": [
            r"Anexo\s*([IVX]+)",
            r"ANEXO\s*([IVX]+)",
        ],
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_file(self, file_path: Path) -> DASData:
        """Extrai dados de um arquivo PDF DAS"""
        self.logger.info(f"Iniciando parsing de DAS: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                text = self._extract_text(pdf)
                return self._parse_text(text)
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF {file_path}: {e}")
            raise PDFParsingError(f"Falha ao processar PDF DAS: {e}")
    
    def parse_bytes(self, pdf_bytes: bytes) -> DASData:
        """Extrai dados de bytes de um PDF DAS"""
        self.logger.info("Iniciando parsing de DAS (bytes)")
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = self._extract_text(pdf)
                return self._parse_text(text)
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF DAS: {e}")
            raise PDFParsingError(f"Falha ao processar PDF DAS: {e}")
    
    def _extract_text(self, pdf) -> str:
        text_parts = []
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        return "\n".join(text_parts)
    
    def _parse_text(self, text: str) -> DASData:
        data = DASData(
            cnpj="",
            raw_text=text[:5000]
        )
        
        extraction_success = 0
        total_fields = 5
        
        # Extrair CNPJ
        cnpj = self._extract_field(text, self.PATTERNS["cnpj"])
        if cnpj:
            data.cnpj = self._normalize_cnpj(cnpj)
            extraction_success += 1
        
        # Extrair período
        periodo = self._extract_field(text, self.PATTERNS["periodo"])
        if periodo:
            data.periodo_apuracao = periodo
            try:
                mes, ano = periodo.split("/")
                data.mes = int(mes)
                data.ano = int(ano)
                extraction_success += 1
            except:
                pass
        
        # Extrair valor
        valor = self._extract_field(text, self.PATTERNS["valor_total"])
        if valor:
            data.valor_total = self._parse_valor(valor)
            extraction_success += 1
        
        # Extrair vencimento
        vencimento = self._extract_field(text, self.PATTERNS["vencimento"])
        if vencimento:
            try:
                data.data_vencimento = datetime.strptime(vencimento, "%d/%m/%Y").date()
                extraction_success += 1
            except:
                pass
        
        # Extrair linha digitável
        linha = self._extract_field(text, self.PATTERNS["linha_digitavel"])
        if linha:
            data.linha_digitavel = re.sub(r"\s+", "", linha)
            extraction_success += 1
        
        # Extrair anexo
        anexo = self._extract_field(text, self.PATTERNS["anexo"])
        if anexo:
            data.anexo_simples = anexo
        
        data.extraction_confidence = (extraction_success / total_fields) * 100
        return data
    
    def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _normalize_cnpj(self, cnpj: str) -> str:
        digits = re.sub(r"[^0-9]", "", cnpj)
        if len(digits) != 14:
            return cnpj
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    
    def _parse_valor(self, valor_str: str) -> float:
        valor = valor_str.replace("R$", "").strip()
        if "," in valor and "." in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif "," in valor:
            valor = valor.replace(",", ".")
        try:
            return float(valor)
        except ValueError:
            return 0.0
