from fastapi import APIRouter

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

@router.get("/")
async def listar_relatorios():
    return []
# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""
Endpoints para geração de Relatórios
"""

import logging
import uuid
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query


from backend.schemas.relatorio import (
    RelatorioCreate,
    RelatorioResponse,
    RelatorioListResponse,
    TipoRelatorio,
    StatusRelatorio,
    FormatoRelatorio,
)
from backend.repositories.relatorios_repository import RelatoriosRepository
from backend.repositories.documentos_repository import DocumentosRepository
from backend.repositories.obrigacoes_repository import ObrigacoesRepository
from backend.repositories.guias_repository import GuiasRepository
from backend.repositories.empresas_repository import EmpresasRepository

logger = logging.getLogger(__name__)

# ===============================
# Router
# ===============================
router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios"],
)

# ===============================
# Criar relatório
# ===============================
@router.post("/", response_model=RelatorioResponse)
async def criar_relatorio(dados: RelatorioCreate):
    repo = RelatoriosRepository()
    doc_repo = DocumentosRepository()
    obrig_repo = ObrigacoesRepository()
    guias_repo = GuiasRepository()
    relatorio_dict = dados.model_dump()
    relatorio_dict["status"] = StatusRelatorio.PROCESSANDO
    relatorio_dict["erro"] = None
    try:
        filtro = {}
        if relatorio_dict.get("empresa_id"):
            filtro["empresa_id"] = relatorio_dict["empresa_id"]
        documentos_count = await doc_repo.count_documentos(filtro)
        obrigacoes_count = await obrig_repo.count_obrigacoes(filtro)
        guias_count = await guias_repo.count_guias(filtro)
        relatorio_dict["dados"] = {
            "documentos": documentos_count,
            "obrigacoes": obrigacoes_count,
            "guias": guias_count,
            "periodo": f"{relatorio_dict.get('periodo_inicio')} a {relatorio_dict.get('periodo_fim')}",
        }
        relatorio_dict["status"] = StatusRelatorio.CONCLUIDO
    except Exception as e:
        logger.exception("Erro ao processar relatório")
        relatorio_dict["status"] = StatusRelatorio.ERRO
        relatorio_dict["erro"] = str(e)
    relatorio_criado = await repo.create_relatorio(relatorio_dict)
    return RelatorioResponse(**relatorio_criado)

# ===============================
# Listar relatórios
# ===============================
@router.get("/", response_model=RelatorioListResponse)
async def listar_relatorios(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    empresa_id: Optional[str] = None,
    tipo: Optional[TipoRelatorio] = None,
    status: Optional[StatusRelatorio] = None,
):
    repo = RelatoriosRepository()
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    skip = (pagina - 1) * por_pagina
    relatorios, total = await repo.list_relatorios(filtro, skip, por_pagina)
    return RelatorioListResponse(
        relatorios=[RelatorioResponse(**r) for r in relatorios],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )

# ===============================
# Obter relatório
# ===============================
@router.get("/{relatorio_id}", response_model=RelatorioResponse)
async def obter_relatorio(relatorio_id: str):
    repo = RelatoriosRepository()
    relatorio = await repo.get_relatorio_by_id(relatorio_id)
    if not relatorio:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return RelatorioResponse(**relatorio)

# ===============================
# Deletar relatório
# ===============================
@router.delete("/{relatorio_id}")
async def deletar_relatorio(relatorio_id: str):
    repo = RelatoriosRepository()
    ok = await repo.delete_relatorio(relatorio_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return {"message": "Relatório deletado com sucesso"}

# ===============================
# Dashboard resumo
# ===============================
@router.get("/dashboard/resumo")
async def resumo_dashboard(empresa_id: Optional[str] = None):
    empresas_repo = EmpresasRepository()
    doc_repo = DocumentosRepository()
    obrig_repo = ObrigacoesRepository()
    guias_repo = GuiasRepository()
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    total_empresas = await empresas_repo.count_empresas({"ativo": True})
    total_documentos = await doc_repo.count_documentos(filtro)
    total_obrigacoes = await obrig_repo.count_obrigacoes(filtro)
    obrigacoes_pendentes = await obrig_repo.count_obrigacoes({**filtro, "status": "pendente"})
    total_guias = await guias_repo.count_guias(filtro)
    guias_pendentes = await guias_repo.count_guias({**filtro, "status": "pendente"})
    valor_guias_pendentes = await guias_repo.sum_valor_pendentes(filtro)
    return {
        "total_empresas": total_empresas,
        "total_documentos": total_documentos,
        "total_obrigacoes": total_obrigacoes,
        "obrigacoes_pendentes": obrigacoes_pendentes,
        "total_guias": total_guias,
        "guias_pendentes": guias_pendentes,
        "valor_guias_pendentes": valor_guias_pendentes,
    }
