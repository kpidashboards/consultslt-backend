import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# 🔥 garante carregamento do .env
load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB") or os.getenv("DB_NAME")

if not MONGO_URL:
    raise RuntimeError("❌ MONGO_URL não configurada no .env")

if not DB_NAME:
    raise RuntimeError("❌ MONGO_DB / DB_NAME não configurado no .env")

_client: AsyncIOMotorClient | None = None
_db = None


async def init_db():
    """
    Inicializa conexão com MongoDB
    """
    global _client, _db

    if _client:
        return

    logger.info("🔄 Conectando ao MongoDB...")
    _client = AsyncIOMotorClient(MONGO_URL)

    # testa conexão
    await _client.admin.command("ping")

    _db = _client[DB_NAME]
    logger.info(f"✅ MongoDB conectado: {DB_NAME}")


async def close_db():
    """
    Fecha conexão com MongoDB
    """
    global _client

    if _client:
        logger.info("🛑 Fechando conexão com MongoDB...")
        _client.close()
        _client = None
        logger.info("✅ MongoDB desconectado")


def get_db():
    """
    Dependency para FastAPI (Depends)
    """
    if _db is None:
        raise RuntimeError("❌ Banco de dados não inicializado")
    return _db
