from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

# Configuração do FastAPI
app = FastAPI()

# Configuração do MongoDB
MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client["consultSLTweb"]
guias_collection = db.get_collection("guias")

# Modelos Pydantic
class Recalculo(BaseModel):
    dataRecalculo: datetime
    novaDataVencimento: str
    juros: float
    multa: float
    valorFinal: float

class Guia(BaseModel):
    empresa: str
    tipo: str = "DAS"
    regime: str
    competencia: str
    valor: float
    vencimento: str
    status: str = "pendente"
    pdfPath: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    userId: str
    historicoRecalculos: List[Recalculo] = []
    deletedAt: Optional[datetime] = None

# Rotas CRUD
@app.post("/api/guias", response_model=Guia)
async def criar_guia(guia: Guia):
    guia_dict = guia.dict()
    result = await guias_collection.insert_one(guia_dict)
    if result.inserted_id:
        return guia
    raise HTTPException(status_code=500, detail="Erro ao criar guia")

@app.get("/api/guias", response_model=List[Guia])
async def listar_guias():
    guias = await guias_collection.find({"deletedAt": None}).to_list(length=100)
    return guias

@app.get("/api/guias/{id}", response_model=Guia)
async def detalhar_guia(id: str):
    guia = await guias_collection.find_one({"_id": ObjectId(id), "deletedAt": None})
    if guia:
        return guia
    raise HTTPException(status_code=404, detail="Guia não encontrada")

@app.put("/api/guias/{id}", response_model=Guia)
async def atualizar_guia(id: str, guia: Guia):
    guia_dict = guia.dict()
    guia_dict["updatedAt"] = datetime.utcnow()
    result = await guias_collection.update_one({"_id": ObjectId(id)}, {"$set": guia_dict})
    if result.modified_count:
        return guia
    raise HTTPException(status_code=404, detail="Guia não encontrada para atualização")

@app.delete("/api/guias/{id}")
async def excluir_guia(id: str):
    result = await guias_collection.update_one({"_id": ObjectId(id)}, {"$set": {"deletedAt": datetime.utcnow()}})
    if result.modified_count:
        return {"msg": "Guia excluída com sucesso"}
    raise HTTPException(status_code=404, detail="Guia não encontrada para exclusão")