"""Configuration management for Skill Management Center.

This module provides centralized configuration management using
environment variables and Pydantic settings.
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Skill Management Center"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/skill_management"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 100
    REDIS_SOCKET_TIMEOUT: int = 5

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600

    # File Storage
    UPLOAD_DIR: str = "/var/lib/skill-management/uploads"
    MAX_FILE_SIZE: str = "100MB"
    ALLOWED_EXTENSIONS: List[str] = [".yaml", ".yml", ".json", ".zip"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False
    LOG_FORMAT: str = "json"

    # Monitoring
    METRICS_ENABLED: bool = True
    TRACING_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 60

    # Skill Management
    DEFAULT_SKILL_VERSION: str = "1.0.0"
    MAX_SKILL_VERSIONS: int = 100
    SKILL_AUTO_SAVE_INTERVAL: int = 30
    SKILL_MAX_CONTENT_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Analytics
    ANALYTICS_RETENTION_DAYS: int = 365
    ANALYTICS_BATCH_SIZE: int = 1000

    # Import/Export
    IMPORT_BATCH_SIZE: int = 100
    EXPORT_BATCH_SIZE: int = 100
    MAX_CONCURRENT_IMPORTS: int = 5
    MAX_CONCURRENT_EXPORTS: int = 5

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Validate secret key."""
        if v == "your-secret-key-change-in-production":
            return v
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
