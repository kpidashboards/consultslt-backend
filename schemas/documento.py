"""
Schemas Pydantic para Documentos
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class TipoDocumento(str, Enum):
    """Tipos de documentos fiscais suportados"""
    DCTFWEB = "dctfweb"
    DAS = "das"
    DARF = "darf"
    NFE = "nfe"
    CERTIDAO = "certidao"
    OUTRO = "outro"


class StatusDocumento(str, Enum):
    """Status de processamento do documento"""
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    PROCESSADO = "processado"
    ERRO = "erro"
    ARQUIVADO = "arquivado"


class DocumentoBase(BaseModel):
    """Schema base para documento"""
    nome: str = Field(..., description="Nome do arquivo")
    tipo: TipoDocumento = Field(default=TipoDocumento.OUTRO, description="Tipo do documento")
    empresa_id: Optional[str] = Field(default=None, description="ID da empresa relacionada")
    cnpj: Optional[str] = Field(default=None, description="CNPJ extraído do documento")


class DocumentoCreate(DocumentoBase):
    """Schema para criação de documento (sem upload)"""
    pass


class DocumentoUpload(BaseModel):
    """Schema para metadados de upload"""
    empresa_id: Optional[str] = None
    tipo: TipoDocumento = TipoDocumento.OUTRO
    processar_automaticamente: bool = True



class DocumentoResponse(DocumentoBase):
    id: str = Field(..., description="ID único do documento")
    entity_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime] = None
    previous_version_id: Optional[str] = None
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: StatusDocumento = Field(default=StatusDocumento.PENDENTE)
    caminho_arquivo: Optional[str] = Field(default=None, description="Caminho do arquivo armazenado")
    tamanho_bytes: int = Field(default=0, description="Tamanho do arquivo em bytes")
    content_type: Optional[str] = Field(default=None, description="MIME type do arquivo")
    dados_extraidos: Optional[Dict[str, Any]] = Field(default=None, description="Dados extraídos pelo parser")
    confianca_extracao: float = Field(default=0.0, description="Confiança da extração (0-100)")
    processado_em: Optional[datetime] = None
    erro_processamento: Optional[str] = None
    obrigacao_id: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentoListResponse(BaseModel):
    """Schema de resposta para lista de documentos"""
    documentos: List[DocumentoResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20


class DocumentoProcessamentoResult(BaseModel):
    """Resultado do processamento de um documento"""
    documento_id: str
    sucesso: bool
    tipo_detectado: Optional[TipoDocumento] = None
    dados_extraidos: Optional[Dict[str, Any]] = None
    obrigacao_criada: bool = False
    obrigacao_id: Optional[str] = None
    erros: List[str] = Field(default_factory=list)
    tempo_processamento_ms: int = 0
