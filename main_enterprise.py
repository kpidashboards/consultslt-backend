"""
SLTWEB Enterprise - Aplicação FastAPI
Arquivo principal da API
"""

from dotenv import load_dotenv
load_dotenv()  # 🔥 PRIMEIRA COISA DO ARQUIVO

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db, close_db

# ===============================
# Importar routers
# ===============================
from api import (
    auth_router,
    fiscal_router,
    sharepoint_router,
    documentos_router,
    obrigacoes_router,
    robots_router,
    auditoria_router,
    health_router,
)

# ===============================
# Logging
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sltweb")

# ===============================
# App FastAPI
# ===============================
app = FastAPI(
    title="SLTWEB - SLT Consult Enterprise",
    description="Plataforma unificada de gestão fiscal e automação documental",
    version="1.0.0",
)

# ===============================
# Eventos de startup / shutdown
# ===============================
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando aplicação SLTWEB Enterprise...")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# Rotas
# ===============================
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(fiscal_router, prefix="/api/fiscal", tags=["Fiscal"])
app.include_router(sharepoint_router, prefix="/api/sharepoint", tags=["SharePoint"])
app.include_router(documentos_router, prefix="/api/documentos", tags=["Documentos"])
app.include_router(obrigacoes_router, prefix="/api/obrigacoes", tags=["Obrigações"])
app.include_router(robots_router, prefix="/api/robots", tags=["Robôs"])
app.include_router(auditoria_router, prefix="/api/auditoria", tags=["Auditoria"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])

@app.get("/")
async def root():
    return {"message": "API SLTWEB funcionando!"}
