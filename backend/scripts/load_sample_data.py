#!/usr/bin/env python3
"""
Script to load sample HTS data into the database
"""
import sys
import asyncio
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.hts_data_service import HTSDataService
from database.connection import init_database


async def load_sample_data():
    """Load sample HTS data"""
    print("🚀 Starting HTS sample data loading...")
    
    # Initialize database
    print("📊 Initializing database...")
    init_database()
    
    # Initialize HTS service
    print("🔧 Initializing HTS Data Service...")
    service = HTSDataService()
    await service.initialize()
    
    # Load sample CSV data
    csv_path = backend_dir / "data" / "sample_hts_data.csv"
    
    if not csv_path.exists():
        print(f"❌ Sample data file not found: {csv_path}")
        return
    
    print(f"📁 Loading data from: {csv_path}")
    
    try:
        result = await service.bulk_import_hts_data(str(csv_path))
        
        print("\n✅ Data loading completed!")
        print(f"📥 Imported: {result['imported']} products")
        print(f"🔄 Updated: {result['updated']} products") 
        print(f"❌ Errors: {result['errors']} products")
        print(f"📊 Total processed: {result['total_processed']} products")
        
        # Display statistics
        stats = service.get_statistics()
        print(f"\n📈 Database Statistics:")
        print(f"   • Total HTS Products: {stats['total_hts_products']}")
        print(f"   • Total Countries: {stats['total_countries']}")
        print(f"   • Total Calculations: {stats['total_calculations']}")
        
        # Test a few products
        print("\n🧪 Testing some sample products:")
        
        test_products = [
            "0101.30.00.00",  # Donkeys (free)
            "0201.10.10.00",  # Beef (26.4%)
            "0102.29.40.00",  # Cattle (4.5¢/kg)
        ]
        
        for hts_number in test_products:
            product = service.get_hts_product(hts_number)
            if product:
                print(f"   ✓ {hts_number}: {product.description[:50]}...")
                print(f"     General Rate: {product.general_duty_rate}")
            else:
                print(f"   ✗ {hts_number}: Not found")
        
        print("\n🎉 Sample data loading complete!")
        print("🔗 You can now test the API endpoints:")
        print("   • Tariff Calculator: POST /api/v1/tariff/calculate")
        print("   • Product Lookup: GET /api/v1/tariff/lookup/{hts_number}")
        print("   • Search Products: POST /api/v1/tariff/search")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(load_sample_data()) 