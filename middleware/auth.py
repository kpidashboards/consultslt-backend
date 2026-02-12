"""
Middleware de Autenticação e Autorização (RBAC)
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from jose import jwt, JWTError
import os
import logging
from functools import wraps
from motor.motor_asyncio import AsyncIOMotorClient

# 🔹 Corrigido: import absoluto dentro do pacote backend
from backend.schemas.usuario import PerfilUsuario

logger = logging.getLogger(__name__)

# Configurações JWT
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE = int(os.environ.get('JWT_EXPIRE', '480'))

# Security scheme
security = HTTPBearer()


def get_db():
    """Obtém conexão com banco de dados"""
    mongo_url = os.environ.get("MONGO_URI") or os.environ.get("MONGO_URL")
    db_name = os.environ.get("MONGO_DB") or os.environ.get("DB_NAME") or "consultslt_db"
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
        from bson import ObjectId
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            user = None
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        # Se o campo ativo não existir, considera ativo
        if user is not None and not user.get('ativo', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
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
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticação necessária"
                )
            
            user_perfil = current_user.get('perfil', 'usuario')
            
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
            
            # Verificar se usuário tem pelo menos uma das permissões necessárias
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
    """
    if user.get('perfil') == PerfilUsuario.SUPER_ADMIN.value:
        return True
    return permission in user.get('permissoes', [])


def check_role(user: dict, roles: List[PerfilUsuario]) -> bool:
    """
    Verifica se usuário tem um dos perfis especificados
    """
    user_perfil = user.get('perfil', 'usuario')
    return user_perfil in [role.value for role in roles]
