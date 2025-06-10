"""
HTS Duty Calculator Engine
Handles parsing and calculation of various duty rate formats
"""
import re
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DutyType(Enum):
    """Types of duty rates"""
    PERCENTAGE = "percentage"
    SPECIFIC_WEIGHT = "specific_weight"  # ¢/kg
    SPECIFIC_UNIT = "specific_unit"      # $/unit
    COMPOUND = "compound"                # Multiple components
    FREE = "free"
    COMPLEX = "complex"                  # Complex formulas


@dataclass
class DutyComponent:
    """Individual duty component"""
    type: DutyType
    rate: float
    unit: str
    description: str
    amount: Decimal = Decimal('0.00')


@dataclass
class DutyCalculation:
    """Result of duty calculation"""
    duty_type: DutyType
    original_rate: str
    components: List[DutyComponent]
    total_amount: Decimal
    effective_rate: float  # As percentage of CIF value
    applicable: bool = True
    notes: List[str] = None


class DutyCalculator:
    """Advanced duty calculator for HTS codes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_duty_rate(self, duty_str: str, cif_value: Decimal, 
                       weight_kg: Optional[float] = None, 
                       quantity: Optional[int] = None) -> DutyCalculation:
        """
        Parse and calculate duty from duty rate string
        
        Args:
            duty_str: Duty rate string (e.g., "5%", "2.5¢/kg", "$1.50/unit")
            cif_value: CIF value in USD
            weight_kg: Product weight in kilograms
            quantity: Number of units
        
        Returns:
            DutyCalculation object with detailed breakdown
        """
        if not duty_str or pd.isna(duty_str):
            return self._create_free_duty(duty_str or "")
        
        duty_str = str(duty_str).strip().lower()
        
        if not duty_str or duty_str in ["", "free", "0", "0%"]:
            return self._create_free_duty(duty_str)
        
        # Try different parsing methods
        if self._is_percentage_duty(duty_str):
            return self._calculate_percentage_duty(duty_str, cif_value)
        elif self._is_weight_duty(duty_str):
            return self._calculate_weight_duty(duty_str, cif_value, weight_kg)
        elif self._is_unit_duty(duty_str):
            return self._calculate_unit_duty(duty_str, cif_value, quantity)
        elif self._is_compound_duty(duty_str):
            return self._calculate_compound_duty(duty_str, cif_value, weight_kg, quantity)
        else:
            return self._calculate_complex_duty(duty_str, cif_value, weight_kg, quantity)
    
    def _create_free_duty(self, duty_str: str) -> DutyCalculation:
        """Create a free duty calculation"""
        return DutyCalculation(
            duty_type=DutyType.FREE,
            original_rate=duty_str,
            components=[DutyComponent(
                type=DutyType.FREE,
                rate=0.0,
                unit="",
                description="Duty-free",
                amount=Decimal('0.00')
            )],
            total_amount=Decimal('0.00'),
            effective_rate=0.0,
            notes=["Product qualifies for duty-free entry"]
        )
    
    def _is_percentage_duty(self, duty_str: str) -> bool:
        """Check if duty is percentage-based"""
        return bool(re.search(r'\d+\.?\d*\s*%', duty_str))
    
    def _is_weight_duty(self, duty_str: str) -> bool:
        """Check if duty is weight-based"""
        return bool(re.search(r'¢/kg|cents/kg|cent/kg', duty_str))
    
    def _is_unit_duty(self, duty_str: str) -> bool:
        """Check if duty is unit-based"""
        return bool(re.search(r'\$/unit|\$\s*/\s*unit|dollar/unit', duty_str))
    
    def _is_compound_duty(self, duty_str: str) -> bool:
        """Check if duty has multiple components"""
        return '+' in duty_str or 'plus' in duty_str or '&' in duty_str
    
    def _calculate_percentage_duty(self, duty_str: str, cif_value: Decimal) -> DutyCalculation:
        """Calculate percentage-based duty"""
        # Extract percentage rate
        match = re.search(r'([\d.]+)\s*%', duty_str)
        if not match:
            return self._create_error_duty(duty_str, "Could not parse percentage rate")
        
        rate = float(match.group(1))
        amount = (cif_value * Decimal(str(rate)) / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        component = DutyComponent(
            type=DutyType.PERCENTAGE,
            rate=rate,
            unit="%",
            description=f"{rate}% of CIF value",
            amount=amount
        )
        
        return DutyCalculation(
            duty_type=DutyType.PERCENTAGE,
            original_rate=duty_str,
            components=[component],
            total_amount=amount,
            effective_rate=rate
        )
    
    def _calculate_weight_duty(self, duty_str: str, cif_value: Decimal, 
                              weight_kg: Optional[float]) -> DutyCalculation:
        """Calculate weight-based duty (¢/kg)"""
        if weight_kg is None:
            return self._create_error_duty(duty_str, "Weight required for weight-based duty")
        
        # Extract cents per kg rate
        match = re.search(r'([\d.]+)\s*¢/kg', duty_str)
        if not match:
            return self._create_error_duty(duty_str, "Could not parse weight rate")
        
        cents_per_kg = float(match.group(1))
        amount = (Decimal(str(cents_per_kg)) * Decimal(str(weight_kg)) / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        effective_rate = float((amount / cif_value * 100)) if cif_value > 0 else 0.0
        
        component = DutyComponent(
            type=DutyType.SPECIFIC_WEIGHT,
            rate=cents_per_kg,
            unit="¢/kg",
            description=f"{cents_per_kg}¢/kg × {weight_kg}kg",
            amount=amount
        )
        
        return DutyCalculation(
            duty_type=DutyType.SPECIFIC_WEIGHT,
            original_rate=duty_str,
            components=[component],
            total_amount=amount,
            effective_rate=effective_rate
        )
    
    def _calculate_unit_duty(self, duty_str: str, cif_value: Decimal, 
                            quantity: Optional[int]) -> DutyCalculation:
        """Calculate unit-based duty ($/unit)"""
        if quantity is None:
            return self._create_error_duty(duty_str, "Quantity required for unit-based duty")
        
        # Extract dollars per unit rate
        match = re.search(r'\$?([\d.]+)\s*/?\s*unit', duty_str)
        if not match:
            return self._create_error_duty(duty_str, "Could not parse unit rate")
        
        dollars_per_unit = float(match.group(1))
        amount = (Decimal(str(dollars_per_unit)) * Decimal(str(quantity))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        effective_rate = float((amount / cif_value * 100)) if cif_value > 0 else 0.0
        
        component = DutyComponent(
            type=DutyType.SPECIFIC_UNIT,
            rate=dollars_per_unit,
            unit="$/unit",
            description=f"${dollars_per_unit}/unit × {quantity} units",
            amount=amount
        )
        
        return DutyCalculation(
            duty_type=DutyType.SPECIFIC_UNIT,
            original_rate=duty_str,
            components=[component],
            total_amount=amount,
            effective_rate=effective_rate
        )
    
    def _calculate_compound_duty(self, duty_str: str, cif_value: Decimal,
                                weight_kg: Optional[float], quantity: Optional[int]) -> DutyCalculation:
        """Calculate compound duty (multiple components)"""
        components = []
        total_amount = Decimal('0.00')
        
        # Split by common delimiters
        parts = re.split(r'\s*[\+&]\s*|,\s*|\s+plus\s+', duty_str)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Calculate each component
            if self._is_percentage_duty(part):
                calc = self._calculate_percentage_duty(part, cif_value)
            elif self._is_weight_duty(part):
                calc = self._calculate_weight_duty(part, cif_value, weight_kg)
            elif self._is_unit_duty(part):
                calc = self._calculate_unit_duty(part, cif_value, quantity)
            else:
                continue
            
            if calc.components:
                components.extend(calc.components)
                total_amount += calc.total_amount
        
        effective_rate = float((total_amount / cif_value * 100)) if cif_value > 0 else 0.0
        
        return DutyCalculation(
            duty_type=DutyType.COMPOUND,
            original_rate=duty_str,
            components=components,
            total_amount=total_amount,
            effective_rate=effective_rate,
            notes=[f"Compound duty with {len(components)} components"]
        )
    
    def _calculate_complex_duty(self, duty_str: str, cif_value: Decimal,
                               weight_kg: Optional[float], quantity: Optional[int]) -> DutyCalculation:
        """Handle complex or unparseable duty strings"""
        
        # Try to extract any numeric values and make educated guesses
        percentage_matches = re.findall(r'([\d.]+)\s*%', duty_str)
        weight_matches = re.findall(r'([\d.]+)\s*¢/kg', duty_str)
        unit_matches = re.findall(r'\$?([\d.]+)\s*/?\s*unit', duty_str)
        
        components = []
        total_amount = Decimal('0.00')
        notes = ["Complex duty structure - manual verification recommended"]
        
        # Process found components
        for pct in percentage_matches:
            rate = float(pct)
            amount = (cif_value * Decimal(str(rate)) / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            components.append(DutyComponent(
                type=DutyType.PERCENTAGE,
                rate=rate,
                unit="%",
                description=f"{rate}% (estimated)",
                amount=amount
            ))
            total_amount += amount
        
        for weight_rate in weight_matches:
            if weight_kg:
                rate = float(weight_rate)
                amount = (Decimal(str(rate)) * Decimal(str(weight_kg)) / 100).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                components.append(DutyComponent(
                    type=DutyType.SPECIFIC_WEIGHT,
                    rate=rate,
                    unit="¢/kg",
                    description=f"{rate}¢/kg (estimated)",
                    amount=amount
                ))
                total_amount += amount
        
        for unit_rate in unit_matches:
            if quantity:
                rate = float(unit_rate)
                amount = (Decimal(str(rate)) * Decimal(str(quantity))).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                components.append(DutyComponent(
                    type=DutyType.SPECIFIC_UNIT,
                    rate=rate,
                    unit="$/unit",
                    description=f"${rate}/unit (estimated)",
                    amount=amount
                ))
                total_amount += amount
        
        if not components:
            # Could not parse anything
            return self._create_error_duty(duty_str, "Unable to parse duty structure")
        
        effective_rate = float((total_amount / cif_value * 100)) if cif_value > 0 else 0.0
        
        return DutyCalculation(
            duty_type=DutyType.COMPLEX,
            original_rate=duty_str,
            components=components,
            total_amount=total_amount,
            effective_rate=effective_rate,
            notes=notes
        )
    
    def _create_error_duty(self, duty_str: str, error_msg: str) -> DutyCalculation:
        """Create an error duty calculation"""
        return DutyCalculation(
            duty_type=DutyType.COMPLEX,
            original_rate=duty_str,
            components=[],
            total_amount=Decimal('0.00'),
            effective_rate=0.0,
            applicable=False,
            notes=[f"Error: {error_msg}"]
        )
    
    def calculate_cif_value(self, product_cost: float, freight: float, 
                           insurance: float) -> Decimal:
        """Calculate CIF (Cost, Insurance, Freight) value"""
        return (Decimal(str(product_cost)) + 
                Decimal(str(freight)) + 
                Decimal(str(insurance))).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
    
    def calculate_landed_cost(self, cif_value: Decimal, total_duty: Decimal) -> Decimal:
        """Calculate total landed cost"""
        return (cif_value + total_duty).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        ) 