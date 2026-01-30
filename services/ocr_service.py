"""
Serviço de OCR e Processamento de Documentos (Paridade Kolossus)
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import aiofiles
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from engines.ocr_engine import OCREngine, TipoDocumentoFiscal

logger = logging.getLogger(__name__)


class OCRService:
    """
    Serviço de OCR para processamento automático de documentos fiscais
    """
    
    UPLOAD_DIR = Path("/data/uploads/ocr")
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.engine = OCREngine()
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def processar_documento(
        self,
        filename: str,
        content: bytes,
        empresa_id: Optional[str] = None,
        tipo_esperado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa um documento com OCR
        
        Args:
            filename: Nome do arquivo
            content: Conteúdo binário
            empresa_id: ID da empresa
            tipo_esperado: Tipo esperado do documento
            
        Returns:
            Dict com resultado do processamento OCR
        """
        logger.info(f"Processando documento OCR: {filename}")
        
        # Gerar ID e salvar arquivo
        doc_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix.lower()
        stored_filename = f"{doc_id}{file_ext}"
        file_path = self.UPLOAD_DIR / stored_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Processar com engine OCR
        resultado_ocr = self.engine.processar_documento(
            str(file_path),
            tipo_esperado
        )
        
        # Criar registro
        documento = {
            "id": doc_id,
            "nome_arquivo": filename,
            "caminho_arquivo": str(file_path),
            "tamanho_bytes": len(content),
            "empresa_id": empresa_id,
            "tipo_detectado": resultado_ocr["tipo"],
            "score_confianca": resultado_ocr["score_confianca"],
            "dados_extraidos": resultado_ocr["dados_extraidos"],
            "validacoes": resultado_ocr["validacoes"],
            "status": "processado" if resultado_ocr["score_confianca"] >= 50 else "revisao_necessaria",
            "created_at": datetime.utcnow()
        }
        
        await self.db.ocr_documentos.insert_one(documento)
        
        logger.info(
            f"Documento processado: ID={doc_id}, "
            f"Tipo={resultado_ocr['tipo']}, "
            f"Confiança={resultado_ocr['score_confianca']}%"
        )
        
        return {
            "id": doc_id,
            "tipo": resultado_ocr["tipo"],
            "score_confianca": resultado_ocr["score_confianca"],
            "dados_extraidos": resultado_ocr["dados_extraidos"],
            "validacoes": resultado_ocr["validacoes"],
            "status": documento["status"]
        }
    
    async def listar_documentos_ocr(
        self,
        empresa_id: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista documentos processados por OCR
        """
        filtro = {}
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        if tipo:
            filtro["tipo_detectado"] = tipo
        if status:
            filtro["status"] = status
        
        cursor = self.db.ocr_documentos.find(
            filtro,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def obter_documento_ocr(self, documento_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um documento OCR
        """
        return await self.db.ocr_documentos.find_one(
            {"id": documento_id},
            {"_id": 0}
        )
    
    async def obter_estatisticas_ocr(
        self,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de processamento OCR
        """
        filtro = {}
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        
        total = await self.db.ocr_documentos.count_documents(filtro)
        processados = await self.db.ocr_documentos.count_documents({**filtro, "status": "processado"})
        revisao = await self.db.ocr_documentos.count_documents({**filtro, "status": "revisao_necessaria"})
        
        # Score médio
        pipeline = [
            {"$match": filtro},
            {"$group": {"_id": None, "score_medio": {"$avg": "$score_confianca"}}}
        ]
        resultado = await self.db.ocr_documentos.aggregate(pipeline).to_list(1)
        score_medio = resultado[0]["score_medio"] if resultado else 0
        
        # Por tipo
        pipeline_tipo = [
            {"$match": filtro},
            {"$group": {"_id": "$tipo_detectado", "count": {"$sum": 1}}}
        ]
        por_tipo = await self.db.ocr_documentos.aggregate(pipeline_tipo).to_list(20)
        
        return {
            "total": total,
            "processados": processados,
            "revisao_necessaria": revisao,
            "score_medio": round(score_medio, 2),
            "taxa_sucesso": round((processados / total * 100) if total > 0 else 0, 2),
            "por_tipo": {item["_id"]: item["count"] for item in por_tipo}
        }
