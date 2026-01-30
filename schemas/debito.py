"""Schemas Pydantic para Débitos"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TipoDebito(str, Enum):
    """Tipos de débitos"""
    TRIBUTO = "tributo"
    CONTRIBUICAO = "contribuicao"
    MULTA = "multa"
    PARCELAMENTO = "parcelamento"
    OUTRO = "outro"


class StatusDebito(str, Enum):
    """Status do débito"""
    ABERTO = "aberto"
    PARCELADO = "parcelado"
    QUITADO = "quitado"
    PRESCRITO = "prescrito"
    EM_DISCUSSAO = "em_discussao"


class DebitoBase(BaseModel):
    """Schema base para débito"""
    tipo: TipoDebito = Field(..., description="Tipo do débito")
    empresa_id: str = Field(..., description="ID da empresa")
    cnpj: str = Field(..., description="CNPJ")
    descricao: str = Field(..., description="Descrição do débito")
    numero_processo: Optional[str] = Field(default=None, description="Número do processo/auto")
    orgao_credor: str = Field(..., description="Órgão credor")
    data_inscricao: date = Field(..., description="Data de inscrição")
    valor_principal: float = Field(..., description="Valor principal")
    valor_multa: float = Field(default=0.0, description="Valor da multa")
    valor_juros: float = Field(default=0.0, description="Valor dos juros")
    valor_total: float = Field(..., description="Valor total atualizado")
    observacoes: Optional[str] = Field(default=None, description="Observações")


class DebitoCreate(DebitoBase):
    """Schema para criação de débito"""
    pass


class DebitoUpdate(BaseModel):
    """Schema para atualização de débito"""
    status: Optional[StatusDebito] = None
    valor_total: Optional[float] = None
    data_quitacao: Optional[date] = None
    observacoes: Optional[str] = None


class DebitoResponse(DebitoBase):
    """Schema de resposta para débito"""
    id: str = Field(..., description="ID único do débito")
    status: StatusDebito = Field(default=StatusDebito.ABERTO)
    data_quitacao: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DebitoListResponse(BaseModel):
    """Schema de resposta para lista de débitos"""
    debitos: List[DebitoResponse]
    total: int
    valor_total_aberto: float
    quantidade_abertos: int
    pagina: int = 1
    por_pagina: int = 20
