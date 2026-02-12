import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from backend.core.database import get_database
from backend.schemas.fiscal import FiscalCreate, FiscalUpdate, FiscalResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fiscal", tags=["Fiscal"])

# Listar todos os registros fiscais
@router.get("/", response_model=List[FiscalResponse])
async def listar_fiscais():
    db = get_database()
    fiscals = await db["fiscal"].find().to_list(100)
    for f in fiscals:
        f["id"] = str(f["_id"])
    return fiscals

# Criar novo registro fiscal
@router.post("/", response_model=FiscalResponse)
async def criar_fiscal(fiscal: FiscalCreate):
    db = get_database()
    fiscal_dict = fiscal.dict()
    fiscal_dict["_id"] = str(uuid.uuid4())
    fiscal_dict["created_at"] = datetime.utcnow()
    fiscal_dict["updated_at"] = None
    await db["fiscal"].insert_one(fiscal_dict)
    fiscal_dict["id"] = fiscal_dict["_id"]
    return fiscal_dict

# Atualizar registro fiscal existente
@router.put("/{fiscal_id}", response_model=FiscalResponse)
async def atualizar_fiscal(fiscal_id: str, fiscal: FiscalUpdate):
    db = get_database()
    result = await db["fiscal"].update_one(
        {"_id": fiscal_id},
        {"$set": {**fiscal.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registro fiscal não encontrado")
    fiscal_atualizado = await db["fiscal"].find_one({"_id": fiscal_id})
    fiscal_atualizado["id"] = fiscal_atualizado["_id"]
    return fiscal_atualizado

# Deletar registro fiscal
@router.delete("/{fiscal_id}")
async def deletar_fiscal(fiscal_id: str):
    db = get_database()
    result = await db["fiscal"].delete_one({"_id": fiscal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registro fiscal não encontrado")
    return {"detail": "Registro fiscal deletado com sucesso"}
