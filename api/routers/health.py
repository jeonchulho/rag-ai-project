"""Health check endpoints."""

import time
import logging
from fastapi import APIRouter, Depends
from typing import List

from api.models import HealthResponse, ServiceHealth
from api.config import Settings
from api.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Overall system health check.
    
    Returns:
        System health status
    """
    services: List[ServiceHealth] = []
    overall_status = "healthy"
    
    # Check Redis
    try:
        import redis
        start = time.time()
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        r.close()
        response_time = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="Redis",
            status="healthy",
            response_time=response_time
        ))
    except Exception as e:
        services.append(ServiceHealth(
            name="Redis",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    # Check PostgreSQL
    try:
        from sqlalchemy import create_engine
        start = time.time()
        engine = create_engine(settings.postgres_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        response_time = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="PostgreSQL",
            status="healthy",
            response_time=response_time
        ))
        engine.dispose()
    except Exception as e:
        services.append(ServiceHealth(
            name="PostgreSQL",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    # Check Milvus
    try:
        from pymilvus import connections, utility
        start = time.time()
        connections.connect(
            alias="health_check",
            host=settings.milvus_host,
            port=settings.milvus_port
        )
        utility.list_collections(using="health_check")
        connections.disconnect(alias="health_check")
        response_time = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="Milvus",
            status="healthy",
            response_time=response_time
        ))
    except Exception as e:
        services.append(ServiceHealth(
            name="Milvus",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    # Check Ollama
    try:
        import httpx
        endpoint = settings.ollama_endpoint_list[0]
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{endpoint}/api/tags", timeout=5.0)
            response.raise_for_status()
        response_time = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="Ollama",
            status="healthy",
            response_time=response_time
        ))
    except Exception as e:
        services.append(ServiceHealth(
            name="Ollama",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.version,
        instance_id=settings.instance_id,
        services=services
    )


@router.get("/health/services", response_model=List[ServiceHealth])
async def service_health(settings: Settings = Depends(get_settings)):
    """
    Individual service health status.
    
    Returns:
        List of service health statuses
    """
    response = await health_check(settings)
    return response.services
