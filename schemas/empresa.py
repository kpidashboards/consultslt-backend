"""
Schemas Pydantic para Empresas
Compatível com CRUD completo, persistência real e testes automatizados
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

# ===============================
# ENUMS (Sem alterações, está ótimo)
# ===============================
class RegimeTributario(str, Enum):
    SIMPLES = "SIMPLES"
    LUCRO_PRESUMIDO = "LUCRO_PRESUMIDO"
    LUCRO_REAL = "LUCRO_REAL"
    MEI = "MEI"

# ===============================
# VALIDADORES (Sem alterações, está ótimo)
# ===============================
def validar_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos")
    return cnpj

# ===============================
# BASE (Sem alterações, está ótimo)
# ===============================
class EmpresaBase(BaseModel):
    cnpj: str = Field(..., example="11222333000181")
    razao_social: str = Field(..., example="Empresa Exemplo LTDA")
    nome_fantasia: Optional[str] = None
    regime: RegimeTributario = RegimeTributario.SIMPLES
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: bool = True

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj_field(cls, v):
        return validar_cnpj(v)

# ===============================
# CREATE (Sem alterações)
# ===============================
class EmpresaCreate(EmpresaBase):
    pass

# ===============================
# UPDATE (Sem alterações)
# ===============================
class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    regime: Optional[RegimeTributario] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None

# ===============================
# RESPONSE (VERSÃO CORRIGIDA E SIMPLIFICADA)
# ===============================
class EmpresaResponse(EmpresaBase):
    # ✅ O ID é uma string (representação do ObjectId do MongoDB).
    id: str
    
    # ✅ O campo 'ativo' já está na classe base, mas podemos mantê-lo se quisermos garantir que ele sempre apareça na resposta.
    ativo: bool
    
    # ✅ 'created_at' é adicionado pela nossa API, então ele deve estar aqui.
    created_at: datetime
    
    # ✅ 'updated_at' é opcional, pois só existirá após uma atualização.
    updated_at: Optional[datetime] = None

    # ❌ REMOVIDOS os campos que não existem no nosso documento do banco de dados:
    # entity_id, version, valid_from, valid_to, previous_version_id, created_by

    class Config:
        # Garante que o Pydantic consiga ler os dados do objeto do MongoDB.
        from_attributes = True

# ===============================
# LIST RESPONSE (Sem alterações, mas agora usará o EmpresaResponse corrigido)
# ===============================
class EmpresaListResponse(BaseModel):
    items: List[EmpresaResponse]
    total: int
