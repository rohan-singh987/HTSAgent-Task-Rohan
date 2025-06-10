import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.config import settings as app_settings
from api.chat.schema import DocumentChunk

logger = logging.getLogger(__name__)


class VectorDBService:
    """Service for managing ChromaDB vector database operations"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            logger.info("Initializing ChromaDB...")
            
            # Ensure database directory exists
            os.makedirs(app_settings.CHROMA_DB_PATH, exist_ok=True)
            
            # Initialize ChromaDB client
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._init_client
            )
            
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _init_client(self):
        """Initialize ChromaDB client (synchronous)"""
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=app_settings.CHROMA_DB_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=app_settings.CHROMA_COLLECTION_NAME
                )
                logger.info(f"Using existing collection: {app_settings.CHROMA_COLLECTION_NAME}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=app_settings.CHROMA_COLLECTION_NAME,
                    metadata={"description": "HTS documents and general notes"}
                )
                logger.info(f"Created new collection: {app_settings.CHROMA_COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise
    
    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to the vector database
        
        Args:
            documents: List of document texts
            embeddings: List of document embeddings
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            Boolean indicating success
        """
        try:
            if not ids:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            logger.info(f"Adding {len(documents)} documents to vector database")
            
            # Add documents in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._add_docs_sync,
                documents,
                embeddings,
                metadatas,
                ids
            )
            
            logger.info("Documents added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def _add_docs_sync(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """Add documents synchronously"""
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Sync add documents error: {str(e)}")
            raise
    
    async def search_similar_documents(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: List[str] = ["documents", "metadatas", "distances"]
    ) -> List[DocumentChunk]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Metadata filter conditions
            include: What to include in results
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            logger.info(f"Searching for {n_results} similar documents")
            
            # Perform search in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._search_sync,
                query_embedding,
                n_results,
                where,
                include
            )
            
            # Convert results to DocumentChunk objects
            chunks = []
            if results and "documents" in results:
                documents = results["documents"][0]  # First query results
                metadatas = results.get("metadatas", [[{}] * len(documents)])[0]
                distances = results.get("distances", [[1.0] * len(documents)])[0]
                
                for i, doc in enumerate(documents):
                    similarity_score = 1.0 - distances[i]  # Convert distance to similarity
                    
                    # Filter by similarity threshold
                    if similarity_score >= app_settings.SIMILARITY_THRESHOLD:
                        chunk = DocumentChunk(
                            content=doc,
                            metadata=metadatas[i] if i < len(metadatas) else {},
                            similarity_score=similarity_score
                        )
                        chunks.append(chunk)
            
            logger.info(f"Found {len(chunks)} relevant documents")
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def _search_sync(
        self,
        query_embedding: List[float],
        n_results: int,
        where: Optional[Dict[str, Any]],
        include: List[str]
    ) -> Dict[str, Any]:
        """Perform synchronous search"""
        try:
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=include
            )
        except Exception as e:
            logger.error(f"Sync search error: {str(e)}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                self.executor,
                self._get_info_sync
            )
            return info
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}
    
    def _get_info_sync(self) -> Dict[str, Any]:
        """Get collection info synchronously"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting sync info: {str(e)}")
            return {"error": str(e)}
    
    async def delete_collection(self) -> bool:
        """Delete the entire collection"""
        try:
            logger.info("Deleting collection...")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._delete_collection_sync
            )
            
            logger.info("Collection deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
    
    def _delete_collection_sync(self):
        """Delete collection synchronously"""
        try:
            self.client.delete_collection(name=app_settings.CHROMA_COLLECTION_NAME)
            self.collection = None
        except Exception as e:
            logger.error(f"Sync delete error: {str(e)}")
            raise
    
    async def upsert_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """
        Upsert documents (update if exists, insert if not)
        
        Args:
            documents: List of document texts
            embeddings: List of document embeddings
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info(f"Upserting {len(documents)} documents")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._upsert_sync,
                documents,
                embeddings,
                metadatas,
                ids
            )
            
            logger.info("Documents upserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting documents: {str(e)}")
            return False
    
    def _upsert_sync(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """Upsert documents synchronously"""
        try:
            self.collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Sync upsert error: {str(e)}")
            raise
    
    async def get_health_status(self) -> Dict[str, str]:
        """Get health status of vector database"""
        try:
            if not self.client or not self.collection:
                return {"chromadb": "not_initialized"}
            
            # Test collection access
            info = await self.get_collection_info()
            if "error" in info:
                return {"chromadb": f"unhealthy: {info['error']}"}
            
            return {"chromadb": "healthy"}
            
        except Exception as e:
            return {"chromadb": f"unhealthy: {str(e)}"}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Vector DB service cleaned up") 