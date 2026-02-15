from fastapi import APIRouter

from .auth import router as auth_router
from .empresas import router as empresas_router
# importe outros routers aqui se existirem

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(empresas_router)
