from fastapi import APIRouter

router = APIRouter(prefix="/debitos", tags=["Débitos"])

@router.get("/")
async def listar_debitos():
    return []
# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""Endpoints para gestão de Débitos"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
from datetime import datetime, date
import uuid
from backend.schemas.debito import (
    DebitoCreate,
    DebitoUpdate,
    DebitoResponse,
    DebitoListResponse,
    TipoDebito,
    StatusDebito
)
from backend.repositories.debitos_repository import DebitosRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debitos", tags=["Débitos"])

def get_debitos_repo():
    return DebitosRepository()

# =========================
# Endpoints
# =========================

@router.post("/", response_model=DebitoResponse)
async def criar_debito(dados: DebitoCreate, repo: DebitosRepository = Depends(get_debitos_repo)):
    """Cria um novo débito"""
    debito_dict = dados.model_dump()
    debito_dict["status"] = StatusDebito.ABERTO
    if "data_inscricao" in debito_dict and isinstance(debito_dict["data_inscricao"], date):
        debito_dict["data_inscricao"] = debito_dict["data_inscricao"].isoformat()
    debito = await repo.create_debito(debito_dict)
    return DebitoResponse(**debito)


@router.get("/", response_model=DebitoListResponse)
async def listar_debitos(
    empresa_id: Optional[str] = None,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    repo: DebitosRepository = Depends(get_debitos_repo)
):
    """Lista débitos com filtros"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    skip = (pagina - 1) * por_pagina
    debitos = await repo.list_debitos(filtro, skip, por_pagina)
    total = await repo.count_debitos(filtro)
    valor_total_aberto = await repo.aggregate_abertos(filtro)
    quantidade_abertos = await repo.count_abertos(filtro)
    return DebitoListResponse(
        debitos=[DebitoResponse(**d) for d in debitos],
        total=total,
        valor_total_aberto=valor_total_aberto,
        quantidade_abertos=quantidade_abertos,
        pagina=pagina,
        por_pagina=por_pagina
    )


@router.get("/{debito_id}", response_model=DebitoResponse)
async def obter_debito(debito_id: str, repo: DebitosRepository = Depends(get_debitos_repo)):
    """Obtém detalhes de um débito"""
    debito = await repo.get_debito(debito_id)
    if not debito:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    return DebitoResponse(**debito)


@router.put("/{debito_id}", response_model=DebitoResponse)
async def atualizar_debito(debito_id: str, dados: DebitoUpdate, repo: DebitosRepository = Depends(get_debitos_repo)):
    """Atualiza um débito"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    if "data_quitacao" in update_data and isinstance(update_data["data_quitacao"], date):
        update_data["data_quitacao"] = update_data["data_quitacao"].isoformat()
    debito = await repo.update_debito(debito_id, update_data)
    if not debito:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    return DebitoResponse(**debito)


@router.delete("/{debito_id}")
async def deletar_debito(debito_id: str, repo: DebitosRepository = Depends(get_debitos_repo)):
    """Deleta um débito"""
    ok = await repo.delete_debito(debito_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    return {"message": "Débito deletado com sucesso"}


@router.get("/resumo/geral")
async def resumo_debitos(empresa_id: Optional[str] = None, repo: DebitosRepository = Depends(get_debitos_repo)):
    """Obtém resumo geral de débitos"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    resumo = await repo.resumo_geral(filtro)
    return resumo


# =========================
# Exportar router
# =========================
debitos_router = router
