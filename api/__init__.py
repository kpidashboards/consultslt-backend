"""
Router central da API
Responsável por registrar todas as rotas do sistema
"""

from fastapi import APIRouter

# ===============================
# CRIAÇÃO DO ROUTER PRINCIPAL
# ===============================
api_router = APIRouter()

# ===============================
# IMPORTAÇÃO DAS ROTAS
# (IMPORTAR APÓS CRIAR api_router)
# ===============================

from .auth import router as auth_router
from .users import router as users_router
from .empresas import router as empresas_router
from .alertas import router as alertas_router
from .auditoria import router as auditoria_router

# Auth Entra é opcional — evita quebrar se não existir
try:
    from .auth_entra import router as auth_entra_router
except ImportError:
    auth_entra_router = None


# ===============================
# REGISTRO DAS ROTAS
# ===============================

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    empresas_router,
    prefix="/empresas",
    tags=["Empresas"],
)

api_router.include_router(
    alertas_router,
    prefix="/alertas",
    tags=["Alertas"],
)

api_router.include_router(
    auditoria_router,
    prefix="/auditoria",
    tags=["Auditoria"],
)

# ===============================
# ENTRA ID (SE EXISTIR)
# ===============================
if auth_entra_router:
    api_router.include_router(
        auth_entra_router,
        prefix="/auth/entra",
        tags=["Auth EntraID"],
    )
