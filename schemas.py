"""
Schemas Pydantic para validação e serialização
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# PERFIS E PERMISSÕES
# ============================================================================

class PerfilUsuario(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    VIEW = "view"


class Permissao(str, Enum):
    # Empresas
    EMPRESAS_CRIAR = "empresas:criar"
    EMPRESAS_EDITAR = "empresas:editar"
    EMPRESAS_EXCLUIR = "empresas:excluir"
    EMPRESAS_VISUALIZAR = "empresas:visualizar"
    
    # Guias
    GUIAS_CRIAR = "guias:criar"
    GUIAS_EDITAR = "guias:editar"
    GUIAS_EXCLUIR = "guias:excluir"
    GUIAS_VISUALIZAR = "guias:visualizar"
    
    # Documentos
    DOCUMENTOS_CRIAR = "documentos:criar"
    DOCUMENTOS_EDITAR = "documentos:editar"
    DOCUMENTOS_EXCLUIR = "documentos:excluir"
    DOCUMENTOS_VISUALIZAR = "documentos:visualizar"
    
    # Usuários
    USUARIOS_CRIAR = "usuarios:criar"
    USUARIOS_EDITAR = "usuarios:editar"
    USUARIOS_EXCLUIR = "usuarios:excluir"
    USUARIOS_VISUALIZAR = "usuarios:visualizar"
    
    # Relatórios
    RELATORIOS_CRIAR = "relatorios:criar"
    RELATORIOS_VISUALIZAR = "relatorios:visualizar"
    
    # Configurações
    CONFIGURACOES_EDITAR = "configuracoes:editar"
    CONFIGURACOES_VISUALIZAR = "configuracoes:visualizar"


# Mapeamento de permissões por perfil
PERMISSOES_POR_PERFIL = {
    PerfilUsuario.SUPER_ADMIN: [p.value for p in Permissao],
    PerfilUsuario.ADMIN: [
        Permissao.EMPRESAS_CRIAR.value,
        Permissao.EMPRESAS_EDITAR.value,
        Permissao.EMPRESAS_VISUALIZAR.value,
        Permissao.GUIAS_CRIAR.value,
        Permissao.GUIAS_EDITAR.value,
        Permissao.GUIAS_VISUALIZAR.value,
        Permissao.DOCUMENTOS_CRIAR.value,
        Permissao.DOCUMENTOS_EDITAR.value,
        Permissao.DOCUMENTOS_VISUALIZAR.value,
        Permissao.USUARIOS_VISUALIZAR.value,
        Permissao.RELATORIOS_CRIAR.value,
        Permissao.RELATORIOS_VISUALIZAR.value,
        Permissao.CONFIGURACOES_VISUALIZAR.value,
    ],
    PerfilUsuario.USER: [
        Permissao.EMPRESAS_VISUALIZAR.value,
        Permissao.GUIAS_VISUALIZAR.value,
        Permissao.DOCUMENTOS_VISUALIZAR.value,
        Permissao.RELATORIOS_VISUALIZAR.value,
    ],
    PerfilUsuario.VIEW: [
        Permissao.EMPRESAS_VISUALIZAR.value,
        Permissao.GUIAS_VISUALIZAR.value,
        Permissao.DOCUMENTOS_VISUALIZAR.value,
        Permissao.RELATORIOS_VISUALIZAR.value,
    ],
}


# ============================================================================
# USUÁRIOS
# ============================================================================

class UserBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: PerfilUsuario = PerfilUsuario.USER
    ativo: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    perfil: Optional[PerfilUsuario] = None
    ativo: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: str
    permissoes: List[str]
    primeiro_login: bool
    created_at: datetime
    ultimo_acesso: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None
    primeiro_login: Optional[bool] = False


class TrocaSenhaRequest(BaseModel):
    senha_atual: str
    senha_nova: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str


# ============================================================================
# EMPRESAS
# ============================================================================

class EmpresaBase(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    regime_tributario: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    cnae: Optional[str] = None
    endereco: Optional[str] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    regime_tributario: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    ativo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    id: str
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# GUIAS
# ============================================================================

class GuiaBase(BaseModel):
    empresa_id: str
    tipo: str
    competencia: str
    vencimento: datetime
    valor: float
    codigo_barras: Optional[str] = None
    observacoes: Optional[str] = None


class GuiaCreate(GuiaBase):
    pass


class GuiaUpdate(BaseModel):
    status: Optional[str] = None
    valor: Optional[float] = None
    observacoes: Optional[str] = None


class GuiaResponse(GuiaBase):
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ALERTAS
# ============================================================================

class AlertaBase(BaseModel):
    titulo: str
    mensagem: str
    tipo: str
    severidade: str = "info"
    empresa_id: Optional[str] = None


class AlertaCreate(AlertaBase):
    pass


class AlertaResponse(AlertaBase):
    id: str
    lido: bool
    created_at: datetime

    class Config:
        from_attributes = True
