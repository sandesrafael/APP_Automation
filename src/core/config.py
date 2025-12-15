"""
Application Configuration
Centralized settings using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Info
    app_name: str = "Automation API"
    version: str = "1.0.0"
    description: str = "API para automação de geração de Masterfiles e JSONs Oracle/PostgreSQL"
    debug: bool = False
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8080
    reload: bool = True
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Paths
    output_base_path: str = ""
    temp_path: str = ""
    
    # Database defaults
    default_db_type: str = "postgres"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_output_path(self) -> str:
        """Returns output path or project root if not set"""
        if self.output_base_path:
            return self.output_base_path
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use dependency injection in FastAPI routes.
    """
    return Settings()
