"""Endpoints para gestão de Débitos"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

from schemas.debito import (
    DebitoCreate,
    DebitoUpdate,
    DebitoResponse,
    DebitoListResponse,
    TipoDebito,
    StatusDebito
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debitos", tags=["Débitos"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=DebitoResponse)
async def criar_debito(dados: DebitoCreate, db=Depends(get_db)):
    """Cria um novo débito"""
    debito_dict = dados.model_dump()
    debito_dict["id"] = str(uuid.uuid4())
    debito_dict["status"] = StatusDebito.ABERTO
    debito_dict["created_at"] = datetime.utcnow()
    debito_dict["updated_at"] = None
    
    if "data_inscricao" in debito_dict:
        from datetime import date
        if isinstance(debito_dict["data_inscricao"], date):
            debito_dict["data_inscricao"] = debito_dict["data_inscricao"].isoformat()
    
    await db.debitos.insert_one(debito_dict)
    return DebitoResponse(**debito_dict)

@router.get("/", response_model=DebitoListResponse)
async def listar_debitos(
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[TipoDebito] = Query(default=None),
    status: Optional[StatusDebito] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
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
    cursor = db.debitos.find(filtro).skip(skip).limit(por_pagina)
    debitos = await cursor.to_list(length=por_pagina)
    total = await db.debitos.count_documents(filtro)
    
    # Calcular totais
    pipeline_abertos = [
        {"$match": {**filtro, "status": StatusDebito.ABERTO}},
        {"$group": {"_id": None, "total": {"$sum": "$valor_total"}}}
    ]
    result_abertos = await db.debitos.aggregate(pipeline_abertos).to_list(length=1)
    valor_total_aberto = result_abertos[0]["total"] if result_abertos else 0
    
    quantidade_abertos = await db.debitos.count_documents({**filtro, "status": StatusDebito.ABERTO})
    
    return DebitoListResponse(
        debitos=[DebitoResponse(**d) for d in debitos],
        total=total,
        valor_total_aberto=valor_total_aberto,
        quantidade_abertos=quantidade_abertos,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{debito_id}", response_model=DebitoResponse)
async def obter_debito(debito_id: str, db=Depends(get_db)):
    """Obtém detalhes de um débito"""
    debito = await db.debitos.find_one({"id": debito_id})
    if not debito:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    return DebitoResponse(**debito)

@router.put("/{debito_id}", response_model=DebitoResponse)
async def atualizar_debito(debito_id: str, dados: DebitoUpdate, db=Depends(get_db)):
    """Atualiza um débito"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    update_data["updated_at"] = datetime.utcnow()
    
    if "data_quitacao" in update_data:
        from datetime import date
        if isinstance(update_data["data_quitacao"], date):
            update_data["data_quitacao"] = update_data["data_quitacao"].isoformat()
    
    result = await db.debitos.update_one({"id": debito_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    
    debito = await db.debitos.find_one({"id": debito_id})
    return DebitoResponse(**debito)

@router.delete("/{debito_id}")
async def deletar_debito(debito_id: str, db=Depends(get_db)):
    """Deleta um débito"""
    result = await db.debitos.delete_one({"id": debito_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Débito não encontrado")
    return {"message": "Débito deletado com sucesso"}

@router.get("/resumo/geral")
async def resumo_debitos(
    empresa_id: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """Obtém resumo geral de débitos"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    pipeline = [
        {"$match": filtro},
        {"$group": {
            "_id": "$status",
            "quantidade": {"$sum": 1},
            "valor_total": {"$sum": "$valor_total"}
        }}
    ]
    
    result = await db.debitos.aggregate(pipeline).to_list(length=None)
    
    resumo = {}
    for item in result:
        resumo[item["_id"]] = {
            "quantidade": item["quantidade"],
            "valor_total": item["valor_total"]
        }
    
    return resumo
