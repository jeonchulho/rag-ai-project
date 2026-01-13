# Deployment Guide

## Prerequisites

### Hardware Requirements

**Minimum** (Development):
- CPU: 8 cores
- RAM: 16 GB
- GPU: 1x NVIDIA GPU with 8GB VRAM
- Storage: 50 GB

**Recommended** (Production):
- CPU: 24 cores (3x8 for Ollama servers)
- RAM: 64 GB
- GPU: 3x NVIDIA GPU with 24GB+ VRAM each
- Storage: 500 GB SSD

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker Runtime (for GPU support)
- Git

### Network Requirements

- Ports 80, 443 (external access)
- Internal network for service communication

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/jeonchulho/rag-ai-project.git
cd rag-ai-project
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```bash
# Email settings (required for email actions)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com

# Optional: Override defaults
OLLAMA_MODEL=qwen2.5-coder:32b
TEXT_EMBEDDING_DIM=768
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Initialize Models

Wait for all services to be healthy, then:

```bash
# Pull Ollama models (this may take 30+ minutes)
./scripts/init_models.sh

# Setup Milvus collections
docker-compose exec api1 python /app/scripts/setup_milvus.py
```

### 5. Verify Installation

```bash
# Run health check
./scripts/health_check.sh

# Test API
curl http://localhost/api/v1/health
```

Access Swagger UI: http://localhost/docs

---

## Production Deployment

### SSL/TLS Configuration

1. Obtain SSL certificates (Let's Encrypt recommended):

```bash
certbot certonly --standalone -d your-domain.com
```

2. Update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration
}
```

3. Mount certificates in docker-compose.yml:

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

### Environment Variables

Production environment variables:

```bash
# Application
APP_NAME=Enterprise RAG System
VERSION=1.0.0
DEBUG=False

# Database (use strong passwords!)
POSTGRES_PASSWORD=<strong-password>
MINIO_SECRET_KEY=<strong-secret>

# Email (production SMTP)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>

# Performance
MAX_WORKERS=10
REQUEST_TIMEOUT=300
CACHE_TTL=3600
```

### Security Hardening

1. **Change default passwords**:
   - PostgreSQL: Update `POSTGRES_PASSWORD`
   - MinIO: Update `MINIO_SECRET_KEY`

2. **Enable firewall**:

```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # Block direct PostgreSQL access
ufw enable
```

3. **Update docker-compose.yml**:

```yaml
# Remove external port mappings for internal services
postgres:
  ports: []  # Remove - "5432:5432"

redis:
  ports: []  # Remove - "6379:6379"
```

### Monitoring Setup

1. **Configure Prometheus retention**:

```yaml
prometheus:
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.retention.time=30d'
    - '--storage.tsdb.path=/prometheus'
```

2. **Setup Grafana**:

```bash
# Access Grafana
http://your-domain.com:3000

# Default credentials
Username: admin
Password: admin

# Import dashboard
Configuration > Data Sources > Add Prometheus
URL: http://prometheus:9090

Import dashboard from monitoring/grafana/dashboards/rag-system.json
```

3. **Configure alerts** (create `monitoring/alerts.yml`):

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        annotations:
          summary: "High error rate detected"
```

### Backup Strategy

1. **Database backup**:

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U user ragdb > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U user ragdb < backup_20240111.sql
```

2. **Vector database backup**:

```bash
# Backup Milvus data
docker-compose exec milvus-standalone /milvus/tools/backup.sh

# Backup MinIO files
docker-compose exec minio mc mirror /minio_data /backup
```

3. **Automated backups**:

Create `/etc/cron.daily/rag-backup`:

```bash
#!/bin/bash
BACKUP_DIR=/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose -f /path/to/docker-compose.yml exec -T postgres \
  pg_dump -U user ragdb > $BACKUP_DIR/postgres.sql

# Backup volumes
docker run --rm -v rag-ai-project_milvus-data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/milvus.tar.gz /data

# Remove backups older than 30 days
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

### Scaling

#### Horizontal Scaling

**Add more API servers**:

```yaml
api4:
  build: ./api
  environment:
    - INSTANCE_ID=4
    # ... same as api1-3
  networks:
    - rag-network
```

Update `nginx/nginx.conf`:

```nginx
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
    server api4:8000;  # Add new server
}
```

**Add more Ollama servers**:

```yaml
ollama4:
  image: ollama/ollama:latest
  ports:
    - "11437:11434"
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            device_ids: ['3']  # Use GPU 3
```

Update `.env`:

```bash
OLLAMA_ENDPOINTS=http://ollama1:11434,http://ollama2:11434,http://ollama3:11434,http://ollama4:11434
```

#### Vertical Scaling

**Increase resource limits**:

```yaml
api1:
  deploy:
    resources:
      limits:
        cpus: '4'      # Increase from 2
        memory: 8G     # Increase from 4G
```

### Load Testing

Use Apache Bench or Locust for load testing:

```bash
# Apache Bench
ab -n 1000 -c 100 http://localhost/api/v1/health

# Locust
pip install locust
locust -f tests/locustfile.py --host http://localhost
```

Create `tests/locustfile.py`:

```python
from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search(self):
        self.client.post("/api/v1/search", json={
            "query": "AI research",
            "top_k": 5
        })

    @task(1)
    def health(self):
        self.client.get("/api/v1/health")
```

### Troubleshooting

#### Services Won't Start

```bash
# Check logs
docker-compose logs api1

# Check resource usage
docker stats

# Restart specific service
docker-compose restart api1
```

#### GPU Not Detected

```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check Docker daemon config
cat /etc/docker/daemon.json
```

Should contain:

```json
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

#### Ollama Model Pull Fails

```bash
# Manual model pull
docker-compose exec ollama1 ollama pull qwen2.5-coder:32b

# Check disk space
df -h

# Check Ollama logs
docker-compose logs ollama1
```

#### Database Connection Issues

```bash
# Check PostgreSQL is ready
docker-compose exec postgres pg_isready

# Check connection
docker-compose exec api1 python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:password@postgres:5432/ragdb')
with engine.connect() as conn:
    print('Connected!')
"
```

### Maintenance

#### Update Services

```bash
# Pull latest images
docker-compose pull

# Restart services (zero-downtime)
docker-compose up -d --no-deps --build api1
docker-compose up -d --no-deps --build api2
docker-compose up -d --no-deps --build api3
```

#### Clean Up

```bash
# Remove old containers
docker system prune -a

# Remove old volumes (CAREFUL!)
docker volume prune

# Clean up old logs
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

#### Update Models

```bash
# Pull new Ollama models
docker-compose exec ollama1 ollama pull qwen2.5-coder:latest

# Update environment
vim .env  # Update OLLAMA_MODEL

# Restart API servers
docker-compose restart api1 api2 api3
```

---

## Cloud Deployment

### AWS

Use ECS or EKS for container orchestration:

```bash
# Create ECR repositories
aws ecr create-repository --repository-name rag-api
aws ecr create-repository --repository-name rag-worker

# Push images
docker tag rag-api:latest <account>.dkr.ecr.<region>.amazonaws.com/rag-api:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/rag-api:latest
```

### Google Cloud

Use GKE with GPU node pools:

```bash
# Create GKE cluster with GPUs
gcloud container clusters create rag-cluster \
  --accelerator type=nvidia-tesla-t4,count=3 \
  --machine-type n1-standard-8 \
  --num-nodes 3
```

### Azure

Use AKS with GPU-enabled nodes:

```bash
# Create AKS cluster
az aks create \
  --resource-group rag-rg \
  --name rag-cluster \
  --node-vm-size Standard_NC6 \
  --node-count 3
```

---

## Kubernetes Deployment (Advanced)

See `k8s/` directory for Kubernetes manifests:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml
```

---

## Support

For deployment issues:
- Documentation: https://github.com/jeonchulho/rag-ai-project/docs
- Issues: https://github.com/jeonchulho/rag-ai-project/issues

---

## Changelog

### Version 1.0.0 (2024-01-11)
- Initial release
- Multimodal RAG system
- Natural language processing
- Email scheduling
- Production-ready infrastructure
