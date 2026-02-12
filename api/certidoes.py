from fastapi import APIRouter

router = APIRouter(prefix="/certidoes", tags=["Certidões"])

# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""Endpoints para gestão de Certidões"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
from datetime import datetime, date
import uuid
from backend.schemas.certidao import (
    CertidaoCreate,
    CertidaoUpdate,
    CertidaoResponse,
    CertidaoListResponse,
    TipoCertidao,
    StatusCertidao
)
from backend.repositories.certidoes_repository import CertidoesRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/certidoes", tags=["Certidões"])

def get_certidoes_repo():
    return CertidoesRepository()

# Função utilitária para calcular status
def calcular_status_certidao(data_validade):
    """Calcula o status baseado na data de validade"""
    if isinstance(data_validade, str):
        data_validade = date.fromisoformat(data_validade)

    dias_ate_vencer = (data_validade - date.today()).days

    if dias_ate_vencer < 0:
        return StatusCertidao.VENCIDA, dias_ate_vencer
    elif dias_ate_vencer <= 30:
        return StatusCertidao.PROXIMA_VENCER, dias_ate_vencer
    else:
        return StatusCertidao.VALIDA, dias_ate_vencer

# =========================
# Endpoints
# =========================

@router.post("/", response_model=CertidaoResponse)
async def criar_certidao(dados: CertidaoCreate, repo: CertidoesRepository = Depends(get_certidoes_repo)):
    """Cria uma nova certidão"""
    certidao_dict = dados.model_dump()
    status, dias = calcular_status_certidao(certidao_dict["data_validade"])
    certidao_dict["status"] = status
    certidao_dict["dias_para_vencer"] = dias if dias > 0 else 0
    if isinstance(certidao_dict.get("data_emissao"), date):
        certidao_dict["data_emissao"] = certidao_dict["data_emissao"].isoformat()
    if isinstance(certidao_dict.get("data_validade"), date):
        certidao_dict["data_validade"] = certidao_dict["data_validade"].isoformat()
    certidao = await repo.create_certidao(certidao_dict)
    return CertidaoResponse(**certidao)


@router.get("/", response_model=CertidaoListResponse)
async def listar_certidoes(
    empresa_id: Optional[str] = None,
    tipo: Optional[TipoCertidao] = None,
    status: Optional[StatusCertidao] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    repo: CertidoesRepository = Depends(get_certidoes_repo)
):
    """Lista certidões com filtros"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    skip = (pagina - 1) * por_pagina
    certidoes = await repo.list_certidoes(filtro, skip, por_pagina)
    total = await repo.count_certidoes(filtro)
    validas = await repo.count_by_status(filtro, StatusCertidao.VALIDA)
    vencidas = await repo.count_by_status(filtro, StatusCertidao.VENCIDA)
    proximas_vencer = await repo.count_by_status(filtro, StatusCertidao.PROXIMA_VENCER)
    return CertidaoListResponse(
        certidoes=[CertidaoResponse(**c) for c in certidoes],
        total=total,
        validas=validas,
        vencidas=vencidas,
        proximas_vencer=proximas_vencer,
        pagina=pagina,
        por_pagina=por_pagina
    )


@router.get("/{certidao_id}", response_model=CertidaoResponse)
async def obter_certidao(certidao_id: str, repo: CertidoesRepository = Depends(get_certidoes_repo)):
    """Obtém detalhes de uma certidão"""
    certidao = await repo.get_certidao(certidao_id)
    if not certidao:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    return CertidaoResponse(**certidao)


@router.put("/{certidao_id}", response_model=CertidaoResponse)
async def atualizar_certidao(certidao_id: str, dados: CertidaoUpdate, repo: CertidoesRepository = Depends(get_certidoes_repo)):
    """Atualiza uma certidão"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    if "data_validade" in update_data:
        status, dias = calcular_status_certidao(update_data["data_validade"])
        update_data["status"] = status
        update_data["dias_para_vencer"] = dias if dias > 0 else 0
        if isinstance(update_data["data_validade"], date):
            update_data["data_validade"] = update_data["data_validade"].isoformat()
    if "data_emissao" in update_data and isinstance(update_data["data_emissao"], date):
        update_data["data_emissao"] = update_data["data_emissao"].isoformat()
    certidao = await repo.update_certidao(certidao_id, update_data)
    if not certidao:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    return CertidaoResponse(**certidao)


@router.delete("/{certidao_id}")
async def deletar_certidao(certidao_id: str, repo: CertidoesRepository = Depends(get_certidoes_repo)):
    """Deleta uma certidão"""
    ok = await repo.delete_certidao(certidao_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Certidão não encontrada")
    return {"message": "Certidão deletada com sucesso"}


@router.post("/atualizar-status")
async def atualizar_status_certidoes(repo: CertidoesRepository = Depends(get_certidoes_repo)):
    """Atualiza status de todas as certidões baseado na data de validade"""
    # O cálculo de status e update deve ser feito iterando e usando update_certidao
    certidoes = await repo.collection.find({"valid_to": None}).to_list(length=None)
    count = 0
    for cert in certidoes:
        status, dias = calcular_status_certidao(cert["data_validade"])
        await repo.update_certidao(cert["id"], {"status": status, "dias_para_vencer": dias if dias > 0 else 0, "updated_at": datetime.utcnow()})
        count += 1
    return {"message": f"{count} certidões atualizadas"}


# Expor o router para importação
certidoes_router = router
