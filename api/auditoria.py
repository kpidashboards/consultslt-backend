"""
API de Auditoria Fiscal (Paridade Kolossus)
Endpoints para auditoria SPED e cruzamento fiscal
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from services.auditoria_service import AuditoriaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auditoria", tags=["Auditoria Fiscal (Kolossus)"])


def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "sltdctfweb")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


def get_auditoria_service(db=Depends(get_db)) -> AuditoriaService:
    return AuditoriaService(db)


@router.post("/executar")
async def executar_auditoria(
    cnpj: str = Form(..., description="CNPJ da empresa"),
    periodo: str = Form(..., description="Período (YYYY-MM)"),
    tipo: str = Form(default="sped_fiscal", description="Tipo: sped_fiscal ou sped_contribuicoes"),
    empresa_id: Optional[str] = Form(default=None),
    arquivo: UploadFile = File(..., description="Arquivo SPED (.txt)"),
    service: AuditoriaService = Depends(get_auditoria_service)
):
    """
    Executa auditoria completa em arquivo SPED
    
    **Funcionalidades:**
    - Validação de estrutura do SPED
    - Auditoria de NCM, CFOP, alíquotas
    - Cruzamento com dados do e-CAC
    - Cálculo de score de conformidade
    - Identificação de não conformidades
    
    **Tipos suportados:**
    - `sped_fiscal`: SPED Fiscal (ICMS/IPI)
    - `sped_contribuicoes`: SPED Contribuições (PIS/COFINS)
    """
    try:
        # Salvar arquivo temporariamente
        import tempfile
        import aiofiles
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            content = await arquivo.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Executar auditoria
        resultado = await service.executar_auditoria_sped(
            cnpj=cnpj,
            periodo=periodo,
            tipo=tipo,
            arquivo_path=tmp_path,
            empresa_id=empresa_id
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro na auditoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def listar_auditorias(
    cnpj: Optional[str] = Query(default=None),
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    service: AuditoriaService = Depends(get_auditoria_service)
):
    """
    Lista auditorias realizadas
    """
    auditorias = await service.listar_auditorias(
        cnpj=cnpj,
        empresa_id=empresa_id,
        tipo=tipo,
        limit=limit
    )
    return {"auditorias": auditorias, "total": len(auditorias)}


@router.get("/estatisticas")
async def obter_estatisticas_conformidade(
    cnpj: Optional[str] = Query(default=None),
    empresa_id: Optional[str] = Query(default=None),
    service: AuditoriaService = Depends(get_auditoria_service)
):
    """
    Obtém estatísticas de conformidade fiscal
    
    Retorna:
    - Total de auditorias
    - Score médio de conformidade
    - Total de não conformidades
    - Distribuição por severidade
    """
    return await service.obter_estatisticas_conformidade(
        cnpj=cnpj,
        empresa_id=empresa_id
    )


@router.get("/{auditoria_id}")
async def obter_auditoria(
    auditoria_id: str,
    service: AuditoriaService = Depends(get_auditoria_service)
):
    """
    Obtém detalhes de uma auditoria específica
    """
    auditoria = await service.obter_auditoria(auditoria_id)
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoria não encontrada")
    return auditoria
auditoria_router = router

