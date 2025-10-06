#!/usr/bin/env python3
"""
Test Database Stats Endpoint
Tests the /api/database-stats endpoint directly to verify it's working
"""

import os
import sys
import requests
import json

def set_environment_variables():
    """Set environment variables like the WSGI file does"""
    
    print("🔧 Setting Environment Variables...")
    print("=" * 40)
    
    # Set the environment variables (same as WSGI file)
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    print("✅ Environment variables set")

def test_database_stats_endpoint():
    """Test the database-stats endpoint directly"""
    
    print("\n🔗 Testing Database Stats Endpoint...")
    print("=" * 40)
    
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        
        print("✅ App imported successfully")
        
        # Test the endpoint directly
        with app.test_client() as client:
            response = client.get('/api/database-stats')
            print(f"✅ Database stats endpoint responded (status: {response.status_code})")
            
            if response.status_code == 200:
                data = response.get_json()
                stats = data.get('stats', {})
                print(f"📊 Database Stats Response:")
                print(f"   Total Products: {stats.get('total_products', 'N/A')}")
                print(f"   Unique Vendors: {stats.get('unique_vendors', 'N/A')}")
                print(f"   Unique Brands: {stats.get('unique_brands', 'N/A')}")
                print(f"   Unique Product Types: {stats.get('unique_product_types', 'N/A')}")
                
                if stats.get('total_products', 0) > 0:
                    print("✅ Database stats show real data!")
                    return True
                else:
                    print("❌ Database stats show 0 products")
                    return False
            else:
                print(f"❌ Database stats returned status {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"❌ Database stats test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection_direct():
    """Test database connection directly"""
    
    print("\n🔗 Testing Database Connection Directly...")
    print("=" * 45)
    
    try:
        import psycopg2
        from src.core.data.product_database import get_database_config
        
        config = get_database_config()
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM products;")
        total_products = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT "Vendor/Supplier*") FROM products WHERE "Vendor/Supplier*" IS NOT NULL AND "Vendor/Supplier*" != \'\' AND "Vendor/Supplier*" != \'Vendor/Supplier*\';')
        unique_vendors = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT "Product Brand") FROM products WHERE "Product Brand" IS NOT NULL AND "Product Brand" != \'\' AND "Product Brand" != \'Product Brand\';')
        unique_brands = cursor.fetchone()[0]
        
        print(f"✅ Direct database connection successful!")
        print(f"📊 Direct Database Stats:")
        print(f"   Total Products: {total_products}")
        print(f"   Unique Vendors: {unique_vendors}")
        print(f"   Unique Brands: {unique_brands}")
        
        cursor.close()
        conn.close()
        
        return total_products > 0
        
    except Exception as e:
        print(f"❌ Direct database connection failed: {e}")
        return False

def test_web_app_url():
    """Test the actual web app URL"""
    
    print("\n🌐 Testing Web App URL...")
    print("=" * 30)
    
    try:
        # Test the actual PythonAnywhere URL
        url = "https://adamcordova.pythonanywhere.com/api/database-stats"
        
        response = requests.get(url, timeout=30)
        print(f"✅ Web app responded (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"📊 Web App Database Stats:")
            print(f"   Total Products: {stats.get('total_products', 'N/A')}")
            print(f"   Unique Vendors: {stats.get('unique_vendors', 'N/A')}")
            print(f"   Unique Brands: {stats.get('unique_brands', 'N/A')}")
            
            if stats.get('total_products', 0) > 0:
                print("✅ Web app shows real data!")
                return True
            else:
                print("❌ Web app shows 0 products")
                return False
        else:
            print(f"❌ Web app returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Web app request timed out")
        return False
    except Exception as e:
        print(f"❌ Web app test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Database Stats Endpoint Test")
    print("=" * 35)
    
    # Set environment variables
    set_environment_variables()
    
    # Test database connection directly
    direct_ok = test_database_connection_direct()
    
    # Test database stats endpoint
    endpoint_ok = test_database_stats_endpoint()
    
    # Test web app URL
    web_ok = test_web_app_url()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Direct Database Connection: {'✅' if direct_ok else '❌'}")
    print(f"Database Stats Endpoint:    {'✅' if endpoint_ok else '❌'}")
    print(f"Web App URL:                {'✅' if web_ok else '❌'}")
    
    if direct_ok and endpoint_ok and web_ok:
        print("\n🎉 All tests PASSED! Database stats are working correctly.")
        print("💡 If your web app still shows 0, try:")
        print("   1. Hard refresh the browser (Ctrl+F5)")
        print("   2. Clear browser cache")
        print("   3. Check browser console for JavaScript errors")
    elif direct_ok and endpoint_ok:
        print("\n⚠️ Database and endpoint work locally, but web app has issues.")
        print("💡 Try reloading the web app on PythonAnywhere:")
        print("   1. Go to PythonAnywhere Web tab")
        print("   2. Click Reload button")
        print("   3. Wait 60 seconds")
        print("   4. Refresh your web app")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
