import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import os
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis do .env
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "consultslt_db")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def reset_passwords(new_password="Teste123!"):
    cursor = db.users.find({})
    async for user in cursor:
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": password_hash}})
        print(f"Senha atualizada: {user.get('email')} -> {new_password}")

asyncio.run(reset_passwords())
