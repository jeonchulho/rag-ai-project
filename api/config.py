"""Configuration management using Pydantic Settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Enterprise RAG System", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    instance_id: str = Field(default="1", alias="INSTANCE_ID")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    
    # PostgreSQL
    postgres_url: str = Field(
        default="postgresql://user:password@localhost:5432/ragdb",
        alias="POSTGRES_URL"
    )
    
    # Milvus
    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    
    # MinIO
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="rag-files", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    
    # Ollama
    ollama_endpoints: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_ENDPOINTS"
    )
    ollama_model: str = Field(default="qwen2.5-coder:32b", alias="OLLAMA_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    vision_model: str = Field(default="llava", alias="VISION_MODEL")
    
    # Vector dimensions
    text_embedding_dim: int = Field(default=768, alias="TEXT_EMBEDDING_DIM")
    image_embedding_dim: int = Field(default=512, alias="IMAGE_EMBEDDING_DIM")
    
    # Search settings
    default_top_k: int = Field(default=5, alias="DEFAULT_TOP_K")
    max_top_k: int = Field(default=50, alias="MAX_TOP_K")
    
    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        alias="CELERY_RESULT_BACKEND"
    )
    
    # Email
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")
    
    # Performance
    max_workers: int = Field(default=10, alias="MAX_WORKERS")
    request_timeout: int = Field(default=300, alias="REQUEST_TIMEOUT")
    
    @property
    def ollama_endpoint_list(self) -> List[str]:
        """Parse Ollama endpoints from comma-separated string."""
        return [e.strip() for e in self.ollama_endpoints.split(",") if e.strip()]
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
