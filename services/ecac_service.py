"""
Serviço e-CAC (Production Ready)
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import Depends

from backend.core.database import get_db

logger = logging.getLogger(__name__)


class ECACService:
    def __init__(self, db):
        self.db = db

    # ===============================
    # CERTIDÕES
    # ===============================
    async def consultar_certidoes(self, cnpj: str) -> List[dict]:
        collection = self.db.ecac_certidoes

        logger.info(f"🔎 Buscando certidões e-CAC para {cnpj}")

        documentos = await collection.find(
            {"cnpj": cnpj},
            {"_id": 0}
        ).to_list(length=100)

        return documentos or []

    async def salvar_certidoes(self, cnpj: str, dados: List[dict]):
        collection = self.db.ecac_certidoes

        await collection.delete_many({"cnpj": cnpj})

        if not dados:
            logger.info(f"ℹ️ Nenhuma certidão para salvar ({cnpj})")
            return

        for item in dados:
            item.update({
                "cnpj": cnpj,
                "updated_at": datetime.utcnow()
            })

        await collection.insert_many(dados)
        logger.info(f"✅ Certidões salvas para {cnpj}")

    # ===============================
    # PENDÊNCIAS
    # ===============================
    async def consultar_pendencias(self, cnpj: str) -> Optional[dict]:
        collection = self.db.ecac_pendencias

        logger.info(f"🔎 Buscando pendências e-CAC para {cnpj}")

        return await collection.find_one(
            {"cnpj": cnpj},
            {"_id": 0}
        )

    async def salvar_pendencias(self, cnpj: str, dados: dict):
        collection = self.db.ecac_pendencias

        await collection.update_one(
            {"cnpj": cnpj},
            {
                "$set": {
                    "cnpj": cnpj,
                    "dados": dados,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"✅ Pendências salvas para {cnpj}")

    # ===============================
    # SIMPLES NACIONAL
    # ===============================
    async def consultar_simples_nacional(self, cnpj: str) -> Optional[dict]:
        collection = self.db.ecac_simples_nacional

        logger.info(f"🔎 Buscando Simples Nacional para {cnpj}")

        return await collection.find_one(
            {"cnpj": cnpj},
            {"_id": 0}
        )

    async def salvar_simples_nacional(self, cnpj: str, dados: dict):
        collection = self.db.ecac_simples_nacional

        await collection.update_one(
            {"cnpj": cnpj},
            {
                "$set": {
                    "cnpj": cnpj,
                    "dados": dados,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"✅ Simples Nacional salvo para {cnpj}")


# ===============================
# Dependency Injection (CORRETA)
# ===============================
def get_ecac_service(db=Depends(get_db)) -> ECACService:
    return ECACService(db)
