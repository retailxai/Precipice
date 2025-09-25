"""
Configuration management for RetailXAI Dashboard
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql+psycopg2://user:pass@localhost:5432/retailxai"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "https://retailxai.github.io",
        "https://retailxai.github.io/Precipice",
    ]
    
    # Observability
    sentry_dsn: Optional[str] = None
    otel_exporter_otlp_endpoint: Optional[str] = None
    
    # AI Services
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Publishing endpoints
    substack_email: Optional[str] = None
    linkedin_api_key: Optional[str] = None
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    
    # Feature flags
    enable_ai_features: bool = True
    enable_publishing: bool = True
    enable_analytics: bool = True
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be a PostgreSQL connection string")
        return v
    
    @validator("redis_url")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
