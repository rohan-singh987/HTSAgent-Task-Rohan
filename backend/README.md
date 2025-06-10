# HTS AI Agent - RAG Backend

A sophisticated RAG (Retrieval-Augmented Generation) backend for the HTS AI Agent that provides intelligent question-answering capabilities for U.S. Harmonized Tariff Schedule documentation.

## Features

- **Dual LLM Support**: Choose between OpenAI GPT-4o-mini or open-source HuggingFace models
- **Advanced Document Processing**: Automated PDF processing with intelligent chunking
- **Vector Database**: ChromaDB for efficient semantic search
- **Embedding Service**: High-quality embeddings using SentenceTransformers
- **RESTful API**: FastAPI-based endpoints with automatic documentation
- **Scalable Architecture**: Modular service-based design
- **Health Monitoring**: Comprehensive health checks and status monitoring

## Architecture

```
backend/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── __init__.py
│   └── config.py          # Application configuration
├── api/
│   ├── __init__.py
│   └── chat/              # Chat API endpoints
│       ├── __init__.py
│       ├── router.py      # FastAPI route handlers
│       └── schema.py      # Pydantic data models
└── services/
    ├── __init__.py
    ├── embedding_service.py    # SentenceTransformers embeddings
    ├── llm_service.py          # OpenAI & HuggingFace LLMs
    ├── vector_db_service.py    # ChromaDB operations
    ├── document_service.py     # PDF processing & chunking
    └── rag_service.py         # Main RAG orchestration
```

## Quick Start

### 1. Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Required: OpenAI API Key (for GPT-4o-mini)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: HuggingFace API Key (for open-source models)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# LLM Provider Selection
LLM_PROVIDER=openai  # or "huggingface"

# App Settings
DEBUG=True
HOST=127.0.0.1
PORT=8000
```

### 3. Ensure Data File

Make sure the HTS documentation file exists:
```
../data/finalCopy.pdf
```

### 4. Run the Application

```bash
# Start the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The application will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **OpenAPI Schema**: http://127.0.0.1:8000/openapi.json

## API Endpoints

### Chat Endpoints

#### Ask Question
```http
POST /api/v1/chat/ask
Content-Type: application/json

{
  "message": "What is the United States-Israel Free Trade Agreement?",
  "llm_provider": "openai",
  "max_tokens": 1000,
  "temperature": 0.3
}
```

#### Health Check
```http
GET /api/v1/chat/health
```

#### Processing Status
```http
GET /api/v1/chat/status
```

#### Reload Documents
```http
POST /api/v1/chat/reload-documents
```

### Example Response

```json
{
  "response": "The United States-Israel Free Trade Agreement is...",
  "session_id": "uuid-string",
  "retrieved_chunks": [
    {
      "content": "Document text chunk...",
      "metadata": {"source_file": "finalCopy.pdf", "page": 1},
      "similarity_score": 0.95
    }
  ],
  "metadata": {
    "llm_provider": "openai",
    "chunks_used": 3,
    "context_length": 2048
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Configuration Options

### LLM Providers

#### OpenAI (Recommended)
- **Model**: GPT-4o-mini
- **Requires**: OPENAI_API_KEY
- **Pros**: High quality, reliable, fast
- **Cons**: Requires API subscription

#### HuggingFace (Open Source)
- **Model**: microsoft/DialoGPT-medium (fallback: GPT-2)
- **Requires**: Optional HUGGINGFACE_API_KEY
- **Pros**: Free, privacy-focused
- **Cons**: Requires more computational resources

### Embedding Model
- **Default**: all-MiniLM-L6-v2 (384 dimensions)
- **Device**: CPU or CUDA (if available)

### Document Processing
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Similarity Threshold**: 0.7
- **Max Context Chunks**: 5

## Development

### Adding New Services

1. Create a new service file in `services/`
2. Follow the async pattern with initialization and cleanup methods
3. Add health check capabilities
4. Register in `rag_service.py` if needed

### Testing

```bash
# Run tests (if available)
pytest

# Test specific endpoint
curl -X POST "http://127.0.0.1:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is HTS?"}'
```

### Logging

The application uses structured logging. Check logs for:
- Service initialization status
- Document processing progress
- Query processing details
- Error tracking

## Troubleshooting

### Common Issues

1. **PDF Not Found**
   - Ensure `../data/finalCopy.pdf` exists
   - Check file permissions

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check account billing status
   - Ensure sufficient quota

3. **Memory Issues**
   - Reduce chunk size or embedding batch size
   - Use CPU instead of GPU if CUDA memory is limited

4. **ChromaDB Issues**
   - Delete `./chroma_db` directory and restart
   - Check disk space availability

### Performance Optimization

- **GPU Acceleration**: Set `EMBEDDING_DEVICE=cuda` if GPU available
- **Batch Processing**: Increase chunk processing batch sizes
- **Caching**: ChromaDB provides built-in vector caching

## Sample Test Queries

1. **Trade Agreements**: "What is the United States-Israel Free Trade Agreement?"
2. **GSP Questions**: "Can a product that exceeds its tariff-rate quota still qualify for duty-free entry under GSP?"
3. **Classification**: "How is classification determined for imported manufacturing parts?"

## Architecture Decisions

- **Async/Await**: All I/O operations are non-blocking
- **Service Pattern**: Modular design for easy testing and maintenance
- **Thread Pools**: CPU-intensive tasks run in separate threads
- **Error Handling**: Comprehensive exception handling with logging
- **Type Safety**: Full Pydantic validation for all data models

## Contributing

1. Follow the existing service pattern
2. Add comprehensive error handling
3. Include health check methods
4. Update documentation
5. Add type hints and docstrings

## License

This project is part of the HTS AI Agent system developed for trade documentation assistance. 