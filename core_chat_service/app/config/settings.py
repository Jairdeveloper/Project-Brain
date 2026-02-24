"""
Configuración de la aplicación Core Chat Service
"""
import os
from typing import Optional


class APISettings:
    """Configuración de la API"""
    app_name: str = "Core Chat Service"
    app_version: str = "1.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8001"))
    
    # Multi-tenant
    max_tenants: int = int(os.getenv("MAX_TENANTS", "1000"))
    tenant_isolation: bool = os.getenv("TENANT_ISOLATION", "True").lower() == "true"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Storage
    storage_dir: str = os.getenv("STORAGE_DIR", "./data")
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convierte settings a diccionario"""
        return {
            "app_name": cls.app_name,
            "app_version": cls.app_version,
            "debug": cls.debug,
            "api_host": cls.api_host,
            "api_port": cls.api_port,
            "max_tenants": cls.max_tenants,
            "tenant_isolation": cls.tenant_isolation,
            "log_level": cls.log_level,
        }


settings = APISettings()
