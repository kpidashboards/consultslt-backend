"""Schemas Pydantic para Alertas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoAlerta(str, Enum):
    """Tipos de alertas"""
    VENCIMENTO = "vencimento"
    OBRIGACAO = "obrigacao"
    CERTIDAO = "certidao"
    DOCUMENTO = "documento"
    SISTEMA = "sistema"
    OUTRO = "outro"


class PrioridadeAlerta(str, Enum):
    """Prioridade do alerta"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class StatusAlerta(str, Enum):
    """Status do alerta"""
    PENDENTE = "pendente"
    LIDO = "lido"
    RESOLVIDO = "resolvido"
    ARQUIVADO = "arquivado"


class AlertaBase(BaseModel):
    """Schema base para alerta"""
    tipo: TipoAlerta = Field(..., description="Tipo do alerta")
    prioridade: PrioridadeAlerta = Field(default=PrioridadeAlerta.MEDIA, description="Prioridade")
    titulo: str = Field(..., description="Título do alerta")
    mensagem: str = Field(..., description="Mensagem do alerta")
    empresa_id: Optional[str] = Field(default=None, description="ID da empresa relacionada")
    entidade_tipo: Optional[str] = Field(default=None, description="Tipo da entidade (obrigacao, documento, etc)")
    entidade_id: Optional[str] = Field(default=None, description="ID da entidade relacionada")


class AlertaCreate(AlertaBase):
    """Schema para criação de alerta"""
    pass


class AlertaUpdate(BaseModel):
    """Schema para atualização de alerta"""
    status: Optional[StatusAlerta] = None
    prioridade: Optional[PrioridadeAlerta] = None
    observacoes: Optional[str] = None


class AlertaResponse(AlertaBase):
    """Schema de resposta para alerta"""
    id: str = Field(..., description="ID único do alerta")
    status: StatusAlerta = Field(default=StatusAlerta.PENDENTE)
    lido_em: Optional[datetime] = None
    resolvido_em: Optional[datetime] = None
    observacoes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertaListResponse(BaseModel):
    """Schema de resposta para lista de alertas"""
    alertas: List[AlertaResponse]
    total: int
    nao_lidos: int
    pendentes: int
    pagina: int = 1
    por_pagina: int = 20
