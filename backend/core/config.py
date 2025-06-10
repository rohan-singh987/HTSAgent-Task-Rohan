from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "HTS AI Agent RAG Backend"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Document paths
    DATA_PATH: str = "../data"
    PDF_FILE_PATH: str = "../data/finalCopy.pdf"
    
    # ChromaDB settings
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "hts_documents"
    
    # Embedding model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # or "cuda" if GPU available
    
    # LLM settings
    LLM_PROVIDER: str = "openai"  # "openai" or "huggingface"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # HuggingFace settings
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    HUGGINGFACE_MODEL: str = "microsoft/DialoGPT-medium"  # Alternative: "google/flan-t5-large"
    
    # Text processing settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_FOR_CONTEXT: int = 5
    
    # RAG settings
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_CONTEXT_LENGTH: int = 4000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings() 