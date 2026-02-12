from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# ✅ IMPORT RELATIVO CORRETO
from ..core.database import get_db


class ObrigacoesRepository:
    def __init__(self):
        db = get_db()
        self.collection = db.obrigacoes
        self.history_collection = db.obrigacoes_history

    async def list_all(self, empresa_id: Optional[str] = None) -> List[dict]:
        filtro = {"empresa_id": empresa_id, "ativo": True} if empresa_id else {"ativo": True}
        cursor = self.collection.find(filtro)
        return await cursor.to_list(length=100)

    async def get_by_id(self, obrigacao_id: str) -> Optional[dict]:
        return await self.collection.find_one(
            {
                "_id": ObjectId(obrigacao_id),
                "ativo": True,
                "valid_to": None
            }
        )

    async def create(self, obrigacao: dict, created_by: Optional[str] = None) -> dict:
        now = datetime.utcnow()
        obrigacao = obrigacao.copy()

        obrigacao.update({
            "entity_id": str(ObjectId()),
            "version": 1,
            "created_at": now,
            "created_by": created_by,
            "valid_from": now,
            "valid_to": None,
            "previous_version_id": None,
            "ativo": True
        })

        result = await self.collection.insert_one(obrigacao)
        obrigacao["_id"] = result.inserted_id
        return obrigacao

    async def update_status(
        self,
        obrigacao_id: str,
        status: str,
        updated_by: Optional[str] = None
    ) -> Optional[dict]:

        current = await self.get_by_id(obrigacao_id)
        if not current:
            return None

        now = datetime.utcnow()

        # 🔒 Fecha validade da versão atual
        await self.collection.update_one(
            {"_id": ObjectId(obrigacao_id)},
            {
                "$set": {
                    "valid_to": now,
                    "ativo": False,
                    "updated_at": now,
                    "updated_by": updated_by
                }
            }
        )

        # 🗂️ Salva histórico
        await self.history_collection.insert_one(current)

        # 🆕 Cria nova versão
        new_version = current.copy()
        new_version.pop("_id", None)

        new_version.update({
            "version": current.get("version", 1) + 1,
            "status": status,
            "valid_from": now,
            "valid_to": None,
            "previous_version_id": str(current["_id"]),
            "ativo": True,
            "updated_at": now,
            "updated_by": updated_by
        })

        result = await self.collection.insert_one(new_version)
        new_version["_id"] = result.inserted_id
        return new_version
