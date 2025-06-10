# HTS Tariff Calculator - Task 2 Implementation

A sophisticated tariff calculation engine that computes duties, CIF values, and landed costs for HTS products with advanced duty rate parsing capabilities.

## 🏗️ Architecture Overview

```
HTS Tariff Calculator/
├── Database Layer
│   ├── SQLite Database (hts_tariff.db)
│   ├── SQLAlchemy Models (HTSProduct, Country, CalculationHistory)
│   └── Connection Management
├── Business Logic Layer
│   ├── DutyCalculator (Advanced parsing engine)
│   ├── HTSDataService (Database operations)
│   └── Country Management
├── API Layer
│   ├── FastAPI Router (/api/v1/tariff/)
│   ├── Pydantic Schemas (Validation)
│   └── Error Handling
└── Data Layer
    ├── CSV Import/Export
    ├── Sample Data
    └── Migration Scripts
```

## ✨ Key Features

### 🧮 Advanced Duty Calculator Engine
- **Percentage Duties**: `"5.2%"` → 5.2% of CIF value
- **Weight-based Duties**: `"2.5¢/kg"` → 2.5 cents per kilogram
- **Unit-based Duties**: `"$1.50/unit"` → $1.50 per unit
- **Compound Duties**: `"5% + $0.50/kg"` → Multiple components
- **Complex Formulas**: Handles special cases and edge scenarios

### 📊 SQLite Database with Enhanced Schema
- **HTSProduct Table**: Complete product information with duty rates
- **Country Table**: Enhanced country codes (AU → Australia)
- **CalculationHistory**: Full audit trail of all calculations
- **Relationship Management**: Foreign keys and data integrity

### 🚀 REST API Endpoints
- `POST /api/v1/tariff/calculate` - Main duty calculation
- `GET /api/v1/tariff/lookup/{hts_number}` - Product details
- `POST /api/v1/tariff/search` - Search products
- `POST /api/v1/tariff/import-csv` - Bulk data import
- `GET /api/v1/tariff/history` - Calculation history
- `GET /api/v1/tariff/statistics` - Database statistics

## 🚀 Quick Start

### 1. Initialize the Database

```bash
cd backend
python scripts/load_sample_data.py
```

This will:
- Create SQLite database
- Initialize country data
- Load sample HTS products
- Display test results

### 2. Start the Server

```bash
cd backend
python main.py
```

The complete backend (RAG + Tariff) will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Tariff API**: http://127.0.0.1:8000/api/v1/tariff/

## 📋 API Usage Examples

### Calculate Tariff Duties

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tariff/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "hts_number": "0101.30.00.00",
    "product_cost": 10000.00,
    "freight": 500.00,
    "insurance": 100.00,
    "quantity": 5,
    "weight_kg": 500.0,
    "country_code": "AU"
  }'
```

**Response:**
```json
{
  "hts_details": {
    "number": "0101.30.00.00",
    "description": "Asses, mules and hinnies, live",
    "unit_of_measure": "No."
  },
  "input_values": {
    "product_cost": 10000.0,
    "freight": 500.0,
    "insurance": 100.0,
    "quantity": 5,
    "weight_kg": 500.0,
    "country_code": "AU",
    "cif_value": 10600.0
  },
  "duty_calculations": {
    "general": {
      "duty_type": "free",
      "original_rate": "Free",
      "total_amount": 0.0,
      "effective_rate": 0.0,
      "applicable": true,
      "components": [
        {
          "type": "free",
          "rate": 0.0,
          "unit": "",
          "description": "Duty-free",
          "amount": 0.0
        }
      ],
      "notes": ["Product qualifies for duty-free entry"]
    }
  },
  "summary": {
    "cif_value": 10600.0,
    "total_duty": 0.0,
    "landed_cost": 10600.0,
    "effective_duty_rate": 0.0
  }
}
```

### Search HTS Products

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tariff/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cattle",
    "limit": 10
  }'
```

### Lookup Specific Product

```bash
curl "http://127.0.0.1:8000/api/v1/tariff/lookup/0102.29.40.00"
```

## 🧪 Testing with Sample Queries

Based on the PRD requirements, here are the test queries:

### 1. Donkeys (HTS: 0101.30.00.00)
```json
{
  "hts_number": "0101.30.00.00",
  "product_cost": 5000.00,
  "freight": 200.00,
  "insurance": 50.00,
  "quantity": 2,
  "weight_kg": 300.0
}
```
**Expected**: Duty-free entry

### 2. Female Cattle (HTS: 0102.29.40.00)
```json
{
  "hts_number": "0102.29.40.00",
  "product_cost": 15000.00,
  "freight": 800.00,
  "insurance": 200.00,
  "quantity": 10,
  "weight_kg": 5000.0
}
```
**Expected**: 4.5¢/kg weight-based duty

### 3. Beef Products (HTS: 0201.10.10.00)
```json
{
  "hts_number": "0201.10.10.00",
  "product_cost": 20000.00,
  "freight": 1000.00,
  "insurance": 300.00,
  "quantity": 100,
  "weight_kg": 1000.0
}
```
**Expected**: 26.4% percentage duty

## 📊 Database Schema Details

### HTSProduct Table
```sql
CREATE TABLE hts_products (
    id INTEGER PRIMARY KEY,
    hts_number VARCHAR(15) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(50),
    general_duty_rate VARCHAR(200),
    special_duty_rate VARCHAR(200),
    column2_duty_rate VARCHAR(200),
    additional_info JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Country Table
```sql
CREATE TABLE countries (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region VARCHAR(50)
);
```

### CalculationHistory Table
```sql
CREATE TABLE calculation_history (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(100),
    hts_number VARCHAR(15),
    country_code VARCHAR(3),
    product_cost DECIMAL(12,2),
    freight DECIMAL(12,2),
    insurance DECIMAL(12,2),
    quantity INTEGER,
    weight_kg DECIMAL(10,2),
    cif_value DECIMAL(12,2),
    total_duty DECIMAL(12,2),
    landed_cost DECIMAL(12,2),
    calculation_details JSON,
    created_at TIMESTAMP
);
```

## 🔧 Advanced Duty Parsing Examples

The duty calculator handles complex duty rate formats:

### Percentage Duties
- `"5%"` → 5% of CIF value
- `"26.4%"` → 26.4% of CIF value

### Weight-based Duties
- `"2.5¢/kg"` → 2.5 cents per kilogram
- `"4.5¢/kg"` → 4.5 cents per kilogram

### Unit-based Duties
- `"$1.50/unit"` → $1.50 per unit
- `"$1.32/head"` → $1.32 per head

### Compound Duties
- `"5% + $0.50/kg"` → Both percentage and weight-based
- `"2.5% + $1.00/unit"` → Percentage plus unit-based

### Special Cases
- `"Free"` → Duty-free entry
- `"Free (AU)"` → Country-specific exemptions
- Complex formulas with multiple conditions

## 📈 Monitoring and Analytics

### Health Check
```bash
curl "http://127.0.0.1:8000/api/v1/tariff/health"
```

### Database Statistics
```bash
curl "http://127.0.0.1:8000/api/v1/tariff/statistics"
```

### Calculation History
```bash
curl "http://127.0.0.1:8000/api/v1/tariff/history?limit=10"
```

## 🔄 Data Import/Export

### Bulk Import from CSV
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tariff/import-csv" \
  -H "Content-Type: application/json" \
  -d '{"csv_file_path": "/path/to/hts_data.csv"}'
```

### Expected CSV Format
```csv
HTS Number,Description,Unit of Measure,General Rate of Duty,Special Rate of Duty,Column 2 Rate of Duty
0101.30.00.00,"Asses, mules and hinnies, live",No.,Free,Free,Free
0102.29.40.00,"Cattle, live: Other",No.,4.5¢/kg,Free,Free
```

## 🏆 Key Achievements

✅ **Advanced Duty Parser**: Handles all major duty formats  
✅ **SQLite Integration**: Lightweight, zero-config database  
✅ **Country Enhancement**: AU → Australia mapping  
✅ **Full API Coverage**: Complete REST API with validation  
✅ **Calculation History**: Complete audit trail  
✅ **Error Handling**: Comprehensive error management  
✅ **Documentation**: Full OpenAPI/Swagger docs  
✅ **Sample Data**: Ready-to-test dataset  

## 🎯 Extensibility

The tariff calculator is designed for easy extension:

- **New Duty Types**: Add new parsing logic in `DutyCalculator`
- **Additional Data Sources**: Extend CSV import functionality
- **Enhanced Countries**: Add more country-specific rules
- **Complex Formulas**: Handle advanced calculation scenarios
- **Caching**: Add Redis for high-performance scenarios
- **Batch Processing**: Handle large-scale calculations

## 🔗 Integration with RAG Service

The tariff calculator runs alongside the RAG service, providing:

- **Unified Backend**: Single FastAPI application
- **Shared Infrastructure**: Common database and configuration
- **Cross-service Queries**: Potential for hybrid Q&A + calculations
- **Consistent API Design**: Similar patterns and responses

## 📝 Next Steps

1. **Extend Data Coverage**: Import all HTS sections
2. **Add Trade Agreements**: Implement NAFTA, FTA rules
3. **Enhanced Search**: Fuzzy matching and categorization
4. **Reporting**: Export calculations to Excel/PDF
5. **Frontend Integration**: Build user interface
6. **Performance Optimization**: Add caching and indexing

The HTS Tariff Calculator provides a solid foundation for accurate duty calculations with room for extensive customization and enhancement! 