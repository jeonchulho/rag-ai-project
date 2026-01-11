"""Ollama LLM service with load balancing and failover."""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from itertools import cycle
import ollama

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama LLM servers with load balancing."""
    
    def __init__(
        self,
        ollama_endpoints: List[str],
        model_name: str,
        embedding_model: str,
        vision_model: str
    ):
        """
        Initialize LLM service with multiple Ollama endpoints.
        
        Args:
            ollama_endpoints: List of Ollama server URLs
            model_name: Default model name for text generation
            embedding_model: Model for text embeddings
            vision_model: Model for image analysis
        """
        self.ollama_endpoints = ollama_endpoints
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.vision_model = vision_model
        self.endpoint_cycle = cycle(ollama_endpoints)
        logger.info(f"LLM service initialized with {len(ollama_endpoints)} endpoints")
    
    def _get_next_endpoint(self) -> str:
        """Get next endpoint using round-robin."""
        return next(self.endpoint_cycle)
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate text using Ollama with automatic failover.
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if not specified)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated text
        """
        model = model or self.model_name
        last_error = None
        
        for attempt in range(max_retries):
            endpoint = self._get_next_endpoint()
            try:
                client = ollama.Client(host=endpoint)
                response = client.generate(model=model, prompt=prompt)
                return response['response']
            except Exception as e:
                last_error = e
                logger.warning(f"Generation failed on {endpoint} (attempt {attempt + 1}): {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        
        raise Exception(f"All Ollama endpoints failed after {max_retries} attempts: {last_error}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate text embeddings.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            endpoint = self._get_next_endpoint()
            client = ollama.Client(host=endpoint)
            response = client.embeddings(model=self.embedding_model, prompt=text)
            return response['embedding']
        except Exception as e:
            logger.error(f"Text embedding failed: {e}")
            raise
    
    async def embed_image(self, image_path: str) -> List[float]:
        """
        Generate image embeddings using CLIP.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector
        """
        try:
            # For now, using text embedding as placeholder
            # In production, use proper CLIP model
            return await self.embed_text(f"image:{image_path}")
        except Exception as e:
            logger.error(f"Image embedding failed: {e}")
            raise
    
    async def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Analyze image using vision model (LLaVA).
        
        Args:
            image_path: Path to image file
            prompt: Question or instruction about the image
            
        Returns:
            Analysis result
        """
        try:
            endpoint = self._get_next_endpoint()
            client = ollama.Client(host=endpoint)
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = client.generate(
                model=self.vision_model,
                prompt=prompt,
                images=[image_data]
            )
            return response['response']
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise
    
    async def summarize(self, text: str, max_length: int = 500) -> str:
        """
        Summarize text content.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following text in approximately {max_length} characters or less. 
Be concise but capture the main points.

Text:
{text}

Summary:"""
        
        return await self.generate(prompt)
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of extracted entities
        """
        prompt = f"""Extract named entities from the following text. 
Return a JSON object with categories: persons, organizations, locations, dates, emails.

Text:
{text}

Entities (JSON):"""
        
        try:
            response = await self.generate(prompt)
            # Parse JSON response
            import json
            entities = json.loads(response.strip())
            return entities
        except Exception as e:
            logger.warning(f"Entity extraction parsing failed: {e}")
            return {
                "persons": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "emails": []
            }
    
    async def parse_intent(self, query: str) -> Dict[str, Any]:
        """
        Parse user intent from natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with intent and parameters
        """
        prompt = f"""Analyze this user query and extract:
1. Primary intent (search, summarize, email, schedule, etc.)
2. Search keywords if applicable
3. Action details if applicable
4. Time/schedule information if mentioned

Query: {query}

Response (JSON format):"""
        
        try:
            response = await self.generate(prompt)
            import json
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"Intent parsing failed: {e}")
            return {"intent": "search", "keywords": query}
