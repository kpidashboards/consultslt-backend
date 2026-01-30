"""Endpoints para Configurações do Sistema"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

from schemas.configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoUpdate,
    ConfiguracaoResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/configuracoes", tags=["Configurações"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=ConfiguracaoResponse)
async def criar_configuracao(dados: ConfiguracaoCreate, db=Depends(get_db)):
    """Cria uma nova configuração"""
    # Verificar se chave já existe
    existe = await db.configuracoes.find_one({"chave": dados.chave})
    if existe:
        raise HTTPException(status_code=400, detail="Chave já existe")
    
    config_dict = dados.model_dump()
    config_dict["id"] = str(uuid.uuid4())
    config_dict["created_at"] = datetime.utcnow()
    config_dict["updated_at"] = None
    
    await db.configuracoes.insert_one(config_dict)
    return ConfiguracaoResponse(**config_dict)

@router.get("/", response_model=list[ConfiguracaoResponse])
async def listar_configuracoes(
    categoria: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """Lista configurações"""
    filtro = {}
    if categoria:
        filtro["categoria"] = categoria
    
    configs = await db.configuracoes.find(filtro).to_list(length=100)
    return [ConfiguracaoResponse(**c) for c in configs]

@router.get("/chave/{chave}", response_model=ConfiguracaoResponse)
async def obter_configuracao_por_chave(chave: str, db=Depends(get_db)):
    """Obtém configuração por chave"""
    config = await db.configuracoes.find_one({"chave": chave})
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return ConfiguracaoResponse(**config)

@router.get("/{config_id}", response_model=ConfiguracaoResponse)
async def obter_configuracao(config_id: str, db=Depends(get_db)):
    """Obtém configuração por ID"""
    config = await db.configuracoes.find_one({"id": config_id})
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return ConfiguracaoResponse(**config)

@router.put("/{config_id}", response_model=ConfiguracaoResponse)
async def atualizar_configuracao(config_id: str, dados: ConfiguracaoUpdate, db=Depends(get_db)):
    """Atualiza uma configuração"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    update_data["updated_at"] = datetime.utcnow()
    result = await db.configuracoes.update_one({"id": config_id}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    config = await db.configuracoes.find_one({"id": config_id})
    return ConfiguracaoResponse(**config)

@router.delete("/{config_id}")
async def deletar_configuracao(config_id: str, db=Depends(get_db)):
    """Deleta uma configuração"""
    result = await db.configuracoes.delete_one({"id": config_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return {"message": "Configuração deletada com sucesso"}
