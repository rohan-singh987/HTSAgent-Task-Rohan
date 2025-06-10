"""
FastAPI router for HTS Tariff Calculator endpoints
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime

from .schema import (
    TariffCalculationRequest, TariffCalculationResponse,
    HTSProductRequest, HTSProductResponse,
    HTSSearchRequest, HTSSearchResponse,
    BulkImportRequest, BulkImportResponse,
    CalculationHistoryResponse, HistoryListResponse,
    StatisticsResponse, HealthResponse, ErrorResponse
)
from services.hts_data_service import HTSDataService
from database.connection import get_db, db_manager
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Create router
tariff_router = APIRouter()

# Global service instance (will be initialized in main.py)
hts_service: Optional[HTSDataService] = None


def get_hts_service() -> HTSDataService:
    """Dependency to get HTS data service"""
    global hts_service
    if hts_service is None:
        raise HTTPException(
            status_code=503,
            detail="HTS Data Service not initialized"
        )
    return hts_service


@tariff_router.post(
    "/calculate",
    response_model=TariffCalculationResponse,
    summary="Calculate HTS Tariff Duties",
    description="Calculate duties, CIF value, and landed cost for a given HTS product"
)
async def calculate_tariff(
    request: TariffCalculationRequest,
    service: HTSDataService = Depends(get_hts_service)
):
    """
    Calculate tariff duties for an HTS product
    
    This endpoint calculates:
    - CIF value (Cost + Insurance + Freight)
    - General, Special, and Column 2 duty rates
    - Applicable duty (usually the lowest)
    - Total landed cost
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Calculate duties
        result = service.calculate_duties(
            hts_number=request.hts_number,
            product_cost=request.product_cost,
            freight=request.freight,
            insurance=request.insurance,
            quantity=request.quantity,
            weight_kg=request.weight_kg,
            country_code=request.country_code,
            session_id=session_id
        )
        
        # Add session ID and timestamp to result
        result["session_id"] = session_id
        result["timestamp"] = datetime.utcnow()
        
        return TariffCalculationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating tariff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during calculation")


@tariff_router.get(
    "/lookup/{hts_number}",
    response_model=HTSProductResponse,
    summary="Lookup HTS Product",
    description="Get details for a specific HTS product by its number"
)
async def lookup_hts_product(
    hts_number: str,
    service: HTSDataService = Depends(get_hts_service)
):
    """Lookup HTS product details by HTS number"""
    try:
        product = service.get_hts_product(hts_number)
        if not product:
            raise HTTPException(status_code=404, detail=f"HTS number {hts_number} not found")
        
        return HTSProductResponse.from_orm(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error looking up HTS product {hts_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@tariff_router.post(
    "/search",
    response_model=HTSSearchResponse,
    summary="Search HTS Products",
    description="Search HTS products by description or HTS number"
)
async def search_hts_products(
    request: HTSSearchRequest,
    service: HTSDataService = Depends(get_hts_service)
):
    """Search HTS products by query string"""
    try:
        products = service.search_hts_products(request.query, request.limit)
        
        return HTSSearchResponse(
            products=[HTSProductResponse.from_orm(p) for p in products],
            total_found=len(products),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching HTS products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search")


@tariff_router.post(
    "/products",
    response_model=HTSProductResponse,
    summary="Add/Update HTS Product",
    description="Add a new HTS product or update an existing one"
)
async def add_hts_product(
    request: HTSProductRequest,
    service: HTSDataService = Depends(get_hts_service)
):
    """Add or update an HTS product"""
    try:
        product = service.add_hts_product(
            hts_number=request.hts_number,
            description=request.description,
            unit_of_measure=request.unit_of_measure,
            general_duty_rate=request.general_duty_rate,
            special_duty_rate=request.special_duty_rate,
            column2_duty_rate=request.column2_duty_rate,
            additional_info=request.additional_info
        )
        
        return HTSProductResponse.from_orm(product)
        
    except Exception as e:
        logger.error(f"Error adding HTS product: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@tariff_router.get(
    "/products",
    response_model=List[HTSProductResponse],
    summary="List HTS Products",
    description="Get a paginated list of all HTS products"
)
async def list_hts_products(
    limit: int = 100,
    offset: int = 0,
    service: HTSDataService = Depends(get_hts_service)
):
    """Get a paginated list of HTS products"""
    try:
        products = service.get_all_hts_products(limit=limit, offset=offset)
        return [HTSProductResponse.from_orm(p) for p in products]
        
    except Exception as e:
        logger.error(f"Error listing HTS products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@tariff_router.post(
    "/import-csv",
    response_model=BulkImportResponse,
    summary="Bulk Import HTS Data",
    description="Import HTS products from a CSV file"
)
async def bulk_import_hts_data(
    request: BulkImportRequest,
    background_tasks: BackgroundTasks,
    service: HTSDataService = Depends(get_hts_service)
):
    """Bulk import HTS data from CSV file"""
    try:
        # Run import in background for large files
        result = await service.bulk_import_hts_data(request.csv_file_path)
        
        message = f"Import completed: {result['imported']} imported, {result['updated']} updated, {result['errors']} errors"
        
        return BulkImportResponse(
            imported=result['imported'],
            updated=result['updated'],
            errors=result['errors'],
            total_processed=result['total_processed'],
            message=message
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        logger.error(f"Error during bulk import: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during import")


@tariff_router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="Get Calculation History",
    description="Get calculation history for a session or all calculations"
)
async def get_calculation_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    service: HTSDataService = Depends(get_hts_service)
):
    """Get calculation history"""
    try:
        history = service.get_calculation_history(session_id=session_id, limit=limit)
        
        return HistoryListResponse(
            calculations=[CalculationHistoryResponse.from_orm(h) for h in history],
            total_count=len(history),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error getting calculation history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@tariff_router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get Database Statistics",
    description="Get statistics about the HTS database"
)
async def get_statistics(
    service: HTSDataService = Depends(get_hts_service)
):
    """Get database statistics"""
    try:
        stats = service.get_statistics()
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@tariff_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health of the tariff calculator service"
)
async def health_check(
    service: HTSDataService = Depends(get_hts_service)
):
    """Health check endpoint"""
    try:
        # Test database connectivity
        stats = service.get_statistics()
        
        return HealthResponse(
            status="healthy",
            database_connected=True,
            total_hts_products=stats["total_hts_products"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            total_hts_products=0
        )


@tariff_router.post(
    "/reload-data",
    summary="Reload HTS Data",
    description="Reload HTS data and reinitialize the service"
)
async def reload_data(
    service: HTSDataService = Depends(get_hts_service)
):
    """Reload HTS data"""
    try:
        await service.initialize()
        
        return {"message": "HTS data reloaded successfully"}
        
    except Exception as e:
        logger.error(f"Error reloading data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during reload")


# Note: Exception handlers should be added to the main FastAPI app, not the router
# They are defined in main.py 