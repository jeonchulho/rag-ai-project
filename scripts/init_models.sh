#!/bin/bash
# Initialize Ollama models on all servers

set -e

echo "Initializing Ollama models..."

# List of Ollama endpoints
OLLAMA_ENDPOINTS=(
    "http://ollama1:11434"
    "http://ollama2:11434"
    "http://ollama3:11434"
)

# Models to pull
MODELS=(
    "qwen2.5-coder:32b"
    "nomic-embed-text"
    "llava"
)

# Function to wait for Ollama to be ready
wait_for_ollama() {
    local endpoint=$1
    echo "Waiting for $endpoint to be ready..."
    
    for i in {1..30}; do
        if curl -s "$endpoint/api/tags" > /dev/null 2>&1; then
            echo "$endpoint is ready"
            return 0
        fi
        echo "Attempt $i/30: $endpoint not ready, waiting..."
        sleep 10
    done
    
    echo "ERROR: $endpoint did not become ready"
    return 1
}

# Function to pull model
pull_model() {
    local endpoint=$1
    local model=$2
    
    echo "Pulling $model on $endpoint..."
    
    curl -X POST "$endpoint/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model\"}" \
        --max-time 3600
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully pulled $model on $endpoint"
    else
        echo "✗ Failed to pull $model on $endpoint"
        return 1
    fi
}

# Main execution
echo "======================================"
echo "Ollama Model Initialization Script"
echo "======================================"

for endpoint in "${OLLAMA_ENDPOINTS[@]}"; do
    echo ""
    echo "Processing $endpoint..."
    
    # Wait for Ollama to be ready
    wait_for_ollama "$endpoint"
    
    # Pull all models
    for model in "${MODELS[@]}"; do
        pull_model "$endpoint" "$model"
    done
done

echo ""
echo "======================================"
echo "Model initialization complete!"
echo "======================================"
