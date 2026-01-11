"""Embedding service placeholder for future expansion."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings.
    
    Currently delegates to LLMService, but can be extended
    to use dedicated embedding models or services.
    """
    
    def __init__(self):
        """Initialize embedding service."""
        logger.info("Embedding service initialized")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate text embedding."""
        # This is a placeholder - actual implementation should use LLMService
        raise NotImplementedError("Use LLMService.embed_text() instead")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError("Use LLMService.embed_text() in batch")
