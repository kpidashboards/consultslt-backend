"""
Engine de OCR e Classificação de Documentos (Paridade Kolossus)
Processa imagens e PDFs para extração de dados fiscais
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import re
import logging
import random

logger = logging.getLogger(__name__)

# Tentar importar bibliotecas opcionais
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class TipoDocumentoFiscal:
    """Tipos de documentos fiscais reconhecidos"""
    NFE = "nfe"
    NFSE = "nfse"
    CTE = "cte"
    DARF = "darf"
    DAS = "das"
    GPS = "gps"
    DCTFWEB = "dctfweb"
    CERTIDAO = "certidao"
    BOLETO = "boleto"
    EXTRATO = "extrato"
    DESCONHECIDO = "desconhecido"


# Padrões para classificação de documentos
PADROES_CLASSIFICACAO = {
    TipoDocumentoFiscal.NFE: [
        r"nota\s*fiscal\s*eletr[oô]nica",
        r"nf-?e",
        r"chave\s*de\s*acesso.*[0-9]{44}",
        r"danfe"
    ],
    TipoDocumentoFiscal.NFSE: [
        r"nota\s*fiscal\s*de\s*servi[cç]o",
        r"nfs-?e",
        r"iss\s*retido"
    ],
    TipoDocumentoFiscal.CTE: [
        r"conhecimento\s*de\s*transporte",
        r"ct-?e",
        r"dacte"
    ],
    TipoDocumentoFiscal.DARF: [
        r"documento\s*de\s*arrecada[cç][aã]o.*receita",
        r"darf",
        r"c[oó]digo\s*da\s*receita"
    ],
    TipoDocumentoFiscal.DAS: [
        r"documento\s*de\s*arrecada[cç][aã]o.*simples",
        r"simples\s*nacional",
        r"\bdas\b"
    ],
    TipoDocumentoFiscal.GPS: [
        r"guia\s*da\s*previd[eê]ncia\s*social",
        r"\bgps\b",
        r"inss"
    ],
    TipoDocumentoFiscal.DCTFWEB: [
        r"dctfweb",
        r"dctf-?web",
        r"declara[cç][aã]o.*d[eé]bitos.*tribut[aá]rios"
    ],
    TipoDocumentoFiscal.CERTIDAO: [
        r"certid[aã]o\s*negativa",
        r"cnd",
        r"regularidade\s*fiscal"
    ]
}

# Padrões para extração de dados
PADROES_EXTRACAO = {
    "cnpj": r"([0-9]{2}[.][0-9]{3}[.][0-9]{3}[/][0-9]{4}[-][0-9]{2})",
    "cpf": r"([0-9]{3}[.][0-9]{3}[.][0-9]{3}[-][0-9]{2})",
    "valor": r"(?:R\$|BRL)\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2}))",
    "data": r"([0-9]{2}[/][0-9]{2}[/][0-9]{4})",
    "chave_nfe": r"([0-9]{44})",
    "codigo_barras": r"([0-9]{47,48})",
    "ncm": r"NCM[:\s]*([0-9]{8})",
    "cfop": r"CFOP[:\s]*([0-9]{4})"
}


class OCREngine:
    """
    Engine para processamento OCR de documentos fiscais
    
    Funcionalidades:
    - Extração de texto de imagens e PDFs
    - Classificação automática de tipo de documento
    - Extração estruturada de dados (CNPJ, valores, datas)
    - Validação de dados extraídos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def processar_documento(
        self,
        arquivo_path: str,
        tipo_esperado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa um documento completo (OCR + Classificação + Extração)
        
        Args:
            arquivo_path: Caminho do arquivo (PDF ou imagem)
            tipo_esperado: Tipo esperado (se conhecido)
            
        Returns:
            Dict com tipo, dados extraídos e score de confiança
        """
        self.logger.info(f"Processando documento: {arquivo_path}")
        
        # 1. Extrair texto
        texto = self._extrair_texto(arquivo_path)
        
        # 2. Classificar documento
        tipo, score_classificacao = self._classificar_documento(texto, tipo_esperado)
        
        # 3. Extrair dados estruturados
        dados = self._extrair_dados(texto, tipo)
        
        # 4. Validar dados
        validacoes = self._validar_dados(dados)
        
        # Score de confiança geral
        score_confianca = self._calcular_score_confianca(
            score_classificacao, dados, validacoes
        )
        
        resultado = {
            "arquivo": arquivo_path,
            "tipo": tipo,
            "score_confianca": score_confianca,
            "dados_extraidos": dados,
            "validacoes": validacoes,
            "processado_em": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"Documento processado: Tipo={tipo}, Confiança={score_confianca}%"
        )
        
        return resultado
    
    def _extrair_texto(self, arquivo_path: str) -> str:
        """
        Extrai texto de arquivo (PDF ou imagem)
        """
        path = Path(arquivo_path)
        extensao = path.suffix.lower()
        
        # Para arquivos PDF
        if extensao == ".pdf" and HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(arquivo_path) as pdf:
                    texto = "\n".join(
                        page.extract_text() or "" 
                        for page in pdf.pages
                    )
                return texto
            except Exception as e:
                self.logger.warning(f"Erro ao extrair texto do PDF: {e}")
        
        # Para imagens - precisaria de Tesseract
        # Por ora, retorna texto mock para simulação
        return self._simular_texto_ocr(arquivo_path)
    
    def _simular_texto_ocr(self, arquivo_path: str) -> str:
        """
        Simula extração OCR para demonstração
        Na implementação real, usaria Tesseract ou serviço de OCR
        """
        nome_arquivo = Path(arquivo_path).name.lower()
        
        # Simular conteúdo baseado no nome do arquivo
        if "nfe" in nome_arquivo or "nota" in nome_arquivo:
            return """
            NOTA FISCAL ELETRÔNICA
            NF-e Nº 001234
            Chave de Acesso: 35250112345678000100550010001234561234567890
            CNPJ Emitente: 12.345.678/0001-00
            Data Emissão: 26/12/2025
            Valor Total: R$ 1.500,00
            ICMS: R$ 270,00
            NCM: 84715010
            CFOP: 5102
            """
        elif "das" in nome_arquivo or "simples" in nome_arquivo:
            return """
            DOCUMENTO DE ARRECADAÇÃO DO SIMPLES NACIONAL
            DAS
            CNPJ: 12.345.678/0001-00
            Período de Apuração: 12/2025
            Data Vencimento: 20/01/2026
            Valor Total: R$ 850,00
            Código de Barras: 85890000008500000000000000012345678901234567
            """
        elif "dctf" in nome_arquivo:
            return """
            DCTFWeb
            Declaração de Débitos e Créditos Tributários Federais
            CNPJ: 12.345.678/0001-00
            Período: 12/2025
            Valor Total Devido: R$ 5.430,00
            Data Transmissão: 15/01/2026
            Recibo: DCTF-2025-12-ABC123
            """
        elif "certidao" in nome_arquivo or "cnd" in nome_arquivo:
            return """
            CERTIDÃO NEGATIVA DE DÉBITOS
            CND
            CNPJ: 12.345.678/0001-00
            Razão Social: EMPRESA EXEMPLO LTDA
            Situação: REGULAR
            Data Emissão: 20/12/2025
            Validade: 20/06/2026
            """
        else:
            # Documento genérico
            return f"""
            DOCUMENTO FISCAL
            Arquivo: {nome_arquivo}
            CNPJ: 12.345.678/0001-00
            Data: 26/12/2025
            Valor: R$ {random.uniform(100, 10000):.2f}
            """
    
    def _classificar_documento(
        self,
        texto: str,
        tipo_esperado: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Classifica o tipo de documento baseado no texto
        
        Returns:
            Tuple com (tipo, score de confiança)
        """
        if tipo_esperado:
            return tipo_esperado, 100.0
        
        texto_lower = texto.lower()
        scores = {}
        
        for tipo, padroes in PADROES_CLASSIFICACAO.items():
            score = 0
            for padrao in padroes:
                if re.search(padrao, texto_lower):
                    score += 25  # Cada padrão encontrado adiciona 25%
            scores[tipo] = min(score, 100)  # Máximo 100%
        
        if scores:
            melhor_tipo = max(scores, key=scores.get)
            if scores[melhor_tipo] > 0:
                return melhor_tipo, scores[melhor_tipo]
        
        return TipoDocumentoFiscal.DESCONHECIDO, 0.0
    
    def _extrair_dados(self, texto: str, tipo: str) -> Dict[str, Any]:
        """
        Extrai dados estruturados do texto
        """
        dados = {}
        
        # Extrair campos comuns
        for campo, padrao in PADROES_EXTRACAO.items():
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dados[campo] = match.group(1)
        
        # Normalizar CNPJ (remover formatação)
        if "cnpj" in dados:
            dados["cnpj_formatado"] = dados["cnpj"]
            dados["cnpj"] = re.sub(r"[^0-9]", "", dados["cnpj"])
        
        # Normalizar valor
        if "valor" in dados:
            valor_str = dados["valor"]
            # Converter formato brasileiro para float
            valor_str = valor_str.replace(".", "").replace(",", ".")
            try:
                dados["valor_float"] = float(valor_str)
            except:
                pass
        
        # Campos específicos por tipo
        if tipo == TipoDocumentoFiscal.NFE:
            dados["tipo_documento"] = "Nota Fiscal Eletrônica"
            # Extrair número da NF
            match = re.search(r"n[f]?-?e?\s*n[º°]?\s*([0-9]+)", texto.lower())
            if match:
                dados["numero_nf"] = match.group(1)
                
        elif tipo == TipoDocumentoFiscal.DAS:
            dados["tipo_documento"] = "DAS - Simples Nacional"
            # Extrair período
            match = re.search(r"per[ií]odo.*?([0-9]{2}/[0-9]{4})", texto.lower())
            if match:
                dados["periodo_apuracao"] = match.group(1)
        
        return dados
    
    def _validar_dados(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida os dados extraídos
        """
        validacoes = {
            "cnpj_valido": False,
            "valor_positivo": False,
            "data_valida": False
        }
        
        # Validar CNPJ
        if "cnpj" in dados:
            validacoes["cnpj_valido"] = self._validar_cnpj(dados["cnpj"])
        
        # Validar valor
        if dados.get("valor_float"):
            validacoes["valor_positivo"] = dados["valor_float"] > 0
        
        # Validar data
        if "data" in dados:
            validacoes["data_valida"] = self._validar_data(dados["data"])
        
        return validacoes
    
    def _validar_cnpj(self, cnpj: str) -> bool:
        """
        Valida dígitos verificadores do CNPJ
        """
        cnpj = re.sub(r"[^0-9]", "", cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Verifica sequências inválidas
        if cnpj == cnpj[0] * 14:
            return False
        
        # Cálculo dos dígitos verificadores
        def calc_digito(cnpj, peso):
            soma = sum(int(d) * p for d, p in zip(cnpj, peso))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        peso2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        d1 = calc_digito(cnpj[:12], peso1)
        d2 = calc_digito(cnpj[:12] + str(d1), peso2)
        
        return cnpj[-2:] == f"{d1}{d2}"
    
    def _validar_data(self, data_str: str) -> bool:
        """
        Valida se a data está no formato correto
        """
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except:
            return False
    
    def _calcular_score_confianca(
        self,
        score_classificacao: float,
        dados: Dict[str, Any],
        validacoes: Dict[str, Any]
    ) -> float:
        """
        Calcula score de confiança geral do processamento
        """
        # Base: score de classificação (peso 40%)
        score = score_classificacao * 0.4
        
        # Dados extraídos (peso 30%)
        campos_importantes = ["cnpj", "valor", "data"]
        campos_encontrados = sum(1 for c in campos_importantes if c in dados)
        score += (campos_encontrados / len(campos_importantes)) * 30
        
        # Validações (peso 30%)
        validacoes_ok = sum(1 for v in validacoes.values() if v)
        if validacoes:
            score += (validacoes_ok / len(validacoes)) * 30
        
        return round(min(score, 100), 2)
