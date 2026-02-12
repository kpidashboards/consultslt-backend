from fastapi import APIRouter
from services.empresa_service import EmpresaService

router = APIRouter(prefix="/api/empresas", tags=["Empresas"])
service = EmpresaService()

@router.post("/")
async def criar_empresa(payload: dict):
    return await service.criar(payload)

@router.get("/")
async def listar_empresas():
    return await service.listar()
