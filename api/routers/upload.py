"""파일 업로드 엔드포인트 - 청킹 및 고급 문서 처리"""

import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

from api.models import UploadResponse
from api.services.vector_store import VectorStoreService
from api.services.llm_service import LLMService
from api.services.file_service import FileService
from api.services.embedding_service import EmbeddingService
from api.dependencies import get_vector_store, get_llm_service, get_file_service, get_embedding_service
from api.utils.text_processing import (
    extract_text_from_file,
    smart_chunk,
    extract_keywords,
    clean_text
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload/text", response_model=UploadResponse)
async def upload_text(
    file: UploadFile = File(...),
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    background_tasks: BackgroundTasks = None,
    vector_store: VectorStoreService = Depends(get_vector_store),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    텍스트 문서 업로드 및 청킹 처리
    
    Args:
        file: 텍스트 파일
        chunk_size: 청크 최대 크기 (문자 수)
        chunk_overlap: 청크 간 겹침 크기
        
    Returns:
        업로드 상태 및 문서 ID (부모 ID와 청크 개수 포함)
    """
    try:
        # 부모 문서 ID 생성
        parent_document_id = str(uuid.uuid4())
        
        # 파일 내용 읽기
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # 텍스트 정제
        cleaned_text = clean_text(text_content)
        
        logger.info(f"Processing text document: {file.filename}, length: {len(cleaned_text)} chars")
        
        # 임시 파일 저장
        temp_path = f"/tmp/{parent_document_id}_{file.filename}"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        # MinIO 업로드
        file_url = file_service.upload_file(
            temp_path,
            f"text/{parent_document_id}_{file.filename}",
            content_type=file.content_type or "text/plain"
        )
        
        # 스마트 청킹
        chunks = smart_chunk(cleaned_text, file_type="text", max_chunk_size=chunk_size)
        
        logger.info(f"Split into {len(chunks)} chunks")
        
        # 키워드 추출 (전체 문서에서)
        keywords = extract_keywords(cleaned_text, max_keywords=10)
        
        # 각 청크별로 임베딩 생성 및 저장
        chunk_ids = []
        for chunk_data in chunks:
            chunk_id = f"{parent_document_id}_chunk_{chunk_data['metadata']['chunk_index']}"
            chunk_content = chunk_data['content']
            
            # 임베딩 생성
            embedding = await embedding_service.embed_text(chunk_content)
            
            # Milvus에 저장
            vector_store.insert_text(
                document_id=chunk_id,
                content=chunk_content,
                embedding=embedding,
                metadata={
                    "parent_id": parent_document_id,
                    "chunk_index": chunk_data['metadata']['chunk_index'],
                    "chunk_count": len(chunks),
                    "filename": file.filename,
                    "file_url": file_url,
                    "content_type": file.content_type or "text/plain",
                    "char_start": chunk_data['metadata'].get('char_start', 0),
                    "char_end": chunk_data['metadata'].get('char_end', 0),
                    "word_count": chunk_data['metadata'].get('word_count', 0),
                    "keywords": ",".join(keywords),
                    "chunking_method": chunk_data['metadata'].get('chunking_method', 'smart')
                }
            )
            
            chunk_ids.append(chunk_id)
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        logger.info(f"Uploaded text document: {parent_document_id} with {len(chunks)} chunks")
        
        return UploadResponse(
            document_id=parent_document_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type or "text/plain",
            status="success",
            message=f"Text document uploaded and indexed successfully ({len(chunks)} chunks created)",
            metadata={
                "chunk_count": len(chunks),
                "chunk_ids": chunk_ids[:5],  # 처음 5개만
                "keywords": keywords
            }
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
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    이미지 업로드 및 임베딩 생성
    
    Args:
        file: 이미지 파일
        description: 선택적 이미지 설명
        
    Returns:
        업로드 상태 및 이미지 ID
    """
    try:
        # 이미지 타입 검증
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # 이미지 ID 생성
        image_id = str(uuid.uuid4())
        
        # 파일 내용 읽기
        content = await file.read()
        
        # 임시 파일 저장
        temp_path = f"/tmp/{image_id}_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # MinIO 업로드
        file_url = file_service.upload_file(
            temp_path,
            f"images/{image_id}_{file.filename}",
            content_type=file.content_type
        )
        
        # 설명이 없으면 자동 생성
        if not description:
            description = await llm_service.analyze_image(
                temp_path,
                "Describe this image in detail"
            )
        
        # 이미지 임베딩 생성
        embedding = await embedding_service.embed_image(temp_path)
        
        # Milvus에 저장
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
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        logger.info(f"Uploaded image: {image_id}")
        
        return UploadResponse(
            document_id=image_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            status="success",
            message="Image uploaded and indexed successfully",
            metadata={"description": description}
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
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
    background_tasks: BackgroundTasks = None,
    vector_store: VectorStoreService = Depends(get_vector_store),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    PDF 또는 DOCX 문서 업로드 및 청킹 처리
    
    Args:
        file: 문서 파일 (PDF/DOCX)
        chunk_size: 청크 최대 크기
        chunk_overlap: 청크 간 겹침
        
    Returns:
        업로드 상태 및 문서 ID
    """
    try:
        # 문서 타입 검증
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be PDF or DOCX"
            )
        
        # 부모 문서 ID 생성
        parent_document_id = str(uuid.uuid4())
        
        # 파일 내용 읽기
        content = await file.read()
        
        # 임시 파일 저장
        temp_path = f"/tmp/{parent_document_id}_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Processing document: {file.filename}, size: {len(content)} bytes")
        
        # MinIO 업로드
        file_url = file_service.upload_file(
            temp_path,
            f"documents/{parent_document_id}_{file.filename}",
            content_type=file.content_type
        )
        
        # 파일 타입 결정
        file_extension = file.filename.split('.')[-1].lower()
        file_type = "pdf" if file_extension == "pdf" else "docx"
        
        # 텍스트 추출
        try:
            text_content = extract_text_from_file(temp_path)
            cleaned_text = clean_text(text_content)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from document: {str(e)}"
            )
        
        logger.info(f"Extracted {len(cleaned_text)} characters from document")
        
        # 스마트 청킹
        chunks = smart_chunk(cleaned_text, file_type=file_type, max_chunk_size=chunk_size)
        
        logger.info(f"Split into {len(chunks)} chunks")
        
        # 키워드 추출
        keywords = extract_keywords(cleaned_text, max_keywords=15)
        
        # 각 청크별로 임베딩 생성 및 저장
        chunk_ids = []
        for chunk_data in chunks:
            chunk_id = f"{parent_document_id}_chunk_{chunk_data['metadata']['chunk_index']}"
            chunk_content = chunk_data['content']
            
            # 임베딩 생성
            embedding = await embedding_service.embed_text(chunk_content)
            
            # Milvus에 저장
            vector_store.insert_document(
                document_id=chunk_id,
                content=chunk_content,
                embedding=embedding,
                metadata={
                    "parent_id": parent_document_id,
                    "chunk_index": chunk_data['metadata']['chunk_index'],
                    "chunk_count": len(chunks),
                    "filename": file.filename,
                    "file_url": file_url,
                    "content_type": file.content_type,
                    "file_type": file_type,
                    "char_start": chunk_data['metadata'].get('char_start', 0),
                    "char_end": chunk_data['metadata'].get('char_end', 0),
                    "word_count": chunk_data['metadata'].get('word_count', 0),
                    "keywords": ",".join(keywords),
                    "chunking_method": chunk_data['metadata'].get('chunking_method', 'smart')
                }
            )
            
            chunk_ids.append(chunk_id)
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        logger.info(f"Uploaded document: {parent_document_id} with {len(chunks)} chunks")
        
        return UploadResponse(
            document_id=parent_document_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            status="success",
            message=f"Document uploaded and indexed successfully ({len(chunks)} chunks created)",
            metadata={
                "chunk_count": len(chunks),
                "chunk_ids": chunk_ids[:5],
                "keywords": keywords,
                "file_type": file_type,
                "extracted_text_length": len(cleaned_text)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
