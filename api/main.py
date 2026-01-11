"""Main FastAPI application with middleware and routers."""

import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from api.config import settings
from api.routers import search, upload, action, health

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.version} (Instance {settings.instance_id})")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API prefix: {settings.api_prefix}")
    
    # Initialize services (connections will be created on first use)
    logger.info("API server ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade multimodal RAG system supporting 500+ concurrent users",
    version=settings.version,
    docs_url=f"{settings.api_prefix}/docs" if settings.api_prefix else "/docs",
    redoc_url=f"{settings.api_prefix}/redoc" if settings.api_prefix else "/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json" if settings.api_prefix else "/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging and timing middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    start_time = time.time()
    
    logger.info(f"Request started: {request.method} {request.url.path} (ID: {request_id})")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"(ID: {request_id}) - Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"(ID: {request_id}) - Error: {str(e)} - Time: {process_time:.3f}s"
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred"
        }
    )


# Include routers
app.include_router(
    search.router,
    prefix=settings.api_prefix,
    tags=["search"]
)
app.include_router(
    upload.router,
    prefix=settings.api_prefix,
    tags=["upload"]
)
app.include_router(
    action.router,
    prefix=settings.api_prefix,
    tags=["actions"]
)
app.include_router(
    health.router,
    prefix=settings.api_prefix,
    tags=["health"]
)


# Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="fastapi_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": f"{settings.api_prefix}/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=settings.max_workers,
        log_level="info"
    )
