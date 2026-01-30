"""Schemas Pydantic para Usuários e Permissões"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PerfilUsuario(str, Enum):
    """Perfis de usuário"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class PermissaoSistema(str, Enum):
    """Permissões disponíveis no sistema"""
    # Empresas
    EMPRESAS_READ = "empresas.read"
    EMPRESAS_WRITE = "empresas.write"
    EMPRESAS_DELETE = "empresas.delete"
    
    # Guias
    GUIAS_READ = "guias.read"
    GUIAS_WRITE = "guias.write"
    GUIAS_DELETE = "guias.delete"
    
    # Alertas
    ALERTAS_READ = "alertas.read"
    ALERTAS_WRITE = "alertas.write"
    ALERTAS_DELETE = "alertas.delete"
    
    # Certidões
    CERTIDOES_READ = "certidoes.read"
    CERTIDOES_WRITE = "certidoes.write"
    CERTIDOES_DELETE = "certidoes.delete"
    
    # Débitos
    DEBITOS_READ = "debitos.read"
    DEBITOS_WRITE = "debitos.write"
    DEBITOS_DELETE = "debitos.delete"
    
    # Relatórios
    RELATORIOS_VIEW = "relatorios.view"
    RELATORIOS_GENERATE = "relatorios.generate"
    RELATORIOS_DELETE = "relatorios.delete"
    
    # Documentos
    DOCUMENTOS_READ = "documentos.read"
    DOCUMENTOS_WRITE = "documentos.write"
    DOCUMENTOS_DELETE = "documentos.delete"
    
    # Obrigações
    OBRIGACOES_READ = "obrigacoes.read"
    OBRIGACOES_WRITE = "obrigacoes.write"
    OBRIGACOES_DELETE = "obrigacoes.delete"
    
    # Usuários (apenas ADMIN+)
    USUARIOS_MANAGE = "usuarios.manage"
    
    # Configurações
    CONFIGURACOES_READ = "configuracoes.read"
    CONFIGURACOES_WRITE = "configuracoes.write"


# Permissões por perfil
PERMISSOES_POR_PERFIL = {
    PerfilUsuario.SUPER_ADMIN: [p.value for p in PermissaoSistema],  # Todas
    PerfilUsuario.ADMIN: [
        # Todas exceto gerenciar outros admins
        PermissaoSistema.EMPRESAS_READ.value,
        PermissaoSistema.EMPRESAS_WRITE.value,
        PermissaoSistema.EMPRESAS_DELETE.value,
        PermissaoSistema.GUIAS_READ.value,
        PermissaoSistema.GUIAS_WRITE.value,
        PermissaoSistema.GUIAS_DELETE.value,
        PermissaoSistema.ALERTAS_READ.value,
        PermissaoSistema.ALERTAS_WRITE.value,
        PermissaoSistema.ALERTAS_DELETE.value,
        PermissaoSistema.CERTIDOES_READ.value,
        PermissaoSistema.CERTIDOES_WRITE.value,
        PermissaoSistema.CERTIDOES_DELETE.value,
        PermissaoSistema.DEBITOS_READ.value,
        PermissaoSistema.DEBITOS_WRITE.value,
        PermissaoSistema.DEBITOS_DELETE.value,
        PermissaoSistema.RELATORIOS_VIEW.value,
        PermissaoSistema.RELATORIOS_GENERATE.value,
        PermissaoSistema.RELATORIOS_DELETE.value,
        PermissaoSistema.DOCUMENTOS_READ.value,
        PermissaoSistema.DOCUMENTOS_WRITE.value,
        PermissaoSistema.DOCUMENTOS_DELETE.value,
        PermissaoSistema.OBRIGACOES_READ.value,
        PermissaoSistema.OBRIGACOES_WRITE.value,
        PermissaoSistema.OBRIGACOES_DELETE.value,
        PermissaoSistema.USUARIOS_MANAGE.value,
        PermissaoSistema.CONFIGURACOES_READ.value,
        PermissaoSistema.CONFIGURACOES_WRITE.value,
    ],
    PerfilUsuario.USER: [
        # Apenas leitura e escrita básica
        PermissaoSistema.EMPRESAS_READ.value,
        PermissaoSistema.GUIAS_READ.value,
        PermissaoSistema.ALERTAS_READ.value,
        PermissaoSistema.CERTIDOES_READ.value,
        PermissaoSistema.DEBITOS_READ.value,
        PermissaoSistema.RELATORIOS_VIEW.value,
        PermissaoSistema.DOCUMENTOS_READ.value,
        PermissaoSistema.OBRIGACOES_READ.value,
        PermissaoSistema.CONFIGURACOES_READ.value,
    ]
}


class UsuarioBase(BaseModel):
    """Schema base para usuário"""
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="Email único do usuário")
    perfil: PerfilUsuario = Field(default=PerfilUsuario.USER, description="Perfil de acesso")
    permissoes: List[str] = Field(default=[], description="Permissões específicas")
    ativo: bool = Field(default=True, description="Se o usuário está ativo")


class UsuarioCreate(UsuarioBase):
    """Schema para criação de usuário"""
    senha: str = Field(..., min_length=6, description="Senha do usuário (mínimo 6 caracteres)")


class UsuarioUpdate(BaseModel):
    """Schema para atualização de usuário"""
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    perfil: Optional[PerfilUsuario] = None
    permissoes: Optional[List[str]] = None
    ativo: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    """Schema de resposta para usuário (sem senha)"""
    id: str = Field(..., description="ID único do usuário")
    primeiro_login: bool = Field(default=True, description="Se é o primeiro login")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    ultimo_acesso: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UsuarioListResponse(BaseModel):
    """Schema de resposta para lista de usuários"""
    usuarios: List[UsuarioResponse]
    total: int
    pagina: int = 1
    por_pagina: int = 20


class TrocarSenhaRequest(BaseModel):
    """Schema para trocar senha"""
    senha_atual: str = Field(..., description="Senha atual")
    senha_nova: str = Field(..., min_length=6, description="Nova senha (mínimo 6 caracteres)")


class AlterarSenhaRequest(BaseModel):
    """Schema para administrador alterar senha de usuário"""
    senha_nova: str = Field(..., min_length=6, description="Nova senha (mínimo 6 caracteres)")
    forcar_troca: bool = Field(default=False, description="Forçar troca no próximo login")
