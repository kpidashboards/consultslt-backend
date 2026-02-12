from fastapi import APIRouter, Depends, HTTPException, status
from backend.repositories.obrigacoes_repository import ObrigacoesRepository
from backend.middleware.auth import get_current_user
from backend.schemas.obrigacao_fiscal import ObrigacaoFiscalCreate, ObrigacaoFiscalResponse, ObrigacaoFiscalUpdate
from typing import List

router = APIRouter(prefix="/obrigacoes-fiscais", tags=["Obrigações Fiscais"])

@router.get("/", response_model=List[ObrigacaoFiscalResponse])
async def listar_obrigacoes(current_user=Depends(get_current_user)):
    repo = ObrigacoesRepository()
    docs = await repo.list_all()
    return [ObrigacaoFiscalResponse(id=str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"}) for doc in docs]

@router.get("/{obrigacao_id}", response_model=ObrigacaoFiscalResponse)
async def consultar_obrigacao(obrigacao_id: str, current_user=Depends(get_current_user)):
    repo = ObrigacoesRepository()
    doc = await repo.get_by_id(obrigacao_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Obrigação não encontrada")
    return ObrigacaoFiscalResponse(id=str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"})

@router.post("/", response_model=ObrigacaoFiscalResponse, status_code=201)
async def criar_obrigacao(obrigacao: ObrigacaoFiscalCreate, current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores podem criar obrigações.")
    repo = ObrigacoesRepository()
    doc = await repo.create(obrigacao.dict())
    return ObrigacaoFiscalResponse(id=str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"})

@router.patch("/{obrigacao_id}/status", response_model=ObrigacaoFiscalResponse)
async def atualizar_status(obrigacao_id: str, update: ObrigacaoFiscalUpdate, current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores podem alterar status.")
    repo = ObrigacoesRepository()
    doc = await repo.update_status(obrigacao_id, update.status)
    if not doc:
        raise HTTPException(status_code=404, detail="Obrigação não encontrada")
    return ObrigacaoFiscalResponse(id=str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"})
