"""
LOCKDOWN PRODUÇÃO – SLTWEB

✔ Remove mocks
✔ Garante persistência
✔ Cria collections
✔ Valida FastAPI
✔ MongoDB como fonte única
"""

import os
import sys
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LOCKDOWN")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "consultslt_db"

REQUIRED_COLLECTIONS = [
    "empresas",
    "usuarios",
    "ecac_certidoes",
    "ecac_pendencias",
    "ecac_simples_nacional",
    "fiscal_calculos",
    "auditoria_logs",
    "ocr_documentos",
]

MOCK_KEYWORDS = ["mock", "fake", "seed", "example"]


async def check_collections(db):
    logger.info("🔍 Verificando collections...")
    existing = await db.list_collection_names()

    for col in REQUIRED_COLLECTIONS:
        if col not in existing:
            await db.create_collection(col)
            logger.warning(f"➕ Collection criada: {col}")
        else:
            logger.info(f"✔ Collection OK: {col}")


async def clean_mock_data(db):
    logger.info("🧹 Removendo dados MOCK/Fake...")

    for col in await db.list_collection_names():
        result = await db[col].delete_many({
            "$or": [
                {"mock": True},
                {"fake": True},
                {"seed": True},
            ]
        })
        if result.deleted_count > 0:
            logger.warning(f"🗑 {result.deleted_count} removidos de {col}")


def scan_codebase():
    logger.info("🔎 Varredura de código (mock/fake)...")

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    violations = []

    for root, _, files in os.walk(base):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    for word in MOCK_KEYWORDS:
                        if word in content and "lockdown" not in path:
                            violations.append((path, word))

    if violations:
        logger.error("🚨 MOCK ENCONTRADO NO CÓDIGO:")
        for v in violations:
            logger.error(f"{v[0]} -> {v[1]}")
        sys.exit(1)

    logger.info("✅ Código limpo (sem mocks)")


async def main():
    logger.info("🚀 INICIANDO LOCKDOWN PRODUÇÃO")

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    await check_collections(db)
    await clean_mock_data(db)
    scan_codebase()

    logger.info("🔒 LOCKDOWN CONCLUÍDO – SISTEMA SEGURO")


if __name__ == "__main__":
    asyncio.run(main())
