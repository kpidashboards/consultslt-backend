from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FiscalIrisSchema(BaseModel):
    cnpj: str
    periodo: str
    receitaBruta12M: float
    receitaMensal: float
    folhaSalarios12M: float
    anexo: str
    fatorR: float
    valorDAS: float
    certidoes: Optional[List[dict]] = []
    pendencias: Optional[List[dict]] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None
    userId: str