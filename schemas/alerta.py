from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class StatusAlerta(str, Enum):
    PENDENTE = "PENDENTE"
    LIDO = "LIDO"
    RESOLVIDO = "RESOLVIDO"


class AlertaBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    empresa_id: Optional[str] = None


class AlertaCreate(AlertaBase):
    pass


class AlertaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[StatusAlerta] = None


class AlertaResponse(AlertaBase):
    id: str
    status: StatusAlerta
    created_at: datetime
    updated_at: Optional[datetime] = None
    lido_em: Optional[datetime] = None
    resolvido_em: Optional[datetime] = None

    class Config:
        from_attributes = True