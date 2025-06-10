#!/usr/bin/env python3
"""
Test script to verify HTS AI Agent RAG Backend setup
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_services():
    """Test individual services"""
    print("🧪 Testing HTS AI Agent RAG Backend Setup")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from services.embedding_service import EmbeddingService
        from services.llm_service import LLMService
        from services.vector_db_service import VectorDBService
        from services.document_service import DocumentService
        from services.rag_service import RAGService
        from core.config import settings
        print("✅ All imports successful")
        
        # Test configuration
        print("\n⚙️  Testing configuration...")
        print(f"   PDF Path: {settings.PDF_FILE_PATH}")
        print(f"   Embedding Model: {settings.EMBEDDING_MODEL}")
        print(f"   LLM Provider: {settings.LLM_PROVIDER}")
        print(f"   ChromaDB Path: {settings.CHROMA_DB_PATH}")
        
        # Check if PDF exists
        if os.path.exists(settings.PDF_FILE_PATH):
            print(f"✅ PDF file found: {settings.PDF_FILE_PATH}")
        else:
            print(f"❌ PDF file not found: {settings.PDF_FILE_PATH}")
            return False
        
        # Test embedding service
        print("\n🔤 Testing Embedding Service...")
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Test a simple embedding
        test_text = "What is the United States-Israel Free Trade Agreement?"
        embedding = await embedding_service.embed_text(test_text)
        print(f"✅ Generated embedding of dimension: {len(embedding)}")
        
        # Test document service
        print("\n📄 Testing Document Service...")
        document_service = DocumentService()
        
        # Load a small portion of the PDF for testing
        try:
            chunks = await document_service.process_pdf_file(settings.PDF_FILE_PATH)
            print(f"✅ Processed PDF into {len(chunks)} chunks")
            
            if chunks:
                print(f"   First chunk preview: {chunks[0].page_content[:100]}...")
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return False
        
        # Test vector database
        print("\n🗄️  Testing Vector Database...")
        vector_db_service = VectorDBService()
        await vector_db_service.initialize()
        
        collection_info = await vector_db_service.get_collection_info()
        print(f"✅ ChromaDB collection initialized: {collection_info}")
        
        # Test LLM service
        print("\n🤖 Testing LLM Service...")
        llm_service = LLMService()
        await llm_service.initialize()
        
        health_status = await llm_service.get_health_status()
        print(f"✅ LLM service status: {health_status}")
        
        # Test simple generation
        if settings.OPENAI_API_KEY or settings.HUGGINGFACE_API_KEY:
            try:
                response = await llm_service.generate_response(
                    "Hello, this is a test.",
                    provider=settings.LLM_PROVIDER,
                    max_tokens=50
                )
                print(f"✅ LLM generation test: {response[:100]}...")
            except Exception as e:
                print(f"⚠️  LLM generation test failed: {e}")
        else:
            print("⚠️  No API keys configured for LLM testing")
        
        # Cleanup
        await embedding_service.cleanup()
        await llm_service.cleanup()
        await vector_db_service.cleanup()
        await document_service.cleanup()
        
        print("\n🎉 All tests completed successfully!")
        print("\n🚀 Your RAG backend is ready to use!")
        print("\nTo start the server:")
        print("   python main.py")
        print("or")
        print("   python start.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("Starting RAG Backend Setup Test...")
    
    try:
        result = asyncio.run(test_services())
        if result:
            print("\n✅ Setup verification completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup verification failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 