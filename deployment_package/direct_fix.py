#!/usr/bin/env python3
"""
Direct PythonAnywhere Fix
Fixes the most common issues directly
"""

import os
import sys

def set_environment_variables():
    """Set environment variables directly"""
    print("🔧 Setting environment variables...")
    
    # Set the environment variables
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    print("✅ Environment variables set")
    
    # Verify they're set
    print("📋 Verification:")
    for var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']:
        value = os.environ.get(var)
        if var == 'DB_PASSWORD':
            print(f"   {var}: {'*' * len(value)}")
        else:
            print(f"   {var}: {value}")

def test_database_connection():
    """Test database connection with set variables"""
    print("\n🔗 Testing database connection...")
    
    try:
        import psycopg2
        
        # Use the environment variables we just set
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
        
        print(f"✅ Database connection successful!")
        print(f"📊 Found {count} products in database")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_app_import():
    """Test importing the app"""
    print("\n🧪 Testing app import...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the app
        from app import app
        
        print("✅ App imported successfully")
        
        # Check if it's a Flask app
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            return True
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        print("\n🔍 Error details:")
        import traceback
        traceback.print_exc()
        return False

def check_wsgi_file():
    """Check if WSGI file is correct"""
    print("\n⚙️ Checking WSGI file...")
    
    wsgi_file = 'wsgi_pythonanywhere_python311.py'
    
    if not os.path.exists(wsgi_file):
        print(f"❌ {wsgi_file} not found")
        return False
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Check for key elements
        checks = [
            ('application', 'WSGI application variable'),
            ('from app import app', 'App import statement'),
            ('adamcordova-4822.postgres.pythonanywhere-services.com', 'PostgreSQL host'),
            ('DB_HOST', 'Database host environment variable'),
            ('DB_NAME', 'Database name environment variable'),
            ('DB_USER', 'Database user environment variable'),
            ('DB_PASSWORD', 'Database password environment variable'),
            ('DB_PORT', 'Database port environment variable')
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
    """Main fix function"""
    print("🚀 Direct PythonAnywhere Fix")
    print("=" * 35)
    
    # Set environment variables
    set_environment_variables()
    
    # Test database connection
    db_ok = test_database_connection()
    
    # Test app import
    app_ok = test_app_import()
    
    # Check WSGI file
    wsgi_ok = check_wsgi_file()
    
    # Summary
    print("\n📊 Fix Summary:")
    print("=" * 20)
    print(f"Database Connection: {'✅' if db_ok else '❌'}")
    print(f"App Import: {'✅' if app_ok else '❌'}")
    print(f"WSGI File: {'✅' if wsgi_ok else '❌'}")
    
    print("\n💡 Next Steps:")
    if db_ok and app_ok and wsgi_ok:
        print("🎉 Everything looks good!")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Make sure wsgi_pythonanywhere_python311.py is selected")
        print("3. Click Reload button")
        print("4. Wait 30-60 seconds")
        print("5. Test your app")
    else:
        print("⚠️ Some issues found:")
        if not db_ok:
            print("- Database connection failed - check PostgreSQL server")
        if not app_ok:
            print("- App import failed - check for missing dependencies")
        if not wsgi_ok:
            print("- WSGI file issues - check configuration")
        
        print("\n🔧 Try these fixes:")
        print("1. pip install -r requirements.txt")
        print("2. Check PythonAnywhere error logs")
        print("3. Make sure WSGI file is selected in Web tab")

if __name__ == "__main__":
    main()
