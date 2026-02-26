"""
Exousía School by Dexos - Application Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Any


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App
    APP_NAME: str = "Exousía School by Dexos"
    APP_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://exousia:exousia123@localhost:5534/exousia_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6481"

    # Weaviate (future)
    WEAVIATE_URL: str = "http://localhost:8087"

    # MinIO S3
    MINIO_ENDPOINT: str = "localhost:9100"
    MINIO_ACCESS_KEY: str = "exousia"
    MINIO_SECRET_KEY: str = "exousia123"
    MINIO_BUCKET: str = "exousia-files"
    MINIO_SECURE: bool = False

    # Biometrics Bridge
    BIOMETRICS_SERVICE_URL: str = "http://exousia-biometrics:9500"

    # Security
    SECRET_KEY: str = "exousia-dev-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()


settings = get_settings()
