"""Schemas Pydantic para Guias de Pagamento"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TipoGuia(str, Enum):
    """Tipos de guias"""
    DARF = "darf"
    GPS = "gps"
    GRF = "grf"
    DAS = "das"
    DAE = "dae"
    OUTRO = "outro"


class StatusGuia(str, Enum):
    """Status da guia"""
    PENDENTE = "pendente"
    PAGA = "paga"
    VENCIDA = "vencida"
    CANCELADA = "cancelada"


class GuiaBase(BaseModel):
    """Schema base para guia"""
    tipo: TipoGuia = Field(..., description="Tipo da guia")
    empresa_id: str = Field(..., description="ID da empresa")
    cnpj: str = Field(..., description="CNPJ")
    codigo_receita: Optional[str] = Field(default=None, description="Código da receita")
    numero_referencia: Optional[str] = Field(default=None, description="Número de referência")
    periodo_apuracao: str = Field(..., description="Período de apuração (MM/YYYY)")
    data_vencimento: date = Field(..., description="Data de vencimento")
    valor_principal: float = Field(..., description="Valor principal")
    valor_multa: float = Field(default=0.0, description="Valor da multa")
    valor_juros: float = Field(default=0.0, description="Valor dos juros")
    valor_total: float = Field(..., description="Valor total")
    observacoes: Optional[str] = Field(default=None, description="Observações")


class GuiaCreate(GuiaBase):
    """Schema para criação de guia"""
    pass


class GuiaUpdate(BaseModel):
    """Schema para atualização de guia"""
    status: Optional[StatusGuia] = None
    data_pagamento: Optional[date] = None
    valor_pago: Optional[float] = None
    comprovante_path: Optional[str] = None
    observacoes: Optional[str] = None



class GuiaResponse(GuiaBase):
    id: str = Field(..., description="ID único da guia")
    entity_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime] = None
    previous_version_id: Optional[str] = None
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: StatusGuia = Field(default=StatusGuia.PENDENTE)
    data_pagamento: Optional[date] = None
    valor_pago: Optional[float] = None
    comprovante_path: Optional[str] = None

    class Config:
        from_attributes = True


class GuiaListResponse(BaseModel):
    """Schema de resposta para lista de guias"""
    guias: List[GuiaResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20
