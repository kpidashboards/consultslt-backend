
from datetime import datetime
from backend.repositories.base import BaseRepository

class EmpresaRepository(BaseRepository):
    async def create(self, data, created_by=None):
        now = datetime.utcnow()
        entity_id = str(uuid.uuid4())
        data = data.copy()
        data["entity_id"] = entity_id
        data["version"] = 1
        data["created_at"] = now
        data["created_by"] = created_by
        data["valid_from"] = now
        data["valid_to"] = None
        data["previous_version_id"] = None
        result = await self.db.empresas.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def list(self):
        return await self.db.empresas.find().to_list(100)

    async def update(self, empresa_id, update_data, updated_by=None):
        # Buscar versão atual
        current = await self.db.empresas.find_one({"_id": empresa_id, "valid_to": None})
        if not current:
            return None
        now = datetime.utcnow()
        # Fechar validade da versão atual
        await self.db.empresas.update_one({"_id": empresa_id}, {"$set": {"valid_to": now}})
        # Mover para histórico
        await self.db.empresas_history.insert_one(current)
        # Criar nova versão
        new_version = current.copy()
        new_version.update(update_data)
        new_version["version"] = current.get("version", 1) + 1
        new_version["created_at"] = current["created_at"]
        new_version["created_by"] = current.get("created_by")
        new_version["valid_from"] = now
        new_version["valid_to"] = None
        new_version["previous_version_id"] = str(empresa_id)
        new_version.pop("_id", None)
        result = await self.db.empresas.insert_one(new_version)
        new_version["_id"] = result.inserted_id
        return new_version
