#!/usr/bin/env python3
"""
PostgreSQL Setup for PythonAnywhere
Step-by-step guide to set up PostgreSQL on PythonAnywhere
"""

import os
import sys

def setup_postgresql_pythonanywhere():
    """Set up PostgreSQL on PythonAnywhere"""
    
    print("🐘 Setting up PostgreSQL on PythonAnywhere...")
    print("=" * 50)
    
    # Check if we're on PythonAnywhere
    if not is_pythonanywhere():
        print("❌ This script is designed for PythonAnywhere")
        print("💡 Run this on your PythonAnywhere account")
        return False
    
    print("📋 Step-by-step PostgreSQL setup:")
    print()
    print("1️⃣ CREATE POSTGRESQL DATABASE")
    print("   • Go to PythonAnywhere Dashboard")
    print("   • Click 'Databases' tab")
    print("   • Click 'Create a new database'")
    print("   • Choose 'PostgreSQL'")
    print("   • Database name: 'labelmaker'")
    print("   • Username: 'labelmaker'")
    print("   • Password: [create secure password]")
    print()
    print("2️⃣ INSTALL POSTGRESQL CLIENT")
    print("   • Run: pip3.11 install --user psycopg2-binary")
    print()
    print("3️⃣ CONFIGURE CONNECTION")
    print("   • Update connection settings below")
    print("   • Test connection")
    print()
    print("4️⃣ MIGRATE DATA")
    print("   • Run migration script")
    print("   • Verify data transfer")
    print()
    
    # Get connection details
    get_connection_details()
    
    # Test connection
    test_postgresql_connection()
    
    return True

def is_pythonanywhere():
    """Check if running on PythonAnywhere"""
    return 'pythonanywhere.com' in os.environ.get('HTTP_HOST', '') or 'PYTHONANYWHERE' in os.environ

def get_connection_details():
    """Get PostgreSQL connection details"""
    
    print("🔧 PostgreSQL Connection Configuration:")
    print()
    
    # PythonAnywhere PostgreSQL connection format
    connection_info = {
        'host': 'adamcordova.mysql.pythonanywhere-services.com',  # This will be different for PostgreSQL
        'database': 'adamcordova$labelmaker',
        'user': 'adamcordova',
        'password': 'YOUR_POSTGRESQL_PASSWORD',
        'port': '5432'
    }
    
    print("📝 Update these connection details:")
    print(f"   Host: {connection_info['host']}")
    print(f"   Database: {connection_info['database']}")
    print(f"   User: {connection_info['user']}")
    print(f"   Password: [Your PostgreSQL password]")
    print(f"   Port: {connection_info['port']}")
    print()
    print("💡 Note: PythonAnywhere will provide the actual connection details")
    print("   when you create the PostgreSQL database.")

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    
    print("🧪 Testing PostgreSQL Connection...")
    
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
        
        # Test connection (this will fail until you set up the database)
        test_config = {
            'host': 'localhost',
            'database': 'test',
            'user': 'test',
            'password': 'test',
            'port': '5432'
        }
        
        print("⚠️ Connection test will work after you:")
        print("   1. Create PostgreSQL database on PythonAnywhere")
        print("   2. Update connection details")
        print("   3. Run: python test_postgresql_connection.py")
        
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip3.11 install --user psycopg2-binary")

def create_pythonanywhere_postgresql_config():
    """Create PostgreSQL configuration for PythonAnywhere"""
    
    config_content = '''"""
PostgreSQL Configuration for PythonAnywhere
Update the connection details below with your actual PostgreSQL credentials
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

class PythonAnywherePostgreSQL:
    def __init__(self):
        # UPDATE THESE WITH YOUR ACTUAL PYTHONANYWHERE POSTGRESQL DETAILS
        self.config = {
            'host': os.getenv('DB_HOST', 'adamcordova.mysql.pythonanywhere-services.com'),
            'database': os.getenv('DB_NAME', 'adamcordova$labelmaker'),
            'user': os.getenv('DB_USER', 'adamcordova'),
            'password': os.getenv('DB_PASSWORD', 'YOUR_POSTGRESQL_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def get_connection(self):
        """Get PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.config)
            conn.autocommit = False
            return conn
        except psycopg2.OperationalError as e:
            logging.error(f"PostgreSQL connection failed: {e}")
            return None
    
    def test_connection(self):
        """Test PostgreSQL connection"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                logging.error(f"PostgreSQL test failed: {e}")
                return False
        return False
    
    def get_database_info(self):
        """Get database information"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size = cursor.fetchone()
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                'size': size['size'] if size else 'Unknown',
                'tables': tables['table_count'] if tables else 0
            }
            
        except Exception as e:
            logging.error(f"Get database info failed: {e}")
            return None

# Global PostgreSQL instance
pg_db = PythonAnywherePostgreSQL()

# Test connection on import
if pg_db.test_connection():
    print("✅ PostgreSQL connection successful")
    info = pg_db.get_database_info()
    if info:
        print(f"📊 Database size: {info['size']}")
        print(f"📊 Tables: {info['tables']}")
else:
    print("❌ PostgreSQL connection failed")
    print("💡 Make sure you've:")
    print("   1. Created PostgreSQL database on PythonAnywhere")
    print("   2. Updated connection details above")
    print("   3. Installed psycopg2-binary")
'''
    
    with open('pythonanywhere_postgresql_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ PostgreSQL configuration created")

if __name__ == "__main__":
    print("🐘 PythonAnywhere PostgreSQL Setup")
    print("=" * 40)
    
    success = setup_postgresql_pythonanywhere()
    
    if success:
        create_pythonanywhere_postgresql_config()
        print("\\n🎉 PostgreSQL setup guide complete!")
        print("\\n📋 Next steps:")
        print("1. Go to PythonAnywhere → Databases → Create PostgreSQL")
        print("2. Update connection details in pythonanywhere_postgresql_config.py")
        print("3. Run migration script")
        print("4. Test performance improvements")
    else:
        print("❌ Setup failed")