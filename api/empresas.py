"""Endpoints para gestão de Empresas"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

from schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse,
    EmpresaListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/empresas", tags=["Empresas"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=EmpresaResponse)
async def criar_empresa(dados: EmpresaCreate, db=Depends(get_db)):
    """Cria uma nova empresa"""
    empresa_dict = dados.model_dump()
    empresa_dict["id"] = str(uuid.uuid4())
    empresa_dict["created_at"] = datetime.utcnow()
    empresa_dict["updated_at"] = None
    
    await db.empresas.insert_one(empresa_dict)
    return EmpresaResponse(**empresa_dict)

@router.get("/", response_model=EmpresaListResponse)
async def listar_empresas(
    ativo: Optional[bool] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
):
    """Lista empresas com filtros"""
    filtro = {}
    if ativo is not None:
        filtro["ativo"] = ativo
    
    skip = (pagina - 1) * por_pagina
    cursor = db.empresas.find(filtro).skip(skip).limit(por_pagina)
    empresas = await cursor.to_list(length=por_pagina)
    total = await db.empresas.count_documents(filtro)
    
    return EmpresaListResponse(
        empresas=[EmpresaResponse(**e) for e in empresas],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: str, db=Depends(get_db)):
    """Obtém detalhes de uma empresa"""
    empresa = await db.empresas.find_one({"id": empresa_id})
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return EmpresaResponse(**empresa)

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: str, dados: EmpresaUpdate, db=Depends(get_db)):
    """Atualiza uma empresa"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    update_data["updated_at"] = datetime.utcnow()
    result = await db.empresas.update_one({"id": empresa_id}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa = await db.empresas.find_one({"id": empresa_id})
    return EmpresaResponse(**empresa)

@router.delete("/{empresa_id}")
async def deletar_empresa(empresa_id: str, db=Depends(get_db)):
    """Deleta uma empresa (soft delete)"""
    result = await db.empresas.update_one(
        {"id": empresa_id},
        {"$set": {"ativo": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"message": "Empresa desativada com sucesso"}
