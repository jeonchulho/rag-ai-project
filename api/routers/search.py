"""Search API endpoints."""

import time
import logging
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status

from api.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    NaturalLanguageRequest,
    NaturalLanguageResponse,
    SearchType
)
from api.services.cache_service import CacheService
from api.services.vector_store import VectorStoreService
from api.services.llm_service import LLMService
from api.agents.search_agent import SearchAgent
from api.dependencies import (
    get_cache_service,
    get_vector_store,
    get_llm_service,
    get_settings
)
from api.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
):
    """
    Basic search endpoint for text, images, or documents.
    
    Args:
        request: Search request with query and parameters
        
    Returns:
        Search results with similarity scores
    """
    start_time = time.time()
    
    # Generate cache key
    cache_key = hashlib.md5(
        f"{request.query}:{request.search_type}:{request.top_k}".encode()
    ).hexdigest()
    
    # Check cache
    cached_result = cache.get("search", cache_key)
    if cached_result:
        logger.info(f"Cache hit for query: {request.query}")
        return SearchResponse(**cached_result)
    
    try:
        # Generate query embedding
        query_embedding = await llm_service.embed_text(request.query)
        
        # Search based on type
        if request.search_type == SearchType.TEXT:
            results = vector_store.search_text(query_embedding, request.top_k, request.filters)
        elif request.search_type == SearchType.IMAGE:
            results = vector_store.search_image(query_embedding, request.top_k, request.filters)
        elif request.search_type == SearchType.DOCUMENT:
            results = vector_store.search_documents(query_embedding, request.top_k, request.filters)
        else:  # ALL
            results = vector_store.search_all(query_embedding, request.top_k, request.filters)
        
        # Format response
        search_results = [SearchResult(**r) for r in results]
        execution_time = time.time() - start_time
        
        response = SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            search_type=request.search_type.value,
            execution_time=execution_time
        )
        
        # Cache result
        cache.set("search", cache_key, response.dict(), ttl=settings.cache_ttl)
        
        logger.info(f"Search completed in {execution_time:.3f}s: {len(search_results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/search/natural", response_model=NaturalLanguageResponse)
async def natural_language_search(
    request: NaturalLanguageRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
):
    """
    Natural language query processing with intent detection and action scheduling.
    
    Handles complex queries like:
    "Search AI papers, summarize them, and email the summary to hong@example.com at 10 AM"
    
    Args:
        request: Natural language query request
        
    Returns:
        Processed response with search results and scheduled actions
    """
    start_time = time.time()
    
    try:
        # Use search agent to process natural language query
        agent = SearchAgent(llm_service, vector_store, cache)
        result = await agent.process_natural_language(request.query, request.context or {})
        
        execution_time = time.time() - start_time
        result["execution_time"] = execution_time
        
        logger.info(f"Natural language query processed in {execution_time:.3f}s")
        return NaturalLanguageResponse(**result)
        
    except Exception as e:
        logger.error(f"Natural language processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Natural language processing failed: {str(e)}"
        )


@router.get("/search/similar/{document_id}", response_model=SearchResponse)
async def find_similar(
    document_id: str,
    top_k: int = 5,
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
):
    """
    Find similar documents based on document ID.
    
    Args:
        document_id: ID of the reference document
        top_k: Number of similar documents to return
        
    Returns:
        Similar documents
    """
    start_time = time.time()
    
    # Check cache
    cache_key = f"{document_id}:{top_k}"
    cached_result = cache.get("similar", cache_key)
    if cached_result:
        return SearchResponse(**cached_result)
    
    try:
        # In a real implementation, we would fetch the document embedding
        # For now, we'll return an empty result
        execution_time = time.time() - start_time
        
        response = SearchResponse(
            results=[],
            total=0,
            query=f"similar_to:{document_id}",
            search_type="similarity",
            execution_time=execution_time
        )
        
        # Cache result
        cache.set("similar", cache_key, response.dict(), ttl=settings.cache_ttl)
        
        return response
        
    except Exception as e:
        logger.error(f"Similar search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar search failed: {str(e)}"
        )
