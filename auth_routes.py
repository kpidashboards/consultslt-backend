"""
Rotas de Autenticação e SharePoint
Endpoints para OAuth com Entra ID e acesso a recibos
"""

import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import logging

from backend.services.entra_auth import EntraIDAuthService
from backend.services.sharepoint_service import SharePointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ============================================================================
# Modelos Pydantic
# ============================================================================

class TokenResponse(BaseModel):
    """Resposta de token"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"


class UserInfo(BaseModel):
    """Informações do usuário"""
    id: str
    displayName: str
    userPrincipalName: str
    mail: str
    givenName: Optional[str] = None
    surname: Optional[str] = None
    jobTitle: Optional[str] = None


class AuthResponse(BaseModel):
    """Resposta de autenticação"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    user: UserInfo


class ReciboInfo(BaseModel):
    """Informações de um recibo"""
    id: str
    nome: str
    tamanho: int
    criado: str
    modificado: str
    url: str
    download_url: Optional[str] = None


class RecibosResponse(BaseModel):
    """Resposta com lista de recibos"""
    recibos: list[ReciboInfo]
    total: int


# ============================================================================
# Endpoints de Autenticação
# ============================================================================

@router.get("/login")
async def login(state: Optional[str] = None):
    """
    Inicia fluxo de autenticação OAuth com Entra ID
    
    Returns:
        Redirecionamento para Entra ID
    """
    try:
        auth_service = EntraIDAuthService()
        
        # Gerar state token para CSRF protection
        state_token = state or str(uuid.uuid4())
        
        # Gerar URL de autorização
        auth_url = auth_service.get_authorization_url(state=state_token)
        
        logger.info("Fluxo de login iniciado")
        
        # Redirecionar para Entra ID
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Erro ao iniciar login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao iniciar login"
        )


@router.get("/callback")
async def auth_callback(code: str = Query(...), state: Optional[str] = None):
    """
    Callback de autenticação do Entra ID
    
    Args:
        code: Authorization code do Entra ID
        state: State token para validação CSRF
        
    Returns:
        Tokens e informações do usuário
    """
    try:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code não fornecido"
            )
        
        auth_service = EntraIDAuthService()
        
        # Trocar código por token
        token_response = auth_service.get_token_from_code(code)
        
        # Obter informações do usuário
        user_info = auth_service.get_user_info(token_response["access_token"])
        
        logger.info(f"Usuário autenticado: {user_info.get('userPrincipalName')}")
        
        # Retornar tokens e informações
        return AuthResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in", 3600),
            user=UserInfo(**user_info)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no callback de autenticação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no callback de autenticação"
        )


@router.post("/refresh")
async def refresh_access_token(refresh_token: str):
    """
    Renova access token usando refresh token
    
    Args:
        refresh_token: Refresh token do usuário
        
    Returns:
        Novo access token
    """
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token não fornecido"
            )
        
        auth_service = EntraIDAuthService()
        token_response = auth_service.refresh_token(refresh_token)
        
        logger.info("Token renovado com sucesso")
        
        return TokenResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in", 3600),
            token_type=token_response.get("token_type", "Bearer")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao renovar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao renovar token"
        )


@router.get("/me")
async def get_current_user(access_token: str = Query(...)):
    """
    Obtém informações do usuário autenticado
    
    Args:
        access_token: Access token do usuário
        
    Returns:
        Informações do usuário
    """
    try:
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token não fornecido"
            )
        
        auth_service = EntraIDAuthService()
        
        # Validar token
        if not auth_service.validate_token(access_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token inválido"
            )
        
        # Obter informações do usuário
        user_info = auth_service.get_user_info(access_token)
        
        return UserInfo(**user_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter informações do usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter informações do usuário"
        )


# ============================================================================
# Endpoints de SharePoint
# ============================================================================

@router.get("/recibos", response_model=RecibosResponse)
async def listar_recibos(
    access_token: str = Query(...),
    empresa_id: Optional[str] = Query(None),
    limite: int = Query(100, ge=1, le=1000)
):
    """
    Lista recibos disponíveis no SharePoint
    
    Args:
        access_token: Access token do usuário
        empresa_id: ID da empresa para filtrar (opcional)
        limite: Número máximo de recibos a retornar
        
    Returns:
        Lista de recibos
    """
    try:
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token não fornecido"
            )
        
        sp_service = SharePointService(access_token)
        recibos = sp_service.listar_recibos(empresa_id=empresa_id, limite=limite)
        
        logger.info(f"Listados {len(recibos)} recibos para empresa {empresa_id}")
        
        return RecibosResponse(
            recibos=[ReciboInfo(**r) for r in recibos],
            total=len(recibos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar recibos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar recibos"
        )


@router.get("/recibos/{nome_arquivo}")
async def baixar_recibo(
    nome_arquivo: str,
    access_token: str = Query(...)
):
    """
    Baixa um recibo do SharePoint
    
    Args:
        nome_arquivo: Nome do arquivo a baixar
        access_token: Access token do usuário
        
    Returns:
        Conteúdo do arquivo
    """
    try:
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token não fornecido"
            )
        
        sp_service = SharePointService(access_token)
        conteudo = sp_service.baixar_recibo(nome_arquivo)
        
        logger.info(f"Recibo {nome_arquivo} baixado com sucesso")
        
        # Retornar arquivo como download
        return {
            "filename": nome_arquivo,
            "content_type": "application/pdf",
            "size": len(conteudo)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao baixar recibo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao baixar recibo"
        )


@router.get("/recibos/{nome_arquivo}/metadados")
async def obter_metadados_recibo(
    nome_arquivo: str,
    access_token: str = Query(...)
):
    """
    Obtém metadados de um recibo
    
    Args:
        nome_arquivo: Nome do arquivo
        access_token: Access token do usuário
        
    Returns:
        Metadados do arquivo
    """
    try:
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token não fornecido"
            )
        
        sp_service = SharePointService(access_token)
        metadados = sp_service.obter_metadados_recibo(nome_arquivo)
        
        logger.info(f"Metadados do recibo {nome_arquivo} obtidos")
        
        return metadados
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter metadados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter metadados"
        )


@router.get("/empresas")
async def listar_empresas(access_token: str = Query(...)):
    """
    Lista empresas disponíveis no SharePoint
    
    Args:
        access_token: Access token do usuário
        
    Returns:
        Lista de IDs de empresas
    """
    try:
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token não fornecido"
            )
        
        sp_service = SharePointService(access_token)
        empresas = sp_service.listar_empresas()
        
        logger.info(f"Listadas {len(empresas)} empresas")
        
        return {
            "empresas": empresas,
            "total": len(empresas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar empresas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar empresas"
        )


@router.get("/health")
async def health_check():
    """
    Verifica saúde do serviço de autenticação
    
    Returns:
        Status do serviço
    """
    try:
        # Tentar inicializar serviço de autenticação
        auth_service = EntraIDAuthService()
        
        return {
            "status": "healthy",
            "service": "auth",
            "entra_id_configured": bool(auth_service.client_id),
            "sharepoint_configured": bool(os.getenv("SHAREPOINT_SITE_URL"))
        }
        
    except Exception as e:
        logger.error(f"Health check falhou: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "auth",
            "error": str(e)
        }
