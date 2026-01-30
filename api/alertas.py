"""Endpoints para gestão de Alertas"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

from schemas.alerta import (
    AlertaCreate,
    AlertaUpdate,
    AlertaResponse,
    AlertaListResponse,
    TipoAlerta,
    StatusAlerta,
    PrioridadeAlerta
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alertas", tags=["Alertas"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=AlertaResponse)
async def criar_alerta(dados: AlertaCreate, db=Depends(get_db)):
    """Cria um novo alerta"""
    alerta_dict = dados.model_dump()
    alerta_dict["id"] = str(uuid.uuid4())
    alerta_dict["status"] = StatusAlerta.PENDENTE
    alerta_dict["created_at"] = datetime.utcnow()
    alerta_dict["updated_at"] = None
    
    await db.alertas.insert_one(alerta_dict)
    return AlertaResponse(**alerta_dict)

@router.get("/", response_model=AlertaListResponse)
async def listar_alertas(
    tipo: Optional[TipoAlerta] = Query(default=None),
    status: Optional[StatusAlerta] = Query(default=None),
    prioridade: Optional[PrioridadeAlerta] = Query(default=None),
    empresa_id: Optional[str] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
):
    """Lista alertas com filtros"""
    filtro = {}
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    if prioridade:
        filtro["prioridade"] = prioridade
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    skip = (pagina - 1) * por_pagina
    cursor = db.alertas.find(filtro).skip(skip).limit(por_pagina)
    alertas = await cursor.to_list(length=por_pagina)
    total = await db.alertas.count_documents(filtro)
    nao_lidos = await db.alertas.count_documents({**filtro, "status": StatusAlerta.PENDENTE})
    pendentes = nao_lidos
    
    return AlertaListResponse(
        alertas=[AlertaResponse(**a) for a in alertas],
        total=total,
        nao_lidos=nao_lidos,
        pendentes=pendentes,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{alerta_id}", response_model=AlertaResponse)
async def obter_alerta(alerta_id: str, db=Depends(get_db)):
    """Obtém detalhes de um alerta"""
    alerta = await db.alertas.find_one({"id": alerta_id})
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return AlertaResponse(**alerta)

@router.put("/{alerta_id}", response_model=AlertaResponse)
async def atualizar_alerta(alerta_id: str, dados: AlertaUpdate, db=Depends(get_db)):
    """Atualiza um alerta"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    update_data["updated_at"] = datetime.utcnow()
    if "status" in update_data:
        if update_data["status"] == StatusAlerta.LIDO and "lido_em" not in update_data:
            update_data["lido_em"] = datetime.utcnow()
        if update_data["status"] == StatusAlerta.RESOLVIDO and "resolvido_em" not in update_data:
            update_data["resolvido_em"] = datetime.utcnow()
    
    result = await db.alertas.update_one({"id": alerta_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    alerta = await db.alertas.find_one({"id": alerta_id})
    return AlertaResponse(**alerta)

@router.delete("/{alerta_id}")
async def deletar_alerta(alerta_id: str, db=Depends(get_db)):
    """Deleta um alerta"""
    result = await db.alertas.delete_one({"id": alerta_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return {"message": "Alerta deletado com sucesso"}

@router.post("/marcar-como-lido")
async def marcar_como_lido(alerta_ids: list[str], db=Depends(get_db)):
    """Marca múltiplos alertas como lidos"""
    result = await db.alertas.update_many(
        {"id": {"$in": alerta_ids}},
        {"$set": {"status": StatusAlerta.LIDO, "lido_em": datetime.utcnow(), "updated_at": datetime.utcnow()}}
    )
    return {"message": f"{result.modified_count} alertas marcados como lidos"}
