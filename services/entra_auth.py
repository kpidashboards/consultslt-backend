"""
Serviço de Autenticação via Entra ID (Azure AD)
Implementa OAuth 2.0 com MSAL (Microsoft Authentication Library)
"""

import os
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import requests
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class EntraIDAuthService:
    """Serviço de autenticação via Entra ID (Azure AD)"""
    
    def __init__(self):
        """Inicializa serviço com credenciais do Entra ID"""
        self.client_id = os.getenv("ENTRA_ID_CLIENT_ID")
        self.client_secret = os.getenv("ENTRA_ID_CLIENT_SECRET")
        self.tenant_id = os.getenv("ENTRA_ID_TENANT_ID")
        self.authority = os.getenv("ENTRA_ID_AUTHORITY", 
                                   f"https://login.microsoftonline.com/{self.tenant_id}")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
        
        # Scopes necessários
        self.scopes = [
            "User.Read",
            "email",
            "profile",
            "Sites.Read.All",
            "Files.Read.All",
            "ListItem.Read.All"
        ]
        
        # Validar credenciais
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Credenciais do Entra ID não configuradas")
        
        logger.info(f"EntraIDAuthService inicializado para tenant {self.tenant_id}")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Gera URL de autorização para redirecionar usuário ao Entra ID
        
        Args:
            state: Token CSRF para segurança
            
        Returns:
            URL de autorização do Entra ID
        """
        try:
            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
                "response_mode": "query",
                "prompt": "select_account"
            }
            
            if state:
                params["state"] = state
            
            # Construir URL de autorização
            auth_url = f"{self.authority}/oauth2/v2.0/authorize?"
            auth_url += "&".join([f"{k}={v}" for k, v in params.items()])
            
            logger.info("URL de autorização gerada com sucesso")
            return auth_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao gerar URL de autorização"
            )
    
    def get_token_from_code(self, code: str) -> Dict:
        """
        Troca authorization code por access token
        
        Args:
            code: Authorization code retornado pelo Entra ID
            
        Returns:
            Dicionário com access_token, refresh_token, expires_in, etc.
        """
        try:
            token_url = f"{self.authority}/oauth2/v2.0/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
                "scope": " ".join(self.scopes)
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Erro ao obter token: {error_data}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Erro ao obter token: {error_data.get('error_description', 'Desconhecido')}"
                )
            
            token_response = response.json()
            logger.info("Token obtido com sucesso")
            
            return {
                "access_token": token_response.get("access_token"),
                "refresh_token": token_response.get("refresh_token"),
                "expires_in": token_response.get("expires_in"),
                "token_type": token_response.get("token_type", "Bearer"),
                "scope": token_response.get("scope")
            }
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com Entra ID"
            )
        except Exception as e:
            logger.error(f"Erro ao trocar código por token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao trocar código por token"
            )
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Obtém informações do usuário autenticado
        
        Args:
            access_token: Access token do usuário
            
        Returns:
            Dicionário com informações do usuário
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter informações do usuário: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Erro ao obter informações do usuário"
                )
            
            user_data = response.json()
            logger.info(f"Informações do usuário obtidas: {user_data.get('userPrincipalName')}")
            
            return {
                "id": user_data.get("id"),
                "displayName": user_data.get("displayName"),
                "userPrincipalName": user_data.get("userPrincipalName"),
                "mail": user_data.get("mail"),
                "givenName": user_data.get("givenName"),
                "surname": user_data.get("surname"),
                "jobTitle": user_data.get("jobTitle"),
                "mobilePhone": user_data.get("mobilePhone")
            }
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter informações do usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com Microsoft Graph"
            )
        except Exception as e:
            logger.error(f"Erro ao obter informações do usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao obter informações do usuário"
            )
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Renova access token usando refresh token
        
        Args:
            refresh_token: Refresh token do usuário
            
        Returns:
            Novo access token
        """
        try:
            token_url = f"{self.authority}/oauth2/v2.0/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(self.scopes)
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Erro ao renovar token: {error_data}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Erro ao renovar token"
                )
            
            token_response = response.json()
            logger.info("Token renovado com sucesso")
            
            return {
                "access_token": token_response.get("access_token"),
                "refresh_token": token_response.get("refresh_token"),
                "expires_in": token_response.get("expires_in"),
                "token_type": token_response.get("token_type", "Bearer")
            }
            
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao renovar token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro de conexão com Entra ID"
            )
        except Exception as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao renovar token"
            )
    
    def validate_token(self, access_token: str) -> bool:
        """
        Valida se o access token é válido
        
        Args:
            access_token: Access token a validar
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erro ao validar token: {str(e)}")
            return False
