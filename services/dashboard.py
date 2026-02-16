"""
Serviço para Dashboard - Lógica de negócio e cálculo de KPIs
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.repositories.dashboard import DashboardRepository
from backend.schemas.dashboard import DashboardMetricCreate, DashboardMetricUpdate


class DashboardService:
    """Serviço para operações com Dashboard e cálculo de métricas"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Inicializa serviço com conexão ao banco
        Args:
            db: AsyncIOMotorDatabase (injetado via FastAPI dependency)
        """
        self.db = db
        self.repository = DashboardRepository(db)

    async def calcular_kpis_atuais(self) -> Dict[str, Any]:
        """
        Calcula KPIs em tempo real consultando outras coleções
        Futura implementação: agregações com empresas, alertas, documentos
        """
        # Placeholder - será integrado com outras APIs
        kpis = {
            'empresas_ativas': 127,
            'empresas_inativas': 12,
            'das_gerados_mes': 98,
            'certidoes_emitidas_mes': 245,
            'alertas_criticos': 3,
            'taxa_conformidade': 94.5,
            'receita_bruta_mes': 458000.00,
            'despesa_mensal': 125000.00,
            'obrigacoes_pendentes': 42
        }
        return kpis

    async def calcular_proximos_vencimentos(self) -> List[Dict[str, Any]]:
        """
        Calcula próximos vencimentos (futura integração com obrigações)
        Retorna lista ordenada por data
        """
        hoje = datetime.utcnow()
        proximos = [
            {
                'empresa_id': '1',
                'empresa_nome': 'TRES PINHEIROS LTDA',
                'tipo': 'DAS 01/2025',
                'data_vencimento': (hoje + timedelta(days=5)).isoformat(),
                'prioridade': 'critica',
                'dias_restantes': 5
            },
            {
                'empresa_id': '2',
                'empresa_nome': 'SUPER GALO REST.',
                'tipo': 'DCTF Web',
                'data_vencimento': (hoje + timedelta(days=7)).isoformat(),
                'prioridade': 'alta',
                'dias_restantes': 7
            },
            {
                'empresa_id': '3',
                'empresa_nome': 'MAFE RESTAURANTE',
                'tipo': 'Certidão FGTS',
                'data_vencimento': (hoje + timedelta(days=10)).isoformat(),
                'prioridade': 'normal',
                'dias_restantes': 10
            },
        ]
        return proximos

    async def registrar_atividade(
        self, 
        empresa_id: str, 
        empresa_nome: str, 
        acao: str, 
        usuario_id: Optional[str] = None, 
        detalhes: Optional[str] = None
    ) -> None:
        """
        Registra atividade recente no dashboard mais recente
        """
        try:
            # Obtém última métrica
            ultima = await self.repository.obter_por_periodo(
                datetime.utcnow() - timedelta(days=1),
                datetime.utcnow(),
                limit=1
            )
            
            if ultima:
                metrica_id = ultima[0].get('id') if ultima else None
                if metrica_id:
                    await self.repository.adicionar_atividade(
                        metrica_id,
                        {
                            'acao': acao,
                            'empresa_id': empresa_id,
                            'empresa_nome': empresa_nome,
                            'usuario_id': usuario_id,
                            'detalhes': detalhes
                        }
                    )
        except Exception as e:
            # Log silencioso - não interrompe fluxo
            print(f"Erro ao registrar atividade: {e}")

    async def gerar_dashboard_inicial(self) -> Dict[str, Any]:
        """
        Gera ou obtém dashboard inicial com KPIs
        Retorna última métrica se foi gerada há menos de 1 hora
        """
        try:
            # Tenta obter última métrica do período de 1 hora
            ultimas = await self.repository.obter_por_periodo(
                datetime.utcnow() - timedelta(hours=1),
                datetime.utcnow(),
                limit=1
            )
            
            if ultimas and len(ultimas) > 0:
                return ultimas[0]

            # Se não existe ou expirou, cria nova
            kpis = await self.calcular_kpis_atuais()
            proximos = await self.calcular_proximos_vencimentos()

            dados = {
                **kpis,
                'proximos_vencimentos': proximos,
                'atividades_recentes': []
            }
            
            nova_metrica = await self.repository.criar_metrica(dados)
            return nova_metrica
            
        except Exception as e:
            # Fallback: retorna KPIs vazio
            print(f"Erro ao gerar dashboard inicial: {e}")
            return {
                'empresas_ativas': 0,
                'empresas_inativas': 0,
                'das_gerados_mes': 0,
                'certidoes_emitidas_mes': 0,
                'alertas_criticos': 0,
                'taxa_conformidade': 0.0,
                'receita_bruta_mes': 0.0,
                'despesa_mensal': 0.0,
                'obrigacoes_pendentes': 0
            }

    async def criar_metrica(self, dados: DashboardMetricCreate) -> Dict[str, Any]:
        """Cria nova métrica com snapshot"""
        metrica_dict = dados.dict()
        metrica = await self.repository.criar_metrica(metrica_dict)
        
        # Cria snapshot inicial
        if 'id' in metrica:
            await self.repository.criar_snapshot(metrica['id'])
        
        return metrica

    async def obter_metricas(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtém lista paginada de métricas"""
        return await self.repository.obter_todas(skip=skip, limit=limit)

    async def obter_pela_id(self, metrica_id: str) -> Optional[Dict[str, Any]]:
        """Obtém métrica por ID"""
        return await self.repository.obter_por_id(metrica_id)

    async def atualizar_metrica(
        self, 
        metrica_id: str, 
        dados: DashboardMetricUpdate
    ) -> Optional[Dict[str, Any]]:
        """Atualiza métrica com rastreamento de alterações"""
        dados_dict = dados.dict(exclude_unset=True)
        
        # Captura estado anterior para comparação
        anterior = await self.repository.obter_por_id(metrica_id)
        
        # Atualiza
        metrica = await self.repository.atualizar(metrica_id, dados_dict)
        
        if metrica:
            # Cria snapshot com alterações
            alteracoes = {}
            for key, value in dados_dict.items():
                if anterior and anterior.get(key) != value:
                    alteracoes[key] = {
                        'anterior': anterior.get(key),
                        'novo': value
                    }
            
            await self.repository.criar_snapshot(
                metrica_id, 
                alteracoes if alteracoes else None
            )
            return metrica
        
        return None

    async def deletar_metrica(self, metrica_id: str) -> bool:
        """Deleta métrica (soft delete)"""
        return await self.repository.deletar(metrica_id)

    async def obter_historico(self, dias: int = 30) -> List[Dict[str, Any]]:
        """Obtém histórico de métricas"""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        data_fim = datetime.utcnow()
        
        return await self.repository.obter_por_periodo(data_inicio, data_fim, limit=100)

    async def comparar_periodos(
        self, 
        data_inicio1: datetime, 
        data_fim1: datetime, 
        data_inicio2: datetime, 
        data_fim2: datetime
    ) -> Dict[str, Any]:
        """Compara métricas entre dois períodos"""
        periodo1 = await self.repository.obter_por_periodo(data_inicio1, data_fim1, limit=100)
        periodo2 = await self.repository.obter_por_periodo(data_inicio2, data_fim2, limit=100)
        
        def calcular_media(metricas, campo):
            if not metricas:
                return 0
            total = sum(m.get(campo, 0) for m in metricas)
            return total / len(metricas)
        
        return {
            'periodo_1': {
                'empresas_ativas_media': calcular_media(periodo1, 'empresas_ativas'),
                'das_media': calcular_media(periodo1, 'das_gerados_mes'),
                'conformidade_media': calcular_media(periodo1, 'taxa_conformidade'),
            },
            'periodo_2': {
                'empresas_ativas_media': calcular_media(periodo2, 'empresas_ativas'),
                'das_media': calcular_media(periodo2, 'das_gerados_mes'),
                'conformidade_media': calcular_media(periodo2, 'taxa_conformidade'),
            }
        }
