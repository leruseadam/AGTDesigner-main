#!/usr/bin/env python3
"""
Quick App Test with Environment Variables
Tests the app with proper environment variables set
"""

import os
import sys

def test_app_with_env():
    """Test the app with environment variables set"""
    
    print("🧪 Testing App with Environment Variables...")
    print("=" * 50)
    
    # Set environment variables
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    print("✅ Environment variables set")
    
    # Test database connection
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ['DB_PORT']
        )
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products;")
        count = cur.fetchone()[0]
        
        print(f"✅ Database connection successful - {count} products")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test app import
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        
        print("✅ App imported successfully")
        
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            
            # Test a simple route
            with app.test_client() as client:
                try:
                    response = client.get('/')
                    print(f"✅ App responds to requests (status: {response.status_code})")
                    return True
                except Exception as e:
                    print(f"❌ App doesn't respond to requests: {e}")
                    return False
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def check_wsgi_file():
    """Check the WSGI file configuration"""
    
    print("\n🔍 Checking WSGI File...")
    print("=" * 25)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file not found: {wsgi_file}")
        return False
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Check for key elements
        checks = [
            ('from app import app', 'App import'),
            ('application = app', 'Application assignment'),
            ('adamcordova-4822.postgres.pythonanywhere-services.com', 'PostgreSQL host'),
            ('os.environ[\'DB_HOST\']', 'Database host env var'),
            ('configure_production_logging', 'Production logging')
        ]
        
        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading WSGI file: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Quick App Test")
    print("=" * 20)
    
    # Test app with environment variables
    app_ok = test_app_with_env()
    
    # Check WSGI file
    wsgi_ok = check_wsgi_file()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"App Test: {'✅' if app_ok else '❌'}")
    print(f"WSGI File: {'✅' if wsgi_ok else '❌'}")
    
    if app_ok and wsgi_ok:
        print("\n🎉 Everything looks good!")
        print("💡 The issue might be in PythonAnywhere Web configuration")
        print("💡 Check the Web tab settings and error logs")
    else:
        print("\n⚠️ Some issues found")
        if not app_ok:
            print("- App test failed")
        if not wsgi_ok:
            print("- WSGI file issues")

if __name__ == "__main__":
    main()
