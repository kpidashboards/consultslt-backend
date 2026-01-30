"""Endpoints para geração de Relatórios"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

from schemas.relatorio import (
    RelatorioCreate,
    RelatorioResponse,
    RelatorioListResponse,
    TipoRelatorio,
    StatusRelatorio,
    FormatoRelatorio
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "consultslt")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

@router.post("/", response_model=RelatorioResponse)
async def criar_relatorio(dados: RelatorioCreate, db=Depends(get_db)):
    """Cria e processa um novo relatório"""
    relatorio_dict = dados.model_dump()
    relatorio_dict["id"] = str(uuid.uuid4())
    relatorio_dict["status"] = StatusRelatorio.PROCESSANDO
    relatorio_dict["created_at"] = datetime.utcnow()
    
    # Converter datas para ISO string
    if "periodo_inicio" in relatorio_dict:
        from datetime import date
        if isinstance(relatorio_dict["periodo_inicio"], date):
            relatorio_dict["periodo_inicio"] = relatorio_dict["periodo_inicio"].isoformat()
    if "periodo_fim" in relatorio_dict:
        from datetime import date
        if isinstance(relatorio_dict["periodo_fim"], date):
            relatorio_dict["periodo_fim"] = relatorio_dict["periodo_fim"].isoformat()
    
    # Simular processamento e geração de dados
    try:
        # Buscar dados para o relatório
        filtro = {}
        if relatorio_dict.get("empresa_id"):
            filtro["empresa_id"] = relatorio_dict["empresa_id"]
        
        documentos_count = await db.documentos.count_documents(filtro)
        obrigacoes_count = await db.obrigacoes.count_documents(filtro)
        guias_count = await db.guias.count_documents(filtro)
        
        relatorio_dict["dados"] = {
            "documentos": documentos_count,
            "obrigacoes": obrigacoes_count,
            "guias": guias_count,
            "periodo": f"{relatorio_dict['periodo_inicio']} a {relatorio_dict['periodo_fim']}"
        }
        relatorio_dict["status"] = StatusRelatorio.CONCLUIDO
        relatorio_dict["processado_em"] = datetime.utcnow()
    except Exception as e:
        relatorio_dict["status"] = StatusRelatorio.ERRO
        relatorio_dict["erro"] = str(e)
    
    await db.relatorios.insert_one(relatorio_dict)
    return RelatorioResponse(**relatorio_dict)

@router.get("/", response_model=RelatorioListResponse)
async def listar_relatorios(
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[TipoRelatorio] = Query(default=None),
    status: Optional[StatusRelatorio] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
):
    """Lista relatórios com filtros"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    if tipo:
        filtro["tipo"] = tipo
    if status:
        filtro["status"] = status
    
    skip = (pagina - 1) * por_pagina
    cursor = db.relatorios.find(filtro).skip(skip).limit(por_pagina)
    relatorios = await cursor.to_list(length=por_pagina)
    total = await db.relatorios.count_documents(filtro)
    
    return RelatorioListResponse(
        relatorios=[RelatorioResponse(**r) for r in relatorios],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.get("/{relatorio_id}", response_model=RelatorioResponse)
async def obter_relatorio(relatorio_id: str, db=Depends(get_db)):
    """Obtém detalhes de um relatório"""
    relatorio = await db.relatorios.find_one({"id": relatorio_id})
    if not relatorio:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return RelatorioResponse(**relatorio)

@router.delete("/{relatorio_id}")
async def deletar_relatorio(relatorio_id: str, db=Depends(get_db)):
    """Deleta um relatório"""
    result = await db.relatorios.delete_one({"id": relatorio_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return {"message": "Relatório deletado com sucesso"}

@router.get("/dashboard/resumo")
async def dashboard_resumo(empresa_id: Optional[str] = Query(default=None), db=Depends(get_db)):
    """Obtém resumo para dashboard"""
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    total_empresas = await db.empresas.count_documents({"ativo": True})
    total_documentos = await db.documentos.count_documents(filtro)
    total_obrigacoes = await db.obrigacoes.count_documents(filtro)
    obrigacoes_pendentes = await db.obrigacoes.count_documents({**filtro, "status": "pendente"})
    total_guias = await db.guias.count_documents(filtro)
    guias_pendentes = await db.guias.count_documents({**filtro, "status": "pendente"})
    alertas_nao_lidos = await db.alertas.count_documents({**filtro, "status": "pendente"})
    certidoes_vencidas = await db.certidoes.count_documents({**filtro, "status": "vencida"})
    
    # Calcular valor total de guias pendentes
    pipeline = [
        {"$match": {**filtro, "status": "pendente"}},
        {"$group": {"_id": None, "total": {"$sum": "$valor_total"}}}
    ]
    result = await db.guias.aggregate(pipeline).to_list(length=1)
    valor_guias_pendentes = result[0]["total"] if result else 0
    
    return {
        "total_empresas": total_empresas,
        "total_documentos": total_documentos,
        "total_obrigacoes": total_obrigacoes,
        "obrigacoes_pendentes": obrigacoes_pendentes,
        "total_guias": total_guias,
        "guias_pendentes": guias_pendentes,
        "valor_guias_pendentes": valor_guias_pendentes,
        "alertas_nao_lidos": alertas_nao_lidos,
        "certidoes_vencidas": certidoes_vencidas
    }
