"""
Endpoints para controle de Robôs
Gerencia execução e monitoramento dos robôs de automação
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from robots.sharepoint_ingestion_robot import (
    SharePointIngestionRobot,
    get_robot,
    start_ingestion_scheduler,
    stop_ingestion_scheduler
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/robots", tags=["Robôs"])


def get_db():
    """Dependência para obter conexão com MongoDB"""
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "sltdctfweb")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


@router.get("/ingestion/status")
async def get_ingestion_status(db=Depends(get_db)):
    """
    Retorna status do robô de ingestão SharePoint
    """
    robot = get_robot(db)
    return await robot.get_status()


@router.post("/ingestion/start")
async def start_ingestion_scheduler_endpoint(
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Inicia o scheduler de ingestão automática
    """
    robot = get_robot(db)
    
    if robot._scheduler and robot._scheduler.running:
        return {
            "status": "already_running",
            "message": "Scheduler já está em execução"
        }
    
    robot.start_scheduler()
    
    return {
        "status": "started",
        "message": f"Scheduler iniciado. Ingestão a cada {robot.config.interval_minutes} minutos"
    }


@router.post("/ingestion/stop")
async def stop_ingestion_scheduler_endpoint(db=Depends(get_db)):
    """
    Para o scheduler de ingestão
    """
    robot = get_robot(db)
    robot.stop_scheduler()
    
    return {
        "status": "stopped",
        "message": "Scheduler parado"
    }


@router.post("/ingestion/run-now")
async def run_ingestion_now(
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Executa o robô de ingestão imediatamente (manual)
    """
    robot = get_robot(db)
    
    if robot.is_running:
        return {
            "status": "already_running",
            "message": "Já existe uma execução em andamento"
        }
    
    # Executar em background
    background_tasks.add_task(robot.run_ingestion_job)
    
    return {
        "status": "started",
        "message": "Job de ingestão iniciado em background"
    }


@router.get("/ingestion/history")
async def get_ingestion_history(
    limit: int = 20,
    db=Depends(get_db)
):
    """
    Retorna histórico de execuções do robô
    """
    cursor = db.ingestion_jobs.find(
        {},
        {"_id": 0}
    ).sort("finished_at", -1).limit(limit)
    
    jobs = await cursor.to_list(length=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/ingestion/files")
async def get_processed_files(
    status: Optional[str] = None,
    limit: int = 50,
    db=Depends(get_db)
):
    """
    Lista arquivos processados do SharePoint
    """
    filtro = {}
    if status == "processed":
        filtro["processed"] = True
    elif status == "pending":
        filtro["processed"] = False
    
    cursor = db.sharepoint_files.find(
        filtro,
        {"_id": 0}
    ).sort("processed_at", -1).limit(limit)
    
    files = await cursor.to_list(length=limit)
    return {"files": files, "total": len(files)}

robots_router = router
