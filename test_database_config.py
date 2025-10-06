#!/usr/bin/env python3
"""
Test Database Configuration
Tests if the database configuration is using the correct environment variables
"""

import os
import sys

def test_database_config():
    """Test database configuration"""
    
    print("🔍 Testing Database Configuration...")
    print("=" * 40)
    
    # Check environment variables
    print("📋 Environment Variables:")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if var == 'DB_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print()
    
    # Test database config function
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
        
        # Check if it's using localhost (wrong) or PythonAnywhere (correct)
        if config['host'] == 'localhost':
            print("\n❌ Database is configured to use localhost (WRONG)")
            print("💡 This means environment variables are not being loaded")
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
    """Test actual database connection"""
    
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

def main():
    """Main test function"""
    print("🚀 Database Configuration Test")
    print("=" * 35)
    
    # Test database config
    config_ok = test_database_config()
    
    # Test database connection
    connection_ok = test_database_connection()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Database Config: {'✅' if config_ok else '❌'}")
    print(f"Database Connection: {'✅' if connection_ok else '❌'}")
    
    if config_ok and connection_ok:
        print("\n🎉 Database configuration is correct!")
        print("💡 The issue might be in the web environment")
    else:
        print("\n⚠️ Database configuration issues found")
        if not config_ok:
            print("- Environment variables are not being loaded")
        if not connection_ok:
            print("- Database connection failed")

if __name__ == "__main__":
    main()
