"""Application configuration and environment settings."""
from __future__ import annotations
import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "magicpin-vera-bot"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Optional LLM integration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL", "")
    
    # Metadata for /v1/metadata endpoint
    TEAM_NAME: str = "Team Vera"
    TEAM_MEMBERS: List[str] = ["Challenge Developer"]
    CONTACT_EMAIL: str = "vera@example.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
