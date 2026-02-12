"""
Security - JWT + Hash + Permissões
ConsultSLT Web
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# ===============================
# CONFIGURAÇÕES
# ===============================

SECRET_KEY = os.getenv("SECRET_KEY", "uma_chave_super_secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)

# ⚠️ IMPORTANTE: usar bcrypt estável
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

security = HTTPBearer()

# ===============================
# PASSWORD HASH
# ===============================

def _truncate_password(password: str) -> str:
    """
    bcrypt suporta no máximo 72 bytes.
    Se ultrapassar, truncamos de forma segura.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode("utf-8", errors="ignore")


def get_password_hash(password: str) -> str:
    """
    Gera hash seguro da senha
    """
    password = _truncate_password(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica senha contra hash
    """
    plain_password = _truncate_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

# ===============================
# JWT
# ===============================

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Cria token JWT
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica token JWT
    """
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ===============================
# DEPENDÊNCIAS FASTAPI
# ===============================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtém usuário atual via JWT
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    return payload


def require_admin(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Exige role admin
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )

    return user