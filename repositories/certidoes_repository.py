import datetime
import uuid
from backend.core.database import get_db
from typing import Optional

class CertidoesRepository:
    def __init__(self):
        self.collection = get_db().certidoes
        self.history_collection = get_db().certidoes_history

    async def create_certidao(self, certidao_data: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow()
        certidao_data = certidao_data.copy()
        certidao_data["id"] = certidao_data.get("id") or str(uuid.uuid4())
        certidao_data["entity_id"] = certidao_data["id"]
        certidao_data["version"] = 1
        certidao_data["created_at"] = now
        certidao_data["created_by"] = created_by
        certidao_data["valid_from"] = now
        certidao_data["valid_to"] = None
        certidao_data["previous_version_id"] = None
        certidao_data["ativo"] = True
        result = await self.collection.insert_one(certidao_data)
        certidao_data["_id"] = result.inserted_id
        return certidao_data

    async def get_certidao(self, certidao_id: str) -> Optional[dict]:
        return await self.collection.find_one({"id": certidao_id, "valid_to": None, "ativo": True})

    async def update_certidao(self, certidao_id: str, update_data: dict, updated_by: Optional[str] = None) -> Optional[dict]:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": certidao_id, "valid_to": None, "ativo": True})
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

    async def delete_certidao(self, certidao_id: str, deleted_by: Optional[str] = None) -> bool:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": certidao_id, "valid_to": None, "ativo": True})
        if not current:
            return False
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if deleted_by:
            current["deleted_by"] = deleted_by
        await self.history_collection.insert_one(current)
        await self.collection.update_one({"id": certidao_id, "valid_to": None, "ativo": True}, {"$set": {"valid_to": now, "ativo": False, "updated_at": now, "deleted_by": deleted_by}})
        return True

    async def list_certidoes(self, filtro: dict, skip: int, limit: int, only_active: bool = True) -> list:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        cursor = self.collection.find(base_filter).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_certidoes(self, filtro: dict, only_active: bool = True) -> int:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        return await self.collection.count_documents(base_filter)

    async def count_by_status(self, filtro: dict, status: str) -> int:
        return await self.collection.count_documents({**filtro, "status": status, "valid_to": None, "ativo": True})

    async def atualizar_status_certidoes(self):
        certidoes = await self.collection.find({"valid_to": None, "ativo": True}).to_list(length=None)
        count = 0
        for cert in certidoes:
            # O cálculo de status deve ser feito externamente e passado para update_certidao
            pass
        return count
