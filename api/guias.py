from fastapi import APIRouter

router = APIRouter(prefix="/guias", tags=["Guias"])

# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""Endpoints para gestão de Guias de Pagamento"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
from datetime import datetime, date, timedelta
import uuid
from backend.schemas.guia import (
    GuiaCreate,
    GuiaUpdate,
    GuiaResponse,
    GuiaListResponse,
    TipoGuia,
    StatusGuia
)
from backend.repositories.guias_repository import GuiasRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/guias", tags=["Guias"])

def get_guias_repo():
    return GuiasRepository()

# =========================
# Endpoints
# =========================


from backend.dependencies.auth import get_current_user

@router.post("/", response_model=GuiaResponse, status_code=201)
async def criar_guia(dados: GuiaCreate, repo: GuiasRepository = Depends(get_guias_repo), user=Depends(get_current_user)):
    """Cria uma nova guia"""
    guia_dict = dados.model_dump()
    guia_dict["status"] = StatusGuia.PENDENTE
    if isinstance(guia_dict.get("data_vencimento"), date):
        guia_dict["data_vencimento"] = guia_dict["data_vencimento"].isoformat()
    guia = await repo.create_guia(guia_dict, created_by=user["id"] if user else None)
    return GuiaResponse(**guia)


@router.get("/", response_model=GuiaListResponse, status_code=200)
async def listar_guias(
    empresa_id: Optional[str] = None,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    repo: GuiasRepository = Depends(get_guias_repo),
    user=Depends(get_current_user)
):
    """Lista guias com filtros"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    skip = (pagina - 1) * por_pagina
    guias = await repo.list_guias(filtro, skip, por_pagina)
    total = await repo.count_guias(filtro)
    return GuiaListResponse(
        guias=[GuiaResponse(**g) for g in guias],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina
    )


@router.get("/{guia_id}", response_model=GuiaResponse, status_code=200)
async def obter_guia(guia_id: str, repo: GuiasRepository = Depends(get_guias_repo), user=Depends(get_current_user)):
    """Obtém detalhes de uma guia"""
    guia = await repo.get_guia(guia_id)
    if not guia:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    return GuiaResponse(**guia)


@router.put("/{guia_id}", response_model=GuiaResponse)
async def atualizar_guia(guia_id: str, dados: GuiaUpdate, repo: GuiasRepository = Depends(get_guias_repo), user=Depends(get_current_user)):
    """Atualiza uma guia"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    if "data_pagamento" in update_data and isinstance(update_data["data_pagamento"], date):
        update_data["data_pagamento"] = update_data["data_pagamento"].isoformat()
    guia = await repo.update_guia(guia_id, update_data, updated_by=user["id"] if user else None)
    if not guia:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    return GuiaResponse(**guia)


@router.delete("/{guia_id}")
async def deletar_guia(guia_id: str, repo: GuiasRepository = Depends(get_guias_repo), user=Depends(get_current_user)):
    """Deleta uma guia"""
    ok = await repo.delete_guia(guia_id, deleted_by=user["id"] if user else None)
    if not ok:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    return {"message": "Guia deletada com sucesso"}


@router.get("/proximos-vencimentos/lista")
async def proximos_vencimentos(dias: int = 7, empresa_id: Optional[str] = None, repo: GuiasRepository = Depends(get_guias_repo), user=Depends(get_current_user)):
    """Obtém guias com vencimento próximo"""
    data_limite = (date.today() + timedelta(days=dias)).isoformat()
    guias = await repo.proximos_vencimentos(data_limite, empresa_id)
    return {"guias": [GuiaResponse(**g) for g in guias], "total": len(guias)}


# =========================
# Exportar router
# =========================
guias_router = router
