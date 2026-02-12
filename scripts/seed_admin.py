import asyncio
from datetime import datetime
from pathlib import Path
import sys

# Adiciona o backend ao sys.path para evitar ModuleNotFoundError
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.core.database import get_database
from backend.core.security import hash_password  # função que gera hash da senha

async def create_admin():
    db = await get_database()

    # Verifica se já existe admin
    admin = await db.usuarios.find_one({"email": "admin@admin.com"})
    if admin:
        print("Admin já existe!")
        return

    # Cria usuário admin
    await db.usuarios.insert_one({
        "nome": "Admin",
        "email": "admin@admin.com",
        "senha": hash_password("admin123"),  # hash da senha
        "perfil": "admin",
        "ativo": True,
        "criado_em": datetime.utcnow(),
        "ultimo_acesso": None
    })
    print("Admin criado com sucesso!")

if __name__ == "__main__":
    asyncio.run(create_admin())
