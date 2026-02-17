from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from backend.core.database import get_db


class OCRRepository:

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.ocr_documentos

    async def create_documento(self, data: dict):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        result = await self.collection.insert_one(data)
        documento = await self.collection.find_one({"_id": result.inserted_id})

        return self._format(documento)

    async def list_documentos(self) -> List[dict]:
        documentos = []
        async for documento in self.collection.find().sort("created_at", -1):
            documentos.append(self._format(documento))
        return documentos

    async def get_documento(self, documento_id: str) -> Optional[dict]:
        documento = await self.collection.find_one({"_id": ObjectId(documento_id)})
        if not documento:
            return None
        return self._format(documento)

    async def update_documento(self, documento_id: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(documento_id)},
            {"$set": update_data}
        )

        documento = await self.collection.find_one({"_id": ObjectId(documento_id)})
        return self._format(documento)

    async def delete_documento(self, documento_id: str):
        result = await self.collection.delete_one({"_id": ObjectId(documento_id)})
        return result.deleted_count > 0

    def _format(self, documento: dict) -> dict:
        documento["id"] = str(documento["_id"])
        del documento["_id"]
        return documento