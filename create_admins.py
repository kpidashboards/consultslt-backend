import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "consultslt_db"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

ADMINS = [
    {
        "email": "admin@empresa.com",
        "password": "admin123",
        "perfil": "admin"
    },
    {
        "email": "william.lucas@sltconsult.com.br",
        "password": "Slt@2024",
        "perfil": "admin"
    },
    {
        "email": "admin@consultslt.com.br",
        "password": "Consult@2026",
        "perfil": "admin"
    }
]

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    for admin in ADMINS:
        admin_doc = {
            "email": admin["email"],
            "password": hash_password(admin["password"]),
            "perfil": admin["perfil"],
            "ativo": True,
            "primeiro_login": False,
            "created_at": datetime.utcnow()
        }

        await db.users.insert_one(admin_doc)
        print(f"Usuário {admin['email']} criado com sucesso")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
