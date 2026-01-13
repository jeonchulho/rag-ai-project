"""Milvus vector database service for similarity search."""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings in Milvus."""
    
    def __init__(self, host: str, port: int):
        """
        Initialize connection to Milvus.
        
        Args:
            host: Milvus server host
            port: Milvus server port
        """
        self.host = host
        self.port = port
        self.collections = {}
        self._connect()
    
    def _connect(self):
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _create_collection_if_not_exists(
        self,
        collection_name: str,
        dimension: int,
        description: str
    ):
        """Create collection if it doesn't exist."""
        if utility.has_collection(collection_name):
            self.collections[collection_name] = Collection(collection_name)
            logger.info(f"Collection '{collection_name}' already exists")
            return
        
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        
        schema = CollectionSchema(fields=fields, description=description)
        collection = Collection(name=collection_name, schema=schema)
        
        # Create IVF_FLAT index for vector field
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        self.collections[collection_name] = collection
        logger.info(f"Created collection '{collection_name}'")
    
    def insert_text(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Insert text document into vector store.
        
        Args:
            document_id: Unique document identifier
            content: Document content
            embedding: Vector embedding
            metadata: Additional metadata
        """
        collection_name = "text_collection"
        self._create_collection_if_not_exists(collection_name, len(embedding), "Text documents")
        
        collection = self.collections[collection_name]
        entities = [
            [document_id],
            [embedding],
            [content],
            [metadata or {}]
        ]
        
        collection.insert(entities)
        collection.flush()
        logger.info(f"Inserted text document: {document_id}")
    
    def insert_image(
        self,
        image_id: str,
        description: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert image into vector store."""
        collection_name = "image_collection"
        self._create_collection_if_not_exists(collection_name, len(embedding), "Images")
        
        collection = self.collections[collection_name]
        entities = [
            [image_id],
            [embedding],
            [description],
            [metadata or {}]
        ]
        
        collection.insert(entities)
        collection.flush()
        logger.info(f"Inserted image: {image_id}")
    
    def insert_document(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert document into vector store."""
        collection_name = "document_collection"
        self._create_collection_if_not_exists(collection_name, len(embedding), "Documents")
        
        collection = self.collections[collection_name]
        entities = [
            [document_id],
            [embedding],
            [content],
            [metadata or {}]
        ]
        
        collection.insert(entities)
        collection.flush()
        logger.info(f"Inserted document: {document_id}")
    
    def search_text(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search text documents by embedding similarity."""
        return self._search("text_collection", query_embedding, top_k, filters)
    
    def search_image(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search images by embedding similarity."""
        return self._search("image_collection", query_embedding, top_k, filters)
    
    def search_documents(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search documents by embedding similarity."""
        return self._search("document_collection", query_embedding, top_k, filters)
    
    def search_all(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search across all collections."""
        results = []
        for collection_name in ["text_collection", "image_collection", "document_collection"]:
            try:
                collection_results = self._search(collection_name, query_embedding, top_k, filters)
                results.extend(collection_results)
            except Exception as e:
                logger.warning(f"Search in {collection_name} failed: {e}")
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Internal search method."""
        if collection_name not in self.collections:
            logger.warning(f"Collection '{collection_name}' not found")
            return []
        
        collection = self.collections[collection_name]
        collection.load()
        
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "content", "metadata"]
        )
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.entity.get("id"),
                    "content": hit.entity.get("content"),
                    "score": 1.0 / (1.0 + hit.distance),  # Convert distance to similarity score
                    "metadata": hit.entity.get("metadata", {}),
                    "document_type": collection_name.replace("_collection", "")
                })
        
        return formatted_results
    
    def close(self):
        """Close Milvus connection."""
        try:
            connections.disconnect(alias="default")
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error disconnecting from Milvus: {e}")
