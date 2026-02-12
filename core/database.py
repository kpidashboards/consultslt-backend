"""
Database Core - Conexão MongoDB
Responsável apenas por conexão e inicialização de dados
"""

import os
import logging
from typing import Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

# IMPORT SEGURO (security NÃO importa database)
from backend.core.security import get_password_hash

# ===============================
# LOGGER
# ===============================
logger = logging.getLogger("database")

if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ===============================
# CONFIGURAÇÕES
# ===============================
MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "consultslt_db")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

# ===============================
# CONEXÃO
# ===============================
async def connect_db():
    global _client, _db

    if _client:
        return

    try:
        logger.info("🔄 Conectando ao MongoDB...")

        _client = AsyncIOMotorClient(MONGO_URL)
        await _client.admin.command("ping")

        _db = _client[DB_NAME]

        logger.info(f"✅ MongoDB conectado: {DB_NAME}")

        # Criar índices antes de inserir dados
        await create_indexes()

        # Inicializações seguras
        await init_users()
        await init_empresas()

    except Exception as e:
        logger.error(f"❌ Falha ao conectar ao MongoDB: {e}")
        raise


async def close_db():
    global _client

    if _client:
        _client.close()
        logger.info("🛑 Conexão com MongoDB encerrada")
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Banco de dados não inicializado")
    return _db


def register_db_events(app: FastAPI):
    app.add_event_handler("startup", connect_db)
    app.add_event_handler("shutdown", close_db)

# ===============================
# ÍNDICES
# ===============================
async def create_indexes():
    """
    Criação de índices únicos para evitar duplicidade
    """
    db = get_db()

    await db.users.create_index("email", unique=True)
    await db.empresas.create_index("cnpj", unique=True)

    logger.info("📌 Índices garantidos (users.email, empresas.cnpj)")

# ===============================
# INICIALIZAÇÃO DE USUÁRIOS
# ===============================
async def init_users():
    """
    Cria usuários iniciais se não existirem.
    Senhas sempre criptografadas.
    """

    db = get_db()

    users_list = [
        {
            "email": "admin@consultslt.com.br",
            "password": "Consult@2026",
            "role": "admin"
        },
        {
            "email": "william.lucas@sltconsult.com.br",
            "password": "Slt@2024",
            "role": "admin"
        },
        {
            "email": "admin@empresa.com",
            "password": "admin123",
            "role": "admin"
        }
    ]

    for user_data in users_list:
        existing = await db.users.find_one({"email": user_data["email"]})

        if not existing:
            hashed_password = get_password_hash(user_data["password"])

            await db.users.insert_one({
                "email": user_data["email"],
                "password": hashed_password,
                "role": user_data["role"],
                "last_login": None,
                "created_at": datetime.utcnow(),
                "active": True
            })

            logger.info(f"⚡ Usuário inicial criado: {user_data['email']}")
        else:
            logger.info(f"ℹ️ Usuário {user_data['email']} já existe. Pulando.")

# ===============================
# INICIALIZAÇÃO DE EMPRESAS
# ===============================
async def init_empresas():
    """
    Cria empresa inicial se o CNPJ não existir.
    """

    db = get_db()

    empresas_iniciais = [
        {
            "cnpj": "11222333000181",
            "razao_social": "Empresa Exemplo LTDA",
            "nome_fantasia": "Empresa Exemplo",
            "regime": "SIMPLES",
            "ativo": True,
            "created_at": datetime.utcnow()
        }
    ]

    for empresa_data in empresas_iniciais:
        existing = await db.empresas.find_one({"cnpj": empresa_data["cnpj"]})

        if not existing:
            await db.empresas.insert_one(empresa_data)
            logger.info(f"🏢 Empresa inicial criada: {empresa_data['cnpj']}")
        else:
            logger.info(f"ℹ️ Empresa {empresa_data['cnpj']} já existe. Pulando.")
