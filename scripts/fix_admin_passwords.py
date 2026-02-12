from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "consultslt_db")

ADMINS = [
    ("admin@empresa.com", "admin123"),
    ("william.lucas@sltconsult.com.br", "Slt@2024"),
    ("admin@consultslt.com.br", "Consult@2026"),
]

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    for email, senha in ADMINS:
        hash_senha = pwd_context.hash(senha)

        await db.usuarios.update_one(
            {"email": email},
            {
                "$set": {
                    "senha": hash_senha,
                    "ativo": True
                }
            },
            upsert=True
        )

        print(f"✔ Senha corrigida: {email}")

    client.close()

asyncio.run(main())
