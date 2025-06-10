"""
Configuration settings for the HTS AI Agent Frontend
"""
import os
from typing import Dict, List

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "120"))  # Increased to 120 seconds for RAG processing

# Streamlit Configuration
PAGE_TITLE = "HTS AI Agent - TariffBot"
PAGE_ICON = "🚢"
LAYOUT = "wide"

# Sample data for demonstration
SAMPLE_QUESTIONS = [
    "What is the United States-Israel Free Trade Agreement?",
    "Can a product that exceeds its tariff-rate quota still qualify for duty-free entry under GSP or any FTA? Why or why not?",
    "How is classification determined for an imported item that will be used as a part in manufacturing but isn't itself a finished part?",
    "What are the requirements for NAFTA preferential treatment?",
    "Explain the Most Favored Nation (MFN) principle.",
    "What is the Generalized System of Preferences (GSP)?",
    "How do trade remedy measures affect duty calculations?",
    "What documentation is required for claiming duty preferences?",
    "Explain the difference between Column 1 and Column 2 duty rates.",
    "What are the rules of origin for USMCA?"
]

SAMPLE_HTS_CODES = [
    ("0101.30.00.00", "Live donkeys, mules and hinnies"),
    ("0102.21.00.00", "Pure-bred dairy cattle"),
    ("0102.29.00.00", "Other cattle"),
    ("0103.10.00.00", "Pure-bred breeding swine"),
    ("0201.10.00.00", "Fresh or chilled beef carcasses and half-carcasses"),
    ("0201.20.00.00", "Other cuts of fresh or chilled beef, with bone in"),
    ("0202.10.00.00", "Frozen beef carcasses and half-carcasses"),
    ("0203.11.00.00", "Fresh or chilled swine carcasses and half-carcasses"),
    ("0204.10.00.00", "Fresh or chilled lamb carcasses and half-carcasses"),
    ("0301.11.00.00", "Live ornamental freshwater fish")
]

# Country codes for demonstration
COMMON_COUNTRIES = {
    "US": "United States",
    "CA": "Canada",
    "MX": "Mexico",
    "AU": "Australia",
    "JP": "Japan",
    "DE": "Germany",
    "FR": "France",
    "UK": "United Kingdom",
    "CN": "China",
    "IN": "India",
    "BR": "Brazil",
    "KR": "South Korea",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands"
}

# UI Color scheme
COLORS = {
    "primary": "#1e3a8a",
    "secondary": "#3b82f6",
    "success": "#16a34a",
    "warning": "#ea580c",
    "error": "#dc2626",
    "info": "#0891b2",
    "light": "#f8fafc",
    "dark": "#1f2937"
}

# API Endpoints
ENDPOINTS = {
    "chat": {
        "ask": "chat/ask",
        "health": "chat/health",
        "status": "chat/status",
        "reload": "chat/reload-documents"
    },
    "tariff": {
        "calculate": "tariff/calculate",
        "lookup": "tariff/lookup",
        "search": "tariff/search",
        "health": "tariff/health",
        "statistics": "tariff/statistics",
        "history": "tariff/history",
        "reload": "tariff/reload-data"
    }
}

# Default calculation values
DEFAULT_CALCULATION = {
    "product_cost": 10000.00,
    "freight": 500.00,
    "insurance": 100.00,
    "quantity": 5,
    "weight_kg": 500.0,
    "country_code": "AU"
}

# LLM Settings
LLM_PROVIDERS = ["openai", "huggingface"]
DEFAULT_LLM_SETTINGS = {
    "provider": "openai",
    "max_tokens": 1000,
    "temperature": 0.3
} 