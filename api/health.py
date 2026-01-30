"""
Endpoints de Health Check
- Simples: /api/health
- Detalhado: /api/health/detailed
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import logging

from core.database import get_db

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["Health"])


@health_router.get("")
async def health_check():
    """
    Health simples (liveness)
    """
    return {
        "status": "healthy",
        "service": "sltweb-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/detailed")
async def detailed_health(db=Depends(get_db)):
    """
    Health detalhado (readiness)
    """
    result = {
        "status": "healthy",
        "service": "sltweb-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # ===============================
    # MongoDB
    # ===============================
    try:
        await db.command("ping")
        result["checks"]["mongodb"] = {"status": "ok"}
    except Exception as e:
        logger.exception("Erro no health check do MongoDB")
        result["checks"]["mongodb"] = {
            "status": "error",
            "error": str(e)
        }
        result["status"] = "degraded"

    return result
