from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    # Environment
    PYTHON_ENV: Literal["development", "staging", "production"] = "production"
    
    # Database
    DATABASE_URL: str
    
    # CORS & URLs
    BACKEND_CORS_ORIGINS: str  # Comma-separated list
    BACKEND_URL: str
    FRONTEND_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    ENCRYPTION_ALGORITHM: str = "HS256"
    
    # GitHub OAuth
    GITHUB_OAUTH_CLIENT_ID: str
    GITHUB_OAUTH_CLIENT_SECRET: str
    GITHUB_OAUTH_CALLBACK_URL: str
    GITHUB_WEBHOOK_URL: str
    
    # GitHub App
    GITHUB_APP_CLIENT_ID: str
    GITHUB_APP_CLIENT_SECRET: str
    
    # Railway
    RAILWAY_INTERNAL: str | None = None
    RAILWAY_PROD: str | None = None
    RAILWAY_STAGING: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Computed properties
    @property
    def is_development(self) -> bool:
        return self.PYTHON_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        return self.PYTHON_ENV == "production"
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins"""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

settings = Settings()