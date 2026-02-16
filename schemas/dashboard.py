"""
Schemas Pydantic para Dashboard e KPIs
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ===============================
# ENUMS
# ===============================
class PrioridadeEnum(str, Enum):
    CRITICA = "critica"
    ALTA = "alta"
    NORMAL = "normal"
    BAIXA = "baixa"


# ===============================
# PROXIMOS VENCIMENTOS
# ===============================
class ProximoVencimento(BaseModel):
    """Representa um vencimento próximo"""
    empresa_id: str = Field(..., description="ID da empresa")
    empresa_nome: str = Field(..., description="Nome da empresa")
    tipo: str = Field(..., description="Tipo de obrigação (DAS, DCTF, Certidão, etc)")
    data_vencimento: datetime = Field(..., description="Data do vencimento")
    prioridade: PrioridadeEnum = Field(default="normal", description="Nível de prioridade")
    dias_restantes: Optional[int] = Field(None, description="Dias até vencimento")


# ===============================
# ATIVIDADES RECENTES
# ===============================
class AtividadeRecente(BaseModel):
    """Representa uma atividade recente no sistema"""
    id: Optional[str] = Field(None, description="ID da atividade")
    acao: str = Field(..., description="Ação realizada (DAS gerado, Certidão emitida, etc)")
    empresa_id: str = Field(..., description="ID da empresa")
    empresa_nome: str = Field(..., description="Nome da empresa")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data/hora da atividade")
    usuario_id: Optional[str] = Field(None, description="ID do usuário que realizou ação")
    detalhes: Optional[dict] = Field(None, description="Detalhes adicionais da atividade")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===============================
# DASHBOARD METRIC (PRINCIPAL)
# ===============================
class DashboardMetricBase(BaseModel):
    """Base para métricas do dashboard"""
    empresas_ativas: int = Field(default=0, description="Total de empresas ativas")
    empresas_inativas: int = Field(default=0, description="Total de empresas inativas")
    das_gerados_mes: int = Field(default=0, description="DAS gerados este mês")
    certidoes_emitidas_mes: int = Field(default=0, description="Certidões emitidas este mês")
    alertas_criticos: int = Field(default=0, description="Alertas críticos pendentes")
    taxa_conformidade: float = Field(default=0.0, description="Taxa de conformidade (%)")
    receita_bruta_mes: float = Field(default=0.0, description="Receita bruta mês atual")
    despesa_mensal: float = Field(default=0.0, description="Despesa mensal")
    obrigacoes_pendentes: int = Field(default=0, description="Total de obrigações pendentes")
    proximos_vencimentos: List[ProximoVencimento] = Field(default_factory=list, description="Lista dos próximos vencimentos")
    atividades_recentes: List[AtividadeRecente] = Field(default_factory=list, description="Últimas atividades")
    data_geracao: datetime = Field(default_factory=datetime.utcnow, description="Data/hora de geração da métrica")


class DashboardMetric(DashboardMetricBase):
    """Métrica completa com ID do MongoDB"""
    id: Optional[str] = Field(None, alias="_id", description="ID da métrica no MongoDB")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardMetricCreate(DashboardMetricBase):
    """Schema para criação de nova métrica"""
    pass


class DashboardMetricUpdate(BaseModel):
    """Schema para atualização de métrica (todos os campos opcionais)"""
    empresas_ativas: Optional[int] = None
    empresas_inativas: Optional[int] = None
    das_gerados_mes: Optional[int] = None
    certidoes_emitidas_mes: Optional[int] = None
    alertas_criticos: Optional[int] = None
    taxa_conformidade: Optional[float] = None
    receita_bruta_mes: Optional[float] = None
    despesa_mensal: Optional[float] = None
    obrigacoes_pendentes: Optional[int] = None
    proximos_vencimentos: Optional[List[ProximoVencimento]] = None
    atividades_recentes: Optional[List[AtividadeRecente]] = None


# ===============================
# OVERVIEW (LEITURA SIMPLES)
# ===============================
class DashboardOverview(BaseModel):
    """Visão simplificada para o dashboard inicial"""
    total_empresas: int
    empresas_ativas: int
    empresas_inativas: int
    das_gerados_mes: int
    certidoes_emitidas_mes: int
    alertas_criticos: int
    taxa_conformidade: float
    obrigacoes_pendentes: int
    ultima_atualizacao: datetime


# ===============================
# SNAPSHOT (HISTÓRICO)
# ===============================
class DashboardSnapshot(BaseModel):
    """Snapshot histórico de métricas para comparação"""
    data: datetime = Field(default_factory=datetime.utcnow, description="Data do snapshot")
    metricas: DashboardMetric = Field(..., description="Métricas capturadas")
    alteracoes: Optional[dict] = Field(None, description="Alterações desde snapshot anterior")
