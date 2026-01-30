"""
Serviço de Documentos
Gerencia upload, armazenamento e processamento de documentos fiscais
"""

import os
import uuid
import aiofiles
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from schemas.documento import (
    TipoDocumento, 
    StatusDocumento, 
    DocumentoResponse,
    DocumentoProcessamentoResult
)
from utils.parsers.dctfweb_parser import DCTFWebParser, DCTFWebData, PDFParsingError
from utils.parsers.das_parser import DASParser, DASData

logger = logging.getLogger(__name__)


class DocumentoService:
    """
    Serviço para gerenciamento de documentos fiscais
    
    Funcionalidades:
    - Upload e armazenamento de arquivos
    - Parsing automático de PDFs (DCTFWeb, DAS)
    - Criação/atualização de obrigações
    - Listagem e busca de documentos
    """
    
    # Diretório de armazenamento
    UPLOAD_DIR = Path(os.environ.get("LOCAL_STORAGE_PATH", "/data/uploads"))
    
    # Tipos de arquivo aceitos
    ALLOWED_EXTENSIONS = {".pdf", ".xml", ".xlsx", ".xls"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/xml",
        "text/xml",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    }
    
    # Tamanho máximo (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.dctfweb_parser = DCTFWebParser()
        self.das_parser = DASParser()
        
        # Garantir que diretório de upload existe
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def upload_documento(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        empresa_id: Optional[str] = None,
        tipo: TipoDocumento = TipoDocumento.OUTRO,
        processar_automaticamente: bool = True
    ) -> DocumentoResponse:
        """
        Faz upload e armazena um documento
        
        Args:
            filename: Nome original do arquivo
            content: Conteúdo binário do arquivo
            content_type: MIME type
            empresa_id: ID da empresa (opcional)
            tipo: Tipo do documento
            processar_automaticamente: Se deve processar o PDF automaticamente
            
        Returns:
            DocumentoResponse com dados do documento criado
        """
        logger.info(f"Upload de documento: {filename}")
        
        # Validar arquivo
        self._validate_file(filename, content, content_type)
        
        # Gerar ID e caminho
        doc_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix.lower()
        stored_filename = f"{doc_id}{file_ext}"
        
        # Organizar por ano/mês
        now = datetime.utcnow()
        subdir = self.UPLOAD_DIR / str(now.year) / f"{now.month:02d}"
        subdir.mkdir(parents=True, exist_ok=True)
        
        file_path = subdir / stored_filename
        
        # Salvar arquivo
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Arquivo salvo em: {file_path}")
        
        # Calcular hash para detectar duplicatas
        file_hash = hashlib.md5(content).hexdigest()
        
        # Criar registro no banco
        documento = {
            "id": doc_id,
            "nome": filename,
            "tipo": tipo.value,
            "status": StatusDocumento.PENDENTE.value,
            "empresa_id": empresa_id,
            "caminho_arquivo": str(file_path),
            "tamanho_bytes": len(content),
            "content_type": content_type,
            "file_hash": file_hash,
            "dados_extraidos": None,
            "confianca_extracao": 0.0,
            "created_at": now,
            "updated_at": None,
            "processado_em": None,
            "erro_processamento": None,
            "obrigacao_id": None,
            "cnpj": None
        }
        
        await self.db.documentos.insert_one(documento)
        
        # Processar automaticamente se for PDF
        if processar_automaticamente and file_ext == ".pdf":
            try:
                result = await self.processar_documento(doc_id, content)
                # Recarregar documento atualizado
                documento = await self.db.documentos.find_one({"id": doc_id})
            except Exception as e:
                logger.error(f"Erro no processamento automático: {e}")
        
        return DocumentoResponse(**documento)
    
    def _validate_file(
        self,
        filename: str,
        content: bytes,
        content_type: str
    ):
        """Valida arquivo antes do upload"""
        # Verificar extensão
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extensão não permitida: {ext}. Permitidas: {self.ALLOWED_EXTENSIONS}")
        
        # Verificar tamanho
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(f"Arquivo muito grande. Máximo: {self.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Verificar MIME type (opcional, pode ser spoofed)
        if content_type and content_type not in self.ALLOWED_MIME_TYPES:
            logger.warning(f"MIME type não reconhecido: {content_type}")
    
    async def processar_documento(
        self,
        documento_id: str,
        content: Optional[bytes] = None
    ) -> DocumentoProcessamentoResult:
        """
        Processa um documento (parsing de PDF)
        
        Args:
            documento_id: ID do documento
            content: Conteúdo do arquivo (opcional, será lido do disco se não fornecido)
            
        Returns:
            DocumentoProcessamentoResult com resultado do processamento
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processando documento: {documento_id}")
        
        # Buscar documento
        doc = await self.db.documentos.find_one({"id": documento_id})
        if not doc:
            raise ValueError(f"Documento não encontrado: {documento_id}")
        
        result = DocumentoProcessamentoResult(
            documento_id=documento_id,
            sucesso=False
        )
        
        try:
            # Atualizar status
            await self.db.documentos.update_one(
                {"id": documento_id},
                {"$set": {"status": StatusDocumento.PROCESSANDO.value}}
            )
            
            # Ler arquivo se necessário
            if content is None:
                async with aiofiles.open(doc["caminho_arquivo"], 'rb') as f:
                    content = await f.read()
            
            # Detectar tipo e fazer parsing
            tipo_detectado, dados_extraidos = await self._parse_pdf(content)
            
            result.tipo_detectado = tipo_detectado
            result.dados_extraidos = dados_extraidos
            
            # Extrair CNPJ
            cnpj = dados_extraidos.get("cnpj", "")
            
            # Atualizar documento
            update_data = {
                "status": StatusDocumento.PROCESSADO.value,
                "tipo": tipo_detectado.value,
                "dados_extraidos": dados_extraidos,
                "confianca_extracao": dados_extraidos.get("extraction_confidence", 0),
                "processado_em": datetime.utcnow(),
                "cnpj": cnpj
            }
            
            # Criar ou atualizar obrigação se aplicável
            if tipo_detectado in [TipoDocumento.DCTFWEB, TipoDocumento.DAS]:
                obrigacao_id = await self._criar_ou_atualizar_obrigacao(
                    doc, tipo_detectado, dados_extraidos
                )
                if obrigacao_id:
                    update_data["obrigacao_id"] = obrigacao_id
                    result.obrigacao_criada = True
                    result.obrigacao_id = obrigacao_id
            
            await self.db.documentos.update_one(
                {"id": documento_id},
                {"$set": update_data}
            )
            
            result.sucesso = True
            
        except PDFParsingError as e:
            logger.error(f"Erro de parsing: {e}")
            result.erros.append(str(e))
            await self.db.documentos.update_one(
                {"id": documento_id},
                {"$set": {
                    "status": StatusDocumento.ERRO.value,
                    "erro_processamento": str(e)
                }}
            )
        except Exception as e:
            logger.error(f"Erro inesperado no processamento: {e}")
            result.erros.append(str(e))
            await self.db.documentos.update_one(
                {"id": documento_id},
                {"$set": {
                    "status": StatusDocumento.ERRO.value,
                    "erro_processamento": str(e)
                }}
            )
        
        result.tempo_processamento_ms = int((time.time() - start_time) * 1000)
        return result
    
    async def _parse_pdf(self, content: bytes) -> Tuple[TipoDocumento, Dict[str, Any]]:
        """
        Detecta o tipo de PDF e faz o parsing apropriado
        """
        # Tentar DCTFWeb primeiro
        try:
            dctfweb_data = self.dctfweb_parser.parse_bytes(content)
            if dctfweb_data.extraction_confidence >= 50:
                logger.info(f"Detectado como DCTFWeb (confiança: {dctfweb_data.extraction_confidence}%)")
                return TipoDocumento.DCTFWEB, dctfweb_data.to_dict()
        except:
            pass
        
        # Tentar DAS
        try:
            das_data = self.das_parser.parse_bytes(content)
            if das_data.extraction_confidence >= 50:
                logger.info(f"Detectado como DAS (confiança: {das_data.extraction_confidence}%)")
                return TipoDocumento.DAS, das_data.to_dict()
        except:
            pass
        
        # Se não conseguiu identificar com confiança, retornar OUTRO
        # Tentar extrair pelo menos o CNPJ
        try:
            dctfweb_data = self.dctfweb_parser.parse_bytes(content)
            return TipoDocumento.OUTRO, dctfweb_data.to_dict()
        except:
            return TipoDocumento.OUTRO, {}
    
    async def _criar_ou_atualizar_obrigacao(
        self,
        documento: Dict,
        tipo: TipoDocumento,
        dados: Dict[str, Any]
    ) -> Optional[str]:
        """
        Cria ou atualiza uma obrigação fiscal baseada nos dados extraídos
        """
        cnpj = dados.get("cnpj", "")
        periodo = dados.get("periodo_apuracao", "")
        
        if not cnpj or not periodo:
            return None
        
        # Buscar obrigação existente
        obrigacao = await self.db.obrigacoes.find_one({
            "cnpj": cnpj,
            "tipo": tipo.value,
            "competencia": periodo
        })
        
        # Preparar dados da obrigação
        obrigacao_data = {
            "tipo": tipo.value,
            "cnpj": cnpj,
            "competencia": periodo,
            "ano": dados.get("ano"),
            "mes": dados.get("mes"),
            "valor": dados.get("valor_total", 0),
            "updated_at": datetime.utcnow()
        }
        
        # Adicionar data de vencimento se disponível
        if dados.get("data_vencimento"):
            obrigacao_data["data_vencimento"] = dados["data_vencimento"]
        
        if obrigacao:
            # Atualizar existente
            obrigacao_id = obrigacao["id"]
            
            # Adicionar documento à lista
            doc_ids = obrigacao.get("documento_ids", [])
            if documento["id"] not in doc_ids:
                doc_ids.append(documento["id"])
                obrigacao_data["documento_ids"] = doc_ids
            
            await self.db.obrigacoes.update_one(
                {"id": obrigacao_id},
                {"$set": obrigacao_data}
            )
            
            logger.info(f"Obrigação atualizada: {obrigacao_id}")
        else:
            # Criar nova
            obrigacao_id = str(uuid.uuid4())
            obrigacao_data.update({
                "id": obrigacao_id,
                "empresa_id": documento.get("empresa_id"),
                "status": "pendente",
                "prioridade": "normal",
                "documento_ids": [documento["id"]],
                "created_at": datetime.utcnow()
            })
            
            await self.db.obrigacoes.insert_one(obrigacao_data)
            logger.info(f"Obrigação criada: {obrigacao_id}")
        
        return obrigacao_id
    
    async def listar_documentos(
        self,
        empresa_id: Optional[str] = None,
        tipo: Optional[TipoDocumento] = None,
        status: Optional[StatusDocumento] = None,
        pagina: int = 1,
        por_pagina: int = 20
    ) -> Dict[str, Any]:
        """
        Lista documentos com filtros e paginação
        """
        filtro = {}
        
        if empresa_id:
            filtro["empresa_id"] = empresa_id
        if tipo:
            filtro["tipo"] = tipo.value
        if status:
            filtro["status"] = status.value
        
        # Contar total
        total = await self.db.documentos.count_documents(filtro)
        
        # Buscar com paginação
        skip = (pagina - 1) * por_pagina
        cursor = self.db.documentos.find(
            filtro,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(por_pagina)
        
        documentos = await cursor.to_list(length=por_pagina)
        
        return {
            "documentos": documentos,
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina
        }
    
    async def obter_documento(self, documento_id: str) -> Optional[Dict[str, Any]]:
        """Obtém um documento pelo ID"""
        return await self.db.documentos.find_one({"id": documento_id}, {"_id": 0})
    
    async def deletar_documento(self, documento_id: str) -> bool:
        """
        Deleta um documento (arquivo e registro)
        """
        doc = await self.db.documentos.find_one({"id": documento_id})
        if not doc:
            return False
        
        # Deletar arquivo físico
        if doc.get("caminho_arquivo"):
            try:
                Path(doc["caminho_arquivo"]).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Não foi possível deletar arquivo: {e}")
        
        # Deletar registro
        await self.db.documentos.delete_one({"id": documento_id})
        
        return True
