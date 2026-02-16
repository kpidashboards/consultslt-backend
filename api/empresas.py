"""
API Routes para Gerenciamento de Empresas
CRUD completo com validações e tratamento de erros
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from backend.core.database import get_db
from backend.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse

router = APIRouter(prefix="/empresas", tags=["Empresas"])

# ===============================
# HELPER: Converter MongoDB document para response
# ===============================
def fix_empresa_id(empresa):
    """Converte _id do MongoDB para id na resposta"""
    if empresa and "_id" in empresa:
        empresa["id"] = str(empresa["_id"])
        empresa.pop("_id", None)
    return empresa

# ===============================
# CREATE - POST /api/empresas/
# ===============================
@router.post("/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def criar_empresa(empresa: EmpresaCreate, db=Depends(get_db)):
    """
    Cria uma nova empresa
    - Valida CNPJ (não pode ser duplicado)
    - Define timestamps automáticos
    - Retorna a empresa criada com ID
    """
    # Preparar dados
    empresa_dict = empresa.model_dump()
    empresa_dict["created_at"] = datetime.utcnow()
    empresa_dict["updated_at"] = None
    
    try:
        # Inserir no MongoDB
        insert_result = await db["empresas"].insert_one(empresa_dict)
        empresa_dict["_id"] = insert_result.inserted_id
        
        return fix_empresa_id(empresa_dict)
    
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma empresa cadastrada com o CNPJ {empresa.cnpj}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar empresa: {str(e)}"
        )

# ===============================
# READ - GET /api/empresas/
# ===============================
@router.get("/", response_model=List[EmpresaResponse])
async def listar_empresas(db=Depends(get_db)):
    """
    Lista todas as empresas cadastradas
    - Retorna lista vazia se nenhuma empresa existe
    - Ordena por razao_social
    """
    try:
        cursor = db["empresas"].find().sort("razao_social", 1)
        empresas = await cursor.to_list(length=None)
        return [fix_empresa_id(e) for e in empresas]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar empresas: {str(e)}"
        )

# ===============================
# READ BY ID - GET /api/empresas/{empresa_id}
# ===============================
@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: str, db=Depends(get_db)):
    """
    Obtém uma empresa específica pelo ID
    """
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    try:
        empresa = await db["empresas"].find_one({"_id": obj_id})
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        return fix_empresa_id(empresa)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter empresa: {str(e)}"
        )

# ===============================
# UPDATE - PUT /api/empresas/{empresa_id}
# ===============================
@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: str, empresa: EmpresaUpdate, db=Depends(get_db)):
    """
    Atualiza uma empresa existente
    - Apenas campos fornecidos são atualizados
    - Define updated_at automaticamente
    """
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    try:
        # Preparar dados para atualização (remover None values)
        update_data = {k: v for k, v in empresa.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Atualizar no banco
        result = await db["empresas"].update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        
        # Retornar empresa atualizada
        updated_empresa = await db["empresas"].find_one({"_id": obj_id})
        return fix_empresa_id(updated_empresa)
        
    except HTTPException:
        raise
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe outra empresa com este CNPJ"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar empresa: {str(e)}"
        )

# ===============================
# DELETE - DELETE /api/empresas/{empresa_id}
# ===============================
@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_empresa(empresa_id: str, db=Depends(get_db)):
    """
    Deleta uma empresa
    """
    try:
        obj_id = ObjectId(empresa_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da empresa inválido"
        )

    try:
        result = await db["empresas"].delete_one({"_id": obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar empresa: {str(e)}"
        )