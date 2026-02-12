import datetime
import uuid
from backend.core.database import get_db
from typing import Optional

class AuditoriaRepository:
    def __init__(self):
        self.collection = get_db().auditorias
        self.history_collection = get_db().auditorias_history

    async def create_auditoria(self, auditoria_data: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow()
        auditoria_data = auditoria_data.copy()
        auditoria_data["id"] = auditoria_data.get("id") or str(uuid.uuid4())
        auditoria_data["entity_id"] = auditoria_data["id"]
        auditoria_data["version"] = 1
        auditoria_data["created_at"] = now
        auditoria_data["created_by"] = created_by
        auditoria_data["valid_from"] = now
        auditoria_data["valid_to"] = None
        auditoria_data["previous_version_id"] = None
        auditoria_data["ativo"] = True
        result = await self.collection.insert_one(auditoria_data)
        auditoria_data["_id"] = result.inserted_id
        return auditoria_data

    async def get_auditoria(self, auditoria_id: str) -> Optional[dict]:
        return await self.collection.find_one({"id": auditoria_id, "valid_to": None, "ativo": True})

    async def update_auditoria(self, auditoria_id: str, update_data: dict, updated_by: Optional[str] = None) -> Optional[dict]:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": auditoria_id, "valid_to": None, "ativo": True})
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

    async def delete_auditoria(self, auditoria_id: str, deleted_by: Optional[str] = None) -> bool:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": auditoria_id, "valid_to": None, "ativo": True})
        if not current:
            return False
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if deleted_by:
            current["deleted_by"] = deleted_by
        await self.history_collection.insert_one(current)
        await self.collection.update_one({"id": auditoria_id, "valid_to": None, "ativo": True}, {"$set": {"valid_to": now, "ativo": False, "updated_at": now, "deleted_by": deleted_by}})
        return True

    async def list_auditorias(self, filtro: dict, limit: int = 20, only_active: bool = True) -> list:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        cursor = self.collection.find(base_filter).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_auditorias(self, filtro: dict, only_active: bool = True) -> int:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        return await self.collection.count_documents(base_filter)
