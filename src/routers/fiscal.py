from fastapi import APIRouter, HTTPException, Depends, FastAPI
from bson import ObjectId
from datetime import datetime
from ..schemas.fiscal_iris import FiscalIrisSchema
from motor.motor_asyncio import AsyncIOMotorClient
from bson.errors import InvalidId

# Configuração do MongoDB
from backend.core.database import get_db as get_database

db_name = "consultslt_db"
collection_fiscal = "fiscal"
collection_fiscal_data = "fiscal_data"

fiscal_router = APIRouter(tags=["Fiscal"])

ecac_router = APIRouter(prefix="/ecac", tags=["e-CAC"])

# Rotas do módulo fiscal (IRIS)
@fiscal_router.post("/fiscal")
async def criar_fiscal(data: dict, db = Depends(get_database)):
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_fiscal].insert_one(data)
    return {"id": str(result.inserted_id)}

@fiscal_router.get("/fiscal")
async def listar_fiscal(db = Depends(get_database)):
    fiscais = await db[collection_fiscal].find().to_list(100)
    return fiscais

@fiscal_router.get("/fiscal_data")
async def listar_fiscal_data(db = Depends(get_database)):
    fiscais_data = await db[collection_fiscal_data].find().to_list(100)
    return fiscais_data

@fiscal_router.get("/fiscal/{id}")
async def buscar_fiscal(id: str, db = Depends(get_database)):
    fiscal = await db[collection_fiscal].find_one({"_id": ObjectId(id)})
    if not fiscal:
        raise HTTPException(status_code=404, detail="Fiscal não encontrado")
    return fiscal

@fiscal_router.get("/fiscal_data/{id}")
async def buscar_fiscal_data(id: str, db=Depends(get_database)):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    fiscal_data = await db[collection_fiscal_data].find_one({"_id": object_id})
    if not fiscal_data:
        raise HTTPException(status_code=404, detail="Fiscal Data não encontrado")
    return fiscal_data

@fiscal_router.get("/fiscal_data/test/all")
async def listar_todos_fiscal_data(db=Depends(get_database)):
    try:
        print("[DEBUG] Iniciando listagem de documentos na coleção fiscal_data")
        fiscais_data = await db["fiscal_data"].find().to_list(100)
        print(f"[DEBUG] Documentos encontrados: {fiscais_data}")
        return {"documents": fiscais_data}
    except Exception as e:
        print(f"[ERROR] Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {e}")

@fiscal_router.get("/fiscal_data/test/{id}")
async def testar_fiscal_data(id: str, db=Depends(get_database)):
    try:
        print(f"[DEBUG] Recebido ID: {id}")
        object_id = ObjectId(id)
        print(f"[DEBUG] ObjectId criado: {object_id}")
    except InvalidId as e:
        print(f"[ERROR] ID inválido: {e}")
        raise HTTPException(status_code=400, detail="ID inválido")

    try:
        print(f"[DEBUG] Consultando no banco de dados com ID: {object_id}")
        fiscal_data = await db["fiscal_data"].find_one({"_id": object_id})
        print(f"[DEBUG] Resultado da consulta: {fiscal_data}")
    except Exception as e:
        print(f"[ERROR] Erro ao consultar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")

    return {"exists": bool(fiscal_data), "data": fiscal_data}

@fiscal_router.put("/fiscal/{id}")
async def atualizar_fiscal(id: str, data: dict, db = Depends(get_database)):
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_fiscal].update_one(
        {"_id": ObjectId(id)},
        {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fiscal não encontrado")
    return {"message": "Fiscal atualizado com sucesso"}

@fiscal_router.put("/fiscal_data/{id}")
async def atualizar_fiscal_data(id: str, data: dict, db=Depends(get_database)):
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_fiscal_data].update_one(
        {"_id": ObjectId(id)},
        {"$set": data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fiscal Data não encontrado")
    return {"message": "Fiscal Data atualizado com sucesso"}

@fiscal_router.delete("/fiscal/{id}")
async def excluir_fiscal(id: str, db = Depends(get_database)):
    result = await db[collection_fiscal].delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fiscal não encontrado")
    return {"message": "Fiscal excluído com sucesso"}

@fiscal_router.delete("/fiscal_data/{id}")
async def excluir_fiscal_data(id: str, db=Depends(get_database)):
    result = await db[collection_fiscal_data].delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fiscal Data não encontrado")
    return {"message": "Fiscal Data excluído com sucesso"}

# Rotas do e-CAC
@ecac_router.get("/pendencias/{cnpj}")
async def consultar_pendencias(cnpj: str, db = Depends(get_database)):
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
async def consultar_certidoes(cnpj: str, db = Depends(get_database)):
    certidoes = {"status": "regular", "consultadoEm": datetime.utcnow()}
    await db[db_name][collection_name].update_one(
        {"cnpj": cnpj},
        {"$set": {"certidoes": certidoes, "updatedAt": datetime.utcnow()}},
        upsert=True
    )
    return certidoes

# Rotas temporárias
@fiscal_router.post("/fiscal_data/test/insert")
async def insert_test_document(db = Depends(get_database)):
    try:
        print("[DEBUG] Iniciando inserção do documento de teste.")
        test_document = {
            "_id": ObjectId("697bb8563e6fe45c7f619b37"),
            "tipo": "simples_nacional",
            "cnpj": "12.345.678/0001-00",
            "periodo_referencia": "2025-12",
            "aliquota_efetiva": 6.3,
            "created_at": datetime.utcnow()
        }

        print(f"[DEBUG] Documento a ser inserido: {test_document}")

        existing = await db["fiscal_data"].find_one({"_id": test_document["_id"]})
        print(f"[DEBUG] Documento existente: {existing}")

        if existing:
            raise HTTPException(status_code=400, detail="Documento já existe na coleção fiscal_data.")

        await db["fiscal_data"].insert_one(test_document)
        print("[DEBUG] Documento inserido com sucesso.")
        return {"message": "Documento de teste inserido com sucesso."}

    except Exception as e:
        print(f"[ERROR] Erro ao inserir documento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao inserir documento.")

@fiscal_router.get("/fiscal_data/test/all-documents")
async def listar_todos_fiscal_data():
    from backend.core.database import connect_db, get_db
    try:
        print("[DEBUG] Rota `/fiscal_data/test/all-documents` iniciada.")
        await connect_db()
        db = get_db()
        print("[DEBUG] Conexão com o banco de dados estabelecida.")

        print("[DEBUG] Listando todos os documentos da coleção fiscal_data.")
        fiscais_data = await db["fiscal_data"].find().to_list(100)
        print(f"[DEBUG] Documentos encontrados: {fiscais_data}")
        return {"documents": fiscais_data}
    except Exception as e:
        print(f"[ERROR] Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {e}")
    finally:
        print("[DEBUG] Rota `/fiscal_data/test/all-documents` finalizada.")

# Remover registro redundante do router
# app = FastAPI()
# app.include_router(fiscal_router)