"""
Engine de Processamento e Auditoria SPED (Paridade Kolossus)
Processa arquivos SPED Fiscal e Contribuições para auditoria e cruzamento
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import random

logger = logging.getLogger(__name__)


class TipoAuditoria(str, Enum):
    SPED_FISCAL = "SPED Fiscal"
    SPED_CONTRIBUICOES = "SPED Contribuições"
    CRUZAMENTO_NFE = "Cruzamento NF-e"
    CRUZAMENTO_ECAC = "Cruzamento e-CAC"


class Severidade(str, Enum):
    INFORMATIVO = "Informativo"
    AVISO = "Aviso"
    CRITICO = "Crítico"


@dataclass
class NaoConformidade:
    """Representa uma não conformidade encontrada na auditoria"""
    severidade: Severidade
    regra: str
    descricao: str
    referencia_documento: Optional[str] = None
    valor_envolvido: Optional[float] = None
    sugestao_correcao: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severidade": self.severidade.value,
            "regra": self.regra,
            "descricao": self.descricao,
            "referencia_documento": self.referencia_documento,
            "valor_envolvido": self.valor_envolvido,
            "sugestao_correcao": self.sugestao_correcao
        }


# Regras de Auditoria SPED Fiscal
REGRAS_SPED_FISCAL = [
    {
        "codigo": "SPED-F001",
        "descricao": "Registro de inventário obrigatório (H010)",
        "severidade": Severidade.CRITICO,
        "validacao": "Verificar existência de bloco H"
    },
    {
        "codigo": "SPED-F002",
        "descricao": "NCM inválido ou inexistente",
        "severidade": Severidade.AVISO,
        "validacao": "Validar NCMs dos produtos"
    },
    {
        "codigo": "SPED-F003",
        "descricao": "Divergência de alíquota ICMS",
        "severidade": Severidade.CRITICO,
        "validacao": "Comparar alíquota declarada vs tabela estadual"
    },
    {
        "codigo": "SPED-F004",
        "descricao": "CFOP incompatível com operação",
        "severidade": Severidade.AVISO,
        "validacao": "Verificar consistência CFOP x natureza operação"
    },
    {
        "codigo": "SPED-F005",
        "descricao": "Base de cálculo zerada com imposto maior que zero",
        "severidade": Severidade.CRITICO,
        "validacao": "BC_ICMS = 0 AND VL_ICMS > 0"
    }
]

# Regras de Auditoria SPED Contribuições
REGRAS_SPED_CONTRIBUICOES = [
    {
        "codigo": "SPED-C001",
        "descricao": "CST de PIS/COFINS inconsistente",
        "severidade": Severidade.AVISO,
        "validacao": "Verificar CST vs regime tributário"
    },
    {
        "codigo": "SPED-C002",
        "descricao": "Crédito indevido de PIS/COFINS",
        "severidade": Severidade.CRITICO,
        "validacao": "Verificar elegibilidade do crédito"
    },
    {
        "codigo": "SPED-C003",
        "descricao": "Receita não tributada sem justificativa",
        "severidade": Severidade.AVISO,
        "validacao": "Verificar natureza da receita isenta"
    }
]


class SPEDEngine:
    """
    Engine para processamento e auditoria de arquivos SPED
    Implementa validações e cruzamentos fiscais
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def auditar_sped(
        self,
        tipo: TipoAuditoria,
        arquivo_path: str
    ) -> List[NaoConformidade]:
        """
        Executa auditoria completa em arquivo SPED
        
        Args:
            tipo: Tipo de SPED (Fiscal ou Contribuições)
            arquivo_path: Caminho do arquivo SPED
            
        Returns:
            Lista de não conformidades encontradas
        """
        self.logger.info(f"Iniciando auditoria {tipo.value}: {arquivo_path}")
        
        # Na implementação real, aqui faria parse do arquivo SPED
        # Por ora, simula validações com resultados mock
        dados_sped = self._simular_parser_sped(arquivo_path)
        
        nao_conformidades = []
        
        # Selecionar regras baseado no tipo
        regras = REGRAS_SPED_FISCAL if tipo == TipoAuditoria.SPED_FISCAL else REGRAS_SPED_CONTRIBUICOES
        
        # Executar validações
        for regra in regras:
            resultado = self._validar_regra(regra, dados_sped)
            if resultado:
                nao_conformidades.append(resultado)
        
        self.logger.info(
            f"Auditoria concluída: {len(nao_conformidades)} não conformidades encontradas"
        )
        
        return nao_conformidades
    
    def _simular_parser_sped(self, arquivo_path: str) -> Dict[str, Any]:
        """
        Simula o parsing de um arquivo SPED
        Na implementação real, faria parse linha a linha do arquivo TXT
        """
        # Dados mock para simulação
        return {
            "cnpj": "12.345.678/0001-00",
            "periodo": "12/2025",
            "regime": "Lucro Real",
            "total_notas_entrada": random.randint(50, 200),
            "total_notas_saida": random.randint(100, 500),
            "valor_total_icms": random.uniform(10000, 100000),
            "valor_total_pis": random.uniform(5000, 50000),
            "valor_total_cofins": random.uniform(20000, 200000),
            "tem_bloco_h": random.choice([True, False]),
            "ncms_invalidos": random.randint(0, 5),
            "cfops_inconsistentes": random.randint(0, 3),
            "divergencias_aliquota": random.randint(0, 2),
            "creditos_suspeitos": random.randint(0, 4)
        }
    
    def _validar_regra(
        self,
        regra: Dict[str, Any],
        dados: Dict[str, Any]
    ) -> Optional[NaoConformidade]:
        """
        Valida uma regra específica contra os dados do SPED
        """
        codigo = regra["codigo"]
        
        # Simular validações específicas
        encontrou_problema = False
        detalhes = None
        
        if codigo == "SPED-F001" and not dados.get("tem_bloco_h", True):
            encontrou_problema = True
            detalhes = "Bloco H (Inventário) não encontrado no arquivo"
            
        elif codigo == "SPED-F002" and dados.get("ncms_invalidos", 0) > 0:
            encontrou_problema = True
            detalhes = f"{dados['ncms_invalidos']} NCMs inválidos encontrados"
            
        elif codigo == "SPED-F003" and dados.get("divergencias_aliquota", 0) > 0:
            encontrou_problema = True
            detalhes = f"{dados['divergencias_aliquota']} divergências de alíquota ICMS"
            
        elif codigo == "SPED-F004" and dados.get("cfops_inconsistentes", 0) > 0:
            encontrou_problema = True
            detalhes = f"{dados['cfops_inconsistentes']} CFOPs inconsistentes"
            
        elif codigo == "SPED-C002" and dados.get("creditos_suspeitos", 0) > 0:
            encontrou_problema = True
            detalhes = f"{dados['creditos_suspeitos']} créditos suspeitos identificados"
        
        if encontrou_problema:
            return NaoConformidade(
                severidade=regra["severidade"],
                regra=codigo,
                descricao=regra["descricao"],
                referencia_documento=detalhes,
                sugestao_correcao=f"Revisar e corrigir: {regra['validacao']}"
            )
        
        return None
    
    def cruzar_dados_fiscais(
        self,
        dados_sped: Dict[str, Any],
        dados_externos: Dict[str, Any]
    ) -> List[NaoConformidade]:
        """
        Cruza dados do SPED com fontes externas (e-CAC, NF-e, etc.)
        
        Args:
            dados_sped: Dados extraídos do arquivo SPED
            dados_externos: Dados de fontes externas (e-CAC, GIA, etc.)
            
        Returns:
            Lista de divergências encontradas
        """
        self.logger.info("Executando cruzamento de dados fiscais")
        
        divergencias = []
        
        # Cruzamento com e-CAC (pendências)
        if dados_externos.get("pendencia_ecac"):
            divergencias.append(NaoConformidade(
                severidade=Severidade.CRITICO,
                regra="CRUZ-001",
                descricao="Pendência identificada no e-CAC",
                referencia_documento="Consulta e-CAC",
                sugestao_correcao="Regularizar pendências junto à RFB"
            ))
        
        # Cruzamento de NF-e (total de entradas)
        total_nfe_recebidas = dados_externos.get("total_nfe_recebidas", 0)
        total_sped_entrada = dados_sped.get("total_notas_entrada", 0)
        
        if abs(total_nfe_recebidas - total_sped_entrada) > 5:
            divergencias.append(NaoConformidade(
                severidade=Severidade.AVISO,
                regra="CRUZ-002",
                descricao="Divergência entre NF-e recebidas e SPED",
                referencia_documento=f"NF-e: {total_nfe_recebidas} vs SPED: {total_sped_entrada}",
                sugestao_correcao="Verificar notas não escrituradas ou canceladas"
            ))
        
        return divergencias
    
    def gerar_relatorio_auditoria(
        self,
        nao_conformidades: List[NaoConformidade],
        dados_sped: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gera relatório consolidado da auditoria
        """
        criticos = sum(1 for nc in nao_conformidades if nc.severidade == Severidade.CRITICO)
        avisos = sum(1 for nc in nao_conformidades if nc.severidade == Severidade.AVISO)
        informativos = sum(1 for nc in nao_conformidades if nc.severidade == Severidade.INFORMATIVO)
        
        # Score de conformidade (0 a 100)
        total = len(nao_conformidades)
        if total == 0:
            score = 100.0
        else:
            # Penalidades: Crítico = 10pts, Aviso = 5pts, Informativo = 1pt
            penalidade = (criticos * 10) + (avisos * 5) + (informativos * 1)
            score = max(0, 100 - penalidade)
        
        return {
            "cnpj": dados_sped.get("cnpj"),
            "periodo": dados_sped.get("periodo"),
            "data_auditoria": datetime.utcnow().isoformat(),
            "score_conformidade": round(score, 2),
            "total_nao_conformidades": total,
            "por_severidade": {
                "critico": criticos,
                "aviso": avisos,
                "informativo": informativos
            },
            "nao_conformidades": [nc.to_dict() for nc in nao_conformidades],
            "recomendacao_geral": self._gerar_recomendacao(score, criticos)
        }
    
    def _gerar_recomendacao(self, score: float, criticos: int) -> str:
        """Gera recomendação baseada no score e criticidade"""
        if score >= 90:
            return "Excelente conformidade. Manter monitoramento regular."
        elif score >= 70:
            return "Boa conformidade. Corrigir avisos identificados."
        elif score >= 50:
            return "Conformidade moderada. Priorizar correção de itens críticos."
        else:
            return "Conformidade baixa. AÇÃO URGENTE: Regularizar itens críticos imediatamente."
