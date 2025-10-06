#!/usr/bin/env python3
"""
Test PythonAnywhere PostgreSQL Connection
Tests your PostgreSQL database on PythonAnywhere
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def test_pythonanywhere_postgresql():
    """Test PythonAnywhere PostgreSQL connection"""
    
    print("🧪 Testing PythonAnywhere PostgreSQL Connection...")
    print("=" * 50)
    
    # Update these with your actual PythonAnywhere PostgreSQL details
    config = {
        'host': os.getenv('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'super'),
        'password': os.getenv('DB_PASSWORD', '193154life'),
        'port': os.getenv('DB_PORT', '14822')
    }
    
    print("📋 Connection Details:")
    print(f"   Host: {config['host']}")
    print(f"   Database: {config['database']}")
    print(f"   User: {config['user']}")
    print(f"   Port: {config['port']}")
    print()
    
    try:
        # Test connection
        conn = psycopg2.connect(**config)
        print("✅ Connection successful!")
        
        # Test query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version['version']}")
        
        # Test database info
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()
        print(f"✅ Connected to database: {db_name['current_database']}")
        
        # Test table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Table creation test passed")
        
        # Test insert
        cursor.execute("INSERT INTO test_table (name) VALUES (%s)", ("test",))
        conn.commit()
        print("✅ Insert test passed")
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        results = cursor.fetchall()
        print(f"✅ Select test passed: {len(results)} rows")
        
        # Clean up
        cursor.execute("DROP TABLE test_table")
        conn.commit()
        print("✅ Cleanup test passed")
        
        cursor.close()
        conn.close()
        
        print("\\n🎉 All PostgreSQL tests passed!")
        print("✅ Your PythonAnywhere PostgreSQL database is ready!")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\\n💡 Check your connection details:")
        print("   • Go to PythonAnywhere → Databases")
        print("   • Find your PostgreSQL database")
        print("   • Copy the correct connection details")
        print("   • Update the config above")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐘 PythonAnywhere PostgreSQL Test")
    print("=" * 35)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip3.11 install --user psycopg2-binary")
        exit(1)
    
    # Run test
    success = test_pythonanywhere_postgresql()
    
    if success:
        print("\\n🚀 Ready to migrate your data!")
        print("Run: python3.11 migrate_to_pythonanywhere_postgresql.py")
    else:
        print("\\n🔧 Fix connection issues first")
        print("Then run this test again")
