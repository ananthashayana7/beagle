"""
Beagle Configuration Module
Centralized settings management using Pydantic
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "Beagle"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # MinIO/S3 Storage
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., env="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="beagle-files", env="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # AI APIs
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    default_ai_model: str = Field(default="gemini-1.5-flash", env="DEFAULT_AI_MODEL")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost", "http://localhost:80", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_execute: str = Field(default="10/minute", env="RATE_LIMIT_EXECUTE")
    rate_limit_chat: str = Field(default="30/minute", env="RATE_LIMIT_CHAT")
    rate_limit_upload: str = Field(default="5/minute", env="RATE_LIMIT_UPLOAD")
    
    # File Upload
    max_file_size_mb: int = Field(default=500, env="MAX_FILE_SIZE_MB")
    allowed_extensions: List[str] = Field(
        default=["csv", "xlsx", "xls", "json", "parquet"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Code Execution
    code_execution_timeout: int = Field(default=30, env="CODE_EXECUTION_TIMEOUT")
    execution_mode: str = Field(default="DOCKER", env="EXECUTION_MODE")  # DOCKER or PROCESS
    allowed_imports: List[str] = Field(
        default=[
            "pandas", "numpy", "scipy", "sklearn", "statsmodels",
            "matplotlib", "seaborn", "plotly", "datetime", "math",
            "statistics", "collections", "itertools", "functools"
        ],
        env="ALLOWED_IMPORTS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in ("allowed_origins", "allowed_extensions", "allowed_imports"):
                return [x.strip() for x in raw_val.split(",")]
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience accessor
settings = get_settings()
