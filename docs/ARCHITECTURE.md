# System Architecture

## Overview

The Enterprise RAG System is a production-ready, scalable multimodal retrieval-augmented generation platform designed to support 500+ concurrent users. The system leverages a microservices architecture with multiple redundant components for high availability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Applications                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx Load Balancer                          │
│              (Round-robin, Rate Limiting)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │ API 1  │      │ API 2  │      │ API 3  │
    │FastAPI │      │FastAPI │      │FastAPI │
    └───┬────┘      └───┬────┘      └───┬────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        ▼               ▼               ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
   │  Redis  │    │Postgres │    │ Milvus  │    │  MinIO   │
   │ Cache   │    │Metadata │    │ Vectors │    │  Files   │
   └─────────┘    └─────────┘    └─────────┘    └──────────┘
                                       ▲
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                   ┌─────────┐   ┌─────────┐   ┌─────────┐
                   │Ollama 1 │   │Ollama 2 │   │Ollama 3 │
                   │ GPU-0   │   │ GPU-1   │   │ GPU-2   │
                   └─────────┘   └─────────┘   └─────────┘
                        ▲
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Celery   │   │ Celery   │   │  Celery  │
   │Worker 1  │   │Worker 2  │   │   Beat   │
   └──────────┘   └──────────┘   └──────────┘
```

## Core Components

### 1. Load Balancer (Nginx)

**Purpose**: Distribute incoming requests across API servers

**Features**:
- Round-robin load balancing with least_conn strategy
- Rate limiting (100 req/s per IP)
- WebSocket support for streaming responses
- Health check monitoring
- SSL/TLS termination (production)

**Configuration**: `/nginx/nginx.conf`

### 2. API Layer (FastAPI)

**Purpose**: Handle HTTP requests and coordinate services

**Components**:
- **Routers**: Separate endpoints for search, upload, actions, health
- **Services**: LLM, Vector Store, Cache, File Storage
- **Agents**: LangGraph-based workflow orchestration
- **Middleware**: CORS, logging, error handling, metrics

**Scaling**: 3 instances, horizontally scalable

**Port Mapping**:
- API 1: 8000
- API 2: 8001
- API 3: 8002

### 3. Vector Database (Milvus)

**Purpose**: Store and search vector embeddings

**Collections**:
- `text_collection`: Text documents (768-dim)
- `image_collection`: Images (512-dim)
- `document_collection`: PDF/DOCX documents (768-dim)

**Index**: IVF_FLAT with L2 distance metric

**Dependencies**:
- etcd: Metadata storage
- MinIO: Object storage

### 4. LLM Layer (Ollama)

**Purpose**: Generate embeddings and text completions

**Models**:
- `qwen2.5-coder:32b`: Text generation
- `nomic-embed-text`: Text embeddings
- `llava`: Image analysis

**Scaling**: 3 GPU-backed instances with round-robin load balancing

**Port Mapping**:
- Ollama 1: 11434 (GPU 0)
- Ollama 2: 11435 (GPU 1)
- Ollama 3: 11436 (GPU 2)

### 5. Cache Layer (Redis)

**Purpose**: High-speed caching and message queue

**Use Cases**:
- Search result caching
- Session management
- Celery broker/backend
- Rate limiting state

**Data Structures**:
- String: Simple key-value cache
- Hash: Complex objects
- Sorted Set: Time-based operations

### 6. Database (PostgreSQL)

**Purpose**: Persistent metadata storage

**Tables**:
- `users`: User accounts
- `documents`: Document metadata
- `actions`: Scheduled actions
- `task_history`: Task execution logs

**Features**:
- JSONB for flexible metadata
- Triggers for auto-updating timestamps
- Indexes on frequent query fields

### 7. Worker Layer (Celery)

**Purpose**: Asynchronous task processing

**Workers**:
- Worker 1: Email queue
- Worker 2: Processing & summarization queue

**Tasks**:
- `send_email_task`: SMTP email sending
- `summarize_content_task`: Content summarization
- `process_document_task`: Document processing
- `cleanup_old_data_task`: Periodic maintenance

**Beat Scheduler**: Periodic task scheduling (daily cleanup at 2 AM)

### 8. Monitoring (Prometheus & Grafana)

**Purpose**: System observability

**Metrics**:
- Request rate and latency
- Error rates
- Active connections
- Cache hit rates
- Vector search performance

**Dashboards**:
- System overview
- API performance
- Resource utilization

## Data Flow

### Search Request Flow

1. Client sends search query to Nginx
2. Nginx routes to available API server
3. API checks cache (Redis)
4. If cache miss:
   - Generate embedding using Ollama
   - Search vectors in Milvus
   - Format results
   - Cache results
5. Return results to client

### Upload Flow

1. Client uploads file to API
2. File saved temporarily
3. Upload to MinIO for permanent storage
4. Generate embedding using Ollama
5. Store embedding in Milvus
6. Store metadata in PostgreSQL
7. Return document ID to client

### Natural Language Processing Flow

1. Client sends NL query
2. Search Agent (LangGraph) workflow:
   - Analyze intent
   - Extract entities (email, time, keywords)
   - Execute search
   - Summarize results (if requested)
   - Schedule actions (if requested)
3. Return comprehensive response

### Email Scheduling Flow

1. Extract email and schedule from query
2. Create Celery task with ETA
3. Store action in PostgreSQL
4. At scheduled time, worker executes task
5. Update task status in database

## Security Considerations

### Network Security
- Internal service network isolation
- External traffic through Nginx only
- Rate limiting to prevent abuse

### Data Security
- Environment variables for secrets
- No hardcoded credentials
- Prepared statements prevent SQL injection

### API Security
- Input validation with Pydantic
- CORS configuration
- Request ID tracking
- Error message sanitization

## Scalability Strategy

### Horizontal Scaling
- Add more API instances
- Add more Ollama servers
- Add more Celery workers

### Vertical Scaling
- Increase GPU memory for larger models
- Increase RAM for caching
- SSD storage for faster I/O

### Database Scaling
- Read replicas for PostgreSQL
- Milvus distributed deployment
- Redis Cluster for high availability

## High Availability

### Redundancy
- 3 API servers
- 3 Ollama servers
- 2 Celery workers

### Health Checks
- Nginx monitors API health
- Docker health checks
- Prometheus alerts

### Failover
- Automatic retry with exponential backoff
- Ollama endpoint rotation
- Graceful degradation

## Performance Optimization

### Caching Strategy
- Search results: 1 hour TTL
- User sessions: 24 hour TTL
- Frequent queries: Pre-warmed cache

### Connection Pooling
- PostgreSQL: 10 connections per instance
- Redis: 50 connections per instance

### Batch Operations
- Bulk embedding generation
- Batch vector insertion
- Parallel search across collections

## Monitoring & Observability

### Metrics
- System: CPU, memory, disk, network
- Application: Request rate, latency, errors
- Business: Searches, uploads, emails sent

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request ID correlation

### Alerting
- High error rate
- Service unavailability
- Resource exhaustion

## Technology Stack

- **API Framework**: FastAPI 0.104.1
- **LLM Framework**: LangChain 0.1.0, LangGraph 0.0.20
- **Vector Database**: Milvus 2.3.3
- **Cache**: Redis 7
- **Database**: PostgreSQL 15
- **LLM Server**: Ollama
- **Task Queue**: Celery 5.3.4
- **Load Balancer**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Storage**: MinIO
- **Container**: Docker + Docker Compose

## Future Enhancements

1. **Authentication & Authorization**: JWT-based user authentication
2. **Multi-tenancy**: Isolated data per organization
3. **Streaming Responses**: Server-sent events for real-time updates
4. **Advanced RAG**: Hybrid search, re-ranking, query expansion
5. **Model Fine-tuning**: Domain-specific model customization
6. **Kubernetes Deployment**: Production-grade orchestration
7. **GraphQL API**: Alternative to REST
8. **WebSocket Support**: Bidirectional communication
