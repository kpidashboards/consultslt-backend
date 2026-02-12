from fastapi import APIRouter

router = APIRouter(prefix="/sharepoint", tags=["SharePoint"])

# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""
Endpoints para integração SharePoint
Permite controle manual e monitoramento da integração
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sharepoint", tags=["SharePoint"])


class ListFilesRequest(BaseModel):
    """Request para listar arquivos"""
    folder_path: str = "/"
    recursive: bool = False
    extensions: Optional[List[str]] = None


class FileInfo(BaseModel):
    """Informações de arquivo do SharePoint"""
    id: str
    name: str
    path: str
    size: int
    content_type: str
    created_at: datetime
    modified_at: datetime


@router.get("/status")
async def get_sharepoint_status():
    """
    Retorna status da integração SharePoint
    """
    from clients.sharepoint_client import SharePointClient
    
    
    if not client.is_configured:
        return {
            "configured": False,
            "message": "SharePoint não configurado. Configure AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET e SHAREPOINT_SITE_URL."
        }
    
    async with client:
        status = await client.check_connectivity()
    
    return status


@router.post("/list-files", response_model=List[FileInfo])
async def list_sharepoint_files(request: ListFilesRequest):
    """
    Lista arquivos em uma pasta do SharePoint
    
    - **folder_path**: Caminho da pasta (ex: /XMLs/2024)
    - **recursive**: Se deve incluir subpastas
    - **extensions**: Filtrar por extensões (ex: [".pdf", ".xml"])
    """
    from clients.sharepoint_client import SharePointClient, SharePointError
    from clients.azure_auth_client import AuthenticationError
    
    
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="SharePoint não configurado"
        )
    
    try:
        async with client:
            files = await client.list_files(
                folder_path=request.folder_path,
                recursive=request.recursive,
                filter_extensions=request.extensions
            )
        
        return [
            FileInfo(
                id=f.id,
                name=f.name,
                path=f.path,
                size=f.size,
                content_type=f.content_type,
                created_at=f.created_at,
                modified_at=f.modified_at
            )
            for f in files
        ]
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except SharePointError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/folders")
async def list_root_folders():
    """
    Lista pastas na raiz da biblioteca de documentos
    """
    from clients.sharepoint_client import SharePointClient, SharePointError
    
    
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="SharePoint não configurado"
        )
    
    try:
        async with client:
            drive_id = await client.get_drive_id()
            response = await client._make_request(
                "GET",
                f"/drives/{drive_id}/root/children"
            )
            
            data = response.json()
            folders = [
                {
                    "name": item["name"],
                    "id": item["id"],
                    "item_count": item.get("folder", {}).get("childCount", 0),
                    "web_url": item.get("webUrl")
                }
                for item in data.get("value", [])
                if "folder" in item
            ]
            
            return folders
            
    except SharePointError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/robots/ingestion/status")
async def get_ingestion_robot_status():
    """
    Retorna status do robô de ingestão
    """
    import os
    
    # Conectar ao MongoDB
    db_name = os.environ.get("DB_NAME", "sltdctfweb")
    
    
    from robots.ingestion_robot import DocumentIngestionRobot
    robot = DocumentIngestionRobot(db)
    
    status = await robot.get_status()
    client.close()
    
    return status


@router.post("/robots/ingestion/run")
async def run_ingestion_once(background_tasks: BackgroundTasks):
    """
    Executa o robô de ingestão uma vez (manualmente)
    """
    from robots.ingestion_robot import DocumentIngestionRobot
    import os
    
    db_name = os.environ.get("DB_NAME", "sltdctfweb")
    
    async def run_robot():
        
        robot = DocumentIngestionRobot(db)
        result = await robot.run_once()
        
        client.close()
        return result
    
    background_tasks.add_task(run_robot)
    
    return {
        "status": "started",
        "message": "Robô de ingestão iniciado em background"
    }
# export explícito do router
sharepoint_router = router

