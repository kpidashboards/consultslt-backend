"""
Type Hints para Dashboard - Motor (async MongoDB driver)
Sem mongoengine - apenas type hints puros
"""
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


# ===============================
# EMBEDDED DOCUMENTS (Type Hints)
# ===============================
class ProximoVencimentoDict(TypedDict, total=False):
    """Documento aninhado: Próximo vencimento"""
    empresa_id: str
    empresa_nome: str
    tipo: str
    data_vencimento: datetime
    prioridade: str  # 'critica', 'alta', 'normal', 'baixa'
    dias_restantes: int


class AtividadeRecenteDict(TypedDict, total=False):
    """Documento aninhado: Atividade recente"""
    acao: str
    empresa_id: str
    empresa_nome: str
    timestamp: datetime
    usuario_id: Optional[str]
    detalhes: Optional[str]


class DashboardMetricDict(TypedDict, total=False):
    """Documento completo de métrica (para MongoDB)"""
    _id: ObjectId
    empresas_ativas: int
    empresas_inativas: int
    das_gerados_mes: int
    certidoes_emitidas_mes: int
    alertas_criticos: int
    taxa_conformidade: float
    receita_bruta_mes: float
    despesa_mensal: float
    obrigacoes_pendentes: int
    proximos_vencimentos: List[ProximoVencimentoDict]
    atividades_recentes: List[AtividadeRecenteDict]
    data_geracao: datetime
    data_atualizacao: datetime
    ativo: bool


class DashboardSnapshotDict(TypedDict, total=False):
    """Documento de snapshot (histórico)"""
    _id: ObjectId
    data_snapshot: datetime
    metricas_json: str
    alteracoes: Optional[str]
    criado_em: datetime


# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def serialize_metric(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Converte documento MongoDB para JSON serializável"""
    if not doc:
        return {}
    
    return {
        'id': str(doc.get('_id', '')),
        'empresas_ativas': doc.get('empresas_ativas', 0),
        'empresas_inativas': doc.get('empresas_inativas', 0),
        'das_gerados_mes': doc.get('das_gerados_mes', 0),
        'certidoes_emitidas_mes': doc.get('certidoes_emitidas_mes', 0),
        'alertas_criticos': doc.get('alertas_criticos', 0),
        'taxa_conformidade': doc.get('taxa_conformidade', 0.0),
        'receita_bruta_mes': doc.get('receita_bruta_mes', 0.0),
        'despesa_mensal': doc.get('despesa_mensal', 0.0),
        'obrigacoes_pendentes': doc.get('obrigacoes_pendentes', 0),
        'proximos_vencimentos': doc.get('proximos_vencimentos', []),
        'atividades_recentes': doc.get('atividades_recentes', []),
        'data_geracao': doc.get('data_geracao', datetime.utcnow()).isoformat() if isinstance(doc.get('data_geracao'), datetime) else doc.get('data_geracao'),
        'data_atualizacao': doc.get('data_atualizacao', datetime.utcnow()).isoformat() if isinstance(doc.get('data_atualizacao'), datetime) else doc.get('data_atualizacao'),
        'ativo': doc.get('ativo', True)
    }


def serialize_snapshot(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Converte snapshot para JSON serializável"""
    if not doc:
        return {}
    
    return {
        'id': str(doc.get('_id', '')),
        'data_snapshot': doc.get('data_snapshot', datetime.utcnow()).isoformat() if isinstance(doc.get('data_snapshot'), datetime) else doc.get('data_snapshot'),
        'metricas_json': doc.get('metricas_json', '{}'),
        'alteracoes': doc.get('alteracoes'),
        'criado_em': doc.get('criado_em', datetime.utcnow()).isoformat() if isinstance(doc.get('criado_em'), datetime) else doc.get('criado_em')
    }


# ===============================
# CONSTANTES
# ===============================
DASHBOARD_COLLECTION = 'dashboard_metrics'
SNAPSHOT_COLLECTION = 'dashboard_snapshots'

# Índices esperados no MongoDB
EXPECTED_INDEXES = {
    DASHBOARD_COLLECTION: [
        ('data_geracao', 1),
        ('data_atualizacao', 1),
        ('ativo', 1),
        ('data_geracao', -1),
    ],
    SNAPSHOT_COLLECTION: [
        ('data_snapshot', 1),
        ('criado_em', -1),
    ]
}
