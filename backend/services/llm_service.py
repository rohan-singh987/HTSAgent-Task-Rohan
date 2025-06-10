from typing import Dict, Any, Optional, List
import logging
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch

from core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for handling Large Language Model interactions"""
    
    def __init__(self):
        self.openai_client = None
        self.hf_pipeline = None
        self.hf_tokenizer = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def initialize(self):
        """Initialize LLM services"""
        try:
            if settings.OPENAI_API_KEY:
                self._initialize_openai()
            
            # Initialize HuggingFace model for fallback
            await self._initialize_huggingface()
            
            logger.info("LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {str(e)}")
            raise
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def _initialize_huggingface(self):
        """Initialize HuggingFace model"""
        try:
            logger.info(f"Loading HuggingFace model: {settings.HUGGINGFACE_MODEL}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._load_hf_model
            )
            
            logger.info("HuggingFace model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {str(e)}")
            # Don't raise here as HF model is optional
    
    def _load_hf_model(self):
        """Load HuggingFace model (synchronous)"""
        try:
            # Use a better model for text generation
            model_name = "microsoft/DialoGPT-medium"  # Good for conversation
            # Alternative: "google/flan-t5-base" for instruction following
            
            device = 0 if torch.cuda.is_available() else -1
            
            self.hf_pipeline = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                device=device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                do_sample=True,
                pad_token_id=50256  # GPT-2 end token
            )
            
            self.hf_tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.hf_tokenizer.pad_token is None:
                self.hf_tokenizer.pad_token = self.hf_tokenizer.eos_token
                
        except Exception as e:
            logger.error(f"Error loading HF model: {str(e)}")
            # Fallback to a simpler model
            try:
                self.hf_pipeline = pipeline(
                    "text-generation", 
                    model="gpt2",
                    device=-1  # Force CPU for compatibility
                )
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {str(fallback_error)}")
    
    async def generate_response(
        self,
        prompt: str,
        provider: str = "openai",
        max_tokens: int = 1000,
        temperature: float = 0.3,
        **kwargs
    ) -> str:
        """
        Generate response using specified LLM provider
        
        Args:
            prompt: Input prompt
            provider: "openai" or "huggingface"
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        try:
            if provider == "openai" and self.openai_client and settings.OPENAI_API_KEY:
                return await self._generate_openai_response(prompt, max_tokens, temperature)
            elif provider == "huggingface" and self.hf_pipeline:
                return await self._generate_hf_response(prompt, max_tokens, temperature)
            else:
                # Fallback logic
                if self.openai_client and settings.OPENAI_API_KEY:
                    return await self._generate_openai_response(prompt, max_tokens, temperature)
                elif self.hf_pipeline:
                    return await self._generate_hf_response(prompt, max_tokens, temperature)
                else:
                    raise Exception("No LLM provider available")
                    
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    async def _generate_openai_response(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Generate response using OpenAI API"""
        try:
            # Format prompt for the HTS agent personality
            system_prompt = self._get_system_prompt()
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def _generate_hf_response(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Generate response using HuggingFace model"""
        try:
            # Format prompt for better results
            formatted_prompt = self._format_hf_prompt(prompt)
            
            # Run generation in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._generate_hf_text,
                formatted_prompt,
                max_tokens,
                temperature
            )
            
            return self._clean_hf_response(response, formatted_prompt)
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {str(e)}")
            raise
    
    def _generate_hf_text(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using HuggingFace pipeline (synchronous)"""
        try:
            # Calculate max_new_tokens based on input length
            input_tokens = len(self.hf_tokenizer.encode(prompt))
            max_new_tokens = min(max_tokens, 512)  # Limit for stability
            
            outputs = self.hf_pipeline(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.hf_pipeline.tokenizer.eos_token_id,
                eos_token_id=self.hf_pipeline.tokenizer.eos_token_id,
                return_full_text=True
            )
            
            return outputs[0]['generated_text']
            
        except Exception as e:
            logger.error(f"HF text generation error: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _format_hf_prompt(self, user_input: str) -> str:
        """Format prompt for HuggingFace models"""
        system_prompt = self._get_system_prompt()
        return f"{system_prompt}\n\nUser: {user_input}\nTariffBot:"
    
    def _clean_hf_response(self, full_response: str, original_prompt: str) -> str:
        """Clean and extract the actual response from HF output"""
        try:
            # Remove the original prompt from the response
            if original_prompt in full_response:
                response = full_response.replace(original_prompt, "").strip()
            else:
                response = full_response
            
            # Extract only the bot's response part
            if "TariffBot:" in response:
                response = response.split("TariffBot:")[-1].strip()
            
            # Clean up common artifacts
            response = response.split("User:")[0].strip()  # Remove any follow-up user input
            response = response.split("\n\n")[0].strip()  # Take first paragraph
            
            # Ensure we have a meaningful response
            if len(response) < 10:
                response = "I understand your question about HTS regulations. However, I need more specific information to provide an accurate answer. Please provide more details about your query."
            
            return response
            
        except Exception as e:
            logger.error(f"Error cleaning HF response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for TariffBot personality"""
        return """You are TariffBot — an intelligent assistant trained on U.S. International Trade Commission data.
You exist to help importers, analysts, and trade professionals quickly understand tariff rules, duty rates, and policy agreements.
You always provide clear, compliant, and factual answers grounded in official HTS documentation.

When given an HTS code and product information, you explain all applicable duties and cost components.
When asked about trade agreements (e.g., NAFTA, Israel FTA), you reference the relevant General Notes with citations.
If a query is ambiguous or unsupported, you politely defer or recommend reviewing the relevant HTS section manually.
You do not speculate or make policy interpretations — you clarify with precision and data.

Please provide accurate, helpful responses based on the context provided."""
    
    async def get_health_status(self) -> Dict[str, str]:
        """Get health status of LLM services"""
        status = {}
        
        # Check OpenAI
        if self.openai_client and settings.OPENAI_API_KEY:
            try:
                # Quick test call
                await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                status["openai"] = "healthy"
            except Exception as e:
                status["openai"] = f"unhealthy: {str(e)}"
        else:
            status["openai"] = "not_configured"
        
        # Check HuggingFace
        if self.hf_pipeline:
            try:
                # Quick test generation
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.hf_pipeline("test", max_new_tokens=1, do_sample=False)
                )
                status["huggingface"] = "healthy"
            except Exception as e:
                status["huggingface"] = f"unhealthy: {str(e)}"
        else:
            status["huggingface"] = "not_loaded"
        
        return status
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("LLM service cleaned up") 