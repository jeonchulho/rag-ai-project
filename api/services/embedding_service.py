"""
임베딩 서비스 - 텍스트/이미지 임베딩 생성 및 관리
"""
import ollama
from sentence_transformers import SentenceTransformer
from PIL import Image
from typing import List, Union, Optional, Dict, Any
import asyncio
import logging
from functools import lru_cache
import hashlib
import numpy as np

from api.config import settings
from api.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    임베딩 생성 서비스
    
    기능:
    - 텍스트 임베딩 (Ollama nomic-embed-text)
    - 이미지 임베딩 (CLIP)
    - 배치 처리
    - 캐싱
    - 로드 밸런싱
    """
    
    def __init__(self):
        self.ollama_endpoints = settings.OLLAMA_ENDPOINTS
        self.current_index = 0
        self.cache = CacheService()
        
        # CLIP 모델 초기화 (이미지 임베딩)
        self._clip_model = None
        
        logger.info(f"EmbeddingService initialized with {len(self.ollama_endpoints)} Ollama endpoints")
    
    @property
    def clip_model(self):
        """CLIP 모델 lazy loading"""
        if self._clip_model is None:
            logger.info("Loading CLIP model...")
            self._clip_model = SentenceTransformer('clip-ViT-B-32')
            logger.info("CLIP model loaded")
        return self._clip_model
    
    def _get_next_endpoint(self) -> str:
        """라운드 로빈 방식으로 다음 Ollama 엔드포인트 선택"""
        endpoint = self.ollama_endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.ollama_endpoints)
        return endpoint
    
    def _generate_cache_key(self, content: str, model: str) -> str:
        """캐시 키 생성"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"embedding:{model}:{content_hash}"
    
    async def embed_text(
        self,
        text: str,
        model: str = None,
        use_cache: bool = True
    ) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            model: 사용할 모델 (기본값: nomic-embed-text)
            use_cache: 캐시 사용 여부
            
        Returns:
            임베딩 벡터 (768차원)
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = await service.embed_text("Hello world")
            >>> len(embedding)
            768
        """
        model = model or settings.EMBEDDING_MODEL
        
        # 캐시 확인
        if use_cache:
            cache_key = self._generate_cache_key(text, model)
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for text embedding")
                return cached
        
        # 임베딩 생성
        endpoint = self._get_next_endpoint()
        
        try:
            logger.debug(f"Generating text embedding using {endpoint}")
            
            client = ollama.Client(host=endpoint)
            response = client.embeddings(
                model=model,
                prompt=text
            )
            
            embedding = response['embedding']
            
            # 캐시 저장
            if use_cache:
                await self.cache.set(cache_key, embedding, ttl=86400)  # 24시간
            
            return embedding
        
        except Exception as e:
            logger.error(f"Text embedding failed on {endpoint}: {e}")
            # 다른 엔드포인트로 재시도
            return await self._retry_text_embedding(text, model, exclude=endpoint)
    
    async def _retry_text_embedding(
        self,
        text: str,
        model: str,
        exclude: str
    ) -> List[float]:
        """임베딩 생성 실패 시 재시도"""
        import random
        
        available_endpoints = [ep for ep in self.ollama_endpoints if ep != exclude]
        
        if not available_endpoints:
            raise Exception("All Ollama endpoints are unavailable")
        
        endpoint = random.choice(available_endpoints)
        
        try:
            client = ollama.Client(host=endpoint)
            response = client.embeddings(
                model=model,
                prompt=text
            )
            return response['embedding']
        
        except Exception as e:
            logger.error(f"Retry text embedding failed on {endpoint}: {e}")
            raise
    
    async def embed_texts_batch(
        self,
        texts: List[str],
        model: str = None,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        여러 텍스트를 배치로 임베딩
        
        Args:
            texts: 임베딩할 텍스트 리스트
            model: 사용할 모델
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
            
        Example:
            >>> texts = ["text 1", "text 2", "text 3"]
            >>> embeddings = await service.embed_texts_batch(texts)
            >>> len(embeddings)
            3
        """
        embeddings = []
        
        # 배치 단위로 처리
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # 병렬 처리
            batch_embeddings = await asyncio.gather(*[
                self.embed_text(text, model)
                for text in batch
            ])
            
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return embeddings
    
    async def embed_image(
        self,
        image_path: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        이미지를 임베딩 벡터로 변환 (CLIP 사용)
        
        Args:
            image_path: 이미지 파일 경로
            use_cache: 캐시 사용 여부
            
        Returns:
            임베딩 벡터 (512차원)
            
        Example:
            >>> embedding = await service.embed_image("dog.jpg")
            >>> len(embedding)
            512
        """
        # 캐시 확인
        if use_cache:
            cache_key = self._generate_cache_key(image_path, "clip")
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for image embedding")
                return cached
        
        try:
            logger.debug(f"Generating image embedding for {image_path}")
            
            # PIL로 이미지 로드
            image = Image.open(image_path)
            
            # CLIP으로 임베딩 생성
            embedding = self.clip_model.encode(image)
            
            # numpy array를 list로 변환
            embedding_list = embedding.tolist()
            
            # 캐시 저장
            if use_cache:
                await self.cache.set(cache_key, embedding_list, ttl=86400)
            
            return embedding_list
        
        except Exception as e:
            logger.error(f"Image embedding failed for {image_path}: {e}")
            raise
    
    async def embed_images_batch(
        self,
        image_paths: List[str],
        batch_size: int = 16
    ) -> List[List[float]]:
        """
        여러 이미지를 배치로 임베딩
        
        Args:
            image_paths: 이미지 경로 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        embeddings = []
        
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            
            # 이미지 로드
            images = [Image.open(path) for path in batch]
            
            # 배치 임베딩 생성
            batch_embeddings = self.clip_model.encode(images)
            
            # numpy array를 list로 변환
            embeddings.extend([emb.tolist() for emb in batch_embeddings])
            
            logger.info(f"Processed image batch {i//batch_size + 1}/{(len(image_paths)-1)//batch_size + 1}")
        
        return embeddings
    
    async def embed_query_for_search(
        self,
        query: str,
        search_type: str = "text"
    ) -> Union[List[float], Dict[str, List[float]]]:
        """
        검색 쿼리를 임베딩으로 변환
        
        Args:
            query: 검색 쿼리
            search_type: "text", "image", "multimodal"
            
        Returns:
            임베딩 벡터 또는 멀티모달 임베딩 딕셔너리
        """
        if search_type == "text":
            return await self.embed_text(query)
        
        elif search_type == "image":
            # 이미지 쿼리의 경우 텍스트를 CLIP 공간으로 변환
            return self.clip_model.encode(query).tolist()
        
        elif search_type == "multimodal":
            # 텍스트와 이미지 모두 생성
            text_embedding = await self.embed_text(query)
            image_embedding = self.clip_model.encode(query).tolist()
            
            return {
                "text": text_embedding,
                "image": image_embedding
            }
        
        else:
            raise ValueError(f"Unknown search_type: {search_type}")
    
    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        metric: str = "cosine"
    ) -> float:
        """
        두 임베딩 간 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩
            metric: "cosine", "euclidean", "dot"
            
        Returns:
            유사도 점수
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        if metric == "cosine":
            # 코사인 유사도
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
        
        elif metric == "euclidean":
            # 유클리드 거리 (거리를 유사도로 변환)
            distance = np.linalg.norm(vec1 - vec2)
            similarity = 1 / (1 + distance)
            return float(similarity)
        
        elif metric == "dot":
            # 내적
            return float(np.dot(vec1, vec2))
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        임베딩 서비스 통계
        
        Returns:
            통계 정보 딕셔너리
        """
        return {
            "ollama_endpoints": len(self.ollama_endpoints),
            "current_endpoint_index": self.current_index,
            "clip_model_loaded": self._clip_model is not None,
            "text_embedding_dim": settings.TEXT_EMBEDDING_DIM,
            "image_embedding_dim": settings.IMAGE_EMBEDDING_DIM
        }
    
    async def warmup(self):
        """
        서비스 워밍업 (모델 로드 및 테스트)
        """
        logger.info("Warming up EmbeddingService...")
        
        # 텍스트 임베딩 테스트
        try:
            test_embedding = await self.embed_text("warmup test", use_cache=False)
            logger.info(f"✓ Text embedding OK (dim: {len(test_embedding)})")
        except Exception as e:
            logger.error(f"✗ Text embedding warmup failed: {e}")
        
        # 이미지 임베딩 테스트 (CLIP 로드)
        try:
            _ = self.clip_model
            logger.info(f"✓ CLIP model loaded")
        except Exception as e:
            logger.error(f"✗ CLIP model load failed: {e}")
        
        logger.info("EmbeddingService warmup complete")


# 싱글톤 인스턴스
_embedding_service_instance = None

def get_embedding_service() -> EmbeddingService:
    """
    EmbeddingService 싱글톤 인스턴스 반환
    
    FastAPI dependency로 사용:
    ```python
    @app.get("/embed")
    async def embed(
        text: str,
        service: EmbeddingService = Depends(get_embedding_service)
    ):
        return await service.embed_text(text)
    ```
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    
    return _embedding_service_instance
