"""
Schemas Pydantic para Obrigações Fiscais
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TipoObrigacao(str, Enum):
    """Tipos de obrigações fiscais"""
    DCTFWEB = "dctfweb"
    DAS = "das"
    DEFIS = "defis"
    DIMOB = "dimob"
    DMED = "dmed"
    EFD_REINF = "efd_reinf"
    IBGE = "ibge"
    SPED_ECD = "sped_ecd"
    SPED_ECF = "sped_ecf"
    DIRF = "dirf"
    DIRBI = "dirbi"
    GIA = "gia"
    CAGED = "caged"
    FGTS_DIGITAL = "fgts_digital"
    DITR = "ditr"
    ITR = "itr"
    EFD_CONTRIBUICOES = "efd_contribuicoes"
    EFD_ICMS_IPI = "efd_icms_ipi"
    DECLAN = "declan"
    DARF = "darf"
    ECD = "ecd"
    ECF = "ecf"
    SPED_FISCAL = "sped_fiscal"
    SPED_CONTRIBUICOES = "sped_contribuicoes"
    DCTF = "dctf"
    CERTIDAO = "certidao"
    OUTRO = "outro"


class StatusObrigacao(str, Enum):
    """Status da obrigação"""
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    ATRASADA = "atrasada"
    CANCELADA = "cancelada"


class PrioridadeObrigacao(str, Enum):
    """Prioridade da obrigação"""
    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    CRITICA = "critica"


class ObrigacaoBase(BaseModel):
    """Schema base para obrigação"""
    tipo: TipoObrigacao = Field(..., description="Tipo da obrigação")
    empresa_id: str = Field(..., description="ID da empresa")
    cnpj: str = Field(..., description="CNPJ da empresa")
    competencia: str = Field(..., description="Período de competência (MM/YYYY)")
    ano: int = Field(..., description="Ano da competência")
    mes: int = Field(..., description="Mês da competência")


class ObrigacaoCreate(ObrigacaoBase):
    """Schema para criação de obrigação"""
    valor: float = Field(default=0.0, description="Valor da obrigação")
    data_vencimento: Optional[date] = Field(default=None, description="Data de vencimento")
    observacoes: Optional[str] = None


class ObrigacaoUpdate(BaseModel):
    """Schema para atualização de obrigação"""
    status: Optional[StatusObrigacao] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    prioridade: Optional[PrioridadeObrigacao] = None
    observacoes: Optional[str] = None



class ObrigacaoResponse(ObrigacaoBase):
    id: str = Field(..., description="ID único da obrigação")
    entity_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime] = None
    previous_version_id: Optional[str] = None
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: StatusObrigacao = Field(default=StatusObrigacao.PENDENTE)
    prioridade: PrioridadeObrigacao = Field(default=PrioridadeObrigacao.NORMAL)
    valor: float = Field(default=0.0)
    valor_pago: float = Field(default=0.0)
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    documento_ids: List[str] = Field(default_factory=list)
    empresa_nome: Optional[str] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


class ObrigacaoListResponse(BaseModel):
    """Schema de resposta para lista de obrigações"""
    obrigacoes: List[ObrigacaoResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20
