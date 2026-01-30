"""Configurações do sistema"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Configurações centralizadas da aplicação"""
    
    # MongoDB
    MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.environ.get("DB_NAME", "sltdctfweb")
    
    # Azure AD / SharePoint
    AZURE_TENANT_ID: Optional[str] = os.environ.get("AZURE_TENANT_ID")
    AZURE_CLIENT_ID: Optional[str] = os.environ.get("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[str] = os.environ.get("AZURE_CLIENT_SECRET")
    SHAREPOINT_SITE_URL: Optional[str] = os.environ.get("SHAREPOINT_SITE_URL")
    SHAREPOINT_DRIVE_ID: Optional[str] = os.environ.get("SHAREPOINT_DRIVE_ID")
    
    # Armazenamento
    LOCAL_STORAGE_PATH: Path = Path(os.environ.get("LOCAL_STORAGE_PATH", "/data/uploads"))
    
    # Auto-start
    AUTO_START_INGESTION: bool = os.environ.get("AUTO_START_INGESTION", "false").lower() == "true"
    
    # CORS
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")
    
    @property
    def sharepoint_configured(self) -> bool:
        """Verifica se SharePoint está configurado"""
        return all([
            self.AZURE_TENANT_ID,
            self.AZURE_CLIENT_ID,
            self.AZURE_CLIENT_SECRET,
            self.SHAREPOINT_SITE_URL
        ])


settings = Settings()
