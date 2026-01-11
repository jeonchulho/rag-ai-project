"""Dependency injection for FastAPI."""

from typing import Generator
from functools import lru_cache

from api.config import Settings, settings
from api.services.cache_service import CacheService
from api.services.vector_store import VectorStoreService
from api.services.llm_service import LLMService
from api.services.file_service import FileService


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)."""
    return settings


def get_cache_service() -> Generator[CacheService, None, None]:
    """Get cache service instance."""
    service = CacheService(settings.redis_url)
    try:
        yield service
    finally:
        service.close()


def get_vector_store() -> Generator[VectorStoreService, None, None]:
    """Get vector store service instance."""
    service = VectorStoreService(
        host=settings.milvus_host,
        port=settings.milvus_port
    )
    try:
        yield service
    finally:
        service.close()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService(
        ollama_endpoints=settings.ollama_endpoint_list,
        model_name=settings.ollama_model,
        embedding_model=settings.embedding_model,
        vision_model=settings.vision_model
    )


def get_file_service() -> FileService:
    """Get file service instance."""
    return FileService(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket_name=settings.minio_bucket,
        secure=settings.minio_secure
    )
