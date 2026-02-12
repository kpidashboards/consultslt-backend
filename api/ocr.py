from fastapi import APIRouter

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.get("/")
async def listar_ocr():
    return []
# TODO: Auditoria deste módulo
# - Conferir todos os endpoints, métodos HTTP e persistência real no MongoDB
"""
API de OCR e Automação Documental (Paridade Kolossus)
Endpoints para processamento inteligente de documentos fiscais
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
import logging
import os

from services.ocr_service import OCRService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR e Automação Documental"])

# =========================
# Nome correto do banco
# =========================
db_name = os.environ.get("DB_NAME", "consultslt_db")


# Dependência para obter o serviço OCR
def get_ocr_service() -> OCRService:
    from services.database import get_db  # supondo que você tenha um client MongoDB
    db = get_db()
    return OCRService(db)


@router.post("/processar")
async def processar_documento_ocr(
    arquivo: UploadFile = File(..., description="Documento (PDF, PNG, JPG)"),
    empresa_id: Optional[str] = Form(default=None),
    tipo_esperado: Optional[str] = Form(default=None, description="Tipo esperado: nfe, nfse, das, darf, etc."),
    service: OCRService = Depends(get_ocr_service)
):
    """Processa um documento com OCR inteligente"""
    try:
        content = await arquivo.read()
        resultado = await service.processar_documento(
            filename=arquivo.filename,
            content=content,
            empresa_id=empresa_id,
            tipo_esperado=tipo_esperado
        )
        return resultado

    except Exception as e:
        logger.error(f"Erro no processamento OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/processar-lote")
async def processar_lote_ocr(
    arquivos: List[UploadFile] = File(..., description="Lista de documentos"),
    empresa_id: Optional[str] = Form(default=None),
    service: OCRService = Depends(get_ocr_service)
):
    """Processa múltiplos documentos em lote (limite: 20 arquivos)"""
    if len(arquivos) > 20:
        raise HTTPException(status_code=400, detail="Máximo de 20 arquivos por lote")

    resultados = []
    erros = []

    for arquivo in arquivos:
        try:
            content = await arquivo.read()
            resultado = await service.processar_documento(
                filename=arquivo.filename,
                content=content,
                empresa_id=empresa_id
            )
            resultados.append(resultado)
        except Exception as e:
            erros.append({
                "arquivo": arquivo.filename,
                "erro": str(e)
            })

    return {
        "processados": len(resultados),
        "erros": len(erros),
        "resultados": resultados,
        "detalhes_erros": erros
    }


@router.get("/documentos")
async def listar_documentos_ocr(
    empresa_id: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100),
    service: OCRService = Depends(get_ocr_service)
):
    """Lista documentos processados por OCR"""
    documentos = await service.listar_documentos_ocr(
        empresa_id=empresa_id,
        tipo=tipo,
        status=status,
        limit=limit
    )
    return {"documentos": documentos, "total": len(documentos)}


@router.get("/estatisticas")
async def obter_estatisticas_ocr(
    empresa_id: Optional[str] = Query(default=None),
    service: OCRService = Depends(get_ocr_service)
):
    """Obtém estatísticas de processamento OCR"""
    return await service.obter_estatisticas_ocr(empresa_id=empresa_id)


@router.get("/documentos/{documento_id}")
async def obter_documento_ocr(
    documento_id: str,
    service: OCRService = Depends(get_ocr_service)
):
    """Obtém detalhes de um documento processado"""
    documento = await service.obter_documento_ocr(documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return documento


@router.get("/tipos-suportados")
async def listar_tipos_suportados():
    """Lista tipos de documentos suportados pela classificação automática"""
    return {
        "tipos": [
            {"codigo": "nfe", "descricao": "Nota Fiscal Eletrônica (NF-e)"},
            {"codigo": "nfse", "descricao": "Nota Fiscal de Serviço Eletrônica (NFS-e)"},
            {"codigo": "cte", "descricao": "Conhecimento de Transporte Eletrônico (CT-e)"},
            {"codigo": "darf", "descricao": "Documento de Arrecadação de Receitas Federais"},
            {"codigo": "das", "descricao": "Documento de Arrecadação do Simples Nacional"},
            {"codigo": "gps", "descricao": "Guia da Previdência Social"},
            {"codigo": "dctfweb", "descricao": "DCTFWeb (Declaração de Débitos e Créditos Tributários)"},
            {"codigo": "certidao", "descricao": "Certidão Negativa de Débitos (CND)"},
            {"codigo": "boleto", "descricao": "Boleto Bancário"},
            {"codigo": "extrato", "descricao": "Extrato Bancário"}
        ]
    }
