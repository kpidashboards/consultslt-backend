"""
Serviço de Documentos
Gerencia upload, armazenamento e processamento de documentos fiscais
"""

import os
import uuid
import time
import hashlib
import logging
import aiofiles

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..schemas.documento import (
    TipoDocumento,
    StatusDocumento,
    DocumentoResponse,
    DocumentoProcessamentoResult,
)

from ..repositories.documentos_repository import DocumentosRepository
from ..utils.parsers.dctfweb_parser import DCTFWebParser, PDFParsingError
from ..utils.parsers.das_parser import DASParser

logger = logging.getLogger(__name__)


class DocumentoService:
    """
    Serviço para gerenciamento de documentos fiscais
    """

    UPLOAD_DIR = Path(os.getenv("LOCAL_STORAGE_PATH", "./data/uploads"))
    ALLOWED_EXTENSIONS = {".pdf", ".xml", ".xlsx", ".xls"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = DocumentosRepository(db)
        self.dctfweb_parser = DCTFWebParser()
        self.das_parser = DASParser()

        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # ======================================================
    # UPLOAD
    # ======================================================

    async def upload_documento(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        empresa_id: Optional[str] = None,
        tipo: TipoDocumento = TipoDocumento.OUTRO,
        processar_automaticamente: bool = True,
    ) -> DocumentoResponse:

        self._validate_file(filename, content)

        now = datetime.utcnow()
        documento_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()

        subdir = self.UPLOAD_DIR / str(now.year) / f"{now.month:02d}"
        subdir.mkdir(parents=True, exist_ok=True)

        file_path = subdir / f"{documento_id}{ext}"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        file_hash = hashlib.md5(content).hexdigest()

        documento = {
            "id": documento_id,
            "empresa_id": empresa_id,
            "nome": filename,
            "tipo": tipo.value,
            "status": StatusDocumento.PENDENTE.value,
            "caminho_arquivo": str(file_path),
            "content_type": content_type,
            "tamanho_bytes": len(content),
            "file_hash": file_hash,
            "created_at": now,
            "updated_at": None,
            "erro_processamento": None,
        }

        await self.repo.create(documento)

        if processar_automaticamente and ext == ".pdf":
            try:
                await self.processar_documento(documento_id)
            except Exception as e:
                logger.error(f"Erro no processamento automático: {e}")

        doc = await self.repo.get_by_id(documento_id)
        return DocumentoResponse(**doc)

    # ======================================================
    # PROCESSAMENTO
    # ======================================================

    async def processar_documento(
        self,
        documento_id: str,
    ) -> DocumentoProcessamentoResult:

        start = time.time()
        result = DocumentoProcessamentoResult(
            documento_id=documento_id,
            sucesso=False,
            erros=[],
        )

        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            result.erros.append("Documento não encontrado")
            return result

        try:
            await self.repo.update(
                documento_id,
                {"status": StatusDocumento.PROCESSANDO.value},
            )

            async with aiofiles.open(documento["caminho_arquivo"], "rb") as f:
                content = await f.read()

            tipo, dados = await self._parse_pdf(content)

            update_data = {
                "status": StatusDocumento.PROCESSADO.value,
                "tipo": tipo.value,
                "dados_extraidos": dados,
                "processado_em": datetime.utcnow(),
            }

            await self.repo.update(documento_id, update_data)

            result.sucesso = True

        except PDFParsingError as e:
            logger.error(e)
            await self.repo.update(
                documento_id,
                {
                    "status": StatusDocumento.ERRO.value,
                    "erro_processamento": str(e),
                },
            )
            result.erros.append(str(e))

        except Exception as e:
            logger.exception(e)
            await self.repo.update(
                documento_id,
                {
                    "status": StatusDocumento.ERRO.value,
                    "erro_processamento": str(e),
                },
            )
            result.erros.append("Erro inesperado no processamento")

        result.tempo_processamento_ms = int((time.time() - start) * 1000)
        return result

    # ======================================================
    # AUXILIARES
    # ======================================================

    async def _parse_pdf(
        self, content: bytes
    ) -> Tuple[TipoDocumento, Dict[str, Any]]:

        try:
            dctf = self.dctfweb_parser.parse_bytes(content)
            if dctf.extraction_confidence >= 50:
                return TipoDocumento.DCTFWEB, dctf.to_dict()
        except Exception:
            pass

        try:
            das = self.das_parser.parse_bytes(content)
            if das.extraction_confidence >= 50:
                return TipoDocumento.DAS, das.to_dict()
        except Exception:
            pass

        return TipoDocumento.OUTRO, {}

    def _validate_file(self, filename: str, content: bytes):
        ext = Path(filename).suffix.lower()

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extensão não permitida: {ext}")

        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError("Arquivo excede o tamanho máximo permitido")

    # ======================================================
    # CRUD
    # ======================================================

    async def listar_documentos(
        self,
        empresa_id: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> Dict[str, Any]:

        filtro = {}
        if empresa_id:
            filtro["empresa_id"] = empresa_id

        total = await self.repo.count(filtro)
        documentos = await self.repo.listar(
            filtro=filtro,
            skip=(pagina - 1) * por_pagina,
            limit=por_pagina,
        )

        return {
            "documentos": documentos,
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
        }

    async def obter_documento(self, documento_id: str):
        return await self.repo.get_by_id(documento_id)

    async def deletar_documento(self, documento_id: str) -> bool:
        doc = await self.repo.get_by_id(documento_id)
        if not doc:
            return False

        try:
            Path(doc["caminho_arquivo"]).unlink(missing_ok=True)
        except Exception:
            pass

        await self.repo.delete(documento_id)
        return True
