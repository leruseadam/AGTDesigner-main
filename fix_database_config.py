#!/usr/bin/env python3
"""
Direct fix for PythonAnywhere database connection
Run this on PythonAnywhere Bash console
"""

import os

def fix_database_config():
    """Fix the database configuration"""
    print("🔧 Fixing Database Configuration...")
    print("=" * 40)
    
    # Check current environment variables
    print("Current environment variables:")
    for var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']:
        value = os.environ.get(var, 'NOT SET')
        if var == 'DB_PASSWORD':
            value = '***' if value != 'NOT SET' else 'NOT SET'
        print(f"  {var}: {value}")
    
    print("\nSetting correct environment variables...")
    
    # Set the correct environment variables
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    print("✅ Environment variables set!")
    
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
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products;')
        count = cursor.fetchone()[0]
        print(f"✅ Database connection successful! Products: {count}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    fix_database_config()
