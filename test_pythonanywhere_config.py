#!/usr/bin/env python3
"""
Test WSGI configuration for PythonAnywhere deployment
Run this in PythonAnywhere console to verify setup
"""

import sys
import os

# Test the WSGI configuration
def test_wsgi_config():
    print("🔍 Testing PythonAnywhere WSGI Configuration...")
    print("=" * 50)
    
    # Add project directory
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    print(f"✅ Project directory: {project_dir}")
    print(f"✅ Directory exists: {os.path.exists(project_dir)}")
    
    # Test imports
    try:
        print("\n📦 Testing imports...")
        import flask
        print(f"✅ Flask version: {flask.__version__}")
        
        import pandas
        print(f"✅ Pandas version: {pandas.__version__}")
        
        import openpyxl
        print(f"✅ OpenPyXL available")
        
        print("\n🚀 Testing Flask app import...")
        from app import app as application
        print(f"✅ Flask app imported: {type(application)}")
        
        # Test database
        print("\n💾 Testing database...")
        db_path = os.path.join(project_dir, 'uploads/product_database_AGT_Bothell.db')
        print(f"✅ Database path: {db_path}")
        print(f"✅ Database exists: {os.path.exists(db_path)}")
        
        if os.path.exists(db_path):
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            print(f"✅ Products in database: {count:,}")
            conn.close()
        
        print("\n🎉 WSGI configuration test PASSED!")
        print("Your app should work on PythonAnywhere!")
        
    except Exception as e:
        print(f"\n❌ WSGI test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_wsgi_config()
    if not success:
        print("\n🔧 Fix the issues above before deploying")
        sys.exit(1)