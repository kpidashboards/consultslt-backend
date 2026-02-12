from fastapi import APIRouter

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])

# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""Endpoints para Configurações do Sistema"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from datetime import datetime
import uuid
from backend.schemas.configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoUpdate,
    ConfiguracaoResponse
)
from backend.repositories.configuracoes_repository import ConfiguracoesRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/configuracoes", tags=["Configurações"])

def get_configuracoes_repo():
    return ConfiguracoesRepository()

# =========================
# Endpoints
# =========================

@router.post("/", response_model=ConfiguracaoResponse)
async def criar_configuracao(dados: ConfiguracaoCreate, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Cria uma nova configuração"""
    existe = await repo.get_configuracao_by_chave(dados.chave)
    if existe:
        raise HTTPException(status_code=400, detail="Chave já existe")
    config_dict = dados.model_dump()
    config = await repo.create_configuracao(config_dict)
    return ConfiguracaoResponse(**config)


@router.get("/", response_model=list[ConfiguracaoResponse])
async def listar_configuracoes(categoria: Optional[str] = None, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Lista configurações"""
    filtro = {}
    if categoria:
        filtro["categoria"] = categoria
    configs = await repo.list_configuracoes(filtro)
    return [ConfiguracaoResponse(**c) for c in configs]


@router.get("/chave/{chave}", response_model=ConfiguracaoResponse)
async def obter_configuracao_por_chave(chave: str, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Obtém configuração por chave"""
    config = await repo.get_configuracao_by_chave(chave)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return ConfiguracaoResponse(**config)


@router.get("/{config_id}", response_model=ConfiguracaoResponse)
async def obter_configuracao_por_id(config_id: str, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Obtém configuração por ID"""
    config = await repo.get_configuracao_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return ConfiguracaoResponse(**config)


@router.put("/{config_id}", response_model=ConfiguracaoResponse)
async def atualizar_configuracao(config_id: str, dados: ConfiguracaoUpdate, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Atualiza uma configuração"""
    update_data = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
    config = await repo.update_configuracao(config_id, update_data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return ConfiguracaoResponse(**config)


@router.delete("/{config_id}")
async def deletar_configuracao(config_id: str, repo: ConfiguracoesRepository = Depends(get_configuracoes_repo)):
    """Deleta uma configuração"""
    ok = await repo.delete_configuracao(config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return {"message": "Configuração deletada com sucesso"}


# =========================
# Exportar router
# =========================
configuracoes_router = router
