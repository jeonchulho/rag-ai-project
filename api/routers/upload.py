"""File upload endpoints."""

import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from api.models import UploadResponse
from api.services.vector_store import VectorStoreService
from api.services.llm_service import LLMService
from api.services.file_service import FileService
from api.dependencies import get_vector_store, get_llm_service, get_file_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload/text", response_model=UploadResponse)
async def upload_text(
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload text document and generate embeddings.
    
    Args:
        file: Text file to upload
        
    Returns:
        Upload status and document ID
    """
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Upload to MinIO
        temp_path = f"/tmp/{document_id}_{file.filename}"
        with open(temp_path, 'w') as f:
            f.write(text_content)
        
        file_url = file_service.upload_file(
            temp_path,
            f"text/{document_id}_{file.filename}",
            content_type=file.content_type
        )
        
        # Generate embedding
        embedding = await llm_service.embed_text(text_content)
        
        # Store in vector database
        vector_store.insert_text(
            document_id=document_id,
            content=text_content[:1000],  # Store first 1000 chars
            embedding=embedding,
            metadata={
                "filename": file.filename,
                "file_url": file_url,
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"Uploaded text document: {document_id}")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type or "text/plain",
            status="success",
            message="Text document uploaded and indexed successfully"
        )
        
    except Exception as e:
        logger.error(f"Text upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    description: str = "",
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload image and generate embeddings.
    
    Args:
        file: Image file to upload
        description: Optional image description
        
    Returns:
        Upload status and image ID
    """
    try:
        # Validate image type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Save temporary file
        temp_path = f"/tmp/{image_id}_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Upload to MinIO
        file_url = file_service.upload_file(
            temp_path,
            f"images/{image_id}_{file.filename}",
            content_type=file.content_type
        )
        
        # Generate description if not provided
        if not description:
            description = await llm_service.analyze_image(
                temp_path,
                "Describe this image in detail"
            )
        
        # Generate embedding
        embedding = await llm_service.embed_image(temp_path)
        
        # Store in vector database
        vector_store.insert_image(
            image_id=image_id,
            description=description,
            embedding=embedding,
            metadata={
                "filename": file.filename,
                "file_url": file_url,
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"Uploaded image: {image_id}")
        
        return UploadResponse(
            document_id=image_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            status="success",
            message="Image uploaded and indexed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload/document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload PDF or DOCX document and generate embeddings.
    
    Args:
        file: Document file to upload (PDF/DOCX)
        
    Returns:
        Upload status and document ID
    """
    try:
        # Validate document type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be PDF or DOCX"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Save temporary file
        temp_path = f"/tmp/{document_id}_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Upload to MinIO
        file_url = file_service.upload_file(
            temp_path,
            f"documents/{document_id}_{file.filename}",
            content_type=file.content_type
        )
        
        # Extract text content (simplified - would use proper PDF/DOCX parsers in production)
        text_content = f"Document: {file.filename}"
        
        # Generate embedding
        embedding = await llm_service.embed_text(text_content)
        
        # Store in vector database
        vector_store.insert_document(
            document_id=document_id,
            content=text_content,
            embedding=embedding,
            metadata={
                "filename": file.filename,
                "file_url": file_url,
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"Uploaded document: {document_id}")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            status="success",
            message="Document uploaded and indexed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
