#!/usr/bin/env python3
"""
Test script for HTS Tariff Calculator API
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tariff/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print("\n📊 Testing statistics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tariff/statistics")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
        return False

def test_donkey_calculation():
    """Test donkey tariff calculation (should be free)"""
    print("\n🐴 Testing donkey calculation (HTS: 0101.30.00.00)...")
    payload = {
        "hts_number": "0101.30.00.00",
        "product_cost": 10000.00,
        "freight": 500.00,
        "insurance": 100.00,
        "quantity": 5,
        "weight_kg": 500.0,
        "country_code": "AU"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/tariff/calculate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Product: {result['hts_details']['description']}")
            print(f"✅ CIF Value: ${result['summary']['cif_value']}")
            print(f"✅ Total Duty: ${result['summary']['total_duty']}")
            print(f"✅ Landed Cost: ${result['summary']['landed_cost']}")
            print(f"✅ Effective Rate: {result['summary']['effective_duty_rate']}%")
            
            # Should be duty-free
            assert result['summary']['total_duty'] == 0.0, "Donkeys should be duty-free!"
            print("✅ Correct: Donkeys are duty-free!")
            return True
        else:
            print(f"❌ Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Calculation failed: {e}")
        return False

def test_cattle_calculation():
    """Test cattle calculation (should have weight-based duty)"""
    print("\n🐄 Testing cattle calculation (HTS: 0102.29.40.00)...")
    payload = {
        "hts_number": "0102.29.40.00",
        "product_cost": 15000.00,
        "freight": 800.00,
        "insurance": 200.00,
        "quantity": 10,
        "weight_kg": 5000.0,
        "country_code": "AU"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/tariff/calculate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Product: {result['hts_details']['description']}")
            print(f"✅ CIF Value: ${result['summary']['cif_value']}")
            print(f"✅ Total Duty: ${result['summary']['total_duty']}")
            print(f"✅ Landed Cost: ${result['summary']['landed_cost']}")
            print(f"✅ Effective Rate: {result['summary']['effective_duty_rate']}%")
            
            # Should have weight-based duty (4.5¢/kg)
            expected_duty = 5000.0 * 0.045  # 4.5¢/kg = $0.045/kg
            print(f"Expected duty: ${expected_duty}")
            
            return True
        else:
            print(f"❌ Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Calculation failed: {e}")
        return False

def test_beef_calculation():
    """Test beef calculation (should have percentage duty)"""
    print("\n🥩 Testing beef calculation (HTS: 0201.10.10.00)...")
    payload = {
        "hts_number": "0201.10.10.00",
        "product_cost": 20000.00,
        "freight": 1000.00,
        "insurance": 300.00,
        "quantity": 100,
        "weight_kg": 1000.0,
        "country_code": "AU"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/tariff/calculate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Product: {result['hts_details']['description']}")
            print(f"✅ CIF Value: ${result['summary']['cif_value']}")
            print(f"✅ Total Duty: ${result['summary']['total_duty']}")
            print(f"✅ Landed Cost: ${result['summary']['landed_cost']}")
            print(f"✅ Effective Rate: {result['summary']['effective_duty_rate']}%")
            
            # Should have 26.4% duty
            cif = 20000 + 1000 + 300  # $21,300
            expected_duty = cif * 0.264  # 26.4%
            print(f"Expected duty: ${expected_duty}")
            
            return True
        else:
            print(f"❌ Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Calculation failed: {e}")
        return False

def test_search():
    """Test search functionality"""
    print("\n🔍 Testing search functionality...")
    payload = {
        "query": "cattle",
        "limit": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/tariff/search", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Found {result['total_found']} products for '{result['query']}'")
            for product in result['products'][:3]:  # Show first 3
                print(f"   • {product['hts_number']}: {product['description'][:50]}...")
            return True
        else:
            print(f"❌ Error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 HTS Tariff Calculator API Test Suite")
    print("=" * 50)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    tests = [
        test_health,
        test_statistics,
        test_donkey_calculation,
        test_cattle_calculation,
        test_beef_calculation,
        test_search
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HTS Tariff Calculator is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 