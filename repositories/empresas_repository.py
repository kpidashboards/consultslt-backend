from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from backend.core.database import get_db


class EmpresasRepository:

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.empresas

    async def create_empresa(self, data: dict):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        result = await self.collection.insert_one(data)
        empresa = await self.collection.find_one({"_id": result.inserted_id})

        return self._format(empresa)

    async def list_empresas(self) -> List[dict]:
        empresas = []
        async for empresa in self.collection.find().sort("created_at", -1):
            empresas.append(self._format(empresa))
        return empresas

    async def get_empresa(self, empresa_id: str) -> Optional[dict]:
        empresa = await self.collection.find_one({"_id": ObjectId(empresa_id)})
        if not empresa:
            return None
        return self._format(empresa)

    async def update_empresa(self, empresa_id: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(empresa_id)},
            {"$set": update_data}
        )

        empresa = await self.collection.find_one({"_id": ObjectId(empresa_id)})
        return self._format(empresa)

    async def delete_empresa(self, empresa_id: str):
        result = await self.collection.delete_one({"_id": ObjectId(empresa_id)})
        return result.deleted_count > 0

    def _format(self, empresa: dict) -> dict:
        empresa["id"] = str(empresa["_id"])
        del empresa["_id"]
        return empresa