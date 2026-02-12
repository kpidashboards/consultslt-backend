import datetime
import uuid
from typing import Optional, List, Dict

# ✅ IMPORT RELATIVO CORRETO
from ..core.database import get_db


class DocumentosRepository:
    def __init__(self):
        db = get_db()
        self.collection = db.documentos
        self.history_collection = db.documentos_history

    # ===============================
    # CREATE
    # ===============================
    async def create_documento(
        self,
        doc_data: Dict,
        created_by: Optional[str] = None
    ) -> Dict:
        now = datetime.datetime.utcnow()

        documento = doc_data.copy()
        documento["id"] = documento.get("id") or str(uuid.uuid4())
        documento["entity_id"] = documento["id"]
        documento["version"] = 1

        documento["created_at"] = now
        documento["created_by"] = created_by

        documento["valid_from"] = now
        documento["valid_to"] = None
        documento["previous_version_id"] = None

        documento["ativo"] = True

        result = await self.collection.insert_one(documento)
        documento["_id"] = result.inserted_id

        return documento

    # ===============================
    # READ (versão ativa)
    # ===============================
    async def get_documento(self, doc_id: str) -> Optional[Dict]:
        return await self.collection.find_one(
            {
                "id": doc_id,
                "valid_to": None,
                "ativo": True,
            }
        )

    # ===============================
    # UPDATE (controle de versão)
    # ===============================
    async def update_documento(
        self,
        doc_id: str,
        update_data: Dict,
        updated_by: Optional[str] = None
    ) -> Optional[Dict]:
        now = datetime.datetime.utcnow()

        current = await self.collection.find_one(
            {
                "id": doc_id,
                "valid_to": None,
                "ativo": True,
            }
        )

        if not current:
            return None

        # 🔁 Move versão atual para histórico
        historico = current.copy()
        historico["valid_to"] = now
        historico["ativo"] = False
        historico["updated_at"] = now

        if updated_by:
            historico["updated_by"] = updated_by

        await self.history_collection.insert_one(historico)

        # 🆕 Cria nova versão
        new_version = current.copy()
        new_version.update(update_data)

        new_version["version"] = current.get("version", 1) + 1
        new_version["previous_version_id"] = str(current["_id"])

        new_version["created_at"] = current["created_at"]
        new_version["created_by"] = current.get("created_by")

        new_version["valid_from"] = now
        new_version["valid_to"] = None

        new_version["ativo"] = True
        new_version["updated_at"] = now

        new_version.pop("_id", None)

        result = await self.collection.insert_one(new_version)
        new_version["_id"] = result.inserted_id

        return new_version

    # ===============================
    # DELETE (soft delete versionado)
    # ===============================
    async def delete_documento(
        self,
        doc_id: str,
        deleted_by: Optional[str] = None
    ) -> bool:
        now = datetime.datetime.utcnow()

        current = await self.collection.find_one(
            {
                "id": doc_id,
                "valid_to": None,
                "ativo": True,
            }
        )

        if not current:
            return False

        historico = current.copy()
        historico["valid_to"] = now
        historico["ativo"] = False
        historico["updated_at"] = now

        if deleted_by:
            historico["deleted_by"] = deleted_by

        await self.history_collection.insert_one(historico)

        await self.collection.update_one(
            {
                "id": doc_id,
                "valid_to": None,
                "ativo": True,
            },
            {
                "$set": {
                    "valid_to": now,
                    "ativo": False,
                    "updated_at": now,
                    "deleted_by": deleted_by,
                }
            },
        )

        return True

    # ===============================
    # LIST
    # ===============================
    async def list_documentos(
        self,
        filtro: Dict,
        skip: int = 0,
        limit: int = 50,
        only_active: bool = True,
    ) -> List[Dict]:
        query = filtro.copy()
        query["valid_to"] = None

        if only_active:
            query["ativo"] = True

        cursor = (
            self.collection
            .find(query)
            .skip(skip)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    # ===============================
    # COUNT
    # ===============================
    async def count_documentos(
        self,
        filtro: Dict,
        only_active: bool = True,
    ) -> int:
        query = filtro.copy()
        query["valid_to"] = None

        if only_active:
            query["ativo"] = True

        return await self.collection.count_documents(query)
