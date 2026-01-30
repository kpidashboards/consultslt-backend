"""
Utilitários de autenticação e autorização
"""

import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import PerfilUsuario

JWT_SECRET = os.getenv('JWT_SECRET', 'sltdctfweb-secret-key-2024-ultra-secure')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def hash_password(password: str) -> str:
    """Hash de senha usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_token(user_id: str, email: str, perfil: str) -> str:
    """Cria token JWT"""
    payload = {
        'user_id': user_id,
        'email': email,
        'perfil': perfil,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency para obter usuário atual a partir do token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    try:
        # Extrair token do header "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Buscar usuário no banco
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        if not user.ativo:
            raise HTTPException(status_code=403, detail="Usuário inativo")
        
        # Atualizar último acesso
        user.ultimo_acesso = datetime.now(timezone.utc)
        db.commit()
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro ao autenticar: {str(e)}")


def check_permission(user: User, permission: str) -> bool:
    """Verifica se usuário tem uma permissão específica"""
    return permission in user.permissoes


def require_permission(permission: str):
    """Decorator para endpoints que requerem permissão específica"""
    async def permission_checker(user: User = Depends(get_current_user)):
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permissão necessária: {permission}"
            )
        return user
    return permission_checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency para endpoints que requerem perfil ADMIN ou SUPER_ADMIN"""
    if user.perfil not in [PerfilUsuario.ADMIN.value, PerfilUsuario.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a administradores"
        )
    return user


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency para endpoints que requerem perfil SUPER_ADMIN"""
    if user.perfil != PerfilUsuario.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a super administradores"
        )
    return user
