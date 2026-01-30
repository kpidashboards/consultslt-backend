"""
Configurações da aplicação (Pydantic v2)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from datetime import timedelta

class Settings(BaseSettings):
    """Configurações principais da aplicação"""

    # MongoDB
    MONGO_URL: str = "mongodb://127.0.0.1:27017"
    DB_NAME: str = "consultslt_db"

    # Admin defaults
    DEFAULT_ADMINS: List[dict] = [
        {
            "email": "admin@empresa.com",
            "password": "admin123",
            "name": "Administrador",
            "role": "ADMIN"
        },
        {
            "email": "william.lucas@sltconsult.com.br",
            "password": "Slt@2024",
            "name": "William Lucas",
            "role": "ADMIN"
        },
        {
            "email": "admin@consultslt.com.br",
            "password": "Consult@2026",
            "name": "Admin SLT",
            "role": "ADMIN"
        }
    ]

    # JWT / Auth
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # Logs
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Criar uma instância global
settings = Settings()
