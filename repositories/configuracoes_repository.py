import datetime
import uuid
from backend.core.database import get_db
from typing import Optional

class ConfiguracoesRepository:
    def __init__(self):
        self.collection = get_db().configuracoes
        self.history_collection = get_db().configuracoes_history

    async def create_configuracao(self, config_data: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow()
        config_data = config_data.copy()
        config_data["id"] = config_data.get("id") or str(uuid.uuid4())
        config_data["entity_id"] = config_data["id"]
        config_data["version"] = 1
        config_data["created_at"] = now
        config_data["created_by"] = created_by
        config_data["valid_from"] = now
        config_data["valid_to"] = None
        config_data["previous_version_id"] = None
        config_data["ativo"] = True
        result = await self.collection.insert_one(config_data)
        config_data["_id"] = result.inserted_id
        return config_data

    async def get_configuracao_by_id(self, config_id: str) -> Optional[dict]:
        return await self.collection.find_one({"id": config_id, "valid_to": None, "ativo": True})

    async def get_configuracao_by_chave(self, chave: str) -> Optional[dict]:
        return await self.collection.find_one({"chave": chave, "valid_to": None, "ativo": True})

    async def update_configuracao(self, config_id: str, update_data: dict, updated_by: Optional[str] = None) -> Optional[dict]:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": config_id, "valid_to": None, "ativo": True})
        if not current:
            return None
        # Move o atual para o histórico
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if updated_by:
            current["updated_by"] = updated_by
        await self.history_collection.insert_one(current)
        # Cria nova versão
        new_version = current.copy()
        new_version.update(update_data)
        new_version["version"] = current.get("version", 1) + 1
        new_version["created_at"] = current["created_at"]
        new_version["created_by"] = current.get("created_by")
        new_version["valid_from"] = now
        new_version["valid_to"] = None
        new_version["previous_version_id"] = str(current.get("_id"))
        new_version["ativo"] = True
        new_version["updated_at"] = now
        new_version.pop("_id", None)
        result = await self.collection.insert_one(new_version)
        new_version["_id"] = result.inserted_id
        return new_version

    async def delete_configuracao(self, config_id: str, deleted_by: Optional[str] = None) -> bool:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": config_id, "valid_to": None, "ativo": True})
        if not current:
            return False
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if deleted_by:
            current["deleted_by"] = deleted_by
        await self.history_collection.insert_one(current)
        await self.collection.update_one({"id": config_id, "valid_to": None, "ativo": True}, {"$set": {"valid_to": now, "ativo": False, "updated_at": now, "deleted_by": deleted_by}})
        return True

    async def list_configuracoes(self, filtro: dict, only_active: bool = True) -> list:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        return await self.collection.find(base_filter).to_list(length=100)
