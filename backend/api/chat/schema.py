from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    message: str = Field(..., description="User's question or message", min_length=1, max_length=2000)
    llm_provider: Optional[LLMProvider] = Field(LLMProvider.OPENAI, description="LLM provider to use")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens in response", ge=100, le=4000)
    temperature: Optional[float] = Field(0.3, description="LLM temperature", ge=0.0, le=2.0)


class DocumentChunk(BaseModel):
    """Schema for document chunks retrieved from vector DB"""
    content: str = Field(..., description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the chunk")
    similarity_score: Optional[float] = Field(None, description="Similarity score with query")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    response: str = Field(..., description="AI assistant's response")
    session_id: str = Field(..., description="Session ID for the conversation")
    retrieved_chunks: List[DocumentChunk] = Field(default_factory=list, description="Retrieved document chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Individual service statuses")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class DocumentProcessingStatus(BaseModel):
    """Status of document processing"""
    status: str = Field(..., description="Processing status")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    vector_db_initialized: bool = Field(..., description="Whether vector DB is initialized")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp") 