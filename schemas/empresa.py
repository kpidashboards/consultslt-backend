"""
Schemas Pydantic para Empresas
Compatível com CRUD completo, persistência real e testes automatizados
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

# ===============================
# ENUMS
# ===============================
class RegimeTributario(str, Enum):
    SIMPLES = "simples"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL = "lucro_real"
    MEI = "mei"

# ===============================
# VALIDADORES
# ===============================
def validar_cnpj(cnpj: str) -> str:
    """Remove formatação e valida CNPJ"""
    cnpj_clean = re.sub(r"\D", "", cnpj)
    if len(cnpj_clean) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos")
    return cnpj_clean

# ===============================
# BASE
# ===============================
class EmpresaBase(BaseModel):
    cnpj: str = Field(..., example="11222333000181", description="CNPJ da empresa (14 dígitos)")
    razao_social: str = Field(..., example="Empresa Exemplo LTDA", description="Razão Social")
    nome_fantasia: Optional[str] = Field(None, example="Empresa Exemplo", description="Nome Fantasia")
    regime: str = Field("simples", description="Regime tributário")
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    receita_bruta: float = Field(0.0, description="Receita bruta anual em R$")
    fator_r: float = Field(0.0, description="Fator R para simples nacional (%)")
    ativo: bool = Field(True, description="Status ativo/inativo")

    @field_validator("cnpj", mode="before")
    @classmethod
    def validar_cnpj_field(cls, v):
        return validar_cnpj(v)

    @field_validator("regime", mode="before")
    @classmethod
    def validar_regime(cls, v):
        if v not in ["simples", "lucro_presumido", "lucro_real", "mei"]:
            raise ValueError("Regime inválido")
        return v

# ===============================
# CREATE
# ===============================
class EmpresaCreate(EmpresaBase):
    pass

# ===============================
# UPDATE (Todos os campos opcionais)
# ===============================
class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    regime: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    receita_bruta: Optional[float] = None
    fator_r: Optional[float] = None
    ativo: Optional[bool] = None

# ===============================
# RESPONSE
# ===============================
class EmpresaResponse(EmpresaBase):
    id: str = Field(..., description="ID único (MongoDB ObjectId)")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ===============================
# LIST RESPONSE
# ===============================
class EmpresaListResponse(BaseModel):
    items: List[EmpresaResponse]
    total: int
