from fastapi import APIRouter, Depends, HTTPException, status
from ..services.auditoria_service import AuditoriaService
from backend.core.database import get_db

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])

def get_auditoria_service(db=Depends(get_db)):
    return AuditoriaService(db)

@router.get("/", status_code=200)
async def listar_auditorias(
    service: AuditoriaService = Depends(get_auditoria_service)
):
    return await service.listar()

@router.get("/{id}", status_code=200)
async def obter_auditoria(
    id: str,
    service: AuditoriaService = Depends(get_auditoria_service)
):
    auditoria = await service.obter(id)
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoria não encontrada")
    return auditoria

@router.post("/", status_code=201)
async def criar_auditoria(
    payload: dict,
    service: AuditoriaService = Depends(get_auditoria_service)
):
    return await service.criar(payload)

__all__ = ["router"]