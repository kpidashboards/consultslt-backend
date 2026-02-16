"""
Repositório para Dashboard - CRUD com Motor (async MongoDB driver)
Motor PURO, sem mongoengine
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

from backend.models.dashboard import (
    serialize_metric, 
    serialize_snapshot,
    DASHBOARD_COLLECTION,
    SNAPSHOT_COLLECTION
)


class DashboardRepository:
    """Repositório para operações com Dashboard usando Motor"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Inicializa repositório com conexão ao banco
        Args:
            db: AsyncIOMotorDatabase (injetado via FastAPI dependency)
        """
        self.db = db
        self.collection = self.db[DASHBOARD_COLLECTION]
        self.snapshot_collection = self.db[SNAPSHOT_COLLECTION]

    async def criar_metrica(self, dados: dict) -> Dict[str, Any]:
        """
        Cria nova métrica no banco
        Args:
            dados: Dicionário com dados da métrica
        Returns:
            Documento criado com _id
        """
        try:
            documento = {
                'empresas_ativas': dados.get('empresas_ativas', 0),
                'empresas_inativas': dados.get('empresas_inativas', 0),
                'das_gerados_mes': dados.get('das_gerados_mes', 0),
                'certidoes_emitidas_mes': dados.get('certidoes_emitidas_mes', 0),
                'alertas_criticos': dados.get('alertas_criticos', 0),
                'taxa_conformidade': dados.get('taxa_conformidade', 0.0),
                'receita_bruta_mes': dados.get('receita_bruta_mes', 0.0),
                'despesa_mensal': dados.get('despesa_mensal', 0.0),
                'obrigacoes_pendentes': dados.get('obrigacoes_pendentes', 0),
                'proximos_vencimentos': dados.get('proximos_vencimentos', []),
                'atividades_recentes': dados.get('atividades_recentes', []),
                'data_geracao': datetime.utcnow(),
                'data_atualizacao': datetime.utcnow(),
                'ativo': True
            }
            
            resultado = await self.collection.insert_one(documento)
            documento['_id'] = resultado.inserted_id
            return serialize_metric(documento)
            
        except Exception as e:
            raise Exception(f"Erro ao criar métrica: {str(e)}")

    async def obter_todas(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém todas as métricas ativas (ordenadas por data descendente)
        Args:
            skip: Número de documentos a pular (paginação)
            limit: Máximo de documentos a retornar
        Returns:
            Lista de métricas serializadas
        """
        try:
            cursor = self.collection.find(
                {'ativo': True}
            ).sort(
                'data_geracao', -1
            ).skip(skip).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            return [serialize_metric(doc) for doc in docs]
            
        except Exception as e:
            raise Exception(f"Erro ao obter métricas: {str(e)}")

    async def obter_por_id(self, id_str: str) -> Optional[Dict[str, Any]]:
        """
        Obtém métrica por ID
        Args:
            id_str: ID como string (será convertido para ObjectId)
        Returns:
            Métrica serializada ou None
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return None
                
            doc = await self.collection.find_one({
                '_id': object_id,
                'ativo': True
            })
            return serialize_metric(doc) if doc else None
            
        except Exception as e:
            raise Exception(f"Erro ao obter métrica: {str(e)}")

    async def obter_ultima() -> Optional[Dict[str, Any]]:
        """
        Obtém a métrica mais recente
        Returns:
            Métrica mais recente serializada ou None
        """
        try:
            doc = await self.collection.find_one(
                {'ativo': True},
                sort=[('data_geracao', -1)]
            )
            return serialize_metric(doc) if doc else None
            
        except Exception as e:
            raise Exception(f"Erro ao obter última métrica: {str(e)}")

    async def obter_por_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtém métricas dentro de um período
        Args:
            data_inicio: Data início
            data_fim: Data fim
            skip: Paginação
            limit: Limite
        Returns:
            Lista de métricas
        """
        try:
            cursor = self.collection.find({
                'ativo': True,
                'data_geracao': {
                    '$gte': data_inicio,
                    '$lte': data_fim
                }
            }).sort('data_geracao', -1).skip(skip).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            return [serialize_metric(doc) for doc in docs]
            
        except Exception as e:
            raise Exception(f"Erro ao obter métricas do período: {str(e)}")

    async def atualizar(self, id_str: str, dados: dict) -> Optional[Dict[str, Any]]:
        """
        Atualiza métrica
        Args:
            id_str: ID como string
            dados: Dicionário com campos a atualizar
        Returns:
            Documento atualizado ou None
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return None
            
            # Remove campos que não devem ser atualizados
            dados.pop('_id', None)
            dados.pop('data_geracao', None)
            dados['data_atualizacao'] = datetime.utcnow()
            
            resultado = await self.collection.find_one_and_update(
                {'_id': object_id, 'ativo': True},
                {'$set': dados},
                return_document=True
            )
            
            return serialize_metric(resultado) if resultado else None
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar métrica: {str(e)}")

    async def deletar(self, id_str: str) -> bool:
        """
        Deleta métrica (soft delete - marca como inativo)
        Args:
            id_str: ID como string
        Returns:
            True se deletada, False se não encontrada
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return False
                
            resultado = await self.collection.update_one(
                {'_id': object_id, 'ativo': True},
                {'$set': {'ativo': False, 'data_atualizacao': datetime.utcnow()}}
            )
            
            return resultado.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Erro ao deletar métrica: {str(e)}")

    async def deletar_permanente(self, id_str: str) -> bool:
        """
        Deleta permanentemente da base
        Args:
            id_str: ID como string
        Returns:
            True se deletada, False se não encontrada
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return False
                
            resultado = await self.collection.delete_one({'_id': object_id})
            return resultado.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Erro ao deletar permanentemente: {str(e)}")

    async def adicionar_vencimento(self, id_str: str, vencimento: dict) -> Optional[Dict[str, Any]]:
        """
        Adiciona um próximo vencimento
        Args:
            id_str: ID como string
            vencimento: Dicionário com dados do vencimento
        Returns:
            Documento atualizado ou None
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return None
                
            venc_doc = {
                'empresa_id': vencimento.get('empresa_id'),
                'empresa_nome': vencimento.get('empresa_nome'),
                'tipo': vencimento.get('tipo'),
                'data_vencimento': vencimento.get('data_vencimento'),
                'prioridade': vencimento.get('prioridade', 'normal'),
                'dias_restantes': vencimento.get('dias_restantes', 0)
            }
            
            resultado = await self.collection.find_one_and_update(
                {'_id': object_id, 'ativo': True},
                {'$push': {'proximos_vencimentos': venc_doc},
                 '$set': {'data_atualizacao': datetime.utcnow()}},
                return_document=True
            )
            
            return serialize_metric(resultado) if resultado else None
            
        except Exception as e:
            raise Exception(f"Erro ao adicionar vencimento: {str(e)}")

    async def adicionar_atividade(self, id_str: str, atividade: dict) -> Optional[Dict[str, Any]]:
        """
        Adiciona atividade recente (mantém últimas 20)
        Args:
            id_str: ID como string
            atividade: Dicionário com dados da atividade
        Returns:
            Documento atualizado ou None
        """
        try:
            try:
                object_id = ObjectId(id_str)
            except Exception:
                return None
                
            ativ_doc = {
                'acao': atividade.get('acao'),
                'empresa_id': atividade.get('empresa_id'),
                'empresa_nome': atividade.get('empresa_nome'),
                'timestamp': datetime.utcnow(),
                'usuario_id': atividade.get('usuario_id'),
                'detalhes': atividade.get('detalhes')
            }
            
            # Adiciona no início da lista
            resultado = await self.collection.find_one_and_update(
                {'_id': object_id, 'ativo': True},
                {'$push': {
                    'atividades_recentes': {
                        '$each': [ativ_doc],
                        '$position': 0,
                        '$slice': 20  # Mantém apenas 20
                    }
                },
                 '$set': {'data_atualizacao': datetime.utcnow()}},
                return_document=True
            )
            
            return serialize_metric(resultado) if resultado else None
            
        except Exception as e:
            raise Exception(f"Erro ao adicionar atividade: {str(e)}")

    async def criar_snapshot(self, metrica_id: str, alteracoes: Optional[dict] = None) -> Dict[str, Any]:
        """
        Cria snapshot histórico das métricas
        Args:
            metrica_id: ID da métrica como string
            alteracoes: Alterações realizadas (opcional)
        Returns:
            Snapshot criado
        """
        try:
            try:
                object_id = ObjectId(metrica_id)
            except Exception:
                raise ValueError("ID inválido")
                
            # Obtém documento original
            doc = await self.collection.find_one({'_id': object_id})
            if not doc:
                raise ValueError("Métrica não encontrada")
            
            # Cria snapshot
            snapshot = {
                'data_snapshot': datetime.utcnow(),
                'metricas_json': json.dumps(serialize_metric(doc), default=str),
                'alteracoes': json.dumps(alteracoes, default=str) if alteracoes else None,
                'criado_em': datetime.utcnow()
            }
            
            resultado = await self.snapshot_collection.insert_one(snapshot)
            snapshot['_id'] = resultado.inserted_id
            return serialize_snapshot(snapshot)
            
        except Exception as e:
            raise Exception(f"Erro ao criar snapshot: {str(e)}")

    async def obter_snapshots(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Obtém últimos snapshots para histórico
        Args:
            limit: Limite de documentos
            skip: Paginação
        Returns:
            Lista de snapshots
        """
        try:
            cursor = self.snapshot_collection.find(
                {}
            ).sort('criado_em', -1).skip(skip).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            return [serialize_snapshot(doc) for doc in docs]
            
        except Exception as e:
            raise Exception(f"Erro ao obter snapshots: {str(e)}")

    async def contar_total(self) -> int:
        """
        Conta total de métricas ativas
        Returns:
            Contagem
        """
        try:
            return await self.collection.count_documents({'ativo': True})
        except Exception as e:
            raise Exception(f"Erro ao contar métricas: {str(e)}")
