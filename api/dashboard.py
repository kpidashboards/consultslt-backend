"""
API Routes para Dashboard - Motor (async MongoDB driver)
Endpoints: GET, POST, PUT, DELETE para métricas
Injeção de dependência para conexão ao banco
"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.core.database import get_db
from backend.schemas.dashboard import (
    DashboardMetric,
    DashboardMetricCreate,
    DashboardMetricUpdate,
    DashboardOverview
)
from backend.services.dashboard import DashboardService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ===============================
# ENDPOINTS
# ===============================

@router.get("/overview", response_model=DashboardOverview, summary="Overview do Dashboard")
async def get_overview(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obtém overview do dashboard com KPIs principais
    
    Returns:
        DashboardOverview com métricas atuais
    """
    try:
        service = DashboardService(db)
        dashboard = await service.gerar_dashboard_inicial()
        
        return DashboardOverview(
            total_empresas=dashboard.get('empresas_ativas', 0) + dashboard.get('empresas_inativas', 0),
            empresas_ativas=dashboard.get('empresas_ativas', 0),
            empresas_inativas=dashboard.get('empresas_inativas', 0),
            das_gerados_mes=dashboard.get('das_gerados_mes', 0),
            certidoes_emitidas_mes=dashboard.get('certidoes_emitidas_mes', 0),
            alertas_criticos=dashboard.get('alertas_criticos', 0),
            taxa_conformidade=dashboard.get('taxa_conformidade', 0.0),
            obrigacoes_pendentes=dashboard.get('obrigacoes_pendentes', 0),
            ultima_atualizacao=datetime.fromisoformat(dashboard.get('data_geracao', datetime.utcnow().isoformat()))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar overview: {str(e)}"
        )


@router.get("/metricas", response_model=List[DashboardMetric], summary="Listar todas as métricas")
async def listar_metricas(
    skip: int = Query(0, ge=0, description="Paginação - pular registros"),
    limit: int = Query(10, ge=1, le=100, description="Paginação - limite de registros"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Lista todas as métricas do dashboard com paginação
    
    Args:
        skip: Número de registros a pular
        limit: Número máximo de registros a retornar
        db: Conexão ao banco (injetada)
    
    Returns:
        Lista de DashboardMetric
    """
    try:
        service = DashboardService(db)
        metricas = await service.obter_metricas(skip=skip, limit=limit)
        return metricas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar métricas: {str(e)}"
        )


@router.post("/metricas", response_model=DashboardMetric, status_code=status.HTTP_201_CREATED, summary="Criar nova métrica")
async def criar_metrica(dados: DashboardMetricCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Cria nova métrica no dashboard
    
    Args:
        dados: DashboardMetricCreate com os dados da métrica
        db: Conexão ao banco (injetada)
    
    Returns:
        DashboardMetric criada
    """
    try:
        service = DashboardService(db)
        metrica = await service.criar_metrica(dados)
        return metrica
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar métrica: {str(e)}"
        )


@router.get("/metricas/{metrica_id}", response_model=DashboardMetric, summary="Obter métrica por ID")
async def obter_metrica(metrica_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obtém uma métrica específica pelo ID
    
    Args:
        metrica_id: ID da métrica (MongoDB ObjectId)
        db: Conexão ao banco (injetada)
    
    Returns:
        DashboardMetric encontrada
    """
    try:
        service = DashboardService(db)
        metrica = await service.obter_pela_id(metrica_id)
        if not metrica:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Métrica {metrica_id} não encontrada"
            )
        return metrica
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter métrica: {str(e)}"
        )


@router.put("/metricas/{metrica_id}", response_model=DashboardMetric, summary="Atualizar métrica")
async def atualizar_metrica(
    metrica_id: str, 
    dados: DashboardMetricUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualiza uma métrica existente
    
    Args:
        metrica_id: ID da métrica a atualizar
        dados: DashboardMetricUpdate com campos a atualizar
        db: Conexão ao banco (injetada)
    
    Returns:
        DashboardMetric atualizada
    """
    try:
        service = DashboardService(db)
        metrica = await service.atualizar_metrica(metrica_id, dados)
        if not metrica:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Métrica {metrica_id} não encontrada"
            )
        return metrica
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao atualizar métrica: {str(e)}"
        )


@router.delete("/metricas/{metrica_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deletar métrica")
async def deletar_metrica(metrica_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Deleta uma métrica (soft delete)
    
    Args:
        metrica_id: ID da métrica a deletar
        db: Conexão ao banco (injetada)
    
    Returns:
        Status 204 se sucesso
    """
    try:
        service = DashboardService(db)
        sucesso = await service.deletar_metrica(metrica_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Métrica {metrica_id} não encontrada"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar métrica: {str(e)}"
        )


@router.get("/historico", response_model=List[DashboardMetric], summary="Obter histórico de métricas")
async def obter_historico(
    dias: int = Query(30, ge=1, le=365, description="Número de dias a retornar"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obtém histórico de métricas dos últimos dias
    
    Args:
        dias: Número de dias a retornar (1-365)
        db: Conexão ao banco (injetada)
    
    Returns:
        Lista de DashboardMetric do período
    """
    try:
        service = DashboardService(db)
        metricas = await service.obter_historico(dias=dias)
        return metricas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter histórico: {str(e)}"
        )


@router.get("/comparacao", summary="Comparar períodos")
async def comparar_periodos(
    data_inicio1: datetime = Query(..., description="Data início período 1"),
    data_fim1: datetime = Query(..., description="Data fim período 1"),
    data_inicio2: datetime = Query(..., description="Data início período 2"),
    data_fim2: datetime = Query(..., description="Data fim período 2"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Compara métricas entre dois períodos
    
    Args:
        data_inicio1: Data de início do período 1
        data_fim1: Data de fim do período 1
        data_inicio2: Data de início do período 2
        data_fim2: Data de fim do período 2
        db: Conexão ao banco (injetada)
    
    Returns:
        Comparação entre os períodos
    """
    try:
        service = DashboardService(db)
        comparacao = await service.comparar_periodos(
            data_inicio1, data_fim1, data_inicio2, data_fim2
        )
        return comparacao
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao comparar períodos: {str(e)}"
        )


@router.post("/registrar-atividade", status_code=status.HTTP_200_OK, summary="Registrar atividade no dashboard")
async def registrar_atividade(
    empresa_id: str = Query(..., description="ID da empresa"),
    empresa_nome: str = Query(..., description="Nome da empresa"),
    acao: str = Query(..., description="Ação realizada"),
    usuario_id: Optional[str] = Query(None, description="ID do usuário (opcional)"),
    detalhes: Optional[str] = Query(None, description="Detalhes adicionais (opcional)"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Registra atividade recente no dashboard
    
    Args:
        empresa_id: ID da empresa
        empresa_nome: Nome da empresa
        acao: Tipo de ação realizada
        usuario_id: ID do usuário que realizou a ação
        detalhes: Detalhes adicionais
        db: Conexão ao banco (injetada)
    
    Returns:
        Confirmação de sucesso
    """
    try:
        service = DashboardService(db)
        await service.registrar_atividade(
            empresa_id=empresa_id,
            empresa_nome=empresa_nome,
            acao=acao,
            usuario_id=usuario_id,
            detalhes=detalhes
        )
        return {"mensagem": "Atividade registrada com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar atividade: {str(e)}"
        )
