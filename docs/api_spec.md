# API 명세서 (예시)

## 문서 업로드
- POST /api/v1/upload/document
  - 파일 업로드 (PDF 등)
  - 반환값: {"document_id": "..."}

## PDF 기반 검색/명령 실행
- POST /api/v1/search
  - 본문: {"query": "aaa.PDF 내용을 요약해서 ..."}
  - 반환값: {"intent": "...", "entities": {...}, "response_text": "...", "scheduled_actions": [...]}

## 상태 확인
- GET /api/v1/status
  - 서버 상태/작업 큐 상태 반환

---