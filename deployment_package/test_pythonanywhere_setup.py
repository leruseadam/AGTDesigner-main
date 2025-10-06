#!/usr/bin/env python3
"""
PythonAnywhere Deployment Test Script
Tests all critical components of the Label Maker application
"""

import sys
import os
import traceback
from pathlib import Path

def test_python_version():
    """Test Python version compatibility."""
    print(f"🐍 Testing Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor != 11:
        print(f"⚠️  Warning: Expected Python 3.11, got {version.major}.{version.minor}")
        return False
    
    print("✅ Python version OK")
    return True

def test_imports():
    """Test critical imports."""
    print(f"\n📦 Testing imports...")
    
    imports = [
        ('flask', 'Flask'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'), 
        ('docx', 'python-docx'),
        ('PIL', 'Pillow'),
        ('requests', 'requests'),
        ('fuzzywuzzy', 'fuzzywuzzy')
    ]
    
    optional_imports = [
        ('jellyfish', 'jellyfish'),
        ('Levenshtein', 'python-Levenshtein')
    ]
    
    success = True
    
    # Test required imports
    for module, package in imports:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            success = False
    
    # Test optional imports
    print(f"\n🔧 Testing optional imports...")
    for module, package in optional_imports:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️  {package}: Not available (fallback will be used)")
    
    return success

def test_directories():
    """Test required directories exist."""
    print(f"\n📁 Testing directories...")
    
    required_dirs = ['uploads', 'output', 'cache', 'sessions', 'static', 'templates']
    success = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ missing")
            success = False
    
    return success

def test_app_import():
    """Test Flask application import."""
    print(f"\n🌐 Testing Flask app import...")
    
    try:
        from app import app
        print("✅ Flask app imported successfully")
        
        # Test app configuration
        print(f"   Debug mode: {app.debug}")
        print(f"   Testing mode: {app.testing}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        print("   Traceback:")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration files."""
    print(f"\n⚙️  Testing configuration...")
    
    config_files = ['config.py', 'pythonanywhere_config.py']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}")
        else:
            print(f"⚠️  {config_file} not found")
    
    return True

def test_wsgi():
    """Test WSGI configuration."""
    print(f"\n🔧 Testing WSGI configuration...")
    
    wsgi_files = ['wsgi_configured.py', 'wsgi_pythonanywhere_python311.py']
    wsgi_found = False
    
    for wsgi_file in wsgi_files:
        if os.path.exists(wsgi_file):
            print(f"✅ {wsgi_file}")
            wsgi_found = True
        else:
            print(f"⚠️  {wsgi_file} not found")
    
    if not wsgi_found:
        print("❌ No WSGI configuration found")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 PythonAnywhere Deployment Test")
    print("=" * 40)
    
    tests = [
        test_python_version,
        test_imports,
        test_directories,
        test_config,
        test_wsgi,
        test_app_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Test Summary")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("✅ Ready for PythonAnywhere deployment")
        return 0
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        print("❌ Fix issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())