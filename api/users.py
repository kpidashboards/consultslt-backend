from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.repositories.users_repository import UsersRepository
from backend.middleware.auth import get_current_user
from backend.schemas.usuario import UserRole

router = APIRouter(prefix="/users", tags=["Usuários"])

class UserCreateRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: UserRole = UserRole.VIEWER
    ativo: bool = True

@router.post("/", status_code=201)
async def create_user(request: UserCreateRequest, current_user=Depends(get_current_user)):
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores podem criar usuários.")
    repo = UsersRepository()
    existing = await repo.get_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email já cadastrado.")
    user = await repo.create_user(
        nome=request.nome,
        email=request.email,
        senha=request.senha,
        role=request.role.value,
        ativo=request.ativo
    )
    return {"id": str(user["_id"]), "email": user["email"], "role": user["role"]}
