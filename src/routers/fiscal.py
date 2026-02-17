from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

# Configuração do MongoDB
from ..database import get_database

db_name = "consultslt_db"
collection_name = "fiscal_iris"

fiscal_router = APIRouter(prefix="/api/fiscal", tags=["Fiscal"])

ecac_router = APIRouter(prefix="/ecac", tags=["e-CAC"])

# Modelos Pydantic
class FiscalIris(BaseModel):
    empresa: str
    cnpj: str
    periodo: str
    receitaBruta12M: float
    receitaMensal: float
    folhaSalarios12M: float
    fatorR: float
    anexo: str
    valorDAS: float
    certidoes: Optional[List[dict]] = []
    pendencias: Optional[List[dict]] = []
    origem: str
    userId: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None

# Rotas do módulo fiscal (IRIS)
@fiscal_router.post("/iris")
async def criar_calculo_fiscal(data: FiscalIris, db: AsyncIOMotorClient = Depends(get_database)):
    data.createdAt = datetime.utcnow()
    data.updatedAt = datetime.utcnow()
    result = await db[db_name][collection_name].insert_one(data.dict())
    return {"id": str(result.inserted_id)}

@fiscal_router.get("/iris")
async def listar_calculos_fiscais(db: AsyncIOMotorClient = Depends(get_database)):
    calculos = await db[db_name][collection_name].find({"deletedAt": None}).to_list(100)
    return calculos

@fiscal_router.get("/iris/{id}")
async def buscar_calculo_fiscal(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    calculo = await db[db_name][collection_name].find_one({"_id": ObjectId(id), "deletedAt": None})
    if not calculo:
        raise HTTPException(status_code=404, detail="Cálculo não encontrado")
    return calculo

@fiscal_router.put("/iris/{id}")
async def atualizar_calculo_fiscal(id: str, data: FiscalIris, db: AsyncIOMotorClient = Depends(get_database)):
    data.updatedAt = datetime.utcnow()
    result = await db[db_name][collection_name].update_one(
        {"_id": ObjectId(id), "deletedAt": None},
        {"$set": data.dict(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cálculo não encontrado")
    return {"message": "Cálculo atualizado com sucesso"}

@fiscal_router.delete("/iris/{id}")
async def excluir_calculo_fiscal(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    result = await db[db_name][collection_name].update_one(
        {"_id": ObjectId(id), "deletedAt": None},
        {"$set": {"deletedAt": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cálculo não encontrado")
    return {"message": "Cálculo excluído com sucesso"}

# Rotas do e-CAC
@ecac_router.get("/pendencias/{cnpj}")
async def consultar_pendencias(cnpj: str, db: AsyncIOMotorClient = Depends(get_database)):
    pendencias = [
        {"descricao": "DAS em atraso", "periodo": "01/2025"},
        {"descricao": "Multa por atraso", "periodo": "12/2024"}
    ]
    await db[db_name][collection_name].update_one(
        {"cnpj": cnpj},
        {"$set": {"pendencias": pendencias, "updatedAt": datetime.utcnow()}},
        upsert=True
    )
    return pendencias

@ecac_router.get("/certidoes/{cnpj}")
async def consultar_certidoes(cnpj: str, db: AsyncIOMotorClient = Depends(get_database)):
    certidoes = {"status": "regular", "consultadoEm": datetime.utcnow()}
    await db[db_name][collection_name].update_one(
        {"cnpj": cnpj},
        {"$set": {"certidoes": certidoes, "updatedAt": datetime.utcnow()}},
        upsert=True
    )
    return certidoes

# Registro de routers
fiscal_router.include_router(ecac_router)

# Exportar o router
app.include_router(fiscal_router)