"""
Serviço de Auditoria Fiscal (Paridade Kolossus)
Orquestra auditorias SPED e cruzamentos fiscais
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from engines.sped_engine import SPEDEngine, TipoAuditoria, NaoConformidade

logger = logging.getLogger(__name__)


class AuditoriaService:
    """
    Serviço para auditoria fiscal e cruzamento de dados
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.engine = SPEDEngine()
    
    async def executar_auditoria_sped(
        self,
        cnpj: str,
        periodo: str,
        tipo: str,
        arquivo_path: str,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa auditoria completa de arquivo SPED
        
        Args:
            cnpj: CNPJ da empresa
            periodo: Período de referência
            tipo: Tipo de SPED (sped_fiscal, sped_contribuicoes)
            arquivo_path: Caminho do arquivo SPED
            empresa_id: ID da empresa
            
        Returns:
            Dict com resultado da auditoria
        """
        logger.info(f"Executando auditoria {tipo}: CNPJ={cnpj}, Período={periodo}")
        
        # Converter tipo para enum
        tipo_auditoria = TipoAuditoria.SPED_FISCAL
        if "contribui" in tipo.lower():
            tipo_auditoria = TipoAuditoria.SPED_CONTRIBUICOES
        
        # Executar auditoria interna
        nao_conformidades = self.engine.auditar_sped(tipo_auditoria, arquivo_path)
        
        # Simular dados do SPED
        dados_sped = self.engine._simular_parser_sped(arquivo_path)
        
        # Buscar dados externos para cruzamento
        dados_externos = await self._coletar_dados_externos(cnpj)
        
        # Executar cruzamentos
        nao_conformidades_cruzamento = self.engine.cruzar_dados_fiscais(
            dados_sped, dados_externos
        )
        
        # Consolidar
        todas_nao_conformidades = nao_conformidades + nao_conformidades_cruzamento
        
        # Gerar relatório
        relatorio = self.engine.gerar_relatorio_auditoria(
            todas_nao_conformidades, dados_sped
        )
        
        # Persistir auditoria
        auditoria_id = str(uuid.uuid4())
        auditoria = {
            "id": auditoria_id,
            "cnpj": cnpj,
            "empresa_id": empresa_id,
            "periodo_referencia": periodo,
            "tipo": tipo_auditoria.value,
            "arquivo_sped": arquivo_path,
            "score_conformidade": relatorio["score_conformidade"],
            "total_nao_conformidades": relatorio["total_nao_conformidades"],
            "por_severidade": relatorio["por_severidade"],
            "nao_conformidades": relatorio["nao_conformidades"],
            "recomendacao": relatorio["recomendacao_geral"],
            "created_at": datetime.utcnow()
        }
        
        await self.db.auditorias.insert_one(auditoria)
        
        logger.info(
            f"Auditoria concluída: ID={auditoria_id}, "
            f"Score={relatorio['score_conformidade']}%, "
            f"Não conformidades={relatorio['total_nao_conformidades']}"
        )
        
        return {
            "id": auditoria_id,
            **relatorio
        }
    
    async def _coletar_dados_externos(self, cnpj: str) -> Dict[str, Any]:
        """
        Coleta dados de fontes externas para cruzamento
        """
        # Verificar pendências e-CAC (mock)
        pendencia_ecac = False
        ecac_data = await self.db.ecac_pendencias.find_one({"cnpj": cnpj})
        if ecac_data:
            pendencia_ecac = ecac_data.get("tem_pendencia", False)
        
        # Contar NF-e recebidas
        total_nfe = await self.db.documentos.count_documents({
            "cnpj": cnpj,
            "tipo": "nfe"
        })
        
        return {
            "pendencia_ecac": pendencia_ecac,
            "total_nfe_recebidas": total_nfe
        }
    
    async def listar_auditorias(
        self,
        cnpj: Optional[str] = None,
        empresa_id: Optional[str] = None,
        tipo: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Lista auditorias realizadas
        """
        filtro = {}
        if cnpj:
            filtro["cnpj"] = cnpj
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        if tipo:
            filtro["tipo"] = tipo
        
        cursor = self.db.auditorias.find(
            filtro,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def obter_auditoria(self, auditoria_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de uma auditoria
        """
        return await self.db.auditorias.find_one(
            {"id": auditoria_id},
            {"_id": 0}
        )
    
    async def obter_estatisticas_conformidade(
        self,
        cnpj: Optional[str] = None,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de conformidade
        """
        filtro = {}
        if cnpj:
            filtro["cnpj"] = cnpj
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        
        # Agregar estatísticas
        pipeline = [
            {"$match": filtro},
            {
                "$group": {
                    "_id": None,
                    "total_auditorias": {"$sum": 1},
                    "score_medio": {"$avg": "$score_conformidade"},
                    "total_nao_conformidades": {"$sum": "$total_nao_conformidades"},
                    "criticos": {"$sum": "$por_severidade.critico"},
                    "avisos": {"$sum": "$por_severidade.aviso"}
                }
            }
        ]
        
        resultado = await self.db.auditorias.aggregate(pipeline).to_list(1)
        
        if resultado:
            return {
                "total_auditorias": resultado[0]["total_auditorias"],
                "score_medio": round(resultado[0]["score_medio"], 2),
                "total_nao_conformidades": resultado[0]["total_nao_conformidades"],
                "total_criticos": resultado[0]["criticos"],
                "total_avisos": resultado[0]["avisos"]
            }
        
        return {
            "total_auditorias": 0,
            "score_medio": 0,
            "total_nao_conformidades": 0,
            "total_criticos": 0,
            "total_avisos": 0
        }
