"""
API de Usuários
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import uuid

from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse, PerfilUsuario, PERMISSOES_POR_PERFIL
from auth_utils import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("/", response_model=List[UserResponse])
async def listar_usuarios(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Lista todos os usuários (apenas admins)"""
    usuarios = db.query(User).all()
    return usuarios


@router.get("/{usuario_id}", response_model=UserResponse)
async def obter_usuario(
    usuario_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Obtém usuário por ID"""
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return usuario


@router.post("/", response_model=UserResponse, status_code=201)
async def criar_usuario(
    usuario: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Cria um novo usuário"""
    # Verificar se email já existe
    existing = db.query(User).filter(User.email == usuario.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Hash da senha
    hashed_password = hash_password(usuario.password)
    
    # Permissões baseadas no perfil
    permissoes = PERMISSOES_POR_PERFIL.get(usuario.perfil, [])
    
    novo_usuario = User(
        id=str(uuid.uuid4()),
        nome=usuario.nome,
        email=usuario.email,
        password=hashed_password,
        perfil=usuario.perfil.value,
        permissoes=permissoes,
        ativo=usuario.ativo,
        primeiro_login=True
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return novo_usuario


@router.put("/{usuario_id}", response_model=UserResponse)
async def atualizar_usuario(
    usuario_id: str,
    usuario_update: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Atualiza usuário"""
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Se trocar senha, fazer hash
    if 'password' in update_data:
        update_data['password'] = hash_password(update_data['password'])
    
    # Se trocar perfil, atualizar permissões
    if 'perfil' in update_data:
        perfil_enum = update_data['perfil']
        update_data['perfil'] = perfil_enum.value
        update_data['permissoes'] = PERMISSOES_POR_PERFIL.get(perfil_enum, [])
    
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    usuario.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete("/{usuario_id}")
async def excluir_usuario(
    usuario_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Desativa usuário (soft delete)"""
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    usuario.ativo = False
    usuario.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"success": True, "message": "Usuário desativado com sucesso"}
