#!/usr/bin/env python3
"""
Set Environment Variables for Current Session
Sets PostgreSQL environment variables for testing
"""

import os

def set_environment_variables():
    """Set environment variables for the current session"""
    
    print("🔧 Setting Environment Variables for Current Session...")
    print("=" * 55)
    
    # Set the environment variables
    env_vars = {
        'DB_HOST': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'DB_NAME': 'postgres',
        'DB_USER': 'super',
        'DB_PASSWORD': '193154life',
        'DB_PORT': '14822'
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value
        if var == 'DB_PASSWORD':
            print(f"✅ Set {var} = {'*' * len(value)}")
        else:
            print(f"✅ Set {var} = {value}")
    
    print("\n🎉 Environment variables set for current session!")

def test_database_connection():
    """Test database connection with the set variables"""
    
    print("\n🔗 Testing Database Connection...")
    print("=" * 35)
    
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
    """Test importing the app with environment variables set"""
    
    print("\n🧪 Testing App Import...")
    print("=" * 25)
    
    try:
        import sys
        sys.path.insert(0, os.getcwd())
        
        from app import app
        
        print("✅ App imported successfully")
        
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            return True
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 PythonAnywhere Environment Variables Test")
    print("=" * 50)
    
    # Set environment variables
    set_environment_variables()
    
    # Test database connection
    db_ok = test_database_connection()
    
    # Test app import
    app_ok = test_app_import()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Database Connection: {'✅' if db_ok else '❌'}")
    print(f"App Import: {'✅' if app_ok else '❌'}")
    
    if db_ok and app_ok:
        print("\n🎉 Everything works with environment variables set!")
        print("💡 The issue is that the WSGI file needs to be updated")
        print("💡 Run: python fix_wsgi_environment.py")
    else:
        print("\n⚠️ Some issues remain")
        if not db_ok:
            print("- Database connection failed")
        if not app_ok:
            print("- App import failed")

if __name__ == "__main__":
    main()
