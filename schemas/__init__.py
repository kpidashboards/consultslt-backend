"""
Schemas Pydantic para validação de dados
"""

# ==============================
# Usuário
# ==============================
from .usuario import (
    PerfilUsuario,       # ✅ Certifique-se que esse Enum existe em usuario.py
    PermissaoSistema,
    UsuarioBase,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    TrocarSenhaRequest,
    AlterarSenhaRequest,
)

# ==============================
# Documento
# ==============================
from .documento import (
    TipoDocumento,
    StatusDocumento,
    DocumentoBase,
    DocumentoCreate,
    DocumentoUpload,
    DocumentoResponse,
    DocumentoListResponse,
    DocumentoProcessamentoResult,
)

# ==============================
# Obrigação
# ==============================
from .obrigacao import (
    TipoObrigacao,
    StatusObrigacao,
    PrioridadeObrigacao,
    ObrigacaoBase,
    ObrigacaoCreate,
    ObrigacaoUpdate,
    ObrigacaoResponse,
    ObrigacaoListResponse,
)

# ==============================
# Empresa
# ==============================
from .empresa import (
    EmpresaBase,
    EmpresaCreate,
    EmpresaResponse,
)

# ==============================
# __all__ — Exportações públicas
# ==============================
__all__ = [
    # ==============================
    # Usuário
    # ==============================
    "PerfilUsuario",
    "PermissaoSistema",
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioResponse",
    "UsuarioListResponse",
    "TrocarSenhaRequest",
    "AlterarSenhaRequest",

    # ==============================
    # Documento
    # ==============================
    "TipoDocumento",
    "StatusDocumento",
    "DocumentoBase",
    "DocumentoCreate",
    "DocumentoUpload",
    "DocumentoResponse",
    "DocumentoListResponse",
    "DocumentoProcessamentoResult",

    # ==============================
    # Obrigação
    # ==============================
    "TipoObrigacao",
    "StatusObrigacao",
    "PrioridadeObrigacao",
    "ObrigacaoBase",
    "ObrigacaoCreate",
    "ObrigacaoUpdate",
    "ObrigacaoResponse",
    "ObrigacaoListResponse",

    # ==============================
    # Empresa
    # ==============================
    "EmpresaBase",
    "EmpresaCreate",
    "EmpresaResponse",
]
