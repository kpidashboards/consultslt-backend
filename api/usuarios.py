# backend/api/usuarios.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.core.security import require_admin, hash_password
from backend.schemas import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from backend.repositories.users_repository import UsersRepository

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

# ===============================
# PERMISSÕES POR PERFIL
# ===============================
PERMISSOES_POR_PERFIL = {
    "SUPER_ADMIN": [
        "usuarios:criar",
        "usuarios:editar",
        "usuarios:remover",
        "usuarios:listar",
        "empresas:gerenciar",
        "documentos:gerenciar",
    ],
    "ADMIN": [
        "usuarios:criar",
        "usuarios:editar",
        "usuarios:listar",
        "documentos:gerenciar",
    ],
    "USUARIO": [
        "documentos:visualizar",
    ],
}

# ===============================
# LISTAR USUÁRIOS
# ===============================
@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(admin_user=Depends(require_admin)):
    repo = UsersRepository()
    usuarios = await repo.list_usuarios_ativos()
    return [UsuarioResponse(**u) for u in usuarios]

# ===============================
# OBTER USUÁRIO POR ID
# ===============================
@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(usuario_id: str, admin_user=Depends(require_admin)):
    repo = UsersRepository()
    usuario = await repo.get_usuario_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioResponse(**usuario)

# ===============================
# CRIAR USUÁRIO
# ===============================
@router.post("/", response_model=UsuarioResponse, status_code=201)
async def criar_usuario(usuario: UsuarioCreate, admin_user=Depends(require_admin)):
    repo = UsersRepository()

    existing = await repo.get_usuario_by_email(usuario.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    perfil = usuario.perfil
    permissoes = PERMISSOES_POR_PERFIL.get(perfil, [])

    novo_usuario = {
        "nome": usuario.nome,
        "email": usuario.email,
        "password": hash_password(usuario.password),
        "perfil": perfil,
        "permissoes": permissoes,
        "ativo": True,
        "primeiro_login": True,
        "ultimo_acesso": None,
    }

    usuario_criado = await repo.create_usuario(novo_usuario)
    return UsuarioResponse(**usuario_criado)

# ===============================
# ATUALIZAR USUÁRIO
# ===============================
@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(
    usuario_id: str,
    usuario_update: UsuarioUpdate,
    admin_user=Depends(require_admin),
):
    repo = UsersRepository()

    usuario = await repo.get_usuario_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = usuario_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    if "perfil" in update_data:
        perfil = update_data["perfil"]
        update_data["permissoes"] = PERMISSOES_POR_PERFIL.get(perfil, [])

    usuario_atualizado = await repo.update_usuario(usuario_id, update_data)
    return UsuarioResponse(**usuario_atualizado)

# ===============================
# DESATIVAR USUÁRIO (SOFT DELETE)
# ===============================
@router.delete("/{usuario_id}")
async def excluir_usuario(usuario_id: str, admin_user=Depends(require_admin)):
    repo = UsersRepository()
    ok = await repo.deactivate_usuario(usuario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"success": True, "message": "Usuário desativado com sucesso"}
