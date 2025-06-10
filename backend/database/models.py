"""
SQLAlchemy models for HTS Tariff Calculator Database
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class HTSProduct(Base):
    """HTS Product table for storing tariff data"""
    __tablename__ = "hts_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hts_number = Column(String(15), nullable=False, index=True)
    description = Column(Text)
    unit_of_measure = Column(String(50))
    general_duty_rate = Column(String(200))
    special_duty_rate = Column(String(200))
    column2_duty_rate = Column(String(200))
    additional_info = Column(JSON)  # For storing complex duty structures
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to calculations
    calculations = relationship("CalculationHistory", back_populates="hts_product")
    
    def __repr__(self):
        return f"<HTSProduct(hts_number='{self.hts_number}', description='{self.description[:50]}...')>"


class Country(Base):
    """Country codes and names table"""
    __tablename__ = "countries"
    
    code = Column(String(3), primary_key=True)  # ISO 3166-1 alpha-2 codes
    name = Column(String(100), nullable=False)
    region = Column(String(50))
    
    # Relationship to calculations
    calculations = relationship("CalculationHistory", back_populates="country")
    
    def __repr__(self):
        return f"<Country(code='{self.code}', name='{self.name}')>"


class CalculationHistory(Base):
    """Store calculation history for auditing and analytics"""
    __tablename__ = "calculation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    hts_number = Column(String(15), ForeignKey('hts_products.hts_number'))
    country_code = Column(String(3), ForeignKey('countries.code'))
    
    # Input values
    product_cost = Column(Numeric(12, 2))
    freight = Column(Numeric(12, 2))
    insurance = Column(Numeric(12, 2))
    quantity = Column(Integer)
    weight_kg = Column(Numeric(10, 2))
    
    # Calculated values
    cif_value = Column(Numeric(12, 2))
    general_duty_amount = Column(Numeric(12, 2))
    special_duty_amount = Column(Numeric(12, 2))
    column2_duty_amount = Column(Numeric(12, 2))
    total_duty = Column(Numeric(12, 2))
    landed_cost = Column(Numeric(12, 2))
    
    # Metadata
    calculation_details = Column(JSON)  # Store detailed breakdown
    applicable_agreements = Column(JSON)  # Store applicable trade agreements
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hts_product = relationship("HTSProduct", back_populates="calculations")
    country = relationship("Country", back_populates="calculations")
    
    def __repr__(self):
        return f"<CalculationHistory(hts_number='{self.hts_number}', total_duty={self.total_duty})>"


class HTSSection(Base):
    """HTS Sections for better organization"""
    __tablename__ = "hts_sections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    section_number = Column(String(10), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<HTSSection(section_number='{self.section_number}', title='{self.title}')>" 