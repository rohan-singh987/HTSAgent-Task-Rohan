#!/usr/bin/env python3
"""
Simple test script for HTS AI Agent Frontend
"""
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_dependencies():
    """Test that all required modules can be imported"""
    print("🧪 Testing dependencies...")
    
    missing = []
    
    try:
        import streamlit
        print("  ✅ Streamlit")
    except ImportError:
        print("  ❌ Streamlit")
        missing.append("streamlit")
    
    try:
        import pandas
        print("  ✅ Pandas")
    except ImportError:
        print("  ❌ Pandas")
        missing.append("pandas")
    
    try:
        import plotly
        print("  ✅ Plotly")
    except ImportError:
        print("  ❌ Plotly")
        missing.append("plotly")
    
    try:
        import requests
        print("  ✅ Requests")
    except ImportError:
        print("  ❌ Requests")
        missing.append("requests")
    
    if missing:
        print(f"\n💡 Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def test_app_files():
    """Test that application files exist"""
    print("\n🧪 Testing application files...")
    
    required_files = ["app.py", "config.py", "utils.py", "requirements.txt"]
    missing = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}")
            missing.append(file)
    
    if missing:
        print(f"💡 Missing files: {', '.join(missing)}")
        return False
    
    return True

def test_imports():
    """Test that custom modules can be imported"""
    print("\n🧪 Testing app modules...")
    
    try:
        from config import API_BASE_URL, SAMPLE_QUESTIONS
        print("  ✅ Config module")
    except Exception as e:
        print(f"  ❌ Config module: {e}")
        return False
    
    try:
        from utils import format_currency, validate_hts_number
        print("  ✅ Utils module")
    except Exception as e:
        print(f"  ❌ Utils module: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚢 HTS AI Agent Frontend - Quick Test")
    print("=" * 40)
    
    tests = [
        test_dependencies,
        test_app_files,
        test_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Frontend is ready to use.")
        print("💡 Run: streamlit run app.py")
        return 0
    else:
        print("⚠️  Some tests failed. Fix the issues above first.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)