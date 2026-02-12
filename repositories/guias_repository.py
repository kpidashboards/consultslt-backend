
import datetime
import uuid
from backend.core.database import get_db
from typing import Optional


class GuiasRepository:
    def __init__(self):
        self.collection = get_db().guias
        self.history_collection = get_db().guias_history

    async def create_guia(self, guia_data: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow()
        guia_data = guia_data.copy()
        guia_data["id"] = guia_data.get("id") or str(uuid.uuid4())
        guia_data["entity_id"] = guia_data["id"]
        guia_data["version"] = 1
        guia_data["created_at"] = now
        guia_data["created_by"] = created_by
        guia_data["valid_from"] = now
        guia_data["valid_to"] = None
        guia_data["previous_version_id"] = None
        guia_data["ativo"] = True
        result = await self.collection.insert_one(guia_data)
        guia_data["_id"] = result.inserted_id
        return guia_data

    async def get_guia(self, guia_id: str) -> Optional[dict]:
        return await self.collection.find_one({"id": guia_id, "valid_to": None, "ativo": True})

    async def update_guia(self, guia_id: str, update_data: dict, updated_by: Optional[str] = None) -> Optional[dict]:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": guia_id, "valid_to": None, "ativo": True})
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

    async def delete_guia(self, guia_id: str, deleted_by: Optional[str] = None) -> bool:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": guia_id, "valid_to": None, "ativo": True})
        if not current:
            return False
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if deleted_by:
            current["deleted_by"] = deleted_by
        await self.history_collection.insert_one(current)
        await self.collection.update_one({"id": guia_id, "valid_to": None, "ativo": True}, {"$set": {"valid_to": now, "ativo": False, "updated_at": now, "deleted_by": deleted_by}})
        return True

    async def list_guias(self, filtro: dict, skip: int, limit: int, only_active: bool = True) -> list:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        cursor = self.collection.find(base_filter).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_guias(self, filtro: dict, only_active: bool = True) -> int:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        return await self.collection.count_documents(base_filter)

    async def proximos_vencimentos(self, data_limite: str, empresa_id: Optional[str] = None) -> list:
        filtro = {
            "data_vencimento": {"$lte": data_limite},
            "status": "PENDENTE",
            "valid_to": None,
            "ativo": True
        }
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        return await self.collection.find(filtro).to_list(length=100)
