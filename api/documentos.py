from fastapi import APIRouter, Depends, HTTPException, status
from ..services.documento_service import DocumentoService  # Corrigido: import relativo
from ..core.database import get_database  # Corrigido: import relativo
from ..dependencies.auth import get_current_user  # Corrigido: import relativo

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def get_documento_service(db=Depends(get_database)):
    return DocumentoService(db)


@router.get("/", status_code=200)
async def listar_documentos(
    service: DocumentoService = Depends(get_documento_service),
    user=Depends(get_current_user)
):
    return await service.listar_documentos()


@router.post("/", status_code=201)
async def criar_documento(
    documento: dict,
    service: DocumentoService = Depends(get_documento_service),
    user=Depends(get_current_user)
):
    return await service.criar_documento(documento)


@router.get("/{documento_id}", status_code=200)
async def obter_documento(
    documento_id: str,
    service: DocumentoService = Depends(get_documento_service),
    user=Depends(get_current_user)
):
    doc = await service.obter_documento(documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return doc


# Exportação obrigatória para compatibilidade
__all__ = ["router"]
