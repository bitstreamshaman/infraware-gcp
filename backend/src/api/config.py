from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """API settings configuration loaded from environment variables"""
    
    # API configurations
    API_PREFIX: str = "/api"
    API_DEBUG: bool = False
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Cloud storage settings
    GCP_PROJECT_ID: str = ""
    GCP_STORAGE_BUCKET: str = ""
    
    # CrewAI settings
    CREWAI_MODEL: str = "gpt-4o-mini"
    
    # Job settings
    JOB_EXPIRY_HOURS: int = 24
    
    # Location of templates and output directories
    TEMPLATES_DIR: str = ""
    OUTPUT_BASE_DIR: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()