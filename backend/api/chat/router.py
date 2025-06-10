from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import uuid
import logging

from .schema import (
    ChatRequest, 
    ChatResponse, 
    HealthCheckResponse, 
    ErrorResponse,
    DocumentProcessingStatus
)
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
chat_router = APIRouter()


def get_rag_service(request: Request) -> RAGService:
    """Dependency to get RAG service from app state"""
    return request.app.state.rag_service


@chat_router.post("/ask", response_model=ChatResponse)
async def ask_question(
    chat_request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Ask a question to the HTS RAG agent
    """
    try:
        # Generate session ID if not provided
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Process the question through RAG pipeline
        response_data = await rag_service.ask_question(
            question=chat_request.message,
            llm_provider=chat_request.llm_provider.value,
            session_id=session_id,
            max_tokens=chat_request.max_tokens,
            temperature=chat_request.temperature
        )
        
        return ChatResponse(
            response=response_data["response"],
            session_id=session_id,
            retrieved_chunks=response_data.get("retrieved_chunks", []),
            metadata=response_data.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)}"
        )


@chat_router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Health check endpoint for chat service
    """
    try:
        # Check service status
        services_status = await rag_service.get_health_status()
        
        return HealthCheckResponse(
            status="healthy" if all(status == "healthy" for status in services_status.values()) else "unhealthy",
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            services={"error": str(e)}
        )


@chat_router.get("/status", response_model=DocumentProcessingStatus)
async def get_processing_status(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get document processing status
    """
    try:
        status = await rag_service.get_processing_status()
        return DocumentProcessingStatus(**status)
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting processing status: {str(e)}"
        )


@chat_router.post("/reload-documents")
async def reload_documents(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Reload documents into vector database
    """
    try:
        await rag_service.reload_documents()
        return {"message": "Documents reloaded successfully"}
        
    except Exception as e:
        logger.error(f"Error reloading documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reloading documents: {str(e)}"
        ) 