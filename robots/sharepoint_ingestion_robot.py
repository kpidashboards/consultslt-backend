"""
Robô de Ingestão do SharePoint com Agendamento
Executa periodicamente para buscar novos documentos do SharePoint

Funcionalidades:
- Lista arquivos em pastas configuradas do SharePoint
- Baixa novos PDFs para processamento
- Invoca parser de documentos fiscais
- Move arquivos processados para pasta de destino
- Logs e auditoria completos
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import hashlib

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from clients.sharepoint_client import SharePointClient, SharePointFile, SharePointError
from clients.azure_auth_client import AzureAuthClient, AuthenticationError
from services.documento_service import DocumentoService

logger = logging.getLogger(__name__)


@dataclass
class SharePointIngestionConfig:
    """Configuração do robô de ingestão SharePoint"""
    
    # Pastas de origem no SharePoint (a serem monitoradas)
    source_folders: List[str] = field(default_factory=lambda: [
        "Escrita Fiscal/Pendentes",
        "Escrita Fiscal/DCTFWeb",
        "Escrita Fiscal/DAS",
        "Documentos Fiscais/Novos"
    ])
    
    # Pasta de destino para arquivos processados
    processed_folder: str = "Escrita Fiscal/Processados"
    
    # Pasta para arquivos com erro
    error_folder: str = "Escrita Fiscal/Erros"
    
    # Extensões aceitas
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".pdf", ".xml"
    ])
    
    # Intervalo de execução em minutos
    interval_minutes: int = 60
    
    # Máximo de arquivos por execução
    batch_size: int = 50
    
    # Diretório local temporário
    temp_dir: Path = field(default_factory=lambda: Path("/data/uploads/temp"))
    
    # Processar apenas arquivos dos últimos N dias
    lookback_days: int = 30


@dataclass
class IngestionJobResult:
    """Resultado de uma execução do job de ingestão"""
    job_id: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    files_found: int = 0
    files_downloaded: int = 0
    files_processed: int = 0
    files_moved: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.files_failed == 0


class SharePointIngestionRobot:
    """
    Robô de ingestão automática do SharePoint
    
    Fluxo de execução:
    1. Autentica no Azure AD (OAuth2 Client Credentials)
    2. Lista arquivos nas pastas de origem do SharePoint
    3. Filtra arquivos novos (não processados anteriormente)
    4. Baixa arquivos para processamento local
    5. Processa PDFs (extração de dados)
    6. Cria/atualiza obrigações fiscais
    7. Move arquivos para pasta de processados
    8. Registra logs e métricas
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        sharepoint_client: SharePointClient = None,
        config: SharePointIngestionConfig = None
    ):
        self.db = db
        self.sharepoint = sharepoint_client or SharePointClient()
        self.config = config or SharePointIngestionConfig()
        self.documento_service = DocumentoService(db)
        
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self._current_job: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def start_scheduler(self):
        """
        Inicia o agendador para execução periódica
        """
        if self._scheduler and self._scheduler.running:
            logger.warning("Scheduler já está em execução")
            return
        
        self._scheduler = AsyncIOScheduler()
        
        # Adicionar job de ingestão
        self._scheduler.add_job(
            self.run_ingestion_job,
            IntervalTrigger(minutes=self.config.interval_minutes),
            id="sharepoint_ingestion",
            name="SharePoint Document Ingestion",
            replace_existing=True
        )
        
        # Adicionar job de atualização de status de obrigações (diário)
        self._scheduler.add_job(
            self._update_overdue_obligations,
            IntervalTrigger(hours=24),
            id="update_overdue",
            name="Update Overdue Obligations",
            replace_existing=True
        )
        
        self._scheduler.start()
        logger.info(
            f"Scheduler iniciado. Ingestão a cada {self.config.interval_minutes} minutos"
        )
    
    def stop_scheduler(self):
        """Para o agendador"""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Scheduler parado")
    
    async def run_ingestion_job(self) -> IngestionJobResult:
        """
        Executa um job de ingestão completo
        """
        import uuid
        
        job_id = str(uuid.uuid4())[:8]
        started_at = datetime.utcnow()
        
        logger.info(f"="*60)
        logger.info(f"Iniciando job de ingestão SharePoint: {job_id}")
        logger.info(f"="*60)
        
        result = IngestionJobResult(
            job_id=job_id,
            started_at=started_at,
            finished_at=started_at,
            duration_seconds=0
        )
        
        self._running = True
        self._current_job = job_id
        
        try:
            # Verificar se SharePoint está configurado
            if not self.sharepoint.is_configured:
                logger.warning("SharePoint não configurado. Pulando ingestão.")
                result.errors.append({
                    "type": "configuration",
                    "message": "SharePoint não configurado"
                })
                return result
            
            # Garantir diretório temp existe
            self.config.temp_dir.mkdir(parents=True, exist_ok=True)
            
            async with self.sharepoint:
                # Processar cada pasta de origem
                for folder in self.config.source_folders:
                    try:
                        folder_result = await self._process_folder(folder)
                        
                        result.files_found += folder_result["found"]
                        result.files_downloaded += folder_result["downloaded"]
                        result.files_processed += folder_result["processed"]
                        result.files_moved += folder_result["moved"]
                        result.files_skipped += folder_result["skipped"]
                        result.files_failed += folder_result["failed"]
                        result.errors.extend(folder_result["errors"])
                        
                    except SharePointError as e:
                        if e.status_code == 404:
                            logger.info(f"Pasta não encontrada: {folder}")
                        else:
                            logger.error(f"Erro ao processar pasta {folder}: {e}")
                            result.errors.append({
                                "folder": folder,
                                "error": str(e)
                            })
                    except Exception as e:
                        logger.error(f"Erro inesperado em {folder}: {e}")
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
        
        except Exception as e:
            logger.error(f"Erro geral no job: {e}")
            result.errors.append({
                "type": "general",
                "error": str(e)
            })
        
        finally:
            self._running = False
            self._current_job = None
        
        result.finished_at = datetime.utcnow()
        result.duration_seconds = (result.finished_at - result.started_at).total_seconds()
        
        # Salvar resultado no banco
        await self._save_job_result(result)
        
        logger.info(f"="*60)
        logger.info(
            f"Job {job_id} concluído em {result.duration_seconds:.1f}s | "
            f"Encontrados: {result.files_found} | "
            f"Processados: {result.files_processed} | "
            f"Falhas: {result.files_failed}"
        )
        logger.info(f"="*60)
        
        return result
    
    async def _process_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Processa uma pasta do SharePoint
        """
        logger.info(f"Processando pasta: {folder_path}")
        
        result = {
            "found": 0,
            "downloaded": 0,
            "processed": 0,
            "moved": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        # Listar arquivos
        files = await self.sharepoint.list_files(
            folder_path=folder_path,
            recursive=False,
            filter_extensions=self.config.allowed_extensions
        )
        
        result["found"] = len(files)
        logger.info(f"Encontrados {len(files)} arquivos em {folder_path}")
        
        # Filtrar por data
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.lookback_days)
        files_to_process = [
            f for f in files
            if f.modified_at.replace(tzinfo=None) >= cutoff_date
        ]
        
        # Processar em lotes
        for file in files_to_process[:self.config.batch_size]:
            try:
                status = await self._process_file(file, folder_path)
                
                if status == "downloaded":
                    result["downloaded"] += 1
                if status == "processed":
                    result["processed"] += 1
                if status == "moved":
                    result["moved"] += 1
                if status == "skipped":
                    result["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar {file.name}: {e}")
                result["failed"] += 1
                result["errors"].append({
                    "file": file.name,
                    "error": str(e)
                })
        
        return result
    
    async def _process_file(self, file: SharePointFile, source_folder: str) -> str:
        """
        Processa um arquivo individual
        
        Returns:
            Status: "processed", "skipped", "moved"
        """
        # Verificar se já foi processado (por ID do SharePoint)
        existing = await self.db.sharepoint_files.find_one({
            "sharepoint_id": file.id
        })
        
        if existing and existing.get("processed"):
            logger.debug(f"Arquivo já processado: {file.name}")
            return "skipped"
        
        logger.info(f"Baixando: {file.name}")
        
        # Baixar arquivo
        local_path = self.config.temp_dir / file.name
        await self.sharepoint.download_file(file, local_path)
        
        # Ler conteúdo
        with open(local_path, 'rb') as f:
            content = f.read()
        
        # Fazer upload via serviço de documentos (que irá processar)
        try:
            documento = await self.documento_service.upload_documento(
                filename=file.name,
                content=content,
                content_type=file.content_type or "application/pdf",
                processar_automaticamente=True
            )
            
            logger.info(
                f"Documento processado: {file.name} -> ID: {documento.id}, "
                f"Status: {documento.status}, Confiança: {documento.confianca_extracao}%"
            )
            
            # Registrar arquivo processado
            await self.db.sharepoint_files.update_one(
                {"sharepoint_id": file.id},
                {"$set": {
                    "sharepoint_id": file.id,
                    "name": file.name,
                    "path": file.path,
                    "source_folder": source_folder,
                    "documento_id": documento.id,
                    "processed": True,
                    "processed_at": datetime.utcnow(),
                    "status": documento.status
                }},
                upsert=True
            )
            
            # Limpar arquivo temp
            local_path.unlink(missing_ok=True)
            
            return "processed"
            
        except Exception as e:
            logger.error(f"Erro ao processar {file.name}: {e}")
            
            # Registrar erro
            await self.db.sharepoint_files.update_one(
                {"sharepoint_id": file.id},
                {"$set": {
                    "sharepoint_id": file.id,
                    "name": file.name,
                    "processed": False,
                    "error": str(e),
                    "last_attempt": datetime.utcnow()
                }},
                upsert=True
            )
            
            raise
    
    async def _update_overdue_obligations(self):
        """
        Atualiza status de obrigações vencidas
        """
        from services.obrigacao_service import ObrigacaoService
        
        service = ObrigacaoService(self.db)
        count = await service.atualizar_status_atrasados()
        logger.info(f"Obrigações atualizadas para atrasada: {count}")
    
    async def _save_job_result(self, result: IngestionJobResult):
        """
        Salva resultado do job no banco para auditoria
        """
        await self.db.ingestion_jobs.insert_one({
            "job_id": result.job_id,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_seconds": result.duration_seconds,
            "files_found": result.files_found,
            "files_downloaded": result.files_downloaded,
            "files_processed": result.files_processed,
            "files_moved": result.files_moved,
            "files_skipped": result.files_skipped,
            "files_failed": result.files_failed,
            "success": result.success,
            "errors": result.errors[:20]  # Limitar erros salvos
        })
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do robô
        """
        # Última execução
        last_job = await self.db.ingestion_jobs.find_one(
            {},
            sort=[("finished_at", -1)]
        )
        
        # Estatísticas
        total_processed = await self.db.sharepoint_files.count_documents({"processed": True})
        total_pending = await self.db.sharepoint_files.count_documents({"processed": False})
        
        # Próxima execução
        next_run = None
        if self._scheduler and self._scheduler.running:
            job = self._scheduler.get_job("sharepoint_ingestion")
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        
        return {
            "running": self._running,
            "current_job": self._current_job,
            "scheduler_active": bool(self._scheduler and self._scheduler.running),
            "interval_minutes": self.config.interval_minutes,
            "next_run": next_run,
            "last_job": {
                "job_id": last_job["job_id"] if last_job else None,
                "finished_at": last_job["finished_at"].isoformat() if last_job else None,
                "success": last_job["success"] if last_job else None,
                "files_processed": last_job.get("files_processed") if last_job else None
            } if last_job else None,
            "statistics": {
                "total_processed": total_processed,
                "total_pending": total_pending
            },
            "config": {
                "source_folders": self.config.source_folders,
                "batch_size": self.config.batch_size
            },
            "sharepoint_configured": self.sharepoint.is_configured
        }


# Instância global do robô (para gerenciamento)
_robot_instance: Optional[SharePointIngestionRobot] = None


def get_robot(db: AsyncIOMotorDatabase) -> SharePointIngestionRobot:
    """Obtém instância do robô"""
    global _robot_instance
    if _robot_instance is None:
        _robot_instance = SharePointIngestionRobot(db)
    return _robot_instance


async def start_ingestion_scheduler(db: AsyncIOMotorDatabase):
    """Inicia o scheduler de ingestão"""
    robot = get_robot(db)
    robot.start_scheduler()
    return robot


async def stop_ingestion_scheduler():
    """Para o scheduler de ingestão"""
    global _robot_instance
    if _robot_instance:
        _robot_instance.stop_scheduler()
