"""
Serviço de Cálculos Fiscais (Paridade IRIS)
Implementa lógica de negócio para Simples Nacional e Fator R
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

# ✅ IMPORT RELATIVO CORRETO
from ..engines.fiscal_engine import FiscalEngine

logger = logging.getLogger(__name__)


class FiscalCalculationService:
    """
    Serviço para cálculos fiscais do Simples Nacional
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.engine = FiscalEngine()

    async def processar_simples_nacional(
        self,
        cnpj: str,
        periodo: str,
        receita_bruta_12m: float,
        receita_mensal: float,
        anexo: str = "anexo_iii",
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(
            f"Processando Simples Nacional: CNPJ={cnpj}, Período={periodo}"
        )

        fator_r_registro = await self.db.fiscal_data.find_one({
            "cnpj": cnpj,
            "periodo_referencia": periodo,
            "tipo": "fator_r"
        })

        fator_r = fator_r_registro.get("fator_r") if fator_r_registro else None

        resultado = self.engine.calcular_simples_nacional(
            receita_bruta_12m=receita_bruta_12m,
            receita_mensal=receita_mensal,
            anexo=anexo,
            fator_r=fator_r
        )

        if resultado["status"] == "SUCESSO":
            registro = {
                "id": str(uuid.uuid4()),
                "tipo": "simples_nacional",
                "cnpj": cnpj,
                "empresa_id": empresa_id,
                "periodo_referencia": periodo,
                "receita_bruta_12m": receita_bruta_12m,
                "receita_mensal": receita_mensal,
                "aliquota_efetiva": resultado["aliquota_efetiva"],
                "valor_das": resultado["valor_das"],
                "anexo": resultado["anexo"],
                "fator_r": fator_r,
                "excede_sublimite": resultado["excede_sublimite_estadual"],
                "detalhes": resultado,
                "created_at": datetime.utcnow()
            }

            await self.db.fiscal_data.update_one(
                {
                    "cnpj": cnpj,
                    "periodo_referencia": periodo,
                    "tipo": "simples_nacional"
                },
                {"$set": registro},
                upsert=True
            )

            logger.info(
                f"Cálculo persistido: DAS=R$ {resultado['valor_das']:,.2f}"
            )

        return resultado

    async def processar_fator_r(
        self,
        cnpj: str,
        periodo: str,
        folha_salarios_12m: float,
        receita_bruta_12m: float,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(
            f"Processando Fator R: CNPJ={cnpj}, Período={periodo}"
        )

        resultado = self.engine.calcular_fator_r(
            folha_salarios_12m=folha_salarios_12m,
            receita_bruta_12m=receita_bruta_12m
        )

        if resultado["status"] == "SUCESSO":
            registro = {
                "id": str(uuid.uuid4()),
                "tipo": "fator_r",
                "cnpj": cnpj,
                "empresa_id": empresa_id,
                "periodo_referencia": periodo,
                "folha_salarios_12m": folha_salarios_12m,
                "receita_bruta_12m": receita_bruta_12m,
                "fator_r": resultado["fator_r"],
                "fator_r_percentual": resultado["fator_r_percentual"],
                "enquadramento": resultado["enquadramento"],
                "detalhes": resultado,
                "created_at": datetime.utcnow()
            }

            await self.db.fiscal_data.update_one(
                {
                    "cnpj": cnpj,
                    "periodo_referencia": periodo,
                    "tipo": "fator_r"
                },
                {"$set": registro},
                upsert=True
            )

            logger.info(
                f"Fator R persistido: {resultado['fator_r_percentual']:.2f}%"
            )

        return resultado

    async def simular_economia_fator_r(
        self,
        cnpj: str,
        receita_bruta_12m: float,
        receita_mensal: float,
        folha_atual_12m: float
    ) -> Dict[str, Any]:
        return self.engine.simular_economia_fator_r(
            receita_bruta_12m=receita_bruta_12m,
            receita_mensal=receita_mensal,
            folha_atual_12m=folha_atual_12m
        )

    async def obter_historico_fiscal(
        self,
        cnpj: str,
        tipo: Optional[str] = None,
        limit: int = 12
    ) -> list:
        filtro = {"cnpj": cnpj}
        if tipo:
            filtro["tipo"] = tipo

        cursor = (
            self.db.fiscal_data
            .find(filtro, {"_id": 0})
            .sort("periodo_referencia", -1)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)
