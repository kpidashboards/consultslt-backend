"""Schemas Pydantic para Relatórios"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class TipoRelatorio(str, Enum):
    """Tipos de relatórios"""
    MENSAL = "mensal"
    TRIMESTRAL = "trimestral"
    ANUAL = "anual"
    PERSONALIZADO = "personalizado"


class FormatoRelatorio(str, Enum):
    """Formatos de exportação"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class StatusRelatorio(str, Enum):
    """Status do relatório"""
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    ERRO = "erro"


class RelatorioBase(BaseModel):
    """Schema base para relatório"""
    tipo: TipoRelatorio = Field(..., description="Tipo do relatório")
    titulo: str = Field(..., description="Título do relatório")
    empresa_id: Optional[str] = Field(default=None, description="ID da empresa")
    periodo_inicio: date = Field(..., description="Data início")
    periodo_fim: date = Field(..., description="Data fim")
    formato: FormatoRelatorio = Field(default=FormatoRelatorio.PDF)
    descricao: Optional[str] = Field(default=None)


class RelatorioCreate(RelatorioBase):
    """Schema para criação de relatório"""
    pass


class RelatorioResponse(RelatorioBase):
    """Schema de resposta para relatório"""
    id: str = Field(..., description="ID único")
    status: StatusRelatorio = Field(default=StatusRelatorio.PROCESSANDO)
    arquivo_path: Optional[str] = None
    dados: Optional[Dict[str, Any]] = Field(default=None, description="Dados do relatório")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processado_em: Optional[datetime] = None
    erro: Optional[str] = None
    
    class Config:
        from_attributes = True


class RelatorioListResponse(BaseModel):
    """Schema de resposta para lista de relatórios"""
    relatorios: List[RelatorioResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20
