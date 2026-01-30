"""Schemas Pydantic para Configurações"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ConfiguracaoBase(BaseModel):
    """Schema base para configuração"""
    chave: str = Field(..., description="Chave da configuração")
    valor: Any = Field(..., description="Valor da configuração")
    descricao: Optional[str] = Field(default=None, description="Descrição")
    categoria: str = Field(default="geral", description="Categoria")


class ConfiguracaoCreate(ConfiguracaoBase):
    """Schema para criação de configuração"""
    pass


class ConfiguracaoUpdate(BaseModel):
    """Schema para atualização de configuração"""
    valor: Optional[Any] = None
    descricao: Optional[str] = None


class ConfiguracaoResponse(ConfiguracaoBase):
    """Schema de resposta para configuração"""
    id: str = Field(..., description="ID único")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
