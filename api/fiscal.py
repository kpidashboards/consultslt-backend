"""
API Fiscal (Paridade IRIS)
Endpoints para cálculos fiscais e integração e-CAC
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from services.fiscal_calculation_service import FiscalCalculationService
from services.ecac_service import ECACService, get_ecac_service
from core.database import get_db

logger = logging.getLogger(__name__)

# ===============================
# Router
# ===============================
router = APIRouter(tags=["Fiscal (IRIS)"])

# ===============================
# Services
# ===============================
def get_fiscal_service(
    db=Depends(get_db),
) -> FiscalCalculationService:
    return FiscalCalculationService(db)

# ===============================
# Schemas
# ===============================
class SimplesNacionalRequest(BaseModel):
    cnpj: str
    periodo: str
    receita_bruta_12m: float = Field(..., gt=0)
    receita_mensal: float = Field(..., gt=0)
    anexo: str = "anexo_iii"
    empresa_id: Optional[str] = None


class FatorRRequest(BaseModel):
    cnpj: str
    periodo: str
    folha_salarios_12m: float = Field(..., gt=0)
    receita_bruta_12m: float = Field(..., gt=0)
    empresa_id: Optional[str] = None


class SimulacaoEconomiaRequest(BaseModel):
    cnpj: str
    receita_bruta_12m: float
    receita_mensal: float
    folha_atual_12m: float

# ===============================
# Cálculos Fiscais
# ===============================
@router.post("/calcular/simples-nacional")
async def calcular_simples_nacional(
    request: SimplesNacionalRequest,
    service: FiscalCalculationService = Depends(get_fiscal_service),
):
    try:
        return await service.processar_simples_nacional(**request.dict())
    except Exception:
        logger.exception("Erro Simples Nacional")
        raise HTTPException(status_code=500, detail="Erro ao calcular Simples Nacional")


@router.post("/calcular/fator-r")
async def calcular_fator_r(
    request: FatorRRequest,
    service: FiscalCalculationService = Depends(get_fiscal_service),
):
    try:
        return await service.processar_fator_r(**request.dict())
    except Exception:
        logger.exception("Erro Fator R")
        raise HTTPException(status_code=500, detail="Erro ao calcular Fator R")


@router.post("/simular/economia-fator-r")
async def simular_economia_fator_r(
    request: SimulacaoEconomiaRequest,
    service: FiscalCalculationService = Depends(get_fiscal_service),
):
    try:
        return await service.simular_economia_fator_r(**request.dict())
    except Exception:
        logger.exception("Erro simulação Fator R")
        raise HTTPException(status_code=500, detail="Erro ao simular economia Fator R")

# ===============================
# e-CAC (PRODUÇÃO – SEM MOCK)
# ===============================
@router.get("/ecac/certidoes/{cnpj}")
async def consultar_certidoes_ecac(
    cnpj: str,
    ecac_service: ECACService = Depends(get_ecac_service),
):
    certidoes = await ecac_service.consultar_certidoes(cnpj)
    return {
        "status": "SUCESSO",
        "cnpj": cnpj,
        "data_consulta": datetime.utcnow().isoformat(),
        "certidoes": certidoes,
    }


@router.get("/ecac/pendencias/{cnpj}")
async def consultar_pendencias_ecac(
    cnpj: str,
    ecac_service: ECACService = Depends(get_ecac_service),
):
    return await ecac_service.consultar_pendencias(cnpj)


@router.get("/ecac/simples-nacional/{cnpj}")
async def consultar_simples_nacional_ecac(
    cnpj: str,
    ecac_service: ECACService = Depends(get_ecac_service),
):
    return await ecac_service.consultar_simples_nacional(cnpj)

# Export
fiscal_router = router
