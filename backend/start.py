#!/usr/bin/env python3
"""
Startup script for HTS AI Agent RAG Backend
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if the environment is properly set up"""
    logger.info("Checking environment setup...")
    
    # Check if data file exists
    data_file = backend_dir.parent / "data" / "finalCopy.pdf"
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        logger.error("Please ensure the finalCopy.pdf file exists in the ../data/ directory")
        return False
    
    logger.info(f"Found data file: {data_file}")
    
    # Check for environment file
    env_file = backend_dir / ".env"
    if not env_file.exists():
        logger.warning(f"No .env file found at {env_file}")
        logger.warning("You may need to set environment variables manually")
        logger.warning("Create a .env file based on the example in the README")
    else:
        logger.info("Found .env file")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("OPENAI_API_KEY not set")
        logger.warning("The application will try to use HuggingFace models as fallback")
    else:
        logger.info("OpenAI API key found")
    
    return True


def main():
    """Main startup function"""
    logger.info("Starting HTS AI Agent RAG Backend...")
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Import and run the FastAPI application
    try:
        import uvicorn
        from core.config import settings
        
        logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
        
        # Run the application
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info" if not settings.DEBUG else "debug"
        )
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 