from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using SentenceTransformers"""
    
    def __init__(self):
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_model
            )
            
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def _load_model(self) -> SentenceTransformer:
        """Load the SentenceTransformer model"""
        return SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if self.model is None:
            await self.initialize()
        
        try:
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._generate_embedding,
                text
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        if self.model is None:
            await self.initialize()
        
        try:
            # Run batch embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._generate_batch_embeddings,
                texts
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text (synchronous)"""
        return self.model.encode([text], convert_to_tensor=False)[0]
    
    def _generate_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (synchronous)"""
        return self.model.encode(texts, convert_to_tensor=False)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model"""
        if self.model is None:
            # Return default dimension for all-MiniLM-L6-v2
            return 384
        return self.model.get_sentence_embedding_dimension()
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Embedding service cleaned up") 