"""Schemas Pydantic para Empresas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RegimeTributario(str, Enum):
    """Regimes tributários"""
    SIMPLES = "simples"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL = "lucro_real"
    MEI = "mei"


class EmpresaBase(BaseModel):
    """Schema base para empresa"""
    cnpj: str = Field(..., description="CNPJ da empresa")
    razao_social: str = Field(..., description="Razão social")
    nome_fantasia: Optional[str] = Field(default=None, description="Nome fantasia")
    regime_tributario: Optional[RegimeTributario] = Field(default=None, description="Regime tributário")
    inscricao_estadual: Optional[str] = Field(default=None, description="Inscrição estadual")
    inscricao_municipal: Optional[str] = Field(default=None, description="Inscrição municipal")
    endereco: Optional[str] = Field(default=None, description="Endereço completo")
    cidade: Optional[str] = Field(default=None, description="Cidade")
    estado: Optional[str] = Field(default=None, description="UF")
    cep: Optional[str] = Field(default=None, description="CEP")
    telefone: Optional[str] = Field(default=None, description="Telefone")
    email: Optional[str] = Field(default=None, description="Email")
    ativo: bool = Field(default=True, description="Se a empresa está ativa")


class EmpresaCreate(EmpresaBase):
    """Schema para criação de empresa"""
    pass


class EmpresaUpdate(BaseModel):
    """Schema para atualização de empresa"""
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    regime_tributario: Optional[RegimeTributario] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    ativo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    """Schema de resposta para empresa"""
    id: str = Field(..., description="ID único da empresa")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmpresaListResponse(BaseModel):
    """Schema de resposta para lista de empresas"""
    empresas: List[EmpresaResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20
