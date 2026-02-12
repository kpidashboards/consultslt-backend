from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

# ✅ IMPORTS CORRETOS (ABSOLUTOS)
from backend.schemas.alerta import (
    AlertaCreate,
    AlertaUpdate,
    AlertaResponse,
    StatusAlerta,
)
from backend.repositories.alertas_repository import AlertasRepository
from backend.dependencies.auth import get_current_user


router = APIRouter(prefix="/alertas", tags=["Alertas"])


# ===============================
# Dependency
# ===============================
def get_alertas_repo():
    return AlertasRepository()


# ===============================
# Criar Alerta
# ===============================
@router.post(
    "/",
    response_model=AlertaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_alerta(
    alerta: AlertaCreate,
    repo: AlertasRepository = Depends(get_alertas_repo),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    alerta_dict = alerta.model_dump()

    alerta_dict.update(
        {
            "status": StatusAlerta.PENDENTE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    novo_alerta = await repo.create_alerta(
        alerta_dict,
        created_by=user.get("id"),
    )

    return AlertaResponse(**novo_alerta)


# ===============================
# Listar Alertas
# ===============================
@router.get(
    "/",
    response_model=List[AlertaResponse],
    status_code=status.HTTP_200_OK,
)
async def listar_alertas(
    repo: AlertasRepository = Depends(get_alertas_repo),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    alertas = await repo.list_alertas()

    return [AlertaResponse(**alerta) for alerta in alertas]


# ===============================
# Marcar como Lido
# ===============================
@router.patch(
    "/{alerta_id}/lido",
    response_model=AlertaResponse,
)
async def marcar_como_lido(
    alerta_id: str,
    repo: AlertasRepository = Depends(get_alertas_repo),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    alerta = await repo.get_alerta(alerta_id)

    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado",
        )

    update_data = {
        "status": StatusAlerta.LIDO,
        "lido_em": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    alerta_atualizado = await repo.update_alerta(
        alerta_id,
        update_data,
        updated_by=user.get("id"),
    )

    return AlertaResponse(**alerta_atualizado)


# ===============================
# Marcar como Resolvido
# ===============================
@router.patch(
    "/{alerta_id}/resolvido",
    response_model=AlertaResponse,
)
async def marcar_como_resolvido(
    alerta_id: str,
    repo: AlertasRepository = Depends(get_alertas_repo),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    alerta = await repo.get_alerta(alerta_id)

    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado",
        )

    update_data = {
        "status": StatusAlerta.RESOLVIDO,
        "resolvido_em": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    alerta_atualizado = await repo.update_alerta(
        alerta_id,
        update_data,
        updated_by=user.get("id"),
    )

    return AlertaResponse(**alerta_atualizado)


# ===============================
# Deletar Alerta
# ===============================
@router.delete(
    "/{alerta_id}",
    status_code=status.HTTP_200_OK,
)
async def deletar_alerta(
    alerta_id: str,
    repo: AlertasRepository = Depends(get_alertas_repo),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    sucesso = await repo.delete_alerta(
        alerta_id,
        deleted_by=user.get("id"),
    )

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado",
        )

    return {
        "ok": True,
        "message": "Alerta removido com sucesso",
    }


# ===============================
# Exportação obrigatória
# ===============================
__all__ = ["router"]
