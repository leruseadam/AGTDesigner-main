#!/usr/bin/env python3
"""
Database Connection Test for PythonAnywhere
Tests the PostgreSQL connection and environment variables
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def test_database_connection():
    """Test database connection with environment variables"""
    
    print("🔍 Testing PythonAnywhere Database Connection...")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'DB_PASSWORD':
            value = '*' * len(value) if value != 'NOT SET' else 'NOT SET'
        print(f"   {var}: {value}")
    
    print()
    
    # Get database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'agt_designer'),
        'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔧 Database Configuration:")
    for key, value in db_config.items():
        if key == 'password':
            value = '*' * len(value) if value else 'EMPTY'
        print(f"   {key}: {value}")
    
    print()
    
    # Test connection
    try:
        print("🔄 Attempting to connect to PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Connection successful!")
        
        # Test basic queries
        print("🧪 Testing basic queries...")
        
        # Test products table
        cur.execute("SELECT COUNT(*) FROM products;")
        product_count = cur.fetchone()[0]
        print(f"   📊 Products: {product_count}")
        
        # Test strains table
        cur.execute("SELECT COUNT(*) FROM strains;")
        strain_count = cur.fetchone()[0]
        print(f"   🌿 Strains: {strain_count}")
        
        # Test database version
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        print(f"   🐘 PostgreSQL version: {db_version[:50]}...")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Database connection test PASSED!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection FAILED: {e}")
        print("\n💡 Troubleshooting steps:")
        print("1. Check if environment variables are set correctly")
        print("2. Verify PostgreSQL server is running on PythonAnywhere")
        print("3. Check database credentials")
        print("4. Ensure the database exists")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def fix_environment_variables():
    """Fix environment variables if they're not set correctly"""
    
    print("\n🔧 Checking and fixing environment variables...")
    
    # Required environment variables
    required_vars = {
        'DB_HOST': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'DB_NAME': 'postgres',
        'DB_USER': 'super',
        'DB_PASSWORD': '193154life',
        'DB_PORT': '14822'
    }
    
    fixed_vars = []
    for var, default_value in required_vars.items():
        current_value = os.environ.get(var)
        if not current_value:
            os.environ[var] = default_value
            fixed_vars.append(var)
            print(f"✅ Set {var} = {default_value}")
        else:
            print(f"✅ {var} already set")
    
    if fixed_vars:
        print(f"\n🔧 Fixed {len(fixed_vars)} environment variables")
    else:
        print("\n✅ All environment variables are correctly set")
    
    return len(fixed_vars) > 0

def test_app_database_config():
    """Test the app's database configuration function"""
    
    print("\n🧪 Testing app's database configuration...")
    
    try:
        # Import the app's database config function
        sys.path.insert(0, '/home/adamcordova/AGTDesigner')
        from src.core.data.product_database import get_database_config
        
        config = get_database_config()
        print("📋 App's database configuration:")
        for key, value in config.items():
            if key == 'password':
                value = '*' * len(value) if value else 'EMPTY'
            print(f"   {key}: {value}")
        
        # Test if it's using the correct host
        if config['host'] == 'localhost':
            print("❌ App is still using localhost instead of PythonAnywhere PostgreSQL")
            return False
        else:
            print("✅ App is using the correct PostgreSQL host")
            return True
            
    except Exception as e:
        print(f"❌ Error testing app config: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PythonAnywhere Database Connection Test")
    print("=" * 50)
    
    # Fix environment variables
    env_fixed = fix_environment_variables()
    
    # Test app's database config
    app_config_ok = test_app_database_config()
    
    # Test database connection
    connection_ok = test_database_connection()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Environment variables fixed: {'✅' if env_fixed else '❌'}")
    print(f"App config correct: {'✅' if app_config_ok else '❌'}")
    print(f"Database connection: {'✅' if connection_ok else '❌'}")
    
    if connection_ok and app_config_ok:
        print("\n🎉 All tests passed! Your database should work correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
        print("\n💡 Next steps:")
        print("1. Reload your PythonAnywhere web app")
        print("2. Check the error logs")
        print("3. Run this test again if needed")
