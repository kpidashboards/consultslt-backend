"""
Cliente Microsoft Graph API para acesso ao SharePoint Online
Implementa operações de leitura de documentos

Restrições:
- Apenas OAuth2 Client Credentials (sem login interativo)
- Apenas Microsoft Graph API (sem scraping)
- Apenas conexões HTTPS de saída
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path
from urllib.parse import urlparse, quote

from .azure_auth_client import AzureAuthClient, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class SharePointFile:
    """Representa um arquivo no SharePoint"""
    id: str
    name: str
    path: str
    size: int
    created_at: datetime
    modified_at: datetime
    download_url: str
    content_type: str
    parent_folder: str
    etag: str
    web_url: str = ""


@dataclass
class SharePointFolder:
    """Representa uma pasta no SharePoint"""
    id: str
    name: str
    path: str
    item_count: int
    created_at: datetime
    modified_at: datetime


class SharePointError(Exception):
    """Exceção para erros do SharePoint"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class SharePointClient:
    """
    Cliente para interação com SharePoint Online via Microsoft Graph API
    
    Funcionalidades:
    - Listar arquivos de bibliotecas de documentos
    - Download de arquivos
    - Streaming de arquivos (sem salvar em disco)
    - Obter metadados de arquivos
    
    Requisitos:
    - App Registration com permissões Sites.Read.All e Files.Read.All
    - Admin Consent concedido
    """
    
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(
        self,
        auth_client: AzureAuthClient = None,
        site_url: str = None,
        drive_id: str = None
    ):
        """
        Inicializa o cliente SharePoint
        
        Args:
            auth_client: Cliente de autenticação Azure AD
            site_url: URL do site SharePoint (ou via SHAREPOINT_SITE_URL)
            drive_id: ID do drive/biblioteca (ou via SHAREPOINT_DRIVE_ID)
        """
        self.auth_client = auth_client or AzureAuthClient()
        self.site_url = site_url or os.environ.get("SHAREPOINT_SITE_URL")
        self.drive_id = drive_id or os.environ.get("SHAREPOINT_DRIVE_ID")
        
        self._site_id: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Verifica se o cliente está configurado"""
        return self.auth_client.is_configured and bool(self.site_url)
    
    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=120.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()
    
    async def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        token = await self.auth_client.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Executa requisição HTTP com retry e tratamento de erros
        
        Args:
            method: Método HTTP (GET, POST, etc)
            endpoint: Endpoint da API (sem base URL)
            **kwargs: Argumentos adicionais para httpx
            
        Returns:
            Resposta HTTP
            
        Raises:
            SharePointError: Para erros do Graph API
            AuthenticationError: Para erros de autenticação
        """
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        
        # URL pode ser completa (pagination) ou relativa
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.GRAPH_BASE_URL}{endpoint}"
        
        headers = await self._get_headers()
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await self._http_client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )
                
                # Rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited pelo Graph API. Aguardando {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                # Erro de autenticação (401)
                if response.status_code == 401:
                    logger.warning("Token expirado ou inválido. Renovando...")
                    self.auth_client._token = None  # Forçar renovação
                    headers = await self._get_headers()
                    continue
                
                # Erro de permissão (403)
                if response.status_code == 403:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", "Access denied")
                    raise SharePointError(
                        f"Sem permissão para acessar o recurso: {error_msg}. "
                        "Verifique as permissões do App Registration no Azure AD.",
                        status_code=403,
                        error_code="access_denied"
                    )
                
                # Não encontrado (404)
                if response.status_code == 404:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", "Resource not found")
                    raise SharePointError(
                        f"Recurso não encontrado: {error_msg}",
                        status_code=404,
                        error_code="not_found"
                    )
                
                # Outros erros
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise SharePointError(
                        f"Erro do Graph API: {error_msg}",
                        status_code=response.status_code
                    )
                
                return response
                
            except httpx.TimeoutException:
                logger.warning(f"Timeout na requisição (tentativa {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise SharePointError("Timeout ao acessar SharePoint")
            
            except httpx.ConnectError as e:
                logger.error(f"Erro de conexão: {e}")
                raise SharePointError(
                    "Não foi possível conectar ao SharePoint. "
                    "Verifique conectividade com graph.microsoft.com:443"
                )
        
        raise SharePointError(f"Falha após {max_retries} tentativas")
    
    async def get_site_id(self) -> str:
        """
        Obtém o Site ID do SharePoint a partir da URL
        
        Returns:
            Site ID no formato "tenant.sharepoint.com,guid,guid"
        """
        if self._site_id:
            return self._site_id
        
        if not self.site_url:
            raise SharePointError(
                "URL do site SharePoint não configurada. "
                "Configure SHAREPOINT_SITE_URL."
            )
        
        # Extrair host e path da URL
        parsed = urlparse(self.site_url)
        hostname = parsed.netloc
        site_path = parsed.path.rstrip('/')
        
        endpoint = f"/sites/{hostname}:{site_path}"
        response = await self._make_request("GET", endpoint)
        data = response.json()
        
        self._site_id = data["id"]
        logger.info(f"Site ID obtido: {self._site_id}")
        
        return self._site_id
    
    async def get_drive_id(self, drive_name: str = "Documentos") -> str:
        """
        Obtém o Drive ID de uma biblioteca de documentos
        
        Args:
            drive_name: Nome da biblioteca (parcial, case-insensitive)
            
        Returns:
            Drive ID
        """
        if self.drive_id:
            return self.drive_id
        
        site_id = await self.get_site_id()
        endpoint = f"/sites/{site_id}/drives"
        
        response = await self._make_request("GET", endpoint)
        drives = response.json().get("value", [])
        
        # Procurar drive por nome
        for drive in drives:
            if drive_name.lower() in drive["name"].lower():
                self.drive_id = drive["id"]
                logger.info(f"Drive ID obtido: {self.drive_id} ({drive['name']})")
                return self.drive_id
        
        # Se não encontrar por nome, usar o primeiro (geralmente "Documents")
        if drives:
            self.drive_id = drives[0]["id"]
            logger.info(f"Usando drive padrão: {self.drive_id} ({drives[0]['name']})")
            return self.drive_id
        
        raise SharePointError(f"Nenhuma biblioteca de documentos encontrada no site")
    
    async def list_files(
        self,
        folder_path: str = "/",
        recursive: bool = False,
        filter_extensions: List[str] = None
    ) -> List[SharePointFile]:
        """
        Lista arquivos em uma pasta do SharePoint
        
        Args:
            folder_path: Caminho da pasta (ex: "/XMLs/2024")
            recursive: Se deve incluir subpastas
            filter_extensions: Lista de extensões para filtrar (ex: [".pdf", ".xml"])
            
        Returns:
            Lista de SharePointFile
        """
        drive_id = await self.get_drive_id()
        
        # Normalizar path
        path = folder_path.strip('/') if folder_path != "/" else ""
        
        if path:
            endpoint = f"/drives/{drive_id}/root:/{quote(path)}:/children"
        else:
            endpoint = f"/drives/{drive_id}/root/children"
        
        files = []
        
        # Pagination
        while endpoint:
            response = await self._make_request("GET", endpoint)
            data = response.json()
            
            for item in data.get("value", []):
                # Pasta
                if "folder" in item:
                    if recursive:
                        subfolder_path = f"{folder_path}/{item['name']}".replace("//", "/")
                        subfiles = await self.list_files(
                            subfolder_path,
                            recursive=True,
                            filter_extensions=filter_extensions
                        )
                        files.extend(subfiles)
                    continue
                
                # Filtrar por extensão
                if filter_extensions:
                    ext = Path(item["name"]).suffix.lower()
                    if ext not in [e.lower() for e in filter_extensions]:
                        continue
                
                # Criar objeto SharePointFile
                file = SharePointFile(
                    id=item["id"],
                    name=item["name"],
                    path=f"{folder_path}/{item['name']}".replace("//", "/"),
                    size=item.get("size", 0),
                    created_at=datetime.fromisoformat(
                        item["createdDateTime"].replace("Z", "+00:00")
                    ),
                    modified_at=datetime.fromisoformat(
                        item["lastModifiedDateTime"].replace("Z", "+00:00")
                    ),
                    download_url=item.get("@microsoft.graph.downloadUrl", ""),
                    content_type=item.get("file", {}).get("mimeType", ""),
                    parent_folder=folder_path,
                    etag=item.get("eTag", ""),
                    web_url=item.get("webUrl", "")
                )
                files.append(file)
            
            # Próxima página
            endpoint = data.get("@odata.nextLink")
        
        logger.info(f"Encontrados {len(files)} arquivos em {folder_path}")
        return files
    
    async def download_file(
        self,
        file: SharePointFile,
        destination: Path
    ) -> Path:
        """
        Faz download de um arquivo do SharePoint
        
        Args:
            file: Objeto SharePointFile
            destination: Caminho local de destino
        
        Returns:
            Path do arquivo baixado
        """
        drive_id = await self.get_drive_id()
        
        # Obter URL de download atualizada
        endpoint = f"/drives/{drive_id}/items/{file.id}"
        response = await self._make_request("GET", endpoint)
        data = response.json()
        
        download_url = data.get("@microsoft.graph.downloadUrl")
        if not download_url:
            raise SharePointError(f"URL de download não disponível para {file.name}")
        
        # Criar diretório de destino
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Download do arquivo (sem autenticação - URL pré-assinada)
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", download_url) as response:
                response.raise_for_status()
                
                with open(destination, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
        
        logger.info(f"Arquivo baixado: {destination} ({file.size} bytes)")
        return destination
    
    async def stream_file(
        self,
        file: SharePointFile
    ) -> AsyncIterator[bytes]:
        """
        Stream de um arquivo do SharePoint (sem salvar em disco)
        
        Args:
            file: Objeto SharePointFile
        
        Yields:
            Chunks do arquivo
        """
        drive_id = await self.get_drive_id()
        
        endpoint = f"/drives/{drive_id}/items/{file.id}"
        response = await self._make_request("GET", endpoint)
        data = response.json()
        
        download_url = data.get("@microsoft.graph.downloadUrl")
        if not download_url:
            raise SharePointError(f"URL de download não disponível para {file.name}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", download_url) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
    
    async def check_connectivity(self) -> Dict[str, Any]:
        """
        Verifica conectividade com SharePoint
        Útil para health checks
        
        Returns:
            Dict com status da conectividade
        """
        result = {
            "configured": self.is_configured,
            "status": "unknown",
            "site_id": None,
            "drive_id": None,
            "site_url": self.site_url,
            "error": None
        }
        
        if not self.is_configured:
            result["status"] = "not_configured"
            result["error"] = "SharePoint não configurado"
            return result
        
        try:
            result["site_id"] = await self.get_site_id()
            result["drive_id"] = await self.get_drive_id()
            result["status"] = "connected"
            
        except SharePointError as e:
            result["status"] = "error"
            result["error"] = str(e)
        except AuthenticationError as e:
            result["status"] = "auth_error"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
