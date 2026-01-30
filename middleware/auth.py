"""
Middleware de Autenticação e Autorização (RBAC)
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import jwt
import os
import logging
from functools import wraps
from motor.motor_asyncio import AsyncIOMotorClient

from schemas.usuario import PerfilUsuario

logger = logging.getLogger(__name__)

# Configurações JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'sltdctfweb-secret-key-2024')
JWT_ALGORITHM = 'HS256'

# Security scheme
security = HTTPBearer()


def get_db():
    """Obtém conexão com banco de dados"""
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> dict:
    """
    Extrai e valida o usuário atual do token JWT
    
    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    token = credentials.credentials
    
    try:
        # Decodificar token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        email = payload.get('email')
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Buscar usuário no banco
        user = await db.users.find_one({"id": user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        if not user.get('ativo', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Retorna usuário ativo"""
    if not current_user.get('ativo', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user


def require_role(required_roles: List[PerfilUsuario]):
    """
    Decorator para exigir perfis específicos
    
    Usage:
        @require_role([PerfilUsuario.ADMIN, PerfilUsuario.SUPER_ADMIN])
        async def minha_rota(current_user: dict = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair current_user dos kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticação necessária"
                )
            
            user_perfil = current_user.get('perfil', 'user')
            
            if user_perfil not in [role.value for role in required_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Acesso negado. Perfil necessário: {[r.value for r in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(required_permissions: List[str]):
    """
    Decorator para exigir permissões específicas
    
    Usage:
        @require_permission(["empresas.write", "empresas.delete"])
        async def minha_rota(current_user: dict = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair current_user dos kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticação necessária"
                )
            
            # SUPER_ADMIN tem todas as permissões
            if current_user.get('perfil') == PerfilUsuario.SUPER_ADMIN.value:
                return await func(*args, **kwargs)
            
            user_permissions = current_user.get('permissoes', [])
            
            # Verificar se usuário tem todas as permissões necessárias
            has_permission = any(perm in user_permissions for perm in required_permissions)
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão negada. Permissões necessárias: {required_permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(user: dict, permission: str) -> bool:
    """
    Verifica se usuário tem uma permissão específica
    
    Args:
        user: Dicionário do usuário
        permission: String da permissão (ex: "empresas.write")
    
    Returns:
        True se tem permissão, False caso contrário
    """
    # SUPER_ADMIN tem todas as permissões
    if user.get('perfil') == PerfilUsuario.SUPER_ADMIN.value:
        return True
    
    user_permissions = user.get('permissoes', [])
    return permission in user_permissions


def check_role(user: dict, roles: List[PerfilUsuario]) -> bool:
    """
    Verifica se usuário tem um dos perfis especificados
    
    Args:
        user: Dicionário do usuário
        roles: Lista de perfis aceitos
    
    Returns:
        True se tem o perfil, False caso contrário
    """
    user_perfil = user.get('perfil', 'user')
    return user_perfil in [role.value for role in roles]
