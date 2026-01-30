"""Schemas Pydantic para Certidões"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TipoCertidao(str, Enum):
    """Tipos de certidões"""
    FEDERAL = "federal"
    ESTADUAL = "estadual"
    MUNICIPAL = "municipal"
    FGTS = "fgts"
    TRABALHISTA = "trabalhista"
    CND = "cnd"
    OUTRO = "outro"


class StatusCertidao(str, Enum):
    """Status da certidão"""
    VALIDA = "valida"
    VENCIDA = "vencida"
    PROXIMA_VENCER = "proxima_vencer"
    PENDENTE = "pendente"


class CertidaoBase(BaseModel):
    """Schema base para certidão"""
    tipo: TipoCertidao = Field(..., description="Tipo da certidão")
    empresa_id: str = Field(..., description="ID da empresa")
    cnpj: str = Field(..., description="CNPJ")
    numero: Optional[str] = Field(default=None, description="Número da certidão")
    data_emissao: date = Field(..., description="Data de emissão")
    data_validade: date = Field(..., description="Data de validade")
    orgao_emissor: Optional[str] = Field(default=None, description="Órgão emissor")
    observacoes: Optional[str] = Field(default=None, description="Observações")


class CertidaoCreate(CertidaoBase):
    """Schema para criação de certidão"""
    pass


class CertidaoUpdate(BaseModel):
    """Schema para atualização de certidão"""
    numero: Optional[str] = None
    data_emissao: Optional[date] = None
    data_validade: Optional[date] = None
    arquivo_path: Optional[str] = None
    observacoes: Optional[str] = None


class CertidaoResponse(CertidaoBase):
    """Schema de resposta para certidão"""
    id: str = Field(..., description="ID único da certidão")
    status: StatusCertidao = Field(default=StatusCertidao.VALIDA)
    arquivo_path: Optional[str] = None
    dias_para_vencer: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CertidaoListResponse(BaseModel):
    """Schema de resposta para lista de certidões"""
    certidoes: List[CertidaoResponse]
    total: int
    validas: int
    vencidas: int
    proximas_vencer: int
    pagina: int = 1
    por_pagina: int = 20
