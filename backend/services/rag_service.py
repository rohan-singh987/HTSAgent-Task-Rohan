from typing import Dict, List, Any, Optional
import logging
import asyncio
import os

from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.vector_db_service import VectorDBService
from services.document_service import DocumentService
from core.config import settings
from api.chat.schema import DocumentChunk

logger = logging.getLogger(__name__)


class RAGService:
    """Main RAG service that orchestrates all components"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.vector_db_service = VectorDBService()
        self.document_service = DocumentService()
        
        self.is_initialized = False
        self.processing_status = {
            "status": "not_started",
            "documents_processed": 0,
            "chunks_created": 0,
            "vector_db_initialized": False
        }
        
    async def initialize(self):
        """Initialize all services and load documents"""
        try:
            logger.info("Initializing RAG service...")
            
            # Initialize all services
            await self._initialize_services()
            
            # Load and process documents
            await self._load_documents()
            
            self.is_initialized = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}")
            self.processing_status["status"] = "failed"
            raise
    
    async def _initialize_services(self):
        """Initialize all individual services"""
        try:
            logger.info("Initializing individual services...")
            
            # Initialize services in parallel for efficiency
            await asyncio.gather(
                self.embedding_service.initialize(),
                self.llm_service.initialize(),
                self.vector_db_service.initialize(),
                return_exceptions=True
            )
            
            logger.info("All services initialized")
            
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise
    
    async def _load_documents(self):
        """Load and process documents into vector database"""
        try:
            logger.info("Loading documents...")
            self.processing_status["status"] = "processing"
            
            # Check if documents are already loaded
            collection_info = await self.vector_db_service.get_collection_info()
            if collection_info.get("count", 0) > 0:
                logger.info(f"Found existing documents in vector DB: {collection_info['count']}")
                self.processing_status.update({
                    "status": "completed",
                    "documents_processed": 1,
                    "chunks_created": collection_info["count"],
                    "vector_db_initialized": True
                })
                return
            
            # Process the finalCopy.pdf document
            pdf_path = settings.PDF_FILE_PATH
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Load and chunk documents
            chunks = await self.document_service.process_pdf_file(pdf_path)
            
            if not chunks:
                logger.warning("No chunks created from PDF")
                self.processing_status["status"] = "completed"
                return
            
            # Generate embeddings for chunks
            logger.info("Generating embeddings for document chunks...")
            documents_data = self.document_service.prepare_documents_for_vectordb(chunks)
            
            embeddings = await self.embedding_service.embed_texts(documents_data["documents"])
            
            # Store in vector database
            logger.info("Storing documents in vector database...")
            success = await self.vector_db_service.add_documents(
                documents=documents_data["documents"],
                embeddings=embeddings,
                metadatas=documents_data["metadatas"],
                ids=documents_data["ids"]
            )
            
            if success:
                self.processing_status.update({
                    "status": "completed",
                    "documents_processed": 1,
                    "chunks_created": len(chunks),
                    "vector_db_initialized": True
                })
                logger.info(f"Successfully loaded {len(chunks)} chunks into vector database")
            else:
                self.processing_status["status"] = "failed"
                raise Exception("Failed to store documents in vector database")
                
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            self.processing_status["status"] = "failed"
            raise
    
    async def ask_question(
        self,
        question: str,
        llm_provider: str = "openai",
        session_id: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Process a question through the RAG pipeline
        
        Args:
            question: User's question
            llm_provider: LLM provider to use ("openai" or "huggingface")
            session_id: Session ID for conversation context
            max_tokens: Maximum tokens in response
            temperature: LLM temperature
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            if not self.is_initialized:
                raise Exception("RAG service not initialized")
            
            logger.info(f"Processing question: {question[:100]}...")
            
            # Generate embedding for the question
            question_embedding = await self.embedding_service.embed_text(question)
            
            # Search for relevant documents
            relevant_chunks = await self.vector_db_service.search_similar_documents(
                query_embedding=question_embedding,
                n_results=settings.MAX_CHUNKS_FOR_CONTEXT
            )
            
            # Build context from retrieved chunks
            context = self._build_context(relevant_chunks)
            
            # Generate prompt for LLM
            prompt = self._create_rag_prompt(question, context)
            
            # Generate response using LLM
            response = await self.llm_service.generate_response(
                prompt=prompt,
                provider=llm_provider,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Prepare response data
            response_data = {
                "response": response,
                "retrieved_chunks": [chunk.dict() for chunk in relevant_chunks],
                "metadata": {
                    "llm_provider": llm_provider,
                    "chunks_used": len(relevant_chunks),
                    "context_length": len(context),
                    "question_length": len(question)
                }
            }
            
            logger.info(f"Generated response using {len(relevant_chunks)} chunks")
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            raise
    
    def _build_context(self, chunks: List[DocumentChunk]) -> str:
        """
        Build context string from retrieved document chunks
        
        Args:
            chunks: List of relevant document chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documents found."
        
        context_parts = []
        total_length = 0
        
        for i, chunk in enumerate(chunks):
            # Add chunk with metadata
            chunk_text = f"Document {i+1} (Similarity: {chunk.similarity_score:.3f}):\n{chunk.content}\n"
            
            # Check if adding this chunk would exceed context limit
            if total_length + len(chunk_text) > settings.MAX_CONTEXT_LENGTH:
                break
                
            context_parts.append(chunk_text)
            total_length += len(chunk_text)
        
        return "\n---\n".join(context_parts)
    
    def _create_rag_prompt(self, question: str, context: str) -> str:
        """
        Create a prompt for the LLM with question and context
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Based on the following HTS documentation context, please answer the user's question accurately and thoroughly.

CONTEXT FROM HTS DOCUMENTS:
{context}

USER QUESTION: {question}

Please provide a detailed answer based on the provided context. If the context doesn't contain enough information to fully answer the question, please say so and indicate what additional information might be needed. Always cite relevant sections or general notes when applicable.

ANSWER:"""
        
        return prompt
    
    async def reload_documents(self):
        """Reload documents into vector database"""
        try:
            logger.info("Reloading documents...")
            
            # Delete existing collection
            await self.vector_db_service.delete_collection()
            
            # Reinitialize vector DB
            await self.vector_db_service.initialize()
            
            # Reload documents
            await self._load_documents()
            
            logger.info("Documents reloaded successfully")
            
        except Exception as e:
            logger.error(f"Error reloading documents: {str(e)}")
            raise
    
    async def get_health_status(self) -> Dict[str, str]:
        """Get health status of all services"""
        try:
            statuses = {}
            
            # Get individual service statuses
            embedding_status = {"embedding": "healthy" if self.embedding_service.model else "not_loaded"}
            llm_status = await self.llm_service.get_health_status()
            vector_db_status = await self.vector_db_service.get_health_status()
            
            statuses.update(embedding_status)
            statuses.update(llm_status)
            statuses.update(vector_db_status)
            
            # Overall RAG service status
            statuses["rag_service"] = "healthy" if self.is_initialized else "not_initialized"
            
            return statuses
            
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return {"error": str(e)}
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get document processing status"""
        return self.processing_status.copy()
    
    async def search_documents(
        self,
        query: str,
        n_results: int = 5,
        similarity_threshold: float = None
    ) -> List[DocumentChunk]:
        """
        Search documents by query
        
        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of matching document chunks
        """
        try:
            if not self.is_initialized:
                raise Exception("RAG service not initialized")
            
            # Use custom threshold if provided
            if similarity_threshold is not None:
                original_threshold = settings.SIMILARITY_THRESHOLD
                settings.SIMILARITY_THRESHOLD = similarity_threshold
            
            # Generate embedding for query
            query_embedding = await self.embedding_service.embed_text(query)
            
            # Search documents
            chunks = await self.vector_db_service.search_similar_documents(
                query_embedding=query_embedding,
                n_results=n_results
            )
            
            # Restore original threshold if changed
            if similarity_threshold is not None:
                settings.SIMILARITY_THRESHOLD = original_threshold
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            collection_info = await self.vector_db_service.get_collection_info()
            return {
                "collection_name": collection_info.get("name", "unknown"),
                "total_documents": collection_info.get("count", 0),
                "processing_status": self.processing_status,
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            logger.info("Cleaning up RAG service...")
            
            # Cleanup all services
            await asyncio.gather(
                self.embedding_service.cleanup(),
                self.llm_service.cleanup(),
                self.vector_db_service.cleanup(),
                self.document_service.cleanup(),
                return_exceptions=True
            )
            
            self.is_initialized = False
            logger.info("RAG service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 