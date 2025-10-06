#!/usr/bin/env python3
"""
Test script to verify deployment is working correctly
"""
import os
import sys
import sqlite3

def test_directories():
    """Test that required directories exist"""
    required_dirs = ['uploads', 'src', 'templates', 'static']
    missing_dirs = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ All required directories present")
    return True

def test_database():
    """Test database connectivity"""
    db_path = 'uploads/product_database_AGT_Bothell.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"✅ Database accessible with {count} products")
        
        # Test concentrate products specifically
        cursor.execute("""
            SELECT COUNT(*) 
            FROM products 
            WHERE `Product Type*` = 'Concentrate'
        """)
        concentrate_count = cursor.fetchone()[0]
        print(f"✅ Found {concentrate_count} concentrate products")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    required_modules = [
        'flask', 'pandas', 'openpyxl', 'docx', 'qrcode', 'PIL'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        print("Install missing modules with: pip install -r requirements.txt")
        return False
    
    print("✅ All required modules imported successfully")
    return True

def test_app():
    """Test that the Flask app can be imported and configured"""
    try:
        sys.path.insert(0, '.')
        from app import app
        
        print(f"✅ Flask app imported successfully")
        print(f"   Debug mode: {app.config.get('DEBUG', 'Not set')}")
        print(f"   Secret key set: {'YES' if app.config.get('SECRET_KEY') else 'NO'}")
        
        return True
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AGT Label Maker Deployment")
    print("=" * 40)
    
    tests = [
        ("Directories", test_directories),
        ("Module Imports", test_imports), 
        ("Database", test_database),
        ("Flask App", test_app)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Deployment is ready.")
        print("\n📋 Next steps:")
        print("1. Upload all files to your web server")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Configure web server to point to wsgi.py")
        print("4. Set environment variables (SECRET_KEY)")
        print("5. Restart web server")
    else:
        print("⚠️ Some tests failed. Fix the issues above before deploying.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
