"""Redis cache service for high-performance caching."""

import json
import logging
from typing import Any, Optional
import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching data in Redis."""
    
    def __init__(self, redis_url: str):
        """
        Initialize cache service with Redis connection.
        
        Args:
            redis_url: Redis connection URL
        """
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            decode_responses=True
        )
        self.redis_client = redis.Redis(connection_pool=self.pool)
        logger.info("Cache service initialized")
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{namespace}:{key}"
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            cache_key = self._make_key(namespace, key)
            value = self.redis_client.get(cache_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._make_key(namespace, key)
            serialized = json.dumps(value)
            if ttl:
                self.redis_client.setex(cache_key, ttl, serialized)
            else:
                self.redis_client.set(cache_key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._make_key(namespace, key)
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            cache_key = self._make_key(namespace, key)
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Cache exists check error: {e}")
            return False
    
    def batch_get(self, namespace: str, keys: list) -> dict:
        """Get multiple values from cache."""
        try:
            cache_keys = [self._make_key(namespace, k) for k in keys]
            values = self.redis_client.mget(cache_keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Batch get error: {e}")
            return {}
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
            self.pool.disconnect()
            logger.info("Cache service closed")
        except Exception as e:
            logger.error(f"Error closing cache service: {e}")
