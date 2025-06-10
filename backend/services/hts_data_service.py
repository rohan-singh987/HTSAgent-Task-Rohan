"""
HTS Data Service
Handles database operations for HTS products and calculations
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
import pandas as pd
from decimal import Decimal

from database.connection import get_db_session, db_manager
from database.models import HTSProduct, Country, CalculationHistory, HTSSection
from .duty_calculator import DutyCalculator, DutyCalculation

logger = logging.getLogger(__name__)


class HTSDataService:
    """Service for managing HTS data and calculations"""
    
    def __init__(self):
        self.duty_calculator = DutyCalculator()
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the service and database"""
        try:
            # Create tables if they don't exist
            db_manager.create_tables()
            
            # Initialize default data
            await self._initialize_countries()
            
            self.logger.info("HTS Data Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize HTS Data Service: {e}")
            raise
    
    async def _initialize_countries(self):
        """Initialize country data"""
        try:
            db = get_db_session()
            try:
                # Check if countries already exist
                count = db.query(Country).count()
                if count > 0:
                    self.logger.info(f"Countries already initialized ({count} records)")
                    return
                
                # Add common countries
                countries = [
                    ("AU", "Australia", "Oceania"),
                    ("CA", "Canada", "North America"),
                    ("CN", "China", "Asia"),
                    ("DE", "Germany", "Europe"),
                    ("GB", "United Kingdom", "Europe"),
                    ("IN", "India", "Asia"),
                    ("JP", "Japan", "Asia"),
                    ("KR", "South Korea", "Asia"),
                    ("MX", "Mexico", "North America"),
                    ("US", "United States", "North America"),
                    ("FR", "France", "Europe"),
                    ("IT", "Italy", "Europe"),
                    ("BR", "Brazil", "South America"),
                    ("VN", "Vietnam", "Asia"),
                    ("TH", "Thailand", "Asia"),
                ]
                
                for code, name, region in countries:
                    country = Country(code=code, name=name, region=region)
                    db.add(country)
                
                db.commit()
                self.logger.info(f"Initialized {len(countries)} countries")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize countries: {e}")
    
    def add_hts_product(self, hts_number: str, description: str, 
                       unit_of_measure: str = None,
                       general_duty_rate: str = None,
                       special_duty_rate: str = None,
                       column2_duty_rate: str = None,
                       additional_info: Dict = None) -> HTSProduct:
        """Add a new HTS product to the database"""
        db = get_db_session()
        try:
            # Check if product already exists
            existing = db.query(HTSProduct).filter(
                HTSProduct.hts_number == hts_number
            ).first()
            
            if existing:
                # Update existing product
                existing.description = description
                existing.unit_of_measure = unit_of_measure
                existing.general_duty_rate = general_duty_rate
                existing.special_duty_rate = special_duty_rate
                existing.column2_duty_rate = column2_duty_rate
                existing.additional_info = additional_info or {}
                db.commit()
                return existing
            
            # Create new product
            product = HTSProduct(
                hts_number=hts_number,
                description=description,
                unit_of_measure=unit_of_measure,
                general_duty_rate=general_duty_rate,
                special_duty_rate=special_duty_rate,
                column2_duty_rate=column2_duty_rate,
                additional_info=additional_info or {}
            )
            
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error adding HTS product {hts_number}: {e}")
            raise
        finally:
            db.close()
    
    def get_hts_product(self, hts_number: str) -> Optional[HTSProduct]:
        """Get HTS product by number"""
        db = get_db_session()
        try:
            product = db.query(HTSProduct).filter(
                HTSProduct.hts_number == hts_number
            ).first()
            return product
        finally:
            db.close()
    
    def search_hts_products(self, query: str, limit: int = 20) -> List[HTSProduct]:
        """Search HTS products by description or HTS number"""
        db = get_db_session()
        try:
            # Search by HTS number or description
            products = db.query(HTSProduct).filter(
                or_(
                    HTSProduct.hts_number.like(f"%{query}%"),
                    HTSProduct.description.like(f"%{query}%")
                )
            ).limit(limit).all()
            
            return products
        finally:
            db.close()
    
    def get_all_hts_products(self, limit: int = 1000, offset: int = 0) -> List[HTSProduct]:
        """Get all HTS products with pagination"""
        db = get_db_session()
        try:
            products = db.query(HTSProduct).offset(offset).limit(limit).all()
            return products
        finally:
            db.close()
    
    def calculate_duties(self, hts_number: str, product_cost: float, 
                        freight: float, insurance: float,
                        quantity: int, weight_kg: float,
                        country_code: str = "US",
                        session_id: str = None) -> Dict[str, Any]:
        """
        Calculate duties for a given HTS product and inputs
        
        Returns comprehensive duty calculation breakdown
        """
        try:
            # Get HTS product
            product = self.get_hts_product(hts_number)
            if not product:
                raise ValueError(f"HTS number {hts_number} not found in database")
            
            # Calculate CIF value
            cif_value = self.duty_calculator.calculate_cif_value(
                product_cost, freight, insurance
            )
            
            # Calculate different duty types
            general_calc = self.duty_calculator.parse_duty_rate(
                product.general_duty_rate, cif_value, weight_kg, quantity
            )
            
            special_calc = self.duty_calculator.parse_duty_rate(
                product.special_duty_rate, cif_value, weight_kg, quantity
            )
            
            column2_calc = self.duty_calculator.parse_duty_rate(
                product.column2_duty_rate, cif_value, weight_kg, quantity
            )
            
            # Determine applicable duty (usually the lowest)
            applicable_duty = min(
                [general_calc, special_calc, column2_calc],
                key=lambda x: x.total_amount if x.applicable else float('inf')
            )
            
            # Calculate landed cost
            landed_cost = self.duty_calculator.calculate_landed_cost(
                cif_value, applicable_duty.total_amount
            )
            
            # Prepare result
            result = {
                "hts_details": {
                    "number": product.hts_number,
                    "description": product.description,
                    "unit_of_measure": product.unit_of_measure
                },
                "input_values": {
                    "product_cost": product_cost,
                    "freight": freight,
                    "insurance": insurance,
                    "quantity": quantity,
                    "weight_kg": weight_kg,
                    "country_code": country_code,
                    "cif_value": float(cif_value)
                },
                "duty_calculations": {
                    "general": self._format_duty_calculation(general_calc),
                    "special": self._format_duty_calculation(special_calc),
                    "column2": self._format_duty_calculation(column2_calc),
                    "applicable": self._format_duty_calculation(applicable_duty)
                },
                "summary": {
                    "cif_value": float(cif_value),
                    "total_duty": float(applicable_duty.total_amount),
                    "landed_cost": float(landed_cost),
                    "effective_duty_rate": applicable_duty.effective_rate
                }
            }
            
            # Save calculation history if session_id provided
            if session_id:
                self._save_calculation_history(
                    session_id, hts_number, country_code,
                    product_cost, freight, insurance, quantity, weight_kg,
                    cif_value, applicable_duty.total_amount, landed_cost,
                    result
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating duties for {hts_number}: {e}")
            raise
    
    def _format_duty_calculation(self, calc: DutyCalculation) -> Dict[str, Any]:
        """Format duty calculation for API response"""
        return {
            "duty_type": calc.duty_type.value,
            "original_rate": calc.original_rate,
            "total_amount": float(calc.total_amount),
            "effective_rate": calc.effective_rate,
            "applicable": calc.applicable,
            "components": [
                {
                    "type": comp.type.value,
                    "rate": comp.rate,
                    "unit": comp.unit,
                    "description": comp.description,
                    "amount": float(comp.amount)
                }
                for comp in calc.components
            ],
            "notes": calc.notes or []
        }
    
    def _save_calculation_history(self, session_id: str, hts_number: str,
                                 country_code: str, product_cost: float,
                                 freight: float, insurance: float,
                                 quantity: int, weight_kg: float,
                                 cif_value: Decimal, total_duty: Decimal,
                                 landed_cost: Decimal, calculation_details: Dict):
        """Save calculation to history"""
        db = get_db_session()
        try:
            history = CalculationHistory(
                session_id=session_id,
                hts_number=hts_number,
                country_code=country_code,
                product_cost=Decimal(str(product_cost)),
                freight=Decimal(str(freight)),
                insurance=Decimal(str(insurance)),
                quantity=quantity,
                weight_kg=Decimal(str(weight_kg)),
                cif_value=cif_value,
                total_duty=total_duty,
                landed_cost=landed_cost,
                calculation_details=calculation_details
            )
            
            db.add(history)
            db.commit()
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to save calculation history: {e}")
        finally:
            db.close()
    
    def get_calculation_history(self, session_id: str = None, 
                               limit: int = 50) -> List[CalculationHistory]:
        """Get calculation history"""
        db = get_db_session()
        try:
            query = db.query(CalculationHistory)
            
            if session_id:
                query = query.filter(CalculationHistory.session_id == session_id)
            
            history = query.order_by(
                CalculationHistory.created_at.desc()
            ).limit(limit).all()
            
            return history
        finally:
            db.close()
    
    async def bulk_import_hts_data(self, csv_file_path: str) -> Dict[str, int]:
        """
        Bulk import HTS data from CSV file
        Expected columns: HTS Number, Description, Unit of Measure, 
                         General Rate of Duty, Special Rate of Duty, Column 2 Rate of Duty
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Standardize column names
            column_mapping = {
                'HTS Number': 'hts_number',
                'Description': 'description',
                'Unit of Measure': 'unit_of_measure',
                'General Rate of Duty': 'general_duty_rate',
                'Special Rate of Duty': 'special_duty_rate',
                'Column 2 Rate of Duty': 'column2_duty_rate'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Track import statistics
            imported = 0
            updated = 0
            errors = 0
            
            for _, row in df.iterrows():
                try:
                    # Skip rows with missing HTS number
                    if pd.isna(row.get('hts_number')):
                        continue
                    
                    hts_number = str(row['hts_number']).strip()
                    description = str(row.get('description', '')).strip()
                    
                    # Check if product exists
                    existing = self.get_hts_product(hts_number)
                    
                    if existing:
                        # Update existing
                        existing.description = description
                        existing.unit_of_measure = str(row.get('unit_of_measure', '')).strip()
                        existing.general_duty_rate = str(row.get('general_duty_rate', '')).strip()
                        existing.special_duty_rate = str(row.get('special_duty_rate', '')).strip()
                        existing.column2_duty_rate = str(row.get('column2_duty_rate', '')).strip()
                        updated += 1
                    else:
                        # Create new
                        self.add_hts_product(
                            hts_number=hts_number,
                            description=description,
                            unit_of_measure=str(row.get('unit_of_measure', '')).strip(),
                            general_duty_rate=str(row.get('general_duty_rate', '')).strip(),
                            special_duty_rate=str(row.get('special_duty_rate', '')).strip(),
                            column2_duty_rate=str(row.get('column2_duty_rate', '')).strip()
                        )
                        imported += 1
                        
                except Exception as e:
                    self.logger.error(f"Error importing row {row.get('hts_number', 'unknown')}: {e}")
                    errors += 1
            
            result = {
                "imported": imported,
                "updated": updated,
                "errors": errors,
                "total_processed": imported + updated + errors
            }
            
            self.logger.info(f"Bulk import completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Bulk import failed: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        db = get_db_session()
        try:
            stats = {
                "total_hts_products": db.query(HTSProduct).count(),
                "total_countries": db.query(Country).count(),
                "total_calculations": db.query(CalculationHistory).count(),
                "recent_calculations": db.query(CalculationHistory).filter(
                    CalculationHistory.created_at >= func.date('now', '-7 days')
                ).count()
            }
            return stats
        finally:
            db.close() 