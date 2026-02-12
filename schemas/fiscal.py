# backend/schemas/fiscal.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FiscalBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class FiscalCreate(FiscalBase):
    pass

class FiscalUpdate(FiscalBase):
    pass

class FiscalResponse(FiscalBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
