#!/usr/bin/env python3
"""
Test script to verify web deployment configuration
"""

import os
import sys

def test_web_config():
    """Test the web deployment configuration"""
    print("🌐 Testing Web Deployment Configuration...")
    print("=" * 50)
    
    # Check if we're in PythonAnywhere environment
    pythonanywhere_domain = os.environ.get('PYTHONANYWHERE_DOMAIN')
    http_host = os.environ.get('HTTP_HOST')
    
    if pythonanywhere_domain or 'pythonanywhere.com' in str(http_host):
        print("✅ Running in PythonAnywhere environment")
        print(f"   Domain: {pythonanywhere_domain}")
        print(f"   HTTP Host: {http_host}")
        
        # Check database environment variables
        db_host = os.environ.get('DB_HOST')
        db_name = os.environ.get('DB_NAME')
        db_user = os.environ.get('DB_USER')
        db_port = os.environ.get('DB_PORT')
        
        print(f"\n📊 Database Configuration:")
        print(f"   Host: {db_host}")
        print(f"   Database: {db_name}")
        print(f"   User: {db_user}")
        print(f"   Port: {db_port}")
        
        if db_host and db_name and db_user and db_port:
            print("✅ Database environment variables are set")
        else:
            print("❌ Missing database environment variables")
            
    else:
        print("🏠 Running in local environment")
        print("   Use run_local.py for local development")
        
    print("\n🧪 Testing app import...")
    try:
        from app import app
        print("✅ App imported successfully")
        
        # Test database connection
        with app.test_client() as client:
            response = client.get('/api/database-stats')
            if response.status_code == 200:
                print("✅ Database connection working")
                data = response.get_json()
                stats = data.get('stats', {})
                print(f"   Products: {stats.get('total_products', 'N/A')}")
                print(f"   Vendors: {stats.get('unique_vendors', 'N/A')}")
                print(f"   Brands: {stats.get('unique_brands', 'N/A')}")
            else:
                print(f"❌ Database connection failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ App import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_config()
