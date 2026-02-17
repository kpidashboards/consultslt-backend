from fastapi import APIRouter

from .auth import router as auth_router
from .empresas import router as empresas_router
from .dashboard import router as dashboard_router
from backend.src.routers.fiscal import fiscal_router
from .auditoria import router as auditoria_router
from .alertas import router as alertas_router
from backend.src.routers.fiscal import insert_test_document
from backend.src.routers.fiscal import testar_fiscal_data
from backend.src.routers.fiscal import listar_todos_fiscal_data

api_router = APIRouter()

# Registro manual da rota temporária
api_router.add_api_route(
    path="/fiscal/fiscal_data/test/insert",
    endpoint=insert_test_document,
    methods=["POST"],
    tags=["Fiscal"]
)

# Registro manual da rota `/fiscal_data/test/all`
api_router.add_api_route(
    path="/fiscal/fiscal_data/test/all",
    endpoint=listar_todos_fiscal_data,
    methods=["GET"],
    tags=["Fiscal"]
)

# Registro manual da rota `/fiscal_data/test/all-documents`
api_router.add_api_route(
    path="/fiscal/fiscal_data/test/all-documents",
    endpoint=listar_todos_fiscal_data,
    methods=["GET"],
    tags=["Fiscal"]
)

# Registro manual da rota `/fiscal_data/test/{id}`
api_router.add_api_route(
    path="/fiscal/fiscal_data/test/{id}",
    endpoint=testar_fiscal_data,
    methods=["GET"],
    tags=["Fiscal"]
)

api_router.include_router(auth_router)
api_router.include_router(empresas_router)
api_router.include_router(dashboard_router)
api_router.include_router(fiscal_router, prefix="/fiscal", tags=["Fiscal"])
api_router.include_router(auditoria_router, prefix="/auditoria", tags=["Auditoria"])
api_router.include_router(alertas_router, prefix="/alertas", tags=["Alertas"])
