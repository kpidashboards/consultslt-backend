"""
Serviço de Integração com SharePoint Online
Implementa leitura de recibos com apenas permissões de leitura
"""

import os
from typing import List, Optional, Dict
import requests
from fastapi import HTTPException, status
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SharePointService:
    """Serviço para leitura de recibos no SharePoint"""
    
    def __init__(self, access_token: str):
        """
        Inicializa serviço com access token do usuário
        
        Args:
            access_token: Access token do Entra ID com permissões SharePoint
        """
        self.access_token = access_token
        self.site_url = os.getenv("SHAREPOINT_SITE_URL")
        self.library_name = os.getenv("SHAREPOINT_LIBRARY_NAME", "Recibos 2024")
        self.folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "/Recibos por Empresa")
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Validar configuração
        if not self.site_url:
            raise ValueError("SHAREPOINT_SITE_URL não configurada")
        
        logger.info(f"SharePointService inicializado para site {self.site_url}")
    
    def listar_recibos(self, empresa_id: Optional[str] = None, 
                       limite: int = 100) -> List[Dict]:
        """
        Lista recibos disponíveis no SharePoint
        
        Args:
            empresa_id: ID da empresa para filtrar (opcional)
            limite: Número máximo de recibos a retornar
            
        Returns:
            Lista de recibos com metadados
        """
        try:
            # Construir URL da API do SharePoint
            # Usar Microsoft Graph para acessar SharePoint
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            # Listar arquivos na pasta
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{self.folder_path}:/children"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao listar recibos: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao listar recibos do SharePoint"
                )
            
            items = response.json().get("value", [])
            
            # Filtrar apenas PDFs e aplicar limite
            recibos = []
            for item in items:
                if item.get("name", "").lower().endswith(".pdf"):
                    # Filtrar por empresa se especificado
                    if empresa_id and not item.get("name", "").startswith(empresa_id):
                        continue
                    
                    recibos.append({
                        "id": item.get("id"),
                        "nome": item.get("name"),
                        "tamanho": item.get("size"),
                        "criado": item.get("createdDateTime"),
                        "modificado": item.get("lastModifiedDateTime"),
                        "url": item.get("webUrl"),
                        "download_url": item.get("@microsoft.graph.downloadUrl")
                    })
                    
                    if len(recibos) >= limite:
                        break
            
            logger.info(f"Listados {len(recibos)} recibos do SharePoint")
            return recibos
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao listar recibos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com SharePoint"
            )
        except Exception as e:
            logger.error(f"Erro ao listar recibos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao listar recibos"
            )
    
    def baixar_recibo(self, nome_arquivo: str) -> bytes:
        """
        Baixa conteúdo de um recibo do SharePoint
        
        Args:
            nome_arquivo: Nome do arquivo a baixar
            
        Returns:
            Conteúdo do arquivo em bytes
        """
        try:
            # Obter URL de download do arquivo
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{self.folder_path}/{nome_arquivo}:/content"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Erro ao baixar recibo: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recibo não encontrado"
                )
            
            logger.info(f"Recibo {nome_arquivo} baixado com sucesso")
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao baixar recibo: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com SharePoint"
            )
        except Exception as e:
            logger.error(f"Erro ao baixar recibo: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao baixar recibo"
            )
    
    def obter_metadados_recibo(self, nome_arquivo: str) -> Dict:
        """
        Obtém metadados de um recibo
        
        Args:
            nome_arquivo: Nome do arquivo
            
        Returns:
            Dicionário com metadados do arquivo
        """
        try:
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{self.folder_path}/{nome_arquivo}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter metadados: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Arquivo não encontrado"
                )
            
            file_data = response.json()
            
            return {
                "id": file_data.get("id"),
                "nome": file_data.get("name"),
                "tamanho": file_data.get("size"),
                "criado": file_data.get("createdDateTime"),
                "modificado": file_data.get("lastModifiedDateTime"),
                "url": file_data.get("webUrl"),
                "criado_por": file_data.get("createdBy", {}).get("user", {}).get("displayName"),
                "modificado_por": file_data.get("lastModifiedBy", {}).get("user", {}).get("displayName")
            }
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter metadados: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com SharePoint"
            )
        except Exception as e:
            logger.error(f"Erro ao obter metadados: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao obter metadados"
            )
    
    def _get_site_id(self) -> str:
        """
        Obtém ID do site do SharePoint
        
        Returns:
            ID do site
        """
        try:
            # Extrair hostname e path da URL
            # Exemplo: https://sltconsult.sharepoint.com/sites/RecibosF iscais
            parts = self.site_url.replace("https://", "").replace("http://", "").split("/")
            hostname = parts[0]  # sltconsult.sharepoint.com
            site_path = "/".join(parts[1:])  # sites/RecibosF iscais
            
            url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/{site_path}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter site ID: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao obter site ID"
                )
            
            site_id = response.json().get("id")
            logger.info(f"Site ID obtido: {site_id}")
            return site_id
            
        except Exception as e:
            logger.error(f"Erro ao obter site ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao obter site ID"
            )
    
    def _get_drive_id(self, site_id: str) -> str:
        """
        Obtém ID da biblioteca de documentos (drive) do site
        
        Args:
            site_id: ID do site
            
        Returns:
            ID da biblioteca
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter drive ID: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao obter drive ID"
                )
            
            drives = response.json().get("value", [])
            
            # Procurar pela biblioteca com o nome especificado
            for drive in drives:
                if drive.get("name") == self.library_name or drive.get("name") == "Documentos":
                    drive_id = drive.get("id")
                    logger.info(f"Drive ID obtido: {drive_id}")
                    return drive_id
            
            # Se não encontrar, usar a primeira biblioteca
            if drives:
                drive_id = drives[0].get("id")
                logger.info(f"Drive ID obtido (padrão): {drive_id}")
                return drive_id
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nenhuma biblioteca encontrada"
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter drive ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao obter drive ID"
            )
    
    def listar_empresas(self) -> List[str]:
        """
        Lista empresas (prefixos de pasta) disponíveis no SharePoint
        
        Returns:
            Lista de IDs de empresas
        """
        try:
            site_id = self._get_site_id()
            drive_id = self._get_drive_id(site_id)
            
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{self.folder_path}:/children"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao listar empresas: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao listar empresas"
                )
            
            items = response.json().get("value", [])
            
            # Extrair prefixos de empresas dos nomes de arquivos
            empresas = set()
            for item in items:
                nome = item.get("name", "")
                if nome.endswith(".pdf"):
                    # Assumir que o prefixo é o CNPJ ou ID da empresa
                    # Exemplo: 12345678000100_recibo.pdf -> 12345678000100
                    prefixo = nome.split("_")[0]
                    if prefixo:
                        empresas.add(prefixo)
            
            logger.info(f"Listadas {len(empresas)} empresas")
            return sorted(list(empresas))
            
        except Exception as e:
            logger.error(f"Erro ao listar empresas: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao listar empresas"
            )
