from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from backend.core.database import get_db


class AlertasRepository:

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.alertas


    async def create_alerta(self, data: dict, created_by: Optional[str] = None):
        data["created_by"] = created_by
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        result = await self.collection.insert_one(data)
        alerta = await self.collection.find_one({"_id": result.inserted_id})

        return self._format(alerta)


    async def list_alertas(self) -> List[dict]:
        alertas = []
        async for alerta in self.collection.find().sort("created_at", -1):
            alertas.append(self._format(alerta))
        return alertas


    async def get_alerta(self, alerta_id: str) -> Optional[dict]:
        alerta = await self.collection.find_one({"_id": ObjectId(alerta_id)})
        if not alerta:
            return None
        return self._format(alerta)


    async def update_alerta(self, alerta_id: str, update_data: dict, updated_by: Optional[str] = None):
        update_data["updated_by"] = updated_by
        update_data["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(alerta_id)},
            {"$set": update_data}
        )

        alerta = await self.collection.find_one({"_id": ObjectId(alerta_id)})
        return self._format(alerta)


    async def delete_alerta(self, alerta_id: str, deleted_by: Optional[str] = None):
        result = await self.collection.delete_one({"_id": ObjectId(alerta_id)})
        return result.deleted_count > 0


    def _format(self, alerta: dict) -> dict:
        alerta["id"] = str(alerta["_id"])
        del alerta["_id"]
        return alerta