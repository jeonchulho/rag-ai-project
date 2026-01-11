# RAG AI Project

A comprehensive Retrieval-Augmented Generation (RAG) system that combines the power of large language models with efficient information retrieval to provide accurate, context-aware responses.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [License](#license)

## 🔍 Overview

This RAG AI project implements a state-of-the-art retrieval-augmented generation system that enhances large language model responses by retrieving relevant information from a knowledge base. The system enables accurate, contextual answers by combining semantic search with generative AI capabilities.

## 🏗️ Architecture

The system follows a multi-stage RAG architecture:

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   Query Processing              │
│   - Tokenization                │
│   - Embedding Generation        │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Vector Database               │
│   - Semantic Search             │
│   - Similarity Matching         │
│   - Document Retrieval          │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Context Assembly              │
│   - Rank Documents              │
│   - Create Prompt Context       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   LLM Generation                │
│   - Context-aware Response      │
│   - Answer Synthesis            │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Response Post-processing      │
│   - Formatting                  │
│   - Citation Addition           │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   Final     │
│   Response  │
└─────────────┘
```

### Key Components:

1. **Document Ingestion Pipeline**: Processes and chunks documents for efficient retrieval
2. **Embedding Engine**: Converts text into high-dimensional vector representations
3. **Vector Store**: Stores and indexes embeddings for fast similarity search
4. **Retrieval System**: Finds the most relevant documents based on query similarity
5. **LLM Integration**: Generates responses using retrieved context
6. **API Layer**: Provides REST API endpoints for easy integration

## ✨ Features

- **🔎 Semantic Search**: Advanced vector-based similarity search for accurate document retrieval
- **📚 Multi-Format Support**: Ingest documents from PDF, DOCX, TXT, MD, and more
- **🤖 Multiple LLM Support**: Compatible with OpenAI, Anthropic, HuggingFace, and local models
- **⚡ Real-time Processing**: Fast query processing and response generation
- **📊 Context Ranking**: Intelligent ranking of retrieved documents by relevance
- **🔒 Privacy-First**: Option to run entirely locally without external API calls
- **📈 Scalable Architecture**: Designed to handle large document collections
- **🎯 Customizable Prompts**: Flexible prompt engineering for different use cases
- **📝 Source Citations**: Automatic citation of source documents in responses
- **🔄 Incremental Updates**: Add documents without rebuilding entire index
- **🌐 REST API**: Easy integration with web and mobile applications
- **📱 Web Interface**: User-friendly chat interface for testing and demos

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)
- Minimum 8GB RAM
- (Optional) GPU for faster embedding generation

### Step 1: Clone the Repository

```bash
git clone https://github.com/jeonchulho/rag-ai-project.git
cd rag-ai-project
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
# Add API keys and configuration parameters
```

### Step 5: Initialize Vector Database

```bash
# Initialize the vector store
python scripts/init_database.py
```

### Step 6: Ingest Documents

```bash
# Add your documents to the knowledge base
python scripts/ingest_documents.py --input ./documents
```

## 💡 Usage

### Basic Usage

```python
from rag_ai import RAGSystem

# Initialize the RAG system
rag = RAGSystem(
    vector_store="chroma",
    llm_model="gpt-4",
    embedding_model="text-embedding-ada-002"
)

# Query the system
response = rag.query("What is retrieval-augmented generation?")
print(response.answer)
print(response.sources)
```

### Advanced Usage

```python
from rag_ai import RAGSystem, RAGConfig

# Custom configuration
config = RAGConfig(
    chunk_size=1000,
    chunk_overlap=200,
    top_k_documents=5,
    temperature=0.7,
    max_tokens=500
)

# Initialize with custom config
rag = RAGSystem(config=config)

# Add documents
rag.add_documents([
    "path/to/document1.pdf",
    "path/to/document2.txt"
])

# Query with filters
response = rag.query(
    "Explain machine learning",
    filters={"category": "AI", "year": 2024},
    return_sources=True
)

# Access detailed response
print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
print(f"Sources: {response.sources}")
```

### Running the API Server

```bash
# Start the REST API server
python -m rag_ai.api --host 0.0.0.0 --port 8000
```

```bash
# Make API request
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 5}'
```

### Running the Web Interface

```bash
# Start the web interface
python -m rag_ai.web
```

Visit `http://localhost:8000` in your browser to access the chat interface.

## ⚙️ Configuration

Edit the `config.yaml` file to customize the system behavior:

```yaml
# Model Configuration
llm:
  provider: "openai"  # openai, anthropic, huggingface, local
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000

# Embedding Configuration
embeddings:
  model: "text-embedding-ada-002"
  dimension: 1536

# Vector Store Configuration
vector_store:
  type: "chroma"  # chroma, pinecone, weaviate, faiss
  path: "./data/vectorstore"
  collection_name: "documents"

# Retrieval Configuration
retrieval:
  top_k: 5
  similarity_threshold: 0.7
  rerank: true

# Document Processing
processing:
  chunk_size: 1000
  chunk_overlap: 200
  supported_formats: [".pdf", ".txt", ".md", ".docx"]
```

## 📁 Project Structure

```
rag-ai-project/
├── rag_ai/
│   ├── __init__.py
│   ├── core/
│   │   ├── rag_system.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── llm.py
│   ├── processing/
│   │   ├── document_loader.py
│   │   ├── chunker.py
│   │   └── preprocessor.py
│   ├── vectorstore/
│   │   ├── base.py
│   │   ├── chroma.py
│   │   └── pinecone.py
│   ├── api/
│   │   ├── app.py
│   │   └── routes.py
│   └── web/
│       ├── app.py
│       └── templates/
├── scripts/
│   ├── init_database.py
│   ├── ingest_documents.py
│   └── evaluate.py
├── tests/
│   ├── test_rag_system.py
│   ├── test_retriever.py
│   └── test_embeddings.py
├── documents/
├── data/
│   └── vectorstore/
├── config.yaml
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

## 🛠️ Technologies

- **LangChain**: Framework for building LLM applications
- **OpenAI API**: GPT models and embeddings
- **ChromaDB**: Vector database for similarity search
- **FAISS**: Facebook AI Similarity Search
- **HuggingFace Transformers**: Open-source models and embeddings
- **FastAPI**: Modern web framework for building APIs
- **Streamlit**: Interactive web interface
- **PyPDF2**: PDF document processing
- **python-docx**: DOCX document processing
- **tiktoken**: Token counting and management

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows PEP 8 style guidelines and includes appropriate tests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

**Chulho Jeon** - [@jeonchulho](https://github.com/jeonchulho)

Project Link: [https://github.com/jeonchulho/rag-ai-project](https://github.com/jeonchulho/rag-ai-project)

## 🙏 Acknowledgments

- OpenAI for providing powerful LLM APIs
- LangChain community for excellent tools and documentation
- ChromaDB team for the efficient vector database
- All contributors who have helped improve this project

---

**⭐ If you find this project useful, please consider giving it a star!**
