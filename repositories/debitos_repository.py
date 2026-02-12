import datetime
import uuid
from backend.core.database import get_db
from typing import Optional

class DebitosRepository:
    def __init__(self):
        self.collection = get_db().debitos
        self.history_collection = get_db().debitos_history

    async def create_debito(self, debito_data: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow()
        debito_data = debito_data.copy()
        debito_data["id"] = debito_data.get("id") or str(uuid.uuid4())
        debito_data["entity_id"] = debito_data["id"]
        debito_data["version"] = 1
        debito_data["created_at"] = now
        debito_data["created_by"] = created_by
        debito_data["valid_from"] = now
        debito_data["valid_to"] = None
        debito_data["previous_version_id"] = None
        debito_data["ativo"] = True
        result = await self.collection.insert_one(debito_data)
        debito_data["_id"] = result.inserted_id
        return debito_data

    async def get_debito(self, debito_id: str) -> Optional[dict]:
        return await self.collection.find_one({"id": debito_id, "valid_to": None, "ativo": True})

    async def update_debito(self, debito_id: str, update_data: dict, updated_by: Optional[str] = None) -> Optional[dict]:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": debito_id, "valid_to": None, "ativo": True})
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

    async def delete_debito(self, debito_id: str, deleted_by: Optional[str] = None) -> bool:
        now = datetime.datetime.utcnow()
        current = await self.collection.find_one({"id": debito_id, "valid_to": None, "ativo": True})
        if not current:
            return False
        current["valid_to"] = now
        current["ativo"] = False
        current["updated_at"] = now
        if deleted_by:
            current["deleted_by"] = deleted_by
        await self.history_collection.insert_one(current)
        await self.collection.update_one({"id": debito_id, "valid_to": None, "ativo": True}, {"$set": {"valid_to": now, "ativo": False, "updated_at": now, "deleted_by": deleted_by}})
        return True

    async def list_debitos(self, filtro: dict, skip: int, limit: int, only_active: bool = True) -> list:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        cursor = self.collection.find(base_filter).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_debitos(self, filtro: dict, only_active: bool = True) -> int:
        base_filter = {**filtro, "valid_to": None}
        if only_active:
            base_filter["ativo"] = True
        return await self.collection.count_documents(base_filter)

    async def aggregate_abertos(self, filtro: dict) -> float:
        pipeline_abertos = [
            {"$match": {**filtro, "status": "ABERTO", "valid_to": None, "ativo": True}},
            {"$group": {"_id": None, "total": {"$sum": "$valor_total"}}}
        ]
        result_abertos = await self.collection.aggregate(pipeline_abertos).to_list(length=1)
        return result_abertos[0]["total"] if result_abertos else 0

    async def count_abertos(self, filtro: dict) -> int:
        return await self.collection.count_documents({**filtro, "status": "ABERTO", "valid_to": None, "ativo": True})

    async def resumo_geral(self, filtro: dict) -> dict:
        pipeline = [
            {"$match": {**filtro, "valid_to": None, "ativo": True}},
            {"$group": {
                "_id": "$status",
                "quantidade": {"$sum": 1},
                "valor_total": {"$sum": "$valor_total"}
            }}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        resumo = {}
        for item in result:
            resumo[item["_id"]] = {
                "quantidade": item["quantidade"],
                "valor_total": item["valor_total"]
            }
        return resumo
