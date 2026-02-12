from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Periodicidade(str, Enum):
    MENSAL = "mensal"
    ANUAL = "anual"
    EVENTUAL = "eventual"

class ObrigacaoFiscalBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    periodicidade: Periodicidade
    status: str = Field(default="pendente")
    empresa_id: Optional[str] = None

class ObrigacaoFiscalCreate(ObrigacaoFiscalBase):
    pass

class ObrigacaoFiscalUpdate(BaseModel):
    status: Optional[str] = None
    descricao: Optional[str] = None

class ObrigacaoFiscalResponse(ObrigacaoFiscalBase):
    id: str

    class Config:
        from_attributes = True
