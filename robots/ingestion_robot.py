"""
Robô de Ingestão de Documentos do SharePoint
Responsável por:
- Varrer bibliotecas do SharePoint
- Baixar documentos novos/modificados
- Registrar metadados no MongoDB
- Disparar processamento posterior

Restrições:
- Apenas Microsoft Graph API
- Sem scraping
- Idempotente (não reprocessa arquivos já baixados)
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import hashlib
from dataclasses import dataclass, field

from motor.motor_asyncio import AsyncIOMotorDatabase

from clients.sharepoint_client import SharePointClient, SharePointFile, SharePointError
from clients.azure_auth_client import AzureAuthClient, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class IngestionConfig:
    """Configuração do robô de ingestão"""
    # Pastas a monitorar no SharePoint
    source_folders: List[str] = field(default_factory=lambda: [
        "/XMLs",
        "/PDFs/DCTFWeb",
        "/PDFs/Recibos",
        "/PDFs/DAS",
        "/PDFs/Certidoes"
    ])
    
    # Extensões permitidas
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".pdf", ".xml", ".xlsx", ".xls"
    ])
    
    # Diretório local para download
    local_storage_path: Path = field(default_factory=lambda: Path("/data/uploads"))
    
    # Intervalo de verificação (segundos)
    check_interval: int = 300  # 5 minutos
    
    # Processar arquivos modificados nos últimos N dias
    lookback_days: int = 30
    
    # Máximo de arquivos por execução (evitar sobrecarga)
    batch_size: int = 100
    
    # Retry em caso de falha
    max_retries: int = 3


@dataclass
class IngestionResult:
    """Resultado de uma execução de ingestão"""
    started_at: datetime
    finished_at: datetime
    files_found: int
    files_downloaded: int
    files_skipped: int
    files_failed: int
    duration_seconds: float = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.files_failed == 0


class DocumentIngestionRobot:
    """
    Robô para ingestão automática de documentos do SharePoint
    
    Fluxo:
    1. Conectar ao SharePoint via Graph API
    2. Listar arquivos nas pastas configuradas
    3. Filtrar arquivos novos/modificados
    4. Baixar arquivos para disco local
    5. Registrar metadados no MongoDB
    6. Marcar para processamento posterior
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        sharepoint_client: SharePointClient = None,
        config: IngestionConfig = None
    ):
        """
        Inicializa o robô de ingestão
        
        Args:
            db: Conexão MongoDB
            sharepoint_client: Cliente SharePoint (ou cria novo)
            config: Configurações do robô
        """
        self.db = db
        self.sharepoint = sharepoint_client or SharePointClient()
        self.config = config or IngestionConfig()
        
        self._running = False
        self._last_run: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    async def start(self):
        """
        Inicia o robô em modo contínuo (background)
        """
        if self._running:
            logger.warning("Robô já está em execução")
            return
        
        self._running = True
        logger.info(f"Robô de ingestão iniciado (intervalo: {self.config.check_interval}s)")
        
        while self._running:
            try:
                result = await self.run_once()
                logger.info(
                    f"Ingestão concluída: {result.files_downloaded} baixados, "
                    f"{result.files_skipped} ignorados, {result.files_failed} falhas "
                    f"({result.duration_seconds:.1f}s)"
                )
            except Exception as e:
                logger.error(f"Erro na execução do robô: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def stop(self):
        """Para o robô"""
        self._running = False
        logger.info("Robô de ingestão parado")
    
    async def run_once(self) -> IngestionResult:
        """
        Executa uma única iteração de ingestão
        
        Returns:
            IngestionResult com estatísticas da execução
        """
        started_at = datetime.utcnow()
        
        result = IngestionResult(
            started_at=started_at,
            finished_at=started_at,
            files_found=0,
            files_downloaded=0,
            files_skipped=0,
            files_failed=0
        )
        
        # Verificar se SharePoint está configurado
        if not self.sharepoint.is_configured:
            logger.warning("SharePoint não configurado. Pulando ingestão.")
            result.finished_at = datetime.utcnow()
            result.duration_seconds = (result.finished_at - result.started_at).total_seconds()
            return result
        
        try:
            async with self.sharepoint:
                for folder in self.config.source_folders:
                    try:
                        folder_result = await self._process_folder(folder)
                        
                        result.files_found += folder_result["found"]
                        result.files_downloaded += folder_result["downloaded"]
                        result.files_skipped += folder_result["skipped"]
                        result.files_failed += folder_result["failed"]
                        result.errors.extend(folder_result["errors"])
                        
                    except SharePointError as e:
                        logger.error(f"Erro ao processar pasta {folder}: {e}")
                        result.errors.append({
                            "folder": folder,
                            "error": str(e),
                            "error_code": e.error_code
                        })
                    except Exception as e:
                        logger.error(f"Erro inesperado ao processar pasta {folder}: {e}")
                        result.errors.append({
                            "folder": folder,
                            "error": str(e)
                        })
        
        except AuthenticationError as e:
            logger.error(f"Erro de autenticação: {e}")
            result.errors.append({
                "type": "authentication",
                "error": str(e)
            })
        
        result.finished_at = datetime.utcnow()
        result.duration_seconds = (result.finished_at - result.started_at).total_seconds()
        self._last_run = result.finished_at
        
        # Registrar execução no banco
        await self._log_execution(result)
        
        return result
    
    async def _process_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Processa uma pasta específica do SharePoint
        
        Args:
            folder_path: Caminho da pasta no SharePoint
            
        Returns:
            Dict com estatísticas de processamento
        """
        logger.info(f"Processando pasta: {folder_path}")
        
        result = {
            "found": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        # Listar arquivos
        try:
            files = await self.sharepoint.list_files(
                folder_path=folder_path,
                recursive=True,
                filter_extensions=self.config.allowed_extensions
            )
        except SharePointError as e:
            if e.status_code == 404:
                logger.warning(f"Pasta não encontrada: {folder_path}")
                return result
            raise
        
        result["found"] = len(files)
        
        # Filtrar arquivos por data de modificação
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.lookback_days)
        files_to_process = [
            f for f in files
            if f.modified_at.replace(tzinfo=None) >= cutoff_date
        ]
        
        logger.info(f"Arquivos a processar: {len(files_to_process)}/{len(files)}")
        
        # Processar em lotes
        for file in files_to_process[:self.config.batch_size]:
            try:
                status = await self._process_file(file)
                
                if status == "downloaded":
                    result["downloaded"] += 1
                elif status == "skipped":
                    result["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar {file.name}: {e}")
                result["failed"] += 1
                result["errors"].append({
                    "file": file.name,
                    "path": file.path,
                    "error": str(e)
                })
        
        return result
    
    async def _process_file(self, file: SharePointFile) -> str:
        """
        Processa um arquivo individual
        
        Args:
            file: Arquivo do SharePoint
            
        Returns:
            Status: "downloaded", "skipped" ou "failed"
        """
        # Calcular hash do arquivo (baseado em etag + modified_at)
        # Isso garante idempotência - não reprocessa arquivo já baixado
        file_hash = hashlib.md5(
            f"{file.etag}:{file.modified_at.isoformat()}".encode()
        ).hexdigest()
        
        # Verificar se já foi processado
        existing = await self.db.documents.find_one({
            "sharepoint_id": file.id,
            "file_hash": file_hash
        })
        
        if existing:
            logger.debug(f"Arquivo já processado: {file.name}")
            return "skipped"
        
        # Determinar caminho local
        local_path = self.config.local_storage_path / file.path.lstrip('/')
        
        # Fazer download
        await self.sharepoint.download_file(file, local_path)
        
        # Registrar no MongoDB
        document_record = {
            "sharepoint_id": file.id,
            "file_hash": file_hash,
            "name": file.name,
            "path": file.path,
            "local_path": str(local_path),
            "size": file.size,
            "content_type": file.content_type,
            "created_at_sharepoint": file.created_at,
            "modified_at_sharepoint": file.modified_at,
            "downloaded_at": datetime.utcnow(),
            "status": "pending_classification",
            "metadata": {},
            "processing_history": [{
                "action": "downloaded",
                "timestamp": datetime.utcnow(),
                "details": {"source": "sharepoint", "robot": "ingestion"}
            }]
        }
        
        await self.db.documents.update_one(
            {"sharepoint_id": file.id},
            {"$set": document_record},
            upsert=True
        )
        
        logger.info(f"Documento baixado: {file.name}")
        return "downloaded"
    
    async def _log_execution(self, result: IngestionResult):
        """
        Registra execução no banco para auditoria
        
        Args:
            result: Resultado da execução
        """
        log_entry = {
            "robot": "ingestion",
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_seconds": result.duration_seconds,
            "files_found": result.files_found,
            "files_downloaded": result.files_downloaded,
            "files_skipped": result.files_skipped,
            "files_failed": result.files_failed,
            "success": result.success,
            "errors": result.errors[:10]  # Limitar erros salvos
        }
        
        await self.db.robot_executions.insert_one(log_entry)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do robô
        
        Returns:
            Dict com informações de status
        """
        # Última execução
        last_execution = await self.db.robot_executions.find_one(
            {"robot": "ingestion"},
            sort=[("finished_at", -1)]
        )
        
        # Estatísticas gerais
        total_docs = await self.db.documents.count_documents({})
        pending_docs = await self.db.documents.count_documents(
            {"status": "pending_classification"}
        )
        
        return {
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_execution": {
                "started_at": last_execution["started_at"].isoformat() if last_execution else None,
                "finished_at": last_execution["finished_at"].isoformat() if last_execution else None,
                "success": last_execution["success"] if last_execution else None,
                "files_downloaded": last_execution.get("files_downloaded") if last_execution else None
            } if last_execution else None,
            "statistics": {
                "total_documents": total_docs,
                "pending_classification": pending_docs
            },
            "config": {
                "source_folders": self.config.source_folders,
                "check_interval_seconds": self.config.check_interval,
                "batch_size": self.config.batch_size,
                "lookback_days": self.config.lookback_days
            },
            "sharepoint_configured": self.sharepoint.is_configured
        }
