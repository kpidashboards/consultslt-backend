"""
BOOTSTRAP DA APLICAÇÃO
Cria estrutura, inicializa banco e garante persistência total
"""

import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("MONGO_DB", "consultslt_db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ensure_dirs():
    dirs = [
        "repositories",
        "services",
        "api"
    ]
    for d in dirs:
        path = os.path.join(BASE_DIR, d)
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, "__init__.py"), "a").close()

async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # USERS
    await db.users.create_index("email", unique=True)


    # Removido seed automático de admin. Criação de usuários deve ser feita via repository, versionada e auditável.

    # EMPRESAS
    await db.empresas.create_index("cnpj", unique=True)

    print("✅ MongoDB inicializado corretamente")

def create_repository_files():
    repo_base = os.path.join(BASE_DIR, "repositories")

    with open(os.path.join(repo_base, "base.py"), "w") as f:
        f.write(
            """from backend.core.database import get_db

class BaseRepository:
    @property
    def db(self):
        return get_db()
"""
        )

    with open(os.path.join(repo_base, "empresa_repository.py"), "w") as f:
        f.write(
            """from datetime import datetime
from backend.repositories.base import BaseRepository

class EmpresaRepository(BaseRepository):

    async def create(self, data):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        await self.db.empresas.insert_one(data)
        return data

    async def list(self):
        return await self.db.empresas.find().to_list(100)
"""
        )

def create_service_files():
    service_base = os.path.join(BASE_DIR, "services")

    with open(os.path.join(service_base, "empresa_service.py"), "w") as f:
        f.write(
            """from backend.repositories.empresa_repository import EmpresaRepository

class EmpresaService:
    def __init__(self):
        self.repo = EmpresaRepository()

    async def criar(self, payload):
        return await self.repo.create(payload)

    async def listar(self):
        return await self.repo.list()
"""
        )

def create_api_files():
    api_base = os.path.join(BASE_DIR, "api")

    with open(os.path.join(api_base, "empresa_routes.py"), "w") as f:
        f.write(
            """from fastapi import APIRouter
from services.empresa_service import EmpresaService

router = APIRouter(prefix="/api/empresas", tags=["Empresas"])
service = EmpresaService()

@router.post("/")
async def criar_empresa(payload: dict):
    return await service.criar(payload)

@router.get("/")
async def listar_empresas():
    return await service.listar()
"""
        )

def create_main():
    with open(os.path.join(BASE_DIR, "main_enterprise.py"), "w") as f:
        f.write(
            """from fastapi import FastAPI
from api.empresa_routes import router as empresa_router
from backend.core.database import register_db_events

app = FastAPI(title="ConsultSLT API")

register_db_events(app)

app.include_router(empresa_router)
"""
        )

async def main():
    print("🚀 Iniciando bootstrap...")
    ensure_dirs()
    create_repository_files()
    create_service_files()
    create_api_files()
    create_main()
    await init_db()
    print("🎉 Aplicação estruturada e persistente!")

if __name__ == "__main__":
    asyncio.run(main())
