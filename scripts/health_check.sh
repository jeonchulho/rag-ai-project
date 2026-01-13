#!/bin/bash
# Health check script for all services

set -e

echo "======================================"
echo "RAG System Health Check"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓ Healthy${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC} (HTTP $response)"
        return 1
    fi
}

check_port() {
    local name=$1
    local host=$2
    local port=$3
    
    echo -n "Checking $name on $host:$port... "
    
    if nc -z -w5 "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Listening${NC}"
        return 0
    else
        echo -e "${RED}✗ Not listening${NC}"
        return 1
    fi
}

# Initialize counters
total=0
passed=0

# Check Nginx
((total++))
check_service "Nginx" "http://localhost/health" "200" && ((passed++))

# Check API servers
for i in {1..3}; do
    ((total++))
    port=$((7999+i))
    check_service "API Server $i" "http://localhost:$port/api/v1/health" "200" && ((passed++))
done

# Check Redis
((total++))
check_port "Redis" "localhost" "6379" && ((passed++))

# Check PostgreSQL
((total++))
check_port "PostgreSQL" "localhost" "5432" && ((passed++))

# Check Milvus
((total++))
check_port "Milvus" "localhost" "19530" && ((passed++))

# Check Ollama servers
for i in {1..3}; do
    ((total++))
    port=$((11433+i))
    check_service "Ollama Server $i" "http://localhost:$port/api/tags" "200" && ((passed++))
done

# Check Prometheus
((total++))
check_service "Prometheus" "http://localhost:9090/-/healthy" "200" && ((passed++))

# Check Grafana
((total++))
check_service "Grafana" "http://localhost:3000/api/health" "200" && ((passed++))

# Summary
echo ""
echo "======================================"
echo "Summary: $passed/$total services healthy"

if [ "$passed" -eq "$total" ]; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
    echo "======================================"
    exit 0
else
    echo -e "${YELLOW}⚠ Some services are unhealthy${NC}"
    echo "======================================"
    exit 1
fi
