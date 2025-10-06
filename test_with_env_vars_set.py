#!/usr/bin/env python3
"""
Test Database Configuration with Environment Variables Set
Simulates the web environment by setting environment variables manually
"""

import os
import sys

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
    
    print("✅ Environment variables set:")
    print(f"   DB_HOST: {os.environ['DB_HOST']}")
    print(f"   DB_NAME: {os.environ['DB_NAME']}")
    print(f"   DB_USER: {os.environ['DB_USER']}")
    print(f"   DB_PASSWORD: {'*' * len(os.environ['DB_PASSWORD'])}")
    print(f"   DB_PORT: {os.environ['DB_PORT']}")

def test_database_config():
    """Test database configuration with environment variables set"""
    
    print("\n🔍 Testing Database Configuration...")
    print("=" * 40)
    
    try:
        sys.path.insert(0, os.getcwd())
        from src.core.data.product_database import get_database_config
        
        config = get_database_config()
        print("🔧 Database Configuration:")
        for key, value in config.items():
            if key == 'password':
                print(f"   {key}: {'*' * len(value)}")
            else:
                print(f"   {key}: {value}")
        
        # Check if it's using PythonAnywhere (correct) or localhost (wrong)
        if config['host'] == 'localhost':
            print("\n❌ Database is still configured to use localhost (WRONG)")
            return False
        elif 'pythonanywhere' in config['host']:
            print("\n✅ Database is configured to use PythonAnywhere PostgreSQL (CORRECT)")
            return True
        else:
            print(f"\n⚠️ Database host is: {config['host']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database config: {e}")
        return False

def test_database_connection():
    """Test actual database connection with environment variables set"""
    
    print("\n🔗 Testing Database Connection...")
    print("=" * 35)
    
    try:
        import psycopg2
        from src.core.data.product_database import get_database_config
        
        config = get_database_config()
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]
        
        print(f"✅ Database connection successful!")
        print(f"📊 Found {count} products in database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_app_with_env():
    """Test the app with environment variables set"""
    
    print("\n🧪 Testing App with Environment Variables...")
    print("=" * 50)
    
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        
        print("✅ App imported successfully")
        
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            
            # Test a simple route
            with app.test_client() as client:
                try:
                    response = client.get('/api/database-stats')
                    print(f"✅ App responds to database-stats (status: {response.status_code})")
                    
                    if response.status_code == 200:
                        data = response.get_json()
                        if 'total_products' in data:
                            print(f"📊 Database stats show: {data['total_products']} products")
                            return True
                        else:
                            print("⚠️ Database stats response doesn't contain product count")
                            return False
                    else:
                        print(f"⚠️ Database stats returned status {response.status_code}")
                        return False
                        
                except Exception as e:
                    print(f"❌ App doesn't respond to database-stats: {e}")
                    return False
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Database Configuration Test with Environment Variables")
    print("=" * 65)
    
    # Set environment variables
    set_environment_variables()
    
    # Test database config
    config_ok = test_database_config()
    
    # Test database connection
    connection_ok = test_database_connection()
    
    # Test app functionality
    app_ok = test_app_with_env()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Database Config: {'✅' if config_ok else '❌'}")
    print(f"Database Connection: {'✅' if connection_ok else '❌'}")
    print(f"App Functionality: {'✅' if app_ok else '❌'}")
    
    if config_ok and connection_ok and app_ok:
        print("\n🎉 Everything works with environment variables set!")
        print("💡 The issue is that the WSGI file needs to be copied and web app reloaded")
        print("💡 The web environment should work the same way")
    else:
        print("\n⚠️ Some issues remain")
        if not config_ok:
            print("- Database config issue")
        if not connection_ok:
            print("- Database connection issue")
        if not app_ok:
            print("- App functionality issue")

if __name__ == "__main__":
    main()
