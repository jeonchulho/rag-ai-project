"""Ollama LLM service with load balancing, failover, and automatic text chunking."""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from itertools import cycle
import ollama

from api.utils.text_processing import (
    chunk_by_tokens,
    truncate_text,
    clean_text,
    estimate_tokens
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama LLM servers with load balancing and smart text handling."""
    
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
        
        # Context window limits (in tokens)
        self.max_context_tokens = 4096  # Most Ollama models
        self.max_prompt_tokens = 3000   # Leave room for response
        
        logger.info(f"LLM service initialized with {len(ollama_endpoints)} endpoints")
    
    def _get_next_endpoint(self) -> str:
        """Get next endpoint using round-robin."""
        return next(self.endpoint_cycle)
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        auto_truncate: bool = True
    ) -> str:
        """
        Generate text using Ollama with automatic failover and prompt truncation.
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if not specified)
            max_retries: Maximum number of retry attempts
            auto_truncate: Automatically truncate long prompts
            
        Returns:
            Generated text
        """
        model = model or self.model_name
        
        # Check prompt length and truncate if necessary
        prompt_tokens = estimate_tokens(prompt)
        if auto_truncate and prompt_tokens > self.max_prompt_tokens:
            logger.warning(f"Prompt too long ({prompt_tokens} tokens), truncating to {self.max_prompt_tokens}")
            # Convert tokens back to approximate characters
            max_chars = self.max_prompt_tokens * 4
            prompt = truncate_text(prompt, max_length=max_chars, suffix="\n\n[... text truncated ...]")
        
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
        Summarize text content with automatic chunking for long texts.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in characters
            
        Returns:
            Summary text
        """
        # Clean input text
        cleaned_text = clean_text(text)
        
        # Estimate tokens
        estimated_tokens = estimate_tokens(cleaned_text)
        
        logger.info(f"Summarizing text: {len(cleaned_text)} chars, ~{estimated_tokens} tokens")
        
        # If text fits in context window, summarize directly
        if estimated_tokens <= self.max_prompt_tokens:
            prompt = f"""Summarize the following text in approximately {max_length} characters or less. 
Be concise but capture the main points.

Text:
{cleaned_text}

Summary:"""
            
            return await self.generate(prompt)
        
        # Text too long - chunk and summarize each chunk
        logger.info(f"Text too long, chunking for summarization")
        
        # Chunk with 512 tokens per chunk (approx 2048 chars)
        chunks = chunk_by_tokens(cleaned_text, max_tokens=512, overlap_tokens=50)
        
        logger.info(f"Created {len(chunks)} chunks for summarization")
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data['content']
            chunk_prompt = f"""Summarize this text section concisely:

{chunk_text}

Summary:"""
            
            try:
                chunk_summary = await self.generate(chunk_prompt)
                chunk_summaries.append(chunk_summary)
                logger.info(f"Summarized chunk {i+1}/{len(chunks)}")
            except Exception as e:
                logger.error(f"Failed to summarize chunk {i}: {e}")
                # Continue with other chunks
                continue
        
        if not chunk_summaries:
            raise Exception("Failed to summarize any chunks")
        
        # Combine chunk summaries
        combined_summary = "\n\n".join(chunk_summaries)
        
        # If combined summary is still too long, summarize again
        if estimate_tokens(combined_summary) > self.max_prompt_tokens:
            final_prompt = f"""Create a final comprehensive summary from these section summaries (max {max_length} characters):

{combined_summary}

Final Summary:"""
            
            return await self.generate(final_prompt)
        
        # Final summary of all chunks
        final_prompt = f"""Create a comprehensive summary from these section summaries (max {max_length} characters):

{combined_summary}

Final Summary:"""
        
        return await self.generate(final_prompt)
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text with automatic truncation for long texts.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of extracted entities
        """
        # Truncate if too long
        if estimate_tokens(text) > self.max_prompt_tokens:
            text = truncate_text(text, max_length=self.max_prompt_tokens * 4)
        
        prompt = f"""Extract named entities from the following text. 
Return a JSON object with categories: persons, organizations, locations, dates, emails.

Text:
{text}

Entities (JSON):"""
        
        try:
            response = await self.generate(prompt, auto_truncate=False)  # Already truncated
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
        # Clean query
        cleaned_query = clean_text(query)
        
        prompt = f"""Analyze this user query and extract:
1. Primary intent (search, summarize, email, schedule, etc.)
2. Search keywords if applicable
3. Action details if applicable
4. Time/schedule information if mentioned

Query: {cleaned_query}

Response (JSON format):"""
        
        try:
            response = await self.generate(prompt)
            import json
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"Intent parsing failed: {e}")
            return {"intent": "search", "keywords": cleaned_query}
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get LLM service statistics.
        
        Returns:
            Service statistics dictionary
        """
        return {
            "endpoints": len(self.ollama_endpoints),
            "model": self.model_name,
            "embedding_model": self.embedding_model,
            "vision_model": self.vision_model,
            "max_context_tokens": self.max_context_tokens,
            "max_prompt_tokens": self.max_prompt_tokens
        }
