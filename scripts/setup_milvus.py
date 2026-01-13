#!/usr/bin/env python3
"""Setup Milvus collections with proper schemas."""

import sys
import logging
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_collection(name: str, dimension: int, description: str):
    """Create a Milvus collection."""
    if utility.has_collection(name):
        logger.info(f"Collection '{name}' already exists, dropping...")
        utility.drop_collection(name)
    
    # Define schema
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="metadata", dtype=DataType.JSON)
    ]
    
    schema = CollectionSchema(fields=fields, description=description)
    collection = Collection(name=name, schema=schema)
    
    # Create IVF_FLAT index
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    
    collection.create_index(field_name="embedding", index_params=index_params)
    
    logger.info(f"✓ Created collection '{name}' with dimension {dimension}")
    return collection


def main():
    """Main setup function."""
    try:
        # Connect to Milvus
        logger.info("Connecting to Milvus...")
        connections.connect(
            alias="default",
            host="milvus-standalone",
            port="19530"
        )
        logger.info("✓ Connected to Milvus")
        
        # Create collections
        logger.info("\nCreating collections...")
        
        create_collection(
            name="text_collection",
            dimension=768,
            description="Text documents with embeddings"
        )
        
        create_collection(
            name="image_collection",
            dimension=512,
            description="Images with embeddings"
        )
        
        create_collection(
            name="document_collection",
            dimension=768,
            description="Documents (PDF/DOCX) with embeddings"
        )
        
        # List collections
        collections = utility.list_collections()
        logger.info(f"\nAvailable collections: {collections}")
        
        logger.info("\n✓ Milvus setup completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Setup failed: {e}")
        return 1
    finally:
        try:
            connections.disconnect(alias="default")
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
