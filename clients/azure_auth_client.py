"""
Cliente OAuth2 para Azure AD / Entra ID
Implementa Client Credentials Flow para acesso ao SharePoint
SEM interação do usuário - 100% automatizado
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
import os

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exceção para erros de autenticação OAuth2"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


@dataclass
class TokenInfo:
    """Estrutura para armazenar informações do token"""
    access_token: str
    token_type: str
    expires_at: datetime
    scope: str


class AzureAuthClient:
    """
    Cliente de autenticação OAuth2 para Azure AD / Entra ID
    Utiliza Client Credentials Flow (sem interação do usuário)
    
    Requisitos:
    - Tenant ID do Azure AD
    - Client ID (Application ID) do App Registration
    - Client Secret gerado no App Registration
    - Permissões Microsoft Graph API concedidas (Admin Consent)
    """
    
    AUTHORITY_URL = "https://login.microsoftonline.com"
    GRAPH_SCOPE = "https://graph.microsoft.com/.default"
    
    def __init__(
        self,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_cache: Optional[Any] = None
    ):
        """
        Inicializa o cliente de autenticação
        
        Args:
            tenant_id: ID do tenant Azure AD (ou via AZURE_TENANT_ID)
            client_id: ID da aplicação registrada (ou via AZURE_CLIENT_ID)
            client_secret: Secret da aplicação (ou via AZURE_CLIENT_SECRET)
            token_cache: Cache externo opcional (Redis)
        """
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID")
        self.client_id = client_id or os.environ.get("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET")
        self.token_cache = token_cache
        
        self._token: Optional[TokenInfo] = None
        self._lock = asyncio.Lock()
        
        # Validação
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            missing = []
            if not self.tenant_id:
                missing.append("AZURE_TENANT_ID")
            if not self.client_id:
                missing.append("AZURE_CLIENT_ID")
            if not self.client_secret:
                missing.append("AZURE_CLIENT_SECRET")
            
            logger.warning(
                f"Credenciais Azure AD incompletas. Faltando: {', '.join(missing)}. "
                "A integração SharePoint não funcionará até configurar as credenciais."
            )
    
    @property
    def is_configured(self) -> bool:
        """Verifica se as credenciais estão configuradas"""
        return all([self.tenant_id, self.client_id, self.client_secret])
    
    @property
    def token_endpoint(self) -> str:
        """URL do endpoint de token"""
        return f"{self.AUTHORITY_URL}/{self.tenant_id}/oauth2/v2.0/token"
    
    async def get_token(self) -> str:
        """
        Obtém um token de acesso válido.
        Implementa cache e renovação automática.
        
        Returns:
            Token de acesso válido
            
        Raises:
            AuthenticationError: Se não for possível obter o token
        """
        if not self.is_configured:
            raise AuthenticationError(
                "Credenciais Azure AD não configuradas. "
                "Configure AZURE_TENANT_ID, AZURE_CLIENT_ID e AZURE_CLIENT_SECRET.",
                error_code="credentials_not_configured"
            )
        
        async with self._lock:
            # Verificar cache em memória
            if self._token and not self._is_token_expired():
                logger.debug("Usando token em cache (memória)")
                return self._token.access_token
            
            # Verificar cache externo (Redis)
            if self.token_cache:
                cached = await self._get_from_cache()
                if cached:
                    logger.debug("Usando token em cache (Redis)")
                    return cached
            
            # Obter novo token
            logger.info("Obtendo novo token OAuth2 do Azure AD")
            token_info = await self._request_token()
            
            # Armazenar em cache
            self._token = token_info
            if self.token_cache:
                await self._save_to_cache(token_info)
            
            return token_info.access_token
    
    async def _request_token(self) -> TokenInfo:
        """
        Requisita novo token ao Azure AD via Client Credentials Flow
        
        Returns:
            TokenInfo com dados do token obtido
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.GRAPH_SCOPE
            }
            
            try:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error_description", "Unknown error")
                    error_code = error_data.get("error", "unknown")
                    
                    logger.error(f"Falha ao obter token: {error_code} - {error_msg}")
                    
                    raise AuthenticationError(
                        f"Falha na autenticação Azure AD: {error_msg}",
                        status_code=response.status_code,
                        error_code=error_code
                    )
                
                data = response.json()
                
                # Calcular expiração (com margem de segurança de 5 minutos)
                expires_in = data.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                
                token_info = TokenInfo(
                    access_token=data["access_token"],
                    token_type=data["token_type"],
                    expires_at=expires_at,
                    scope=data.get("scope", self.GRAPH_SCOPE)
                )
                
                logger.info(f"Token obtido com sucesso. Expira em {expires_in}s")
                return token_info
                
            except httpx.ConnectError as e:
                logger.error(f"Erro de conexão com Azure AD: {e}")
                raise AuthenticationError(
                    "Não foi possível conectar ao Azure AD. "
                    "Verifique conectividade com login.microsoftonline.com:443",
                    error_code="connection_error"
                )
            except httpx.TimeoutException as e:
                logger.error(f"Timeout na conexão com Azure AD: {e}")
                raise AuthenticationError(
                    "Timeout ao conectar com Azure AD.",
                    error_code="timeout"
                )
    
    def _is_token_expired(self) -> bool:
        """Verifica se o token em cache está expirado"""
        if not self._token:
            return True
        return datetime.utcnow() >= self._token.expires_at
    
    async def _get_from_cache(self) -> Optional[str]:
        """Recupera token do cache externo (Redis)"""
        if not self.token_cache:
            return None
        try:
            cached_token = await self.token_cache.get("azure_ad_token")
            if cached_token:
                expires_at = await self.token_cache.get("azure_ad_token_expires")
                if expires_at and datetime.fromisoformat(expires_at) > datetime.utcnow():
                    return cached_token.decode() if isinstance(cached_token, bytes) else cached_token
        except Exception as e:
            logger.warning(f"Erro ao ler cache de token: {e}")
        return None
    
    async def _save_to_cache(self, token_info: TokenInfo):
        """Salva token no cache externo (Redis)"""
        if not self.token_cache:
            return
        try:
            ttl = int((token_info.expires_at - datetime.utcnow()).total_seconds())
            await self.token_cache.setex(
                "azure_ad_token",
                ttl,
                token_info.access_token
            )
            await self.token_cache.setex(
                "azure_ad_token_expires",
                ttl,
                token_info.expires_at.isoformat()
            )
        except Exception as e:
            logger.warning(f"Erro ao salvar token em cache: {e}")
    
    async def validate_connectivity(self) -> Dict[str, Any]:
        """
        Valida conectividade com Azure AD
        Útil para health checks
        
        Returns:
            Dict com status da conectividade
        """
        result = {
            "configured": self.is_configured,
            "can_connect": False,
            "can_authenticate": False,
            "error": None
        }
        
        if not self.is_configured:
            result["error"] = "Credenciais não configuradas"
            return result
        
        try:
            # Testar conectividade
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.AUTHORITY_URL}/{self.tenant_id}/v2.0/.well-known/openid-configuration"
                )
                result["can_connect"] = response.status_code == 200
            
            # Testar autenticação
            if result["can_connect"]:
                try:
                    await self.get_token()
                    result["can_authenticate"] = True
                except AuthenticationError as e:
                    result["error"] = str(e)
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result
