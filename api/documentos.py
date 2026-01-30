"""
Endpoints para gestão de Documentos
Implementa upload, processamento e consulta de documentos fiscais
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from schemas.documento import (
    TipoDocumento,
    StatusDocumento,
    DocumentoResponse,
    DocumentoListResponse,
    DocumentoProcessamentoResult
)
from services.documento_service import DocumentoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def get_db():
    """Dependência para obter conexão com MongoDB"""
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "sltdctfweb")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


def get_documento_service(db=Depends(get_db)) -> DocumentoService:
    """Dependência para obter serviço de documentos"""
    return DocumentoService(db)


@router.post("/upload", response_model=DocumentoResponse)
async def upload_documento(
    file: UploadFile = File(..., description="Arquivo PDF, XML ou Excel"),
    empresa_id: Optional[str] = Form(default=None, description="ID da empresa"),
    tipo: TipoDocumento = Form(default=TipoDocumento.OUTRO, description="Tipo do documento"),
    processar: bool = Form(default=True, description="Processar automaticamente"),
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Faz upload de um documento fiscal
    
    - **file**: Arquivo PDF, XML ou Excel (máx. 50MB)
    - **empresa_id**: ID da empresa relacionada (opcional)
    - **tipo**: Tipo do documento (dctfweb, das, darf, nfe, certidao, outro)
    - **processar**: Se deve extrair dados automaticamente (default: true)
    
    O sistema detecta automaticamente o tipo de documento e extrai:
    - CNPJ do contribuinte
    - Período de apuração
    - Valor total
    - Data de vencimento
    
    Se for um documento DCTFWeb ou DAS, uma obrigação fiscal é criada/atualizada automaticamente.
    """
    logger.info(f"Upload recebido: {file.filename}")
    
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        
        # Fazer upload e processar
        documento = await service.upload_documento(
            filename=file.filename,
            content=content,
            content_type=file.content_type or "application/octet-stream",
            empresa_id=empresa_id,
            tipo=tipo,
            processar_automaticamente=processar
        )
        
        return documento
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@router.post("/{documento_id}/processar", response_model=DocumentoProcessamentoResult)
async def processar_documento(
    documento_id: str,
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Processa (ou reprocessa) um documento
    
    Extrai dados do PDF e cria/atualiza obrigação fiscal se aplicável.
    """
    try:
        result = await service.processar_documento(documento_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentoListResponse)
async def listar_documentos(
    empresa_id: Optional[str] = Query(default=None, description="Filtrar por empresa"),
    tipo: Optional[TipoDocumento] = Query(default=None, description="Filtrar por tipo"),
    status: Optional[StatusDocumento] = Query(default=None, description="Filtrar por status"),
    pagina: int = Query(default=1, ge=1, description="Número da página"),
    por_pagina: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Lista documentos com filtros e paginação
    """
    result = await service.listar_documentos(
        empresa_id=empresa_id,
        tipo=tipo,
        status=status,
        pagina=pagina,
        por_pagina=por_pagina
    )
    
    return DocumentoListResponse(**result)


@router.get("/{documento_id}", response_model=DocumentoResponse)
async def obter_documento(
    documento_id: str,
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Obtém detalhes de um documento específico
    """
    documento = await service.obter_documento(documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return DocumentoResponse(**documento)


@router.delete("/{documento_id}")
async def deletar_documento(
    documento_id: str,
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Deleta um documento (arquivo e registro)
    """
    sucesso = await service.deletar_documento(documento_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return {"message": "Documento deletado com sucesso"}


@router.get("/estatisticas/resumo")
async def obter_estatisticas(
    empresa_id: Optional[str] = Query(default=None),
    service: DocumentoService = Depends(get_documento_service)
):
    """
    Obtém estatísticas de documentos
    """
    filtro = {}
    if empresa_id:
        filtro["empresa_id"] = empresa_id
    
    total = await service.db.documentos.count_documents(filtro)
    processados = await service.db.documentos.count_documents({**filtro, "status": "processado"})
    pendentes = await service.db.documentos.count_documents({**filtro, "status": "pendente"})
    erros = await service.db.documentos.count_documents({**filtro, "status": "erro"})
    
    return {
        "total": total,
        "processados": processados,
        "pendentes": pendentes,
        "erros": erros,
        "taxa_sucesso": (processados / total * 100) if total > 0 else 0
    }
documentos_router = router

