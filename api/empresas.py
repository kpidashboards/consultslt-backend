from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from backend.core.database import get_db
from backend.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse

router = APIRouter(prefix="/empresas", tags=["Empresas"])

def fix_empresa_id(empresa):
    if empresa and "_id" in empresa:
        empresa["id"] = str(empresa["_id"])
    return empresa

@router.post("/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def criar_empresa(empresa: EmpresaCreate, db=Depends(get_db)):
    """
    Cria uma nova empresa. 
    Captura DuplicateKeyError caso o CNPJ já exista e retorna 409 Conflict.
    """
    empresa_dict = empresa.model_dump()
    empresa_dict["created_at"] = datetime.utcnow()
    empresa_dict["updated_at"] = None
    empresa_dict["ativo"] = True
    
    try:
        # Tenta inserir no MongoDB
        insert_result = await db["empresas"].insert_one(empresa_dict)
        empresa_dict["_id"] = insert_result.inserted_id
        return fix_empresa_id(empresa_dict)
    
    except DuplicateKeyError:
        # ✅ TRATAMENTO DO ERRO: Retorna uma resposta clara em vez de quebrar a API
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma empresa cadastrada com o CNPJ {empresa.cnpj}"
        )
    except Exception as e:
        # Captura outros erros inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar empresa: {str(e)}"
        )

@router.get("/", response_model=List[EmpresaResponse])
async def listar_empresas(db=Depends(get_db)):
    cursor = db["empresas"].find()
    empresas = await cursor.to_list(length=100)
    return [fix_empresa_id(e) for e in empresas]

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: str, db=Depends(get_db)):
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID inválido")
        
    empresa = await db["empresas"].find_one({"_id": obj_id})
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return fix_empresa_id(empresa)

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: str, empresa: EmpresaUpdate, db=Depends(get_db)):
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID inválido")
        
    update_data = {k: v for k, v in empresa.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db["empresas"].update_one(
        {"_id": obj_id}, {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
    updated_empresa = await db["empresas"].find_one({"_id": obj_id})
    return fix_empresa_id(updated_empresa)

@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_empresa(empresa_id: str, db=Depends(get_db)):
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID da empresa inválido")

    result = await db["empresas"].delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    return None