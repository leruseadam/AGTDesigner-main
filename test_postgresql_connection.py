#!/usr/bin/env python3
"""
Test PostgreSQL connection on PythonAnywhere
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def test_postgresql_connection():
    """Test PostgreSQL connection with environment variables"""
    
    print("🔍 Testing PostgreSQL Connection...")
    print("=" * 50)
    
    # Get environment variables
    db_host = os.environ.get('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com')
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = os.environ.get('DB_USER', 'super')
    db_password = os.environ.get('DB_PASSWORD', '193154life')
    db_port = os.environ.get('DB_PORT', '14822')
    
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Port: {db_port}")
    print(f"Password: {'*' * len(db_password)}")
    print()
    
    try:
        # Test connection
        print("🔄 Attempting to connect...")
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        print("✅ Connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 PostgreSQL version: {version[0]}")
        
        # Check if our tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('products', 'strains', 'vendors', 'brands');
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Found tables: {[table[0] for table in tables]}")
        else:
            print("⚠️  No product tables found - database may need initialization")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are set correctly"""
    
    print("🔍 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print()

if __name__ == "__main__":
    print("🐘 PythonAnywhere PostgreSQL Connection Test")
    print("=" * 60)
    
    # Test environment variables
    test_environment_variables()
    
    # Test connection
    success = test_postgresql_connection()
    
    if success:
        print("\n🎉 PostgreSQL connection test PASSED!")
        print("Your database is ready for the Label Maker app.")
    else:
        print("\n💥 PostgreSQL connection test FAILED!")
        print("Please check your database configuration.")
        
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify PostgreSQL service is running")
        print("2. Check database credentials")
        print("3. Ensure database exists")
        print("4. Check firewall/network settings")