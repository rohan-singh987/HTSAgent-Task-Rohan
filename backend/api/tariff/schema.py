"""
Pydantic schemas for HTS Tariff Calculator API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class DutyTypeEnum(str, Enum):
    """Enum for duty types"""
    PERCENTAGE = "percentage"
    SPECIFIC_WEIGHT = "specific_weight"
    SPECIFIC_UNIT = "specific_unit"
    COMPOUND = "compound"
    FREE = "free"
    COMPLEX = "complex"


class TariffCalculationRequest(BaseModel):
    """Request schema for tariff calculation"""
    hts_number: str = Field(..., description="HTS product code", example="0101.30.00.00")
    product_cost: float = Field(..., gt=0, description="Product cost in USD", example=10000.00)
    freight: float = Field(default=0.0, ge=0, description="Freight cost in USD", example=500.00)
    insurance: float = Field(default=0.0, ge=0, description="Insurance cost in USD", example=100.00)
    quantity: int = Field(..., gt=0, description="Number of units", example=5)
    weight_kg: float = Field(..., gt=0, description="Total weight in kilograms", example=500.0)
    country_code: str = Field(default="US", description="Country of origin code", example="AU")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    @validator('hts_number')
    def validate_hts_number(cls, v):
        """Validate HTS number format"""
        v = str(v).strip()
        if not v:
            raise ValueError("HTS number cannot be empty")
        # Basic format validation - HTS numbers are typically 10 digits
        if len(v.replace('.', '')) < 8:
            raise ValueError("HTS number appears to be too short")
        return v
    
    @validator('country_code')
    def validate_country_code(cls, v):
        """Validate country code format"""
        v = str(v).strip().upper()
        if len(v) < 2 or len(v) > 3:
            raise ValueError("Country code should be 2-3 characters")
        return v


class DutyComponent(BaseModel):
    """Individual duty component"""
    type: DutyTypeEnum
    rate: float
    unit: str
    description: str
    amount: float


class DutyCalculationResult(BaseModel):
    """Result of duty calculation"""
    duty_type: DutyTypeEnum
    original_rate: str
    total_amount: float
    effective_rate: float
    applicable: bool
    components: List[DutyComponent]
    notes: List[str] = []


class HTSDetails(BaseModel):
    """HTS product details"""
    number: str
    description: str
    unit_of_measure: Optional[str]


class InputValues(BaseModel):
    """Input values used in calculation"""
    product_cost: float
    freight: float
    insurance: float
    quantity: int
    weight_kg: float
    country_code: str
    cif_value: float


class CalculationSummary(BaseModel):
    """Summary of the calculation"""
    cif_value: float
    total_duty: float
    landed_cost: float
    effective_duty_rate: float


class TariffCalculationResponse(BaseModel):
    """Response schema for tariff calculation"""
    hts_details: HTSDetails
    input_values: InputValues
    duty_calculations: Dict[str, DutyCalculationResult]
    summary: CalculationSummary
    session_id: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HTSProductRequest(BaseModel):
    """Request to add/update HTS product"""
    hts_number: str = Field(..., description="HTS product code")
    description: str = Field(..., description="Product description")
    unit_of_measure: Optional[str] = Field(None, description="Unit of measure")
    general_duty_rate: Optional[str] = Field(None, description="General duty rate")
    special_duty_rate: Optional[str] = Field(None, description="Special duty rate")
    column2_duty_rate: Optional[str] = Field(None, description="Column 2 duty rate")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional information")


class HTSProductResponse(BaseModel):
    """Response schema for HTS product"""
    id: int
    hts_number: str
    description: str
    unit_of_measure: Optional[str]
    general_duty_rate: Optional[str]
    special_duty_rate: Optional[str]
    column2_duty_rate: Optional[str]
    additional_info: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HTSSearchRequest(BaseModel):
    """Request schema for HTS product search"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class HTSSearchResponse(BaseModel):
    """Response schema for HTS product search"""
    products: List[HTSProductResponse]
    total_found: int
    query: str


class BulkImportRequest(BaseModel):
    """Request schema for bulk import"""
    csv_file_path: str = Field(..., description="Path to CSV file")


class BulkImportResponse(BaseModel):
    """Response schema for bulk import"""
    imported: int
    updated: int
    errors: int
    total_processed: int
    message: str


class CalculationHistoryResponse(BaseModel):
    """Response schema for calculation history"""
    id: int
    session_id: str
    hts_number: str
    country_code: str
    product_cost: float
    freight: float
    insurance: float
    quantity: int
    weight_kg: float
    cif_value: float
    total_duty: float
    landed_cost: float
    calculation_details: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """Response schema for history list"""
    calculations: List[CalculationHistoryResponse]
    total_count: int
    session_id: Optional[str]


class StatisticsResponse(BaseModel):
    """Response schema for database statistics"""
    total_hts_products: int
    total_countries: int
    total_calculations: int
    recent_calculations: int


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str]
    error_code: Optional[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database_connected: bool
    total_hts_products: int
    timestamp: datetime = Field(default_factory=datetime.utcnow) 