"""
Endpoints de Autenticação - usando MongoDB
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
import bcrypt

auth_router = APIRouter(tags=["Authentication"])

# DB Dependency
def get_db():
    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "consultslt_db")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

# Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@auth_router.get("/ping")
async def ping():
    return {"message": "Auth endpoint OK"}

@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db=Depends(get_db)):
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if "password_hash" not in user:
        raise HTTPException(status_code=500, detail="Usuário sem senha configurada")

    if not bcrypt.checkpw(
        request.password.encode(),
        user["password_hash"].encode()
    ):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return {
        "access_token": f"token-{user['email']}",
        "token_type": "bearer"
    }
