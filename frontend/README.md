# HTS AI Agent Frontend

A simple, user-friendly Streamlit application for the HTS AI Agent system, providing both RAG-based question answering and HTS duty calculation capabilities.

## 🌟 Features

### 🤖 RAG Question Answering
- Ask trade-related policy and agreement questions
- Document-grounded responses backed by official HTS documentation
- Conversation history and source citations
- Adjustable LLM settings

### 📊 HTS Duty Calculator
- Calculate CIF value, duties, and landed costs
- Product search by description or HTS code
- Input validation and country selection
- Export results as CSV
- Visual charts for duty breakdown

### 📈 Analytics & Monitoring
- System statistics and health monitoring
- Calculation history and analytics
- Real-time backend connectivity status

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Backend API running on `http://localhost:8000`

### Installation

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Access the application**:
   Open your browser to `http://localhost:8501`

## 📋 Usage Guide

### RAG Question Answering
1. Navigate to the RAG tab
2. Enter your trade-related question
3. Adjust LLM settings if needed
4. Click "Ask Question" to get responses
5. Review source documents in expandable sections

**Sample Questions:**
- "What is the United States-Israel Free Trade Agreement?"
- "Can a product that exceeds its tariff-rate quota still qualify for duty-free entry under GSP?"
- "How is classification determined for an imported item used in manufacturing?"

### HTS Duty Calculator
1. Navigate to the Calculator tab
2. Search for products or enter HTS code directly
3. Enter product details (cost, freight, insurance, quantity, weight)
4. Select country of origin
5. Click "Calculate Duties" to see results
6. Export results as CSV if needed

**Sample HTS Codes:**
- `0101.30.00.00` - Live donkeys, mules and hinnies
- `0102.21.00.00` - Pure-bred dairy cattle
- `0201.10.00.00` - Fresh or chilled beef carcasses

## 🔧 Configuration

You can modify settings in `config.py`:
- API endpoints and timeouts
- Sample questions and HTS codes
- Default calculation values
- Country codes and names

## 🛠️ File Structure
```
frontend/
├── app.py              # Main Streamlit application
├── config.py           # Configuration settings
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── start.sh           # Unix/Linux startup script
└── README.md          # This file
```

## 🐛 Troubleshooting

**Backend Connection Failed**
- Ensure backend is running on `http://localhost:8000`
- Check the System Status page in the app

**Calculation Errors**
- Validate HTS number format (8-10 digits)
- Check country code (2-3 letters)
- Ensure positive values for costs and quantities
