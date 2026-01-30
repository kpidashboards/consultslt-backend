"""Endpoints para gestão de Guias de Pagamento"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import uuid

from schemas.guia import (
    GuiaCreate,
    GuiaUpdate,
    GuiaResponse,
    GuiaListResponse,
    TipoGuia,
    StatusGuia
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/guias", tags=["Guias"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=GuiaResponse)
async def criar_guia(dados: GuiaCreate, db=Depends(get_db)):
    """Cria uma nova guia"""
    guia_dict = dados.model_dump()
    guia_dict["id"] = str(uuid.uuid4())
    guia_dict["status"] = StatusGuia.PENDENTE
    guia_dict["created_at"] = datetime.utcnow()
    guia_dict["updated_at"] = None
    
    if isinstance(guia_dict.get("data_vencimento"), date):
        guia_dict["data_vencimento"] = guia_dict["data_vencimento"].isoformat()
    
    await db.guias.insert_one(guia_dict)
    return GuiaResponse(**guia_dict)

@router.get("/", response_model=GuiaListResponse)
async def listar_guias(
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[TipoGuia] = Query(default=None),
    status: Optional[StatusGuia] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
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
    cursor = db.guias.find(filtro).skip(skip).limit(por_pagina)
    guias = await cursor.to_list(length=por_pagina)
    total = await db.guias.count_documents(filtro)
    
    return GuiaListResponse(
        guias=[GuiaResponse(**g) for g in guias],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{guia_id}", response_model=GuiaResponse)
async def obter_guia(guia_id: str, db=Depends(get_db)):
    """Obtém detalhes de uma guia"""
    guia = await db.guias.find_one({"id": guia_id})
    if not guia:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    return GuiaResponse(**guia)

@router.put("/{guia_id}", response_model=GuiaResponse)
async def atualizar_guia(guia_id: str, dados: GuiaUpdate, db=Depends(get_db)):
    """Atualiza uma guia"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    update_data["updated_at"] = datetime.utcnow()
    if "data_pagamento" in update_data and isinstance(update_data["data_pagamento"], date):
        update_data["data_pagamento"] = update_data["data_pagamento"].isoformat()
    
    result = await db.guias.update_one({"id": guia_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    
    guia = await db.guias.find_one({"id": guia_id})
    return GuiaResponse(**guia)

@router.delete("/{guia_id}")
async def deletar_guia(guia_id: str, db=Depends(get_db)):
    """Deleta uma guia"""
    result = await db.guias.delete_one({"id": guia_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Guia não encontrada")
    return {"message": "Guia deletada com sucesso"}

@router.get("/proximos-vencimentos/lista")
async def proximos_vencimentos(
    dias: int = Query(default=30, ge=1, le=365),
    empresa_id: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """Obtém guias com vencimento próximo"""
    from datetime import timedelta
    data_limite = (date.today() + timedelta(days=dias)).isoformat()
    
    filtro = {
        "data_vencimento": {"$lte": data_limite},
        "status": StatusGuia.PENDENTE
    }
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    guias = await db.guias.find(filtro).to_list(length=100)
    return {"guias": [GuiaResponse(**g) for g in guias], "total": len(guias)}
