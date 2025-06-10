from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.chat.router import chat_router
from api.tariff.router import tariff_router
from services.embedding_service import EmbeddingService
from services.rag_service import RAGService
from services.hts_data_service import HTSDataService
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize services on startup
    embedding_service = EmbeddingService()
    rag_service = RAGService()
    hts_service = HTSDataService()
    
    # Initialize vector database and load documents
    await rag_service.initialize()
    
    # Initialize HTS database and data
    await hts_service.initialize()
    
    # Store services in app state
    app.state.embedding_service = embedding_service
    app.state.rag_service = rag_service
    app.state.hts_service = hts_service
    
    # Set global hts_service for the router
    import api.tariff.router as tariff_router_module
    tariff_router_module.hts_service = hts_service
    
    yield
    
    # Cleanup on shutdown
    if hasattr(app.state, 'rag_service'):
        await app.state.rag_service.cleanup()


# Create FastAPI app
app = FastAPI(
    title="HTS AI Agent",
    description="RAG-based Question Answering + HTS Tariff Calculator",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tariff_router, prefix="/api/v1/tariff", tags=["tariff"])


# Error handlers for tariff service
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    from fastapi.responses import JSONResponse
    from api.tariff.schema import ErrorResponse
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Invalid input",
            detail=str(exc),
            error_code="INVALID_INPUT"
        ).dict()
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    """Handle file not found exceptions"""
    from fastapi.responses import JSONResponse
    from api.tariff.schema import ErrorResponse
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="File not found",
            detail=str(exc),
            error_code="FILE_NOT_FOUND"
        ).dict()
    )


@app.get("/")
async def root():
    return {
        "message": "HTS AI Agent Complete Backend is running!",
        "services": {
            "rag_agent": "Available at /api/v1/chat/",
            "tariff_calculator": "Available at /api/v1/tariff/",
            "docs": "Available at /docs"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "services": ["rag", "tariff"],
        "endpoints": {
            "rag_health": "/api/v1/chat/health",
            "tariff_health": "/api/v1/tariff/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 