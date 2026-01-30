"""Endpoints da API"""

from .auth import auth_router
from .fiscal import fiscal_router
from .sharepoint import sharepoint_router
from .documentos import documentos_router
from .obrigacoes import obrigacoes_router
from .robots import robots_router
from .auditoria import auditoria_router
from .health import health_router

__all__ = [
    "auth_router",
    "fiscal_router",
    "sharepoint_router",
    "documentos_router",
    "obrigacoes_router",
    "robots_router",
    "auditoria_router",
    "health_router",
]
