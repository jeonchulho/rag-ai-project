# Enterprise RAG System

대규모 멀티모달 RAG 시스템 - 동시 500명 이상 지원

## 🎯 주요 기능

- **멀티모달 검색**: 텍스트, 이미지, 문서 통합 검색
- **자연어 처리**: "AI 논문 검색해서 요약본을 홍길동에게 10시에 메일 보내줘" 같은 복잡한 요청 처리
- **스케줄링**: 예약된 시간에 자동으로 액션 실행
- **고가용성**: 로드 밸런싱, 캐싱, 분산 처리
- **확장성**: 수평 확장 가능한 마이크로서비스 아키텍처

## 🏗️ 시스템 아키텍처

```
Load Balancer (Nginx)
    ↓
API Servers (FastAPI) x3
    ↓
Processing Layer
├── Ollama Servers x3 (GPU)
├── Milvus (Vector DB)
├── Redis (Cache/Queue)
└── PostgreSQL (Metadata)
    ↓
Async Workers (Celery)
```

## 🚀 빠른 시작

### 1. 사전 요구사항

- Docker & Docker Compose
- NVIDIA GPU (권장: 3개 이상)
- 16GB+ RAM
- 100GB+ 디스크 공간

### 2. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/jeonchulho/rag-ai-project.git
cd rag-ai-project

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (이메일 설정 등)
```

### 3. 시스템 시작

```bash
# 전체 스택 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api1

# Ollama 모델 다운로드 (최초 1회)
docker exec -it rag-ai-project-ollama1-1 ollama pull qwen2.5-coder:32b
docker exec -it rag-ai-project-ollama1-1 ollama pull nomic-embed-text
docker exec -it rag-ai-project-ollama1-1 ollama pull llava

# 다른 Ollama 서버들도 동일하게
docker exec -it rag-ai-project-ollama2-1 ollama pull qwen2.5-coder:32b
docker exec -it rag-ai-project-ollama3-1 ollama pull qwen2.5-coder:32b
```

### 4. API 테스트

```bash
# Health Check
curl http://localhost/api/v1/health

# 자연어 검색
curl -X POST http://localhost/api/v1/search/natural \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI 논문 검색해서 요약본을 hong@example.com에게 오전 10시에 메일로 보내줘"
  }'
```

## 📁 프로젝트 구조

```
rag-ai-project/
├── docker-compose.yml          # 전체 인프라 정의
├── .env.example                # 환경 변수 템플릿
├── requirements.txt            # Python 의존성
│
├── nginx/                      # 로드 밸런서
│   └── nginx.conf
│
├── api/                        # FastAPI 애플리케이션
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── routers/                # API 엔드포인트
│   ├── services/               # 핵심 서비스
│   └── agents/                 # LangGraph 에이전트
│
├── workers/                    # Celery 워커
│   ├── celery_app.py
│   └── tasks.py
│
├── database/                   # DB 마이그레이션
│   └── migrations/
│
└── tests/                      # 테스트
```

## 🔧 주요 컴포넌트

### API Gateway (FastAPI)
- 3개 인스턴스로 로드 밸런싱
- Rate Limiting
- 캐싱
- 스트리밍 지원

### Vector Database (Milvus)
- 텍스트, 이미지, 문서 별도 컬렉션
- ANN 검색
- 분산 아키텍처 지원

### LLM Layer (Ollama)
- 3개 GPU 서버로 분산
- 로드 밸런싱
- 자동 Failover

### Async Processing (Celery)
- 이메일 전송
- 문서 처리
- 스케줄링

## 📊 모니터링

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔐 보안

- Rate Limiting: 초당 100 요청
- SSL/TLS 지원
- API 키 인증 (선택사항)

## 📈 성능

- **동시 사용자**: 500+
- **응답 시간**: < 2초 (캐시 히트 시)
- **처리량**: 1000+ requests/sec

## 🛠️ 개발

### 로컬 개발 환경

```bash
# API 서버만 실행
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# Celery Worker 실행
cd workers
celery -A celery_app worker --loglevel=info
```

### 테스트

```bash
pytest tests/ -v
```

## 📝 API 문서

시스템 시작 후 http://localhost/docs 에서 Swagger UI를 통해 전체 API 문서를 확인할 수 있습니다.

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License

## 👨‍💻 제작자

jeonchulho

---

**Note**: 이 프로젝트는 프로덕션 환경을 위한 엔터프라이즈급 RAG 시스템입니다. 개발 환경에서는 docker-compose.dev.yml을 사용하세요.
