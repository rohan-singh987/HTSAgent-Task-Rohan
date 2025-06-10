from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Dict, Any
import logging
import os
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for loading and processing PDF documents"""
    
    def __init__(self):
        self.text_splitter = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_text_splitter()
        
    def _initialize_text_splitter(self):
        """Initialize the text splitter for chunking documents"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def load_pdf_document(self, file_path: str) -> List[Document]:
        """
        Load a PDF document and extract text
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of Document objects
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            logger.info(f"Loading PDF document: {file_path}")
            
            # Load PDF in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(
                self.executor,
                self._load_pdf_sync,
                file_path
            )
            
            logger.info(f"Loaded {len(documents)} pages from PDF")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            raise
    
    def _load_pdf_sync(self, file_path: str) -> List[Document]:
        """Load PDF synchronously"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Add file metadata to documents
            for doc in documents:
                doc.metadata.update({
                    "source_file": os.path.basename(file_path),
                    "file_path": file_path,
                    "document_type": "pdf"
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in sync PDF loading: {str(e)}")
            raise
    
    async def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks
        
        Args:
            documents: List of Document objects to chunk
            
        Returns:
            List of chunked Document objects
        """
        try:
            logger.info(f"Chunking {len(documents)} documents")
            
            # Chunk documents in thread pool
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                self.executor,
                self._chunk_documents_sync,
                documents
            )
            
            logger.info(f"Created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            raise
    
    def _chunk_documents_sync(self, documents: List[Document]) -> List[Document]:
        """Chunk documents synchronously"""
        try:
            all_chunks = []
            
            for doc_idx, document in enumerate(documents):
                # Split the document into chunks
                chunks = self.text_splitter.split_documents([document])
                
                # Add chunk-specific metadata
                for chunk_idx, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        "chunk_id": f"{doc_idx}_{chunk_idx}",
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "original_document_index": doc_idx,
                        "content_hash": self._generate_content_hash(chunk.page_content)
                    })
                    
                all_chunks.extend(chunks)
            
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error in sync chunking: {str(e)}")
            raise
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def process_pdf_file(self, file_path: str) -> List[Document]:
        """
        Complete pipeline to load and chunk a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of processed and chunked Document objects
        """
        try:
            logger.info(f"Processing PDF file: {file_path}")
            
            # Load the PDF
            documents = await self.load_pdf_document(file_path)
            
            # Filter out empty documents
            documents = [doc for doc in documents if doc.page_content.strip()]
            
            if not documents:
                logger.warning(f"No content found in PDF: {file_path}")
                return []
            
            # Chunk the documents
            chunks = await self.chunk_documents(documents)
            
            # Filter out very short chunks
            min_chunk_length = 50
            chunks = [chunk for chunk in chunks if len(chunk.page_content.strip()) >= min_chunk_length]
            
            logger.info(f"Processed PDF into {len(chunks)} valid chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF file: {str(e)}")
            raise
    
    async def load_multiple_pdfs(self, file_paths: List[str]) -> List[Document]:
        """
        Load and process multiple PDF files
        
        Args:
            file_paths: List of PDF file paths
            
        Returns:
            List of all processed chunks from all PDFs
        """
        try:
            logger.info(f"Processing {len(file_paths)} PDF files")
            
            all_chunks = []
            
            for file_path in file_paths:
                try:
                    chunks = await self.process_pdf_file(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    continue
            
            logger.info(f"Total chunks from all PDFs: {len(all_chunks)}")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error processing multiple PDFs: {str(e)}")
            raise
    
    def prepare_documents_for_vectordb(self, chunks: List[Document]) -> Dict[str, List]:
        """
        Prepare document chunks for vector database storage
        
        Args:
            chunks: List of Document chunks
            
        Returns:
            Dictionary with documents, metadatas, and ids
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Extract text content
                documents.append(chunk.page_content)
                
                # Prepare metadata (ensure all values are JSON-serializable)
                metadata = {}
                for key, value in chunk.metadata.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        metadata[key] = value
                    else:
                        metadata[key] = str(value)
                
                metadatas.append(metadata)
                
                # Generate unique ID
                chunk_id = chunk.metadata.get("chunk_id", f"chunk_{i}")
                source_file = chunk.metadata.get("source_file", "unknown")
                ids.append(f"{source_file}_{chunk_id}")
            
            return {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids
            }
            
        except Exception as e:
            logger.error(f"Error preparing documents for vectordb: {str(e)}")
            raise
    
    async def get_document_stats(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about processed documents
        
        Args:
            chunks: List of Document chunks
            
        Returns:
            Dictionary with document statistics
        """
        try:
            if not chunks:
                return {
                    "total_chunks": 0,
                    "total_characters": 0,
                    "average_chunk_length": 0,
                    "unique_sources": 0,
                    "sources": []
                }
            
            total_chars = sum(len(chunk.page_content) for chunk in chunks)
            sources = list(set(chunk.metadata.get("source_file", "unknown") for chunk in chunks))
            
            stats = {
                "total_chunks": len(chunks),
                "total_characters": total_chars,
                "average_chunk_length": total_chars // len(chunks) if chunks else 0,
                "unique_sources": len(sources),
                "sources": sources
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Document service cleaned up") 