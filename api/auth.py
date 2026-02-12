from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

from backend.core.database import get_db
from backend.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)

# ==========================================================
# 🚀 Router
# ==========================================================

router = APIRouter(prefix="/auth", tags=["Auth"])


# ==========================================================
# 📦 Schemas
# ==========================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr
    perfil: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"


# ==========================================================
# 🔐 LOGIN
# ==========================================================

@router.post("/login", response_model=LoginResponse)
async def login(dados: LoginRequest):
    db = get_db()

    # 🔎 Busca usuário
    user = await db.users.find_one({"email": dados.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 🔐 Verifica senha
    if not verify_password(dados.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 🕒 Atualiza último login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    # 🎟 Cria token JWT
    token_data = {
        "sub": user["email"],
        "role": user.get("role", "user"),
        "user_id": str(user["_id"])
    }

    access_token = create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        email=user["email"],
        perfil=user.get("role", "user")
    )


# ==========================================================
# 👤 REGISTRO (opcional, mas recomendado)
# ==========================================================

@router.post("/register", status_code=201)
async def register(dados: RegisterRequest):
    db = get_db()

    # Verifica duplicidade
    existing_user = await db.users.find_one({"email": dados.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário já cadastrado"
        )

    hashed_password = get_password_hash(dados.password)

    new_user = {
        "email": dados.email,
        "password": hashed_password,
        "role": dados.role,
        "created_at": datetime.utcnow(),
        "last_login": None,
        "ativo": True
    }

    await db.users.insert_one(new_user)

    return {"message": "Usuário criado com sucesso"}
