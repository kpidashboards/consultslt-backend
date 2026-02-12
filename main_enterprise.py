"""
ConsultSLT API
Arquivo principal da aplicação FastAPI
"""

# ===============================
# 🔥 PRIMEIRA COISA DO ARQUIVO
# ===============================
from dotenv import load_dotenv
load_dotenv()

# ===============================
# IMPORTS
# ===============================
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ===============================
# CONFIGURAÇÃO DE LOGGING
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("consultslt")

# ===============================
# CRIAÇÃO DA APP
# ===============================
app = FastAPI(
    title="ConsultSLT API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ===============================
# CORS (React Frontend)
# ===============================
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.5.162:3000",  # acesso LAN se necessário
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# EVENTOS DO BANCO
# ===============================
from backend.core.database import register_db_events
register_db_events(app)

# ===============================
# IMPORTAÇÃO DO ROUTER CENTRAL (RECOMENDADO)
# ===============================
from backend.api import api_router

# ===============================
# REGISTRO GLOBAL DAS ROTAS
# ===============================
app.include_router(api_router, prefix="/api")

# ===============================
# HEALTHCHECK
# ===============================
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
