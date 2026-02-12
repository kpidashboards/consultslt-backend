"""
Serviço de OCR e Processamento de Documentos
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import aiofiles

from ..repositories.documentos_repository import DocumentosRepository
from ..engines.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class OCRService:
    """
    Serviço de OCR para processamento automático de documentos fiscais
    """

    # Diretório seguro dentro do projeto
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_DIR = BASE_DIR / "data" / "uploads" / "ocr"

    def __init__(self):
        self.repo = DocumentosRepository()
        self.engine = OCREngine()

        # Garante que a pasta exista
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
        """

        try:
            logger.info(f"Iniciando processamento OCR: {filename}")

            # Gerar ID único
            doc_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix.lower()
            stored_filename = f"{doc_id}{file_ext}"
            file_path = self.UPLOAD_DIR / stored_filename

            # Salvar arquivo
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # Processar com engine
            resultado_ocr = self.engine.processar_documento(
                str(file_path),
                tipo_esperado
            )

            # Montar objeto de persistência
            documento = {
                "id": doc_id,
                "nome_arquivo": filename,
                "caminho_arquivo": str(file_path),
                "tamanho_bytes": len(content),
                "empresa_id": empresa_id,
                "tipo_detectado": resultado_ocr.get("tipo"),
                "score_confianca": resultado_ocr.get("score_confianca", 0),
                "dados_extraidos": resultado_ocr.get("dados_extraidos", {}),
                "validacoes": resultado_ocr.get("validacoes", []),
                "status": (
                    "processado"
                    if resultado_ocr.get("score_confianca", 0) >= 50
                    else "revisao_necessaria"
                ),
                "created_at": datetime.utcnow()
            }

            # Persistir
            await self.repo.create_documento(documento)

            logger.info(
                f"OCR concluído: ID={doc_id}, "
                f"Tipo={documento['tipo_detectado']}, "
                f"Confiança={documento['score_confianca']}%"
            )

            return {
                "id": doc_id,
                "tipo": documento["tipo_detectado"],
                "score_confianca": documento["score_confianca"],
                "dados_extraidos": documento["dados_extraidos"],
                "validacoes": documento["validacoes"],
                "status": documento["status"]
            }

        except Exception as e:
            logger.exception("Erro ao processar documento OCR")
            raise e

    async def listar_documentos_ocr(
        self,
        empresa_id: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista documentos processados via OCR
        """

        filtro = {}

        if empresa_id:
            filtro["empresa_id"] = empresa_id

        if tipo:
            filtro["tipo_detectado"] = tipo

        if status:
            filtro["status"] = status

        return await self.repo.list_documentos(filtro, limit)

    async def obter_documento_ocr(
        self,
        documento_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um documento OCR
        """
        return await self.repo.get_documento_by_id(documento_id)

    async def obter_estatisticas_ocr(
        self,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de OCR
        """

        filtro = {}

        if empresa_id:
            filtro["empresa_id"] = empresa_id

        return await self.repo.get_estatisticas_ocr(filtro)