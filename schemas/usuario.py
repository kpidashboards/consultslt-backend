"""
Schemas Pydantic relacionados a Usuários
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# ==============================
# Enums
# ==============================

class UserRole(str, Enum):
    ADMIN = "admin"
    VIEWER = "viewer"

class PerfilUsuario(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    USUARIO = "usuario"

class PermissaoSistema(str, Enum):
    USUARIOS_CRIAR = "USUARIOS_CRIAR"
    USUARIOS_EDITAR = "USUARIOS_EDITAR"
    USUARIOS_EXCLUIR = "USUARIOS_EXCLUIR"
    DOCUMENTOS_UPLOAD = "DOCUMENTOS_UPLOAD"
    DOCUMENTOS_PROCESSAR = "DOCUMENTOS_PROCESSAR"
    EMPRESAS_GERENCIAR = "EMPRESAS_GERENCIAR"

# ==============================
# Base
# ==============================

class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    ativo: bool = True

# ==============================
# Create
# ==============================

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8)

# ==============================
# Update
# ==============================

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    role: Optional[UserRole] = None
    ativo: Optional[bool] = None

# ==============================
# Password
# ==============================

class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(..., min_length=8)

class AlterarSenhaRequest(BaseModel):
    nova_senha: str = Field(..., min_length=8)

# ==============================
# Response
# ==============================

class UsuarioResponse(UsuarioBase):
    id: str
    entity_id: str
    version: int
    valid_from: datetime
    valid_to: Optional[datetime] = None
    previous_version_id: Optional[str] = None
    ativo: bool = True
    created_at: datetime
    created_by: Optional[str] = None
    criado_em: datetime
    ultimo_acesso: Optional[datetime] = None
    permissoes: List[str] = []

    class Config:
        from_attributes = True

class UsuarioListResponse(BaseModel):
    total: int
    usuarios: List[UsuarioResponse]

# ==============================
# Exportações explícitas
# ==============================
__all__ = [
    "UserRole",
    "PerfilUsuario",
    "PermissaoSistema",
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioResponse",
    "UsuarioListResponse",
    "TrocarSenhaRequest",
    "AlterarSenhaRequest",
]
