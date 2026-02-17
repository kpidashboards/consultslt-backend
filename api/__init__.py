from fastapi import APIRouter

from .auth import router as auth_router
from .empresas import router as empresas_router
from .dashboard import router as dashboard_router
from backend.src.routers.fiscal import fiscal_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(empresas_router)
api_router.include_router(dashboard_router)
api_router.include_router(fiscal_router, prefix="/fiscal", tags=["Fiscal"])
