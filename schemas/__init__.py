"""Schemas Pydantic para validação de dados"""

from .usuario import (
    PerfilUsuario,
    PermissaoSistema,
    UsuarioBase,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    TrocarSenhaRequest,
    AlterarSenhaRequest,
)

from .documento import (
    TipoDocumento,
    StatusDocumento,
    DocumentoBase,
    DocumentoCreate,
    DocumentoUpload,
    DocumentoResponse,
    DocumentoListResponse,
    DocumentoProcessamentoResult
)

from .obrigacao import (
    TipoObrigacao,
    StatusObrigacao,
    PrioridadeObrigacao,
    ObrigacaoBase,
    ObrigacaoCreate,
    ObrigacaoUpdate,
    ObrigacaoResponse,
    ObrigacaoListResponse
)

from .empresa import (
    EmpresaBase,
    EmpresaCreate,
    EmpresaResponse
)

__all__ = [
    # ==============================
    # Documento
    # ==============================
    'TipoDocumento',
    'StatusDocumento',
    'DocumentoBase',
    'DocumentoCreate',
    'DocumentoUpload',
    'DocumentoResponse',
    'DocumentoListResponse',
    'DocumentoProcessamentoResult',

    # ==============================
    # Obrigação
    # ==============================
    'TipoObrigacao',
    'StatusObrigacao',
    'PrioridadeObrigacao',
    'ObrigacaoBase',
    'ObrigacaoCreate',
    'ObrigacaoUpdate',
    'ObrigacaoResponse',
    'ObrigacaoListResponse',

    # ==============================
    # Empresa
    # ==============================
    'EmpresaBase',
    'EmpresaCreate',
    'EmpresaResponse',
]
