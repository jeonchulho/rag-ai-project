"""텍스트 처리 유틸리티 - 고급 청킹 및 문서 파싱"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    텍스트 정제 및 정규화
    
    Args:
        text: 입력 텍스트
        
    Returns:
        정제된 텍스트
    """
    # 여러 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    
    # 특수문자 제거 (구두점은 유지)
    text = re.sub(r'[^\w\s.,!?;:\'-]', '', text)
    
    return text.strip()


def chunk_text_advanced(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separator: str = "\n\n"
) -> List[Dict[str, Any]]:
    """
    고급 텍스트 청킹 - 의미 단위 보존
    
    LangChain의 RecursiveCharacterTextSplitter 스타일 구현
    
    Args:
        text: 입력 텍스트
        chunk_size: 청크 최대 크기 (문자 수)
        chunk_overlap: 청크 간 겹침 크기
        separator: 우선 분할 구분자
        
    Returns:
        청크 리스트 (메타데이터 포함)
    """
    if len(text) <= chunk_size:
        return [{
            "content": text,
            "metadata": {
                "chunk_index": 0,
                "char_start": 0,
                "char_end": len(text),
                "word_count": len(text.split())
            }
        }]
    
    chunks = []
    
    # 분할 우선순위 (의미 단위 보존)
    separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
    
    def _split_text(text: str, separators: List[str]) -> List[str]:
        """재귀적으로 텍스트 분할"""
        if not separators:
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
        
        separator = separators[0]
        splits = text.split(separator) if separator else [text]
        
        result = []
        current_chunk = ""
        
        for split in splits:
            if len(split) > chunk_size:
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = ""
                result.extend(_split_text(split, separators[1:]))
            else:
                if len(current_chunk) + len(split) + len(separator) <= chunk_size:
                    current_chunk += (separator if current_chunk else "") + split
                else:
                    if current_chunk:
                        result.append(current_chunk)
                    current_chunk = split
        
        if current_chunk:
            result.append(current_chunk)
        
        return result
    
    raw_chunks = _split_text(text, separators)
    
    # 겹침 처리 및 메타데이터 추가
    char_position = 0
    for idx, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue
        
        if idx > 0 and chunk_overlap > 0:
            prev_chunk = raw_chunks[idx - 1]
            overlap_text = prev_chunk[-chunk_overlap:].strip()
            chunk_text = overlap_text + " " + chunk_text
        
        chunks.append({
            "content": chunk_text,
            "metadata": {
                "chunk_index": idx,
                "char_start": char_position,
                "char_end": char_position + len(chunk_text),
                "word_count": len(chunk_text.split()),
                "char_count": len(chunk_text)
            }
        })
        
        char_position += len(chunk_text)
    
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


def extract_text_from_pdf(file_path: str) -> str:
    """PDF 파일에서 텍스트 추출"""
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise


def extract_text_from_docx(file_path: str) -> str:
    """DOCX 파일에서 텍스트 추출"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs).strip()
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise


def extract_text_from_file(file_path: str) -> str:
    """파일 확장자에 따라 자동 텍스트 추출"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def smart_chunk(text: str, file_type: str = "text", max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """파일 타입과 크기에 따라 최적의 청킹 방법 선택"""
    if len(text) <= max_chunk_size:
        return [{
            "content": text,
            "metadata": {"chunk_index": 0, "char_count": len(text), "chunking_method": "none"}
        }]
    
    chunks = chunk_text_advanced(text, max_chunk_size, max_chunk_size // 5)
    for chunk in chunks:
        chunk["metadata"]["chunking_method"] = "advanced"
    return chunks


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """키워드 추출"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = {}
    
    for word in words:
        if len(word) > 3 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:max_keywords]]


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """텍스트 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
