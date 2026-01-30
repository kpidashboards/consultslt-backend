"""Endpoints para gestão de Certidões"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date, timedelta
import uuid

from schemas.certidao import (
    CertidaoCreate,
    CertidaoUpdate,
    CertidaoResponse,
    CertidaoListResponse,
    TipoCertidao,
    StatusCertidao
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/certidoes", tags=["Certidões"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

def calcular_status_certidao(data_validade):
    """Calcula o status baseado na data de validade"""
    if isinstance(data_validade, str):
        data_validade = date.fromisoformat(data_validade)
    
    dias_ate_vencer = (data_validade - date.today()).days
    
    if dias_ate_vencer < 0:
        return StatusCertidao.VENCIDA, dias_ate_vencer
    elif dias_ate_vencer <= 30:
        return StatusCertidao.PROXIMA_VENCER, dias_ate_vencer
    else:
        return StatusCertidao.VALIDA, dias_ate_vencer

@router.post("/", response_model=CertidaoResponse)
async def criar_certidao(dados: CertidaoCreate, db=Depends(get_db)):
    """Cria uma nova certidão"""
    certidao_dict = dados.model_dump()
    certidao_dict["id"] = str(uuid.uuid4())
    
    status, dias = calcular_status_certidao(certidao_dict["data_validade"])
    certidao_dict["status"] = status
    certidao_dict["dias_para_vencer"] = dias if dias > 0 else 0
    
    certidao_dict["created_at"] = datetime.utcnow()
    certidao_dict["updated_at"] = None
    
    if isinstance(certidao_dict.get("data_emissao"), date):
        certidao_dict["data_emissao"] = certidao_dict["data_emissao"].isoformat()
    if isinstance(certidao_dict.get("data_validade"), date):
        certidao_dict["data_validade"] = certidao_dict["data_validade"].isoformat()
    
    await db.certidoes.insert_one(certidao_dict)
    return CertidaoResponse(**certidao_dict)

@router.get("/", response_model=CertidaoListResponse)
async def listar_certidoes(
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[TipoCertidao] = Query(default=None),
    status: Optional[StatusCertidao] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
):
    """Lista certidões com filtros"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    
    skip = (pagina - 1) * por_pagina
    cursor = db.certidoes.find(filtro).skip(skip).limit(por_pagina)
    certidoes = await cursor.to_list(length=por_pagina)
    total = await db.certidoes.count_documents(filtro)
    
    validas = await db.certidoes.count_documents({**filtro, "status": StatusCertidao.VALIDA})
    vencidas = await db.certidoes.count_documents({**filtro, "status": StatusCertidao.VENCIDA})
    proximas_vencer = await db.certidoes.count_documents({**filtro, "status": StatusCertidao.PROXIMA_VENCER})
    
    return CertidaoListResponse(
        certidoes=[CertidaoResponse(**c) for c in certidoes],
        total=total,
        validas=validas,
        vencidas=vencidas,
        proximas_vencer=proximas_vencer,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{certidao_id}", response_model=CertidaoResponse)
async def obter_certidao(certidao_id: str, db=Depends(get_db)):
    """Obtém detalhes de uma certidão"""
    certidao = await db.certidoes.find_one({"id": certidao_id})
    if not certidao:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    return CertidaoResponse(**certidao)

@router.put("/{certidao_id}", response_model=CertidaoResponse)
async def atualizar_certidao(certidao_id: str, dados: CertidaoUpdate, db=Depends(get_db)):
    """Atualiza uma certidão"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    
    if "data_validade" in update_data:
        status, dias = calcular_status_certidao(update_data["data_validade"])
        update_data["status"] = status
        update_data["dias_para_vencer"] = dias if dias > 0 else 0
        if isinstance(update_data["data_validade"], date):
            update_data["data_validade"] = update_data["data_validade"].isoformat()
    
    if "data_emissao" in update_data and isinstance(update_data["data_emissao"], date):
        update_data["data_emissao"] = update_data["data_emissao"].isoformat()
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.certidoes.update_one({"id": certidao_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    
    certidao = await db.certidoes.find_one({"id": certidao_id})
    return CertidaoResponse(**certidao)

@router.delete("/{certidao_id}")
async def deletar_certidao(certidao_id: str, db=Depends(get_db)):
    """Deleta uma certidão"""
    result = await db.certidoes.delete_one({"id": certidao_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    return {"message": "Certidão deletada com sucesso"}

@router.post("/atualizar-status")
async def atualizar_status_certidoes(db=Depends(get_db)):
    """Atualiza status de todas as certidões baseado na data de validade"""
    certidoes = await db.certidoes.find({}).to_list(length=None)
    count = 0
    
    for cert in certidoes:
        status, dias = calcular_status_certidao(cert["data_validade"])
        await db.certidoes.update_one(
            {"id": cert["id"]},
            {"$set": {"status": status, "dias_para_vencer": dias if dias > 0 else 0, "updated_at": datetime.utcnow()}}
        )
        count += 1
    
    return {"message": f"{count} certidões atualizadas"}
