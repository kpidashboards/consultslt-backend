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
    DARF = "darf"
    ECD = "ecd"
    ECF = "ecf"
    SPED_FISCAL = "sped_fiscal"
    SPED_CONTRIBUICOES = "sped_contribuicoes"
    DIRF = "dirf"
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
    """Schema de resposta para obrigação"""
    id: str = Field(..., description="ID único da obrigação")
    status: StatusObrigacao = Field(default=StatusObrigacao.PENDENTE)
    prioridade: PrioridadeObrigacao = Field(default=PrioridadeObrigacao.NORMAL)
    
    # Valores
    valor: float = Field(default=0.0)
    valor_pago: float = Field(default=0.0)
    
    # Datas
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    
    # Relacionamentos
    documento_ids: List[str] = Field(default_factory=list)
    empresa_nome: Optional[str] = None
    
    # Metadados
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    observacoes: Optional[str] = None
    
    class Config:
        from_attributes = True


class ObrigacaoListResponse(BaseModel):
    """Schema de resposta para lista de obrigações"""
    obrigacoes: List[ObrigacaoResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20
