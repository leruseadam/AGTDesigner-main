"""
PythonAnywhere PostgreSQL Configuration
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
            'host': os.getenv('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'super'),
            'password': os.getenv('DB_PASSWORD', '193154life'),
            'port': os.getenv('DB_PORT', '14822')
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
    
    def search_products(self, query, limit=50):
        """Search products with PostgreSQL full-text search"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT *, 
                       ts_rank(to_tsvector('english', product_name), plainto_tsquery('english', %s)) as rank
                FROM products 
                WHERE to_tsvector('english', product_name) @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', product_strain) @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', vendor_supplier) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC, product_name
                LIMIT %s
            """, (query, query, query, query, limit))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_all_products(self, limit=1000):
        """Get all products"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM products 
                ORDER BY product_name
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"Get products failed: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
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
pa_pg = PythonAnywherePostgreSQL()

# Test connection on import
if pa_pg.test_connection():
    print("✅ PythonAnywhere PostgreSQL connection successful")
    info = pa_pg.get_database_info()
    if info:
        print(f"📊 Database size: {info['size']}")
        print(f"📊 Tables: {info['tables']}")
else:
    print("❌ PythonAnywhere PostgreSQL connection failed")
    print("💡 Make sure you've:")
    print("   1. Created PostgreSQL database on PythonAnywhere")
    print("   2. Updated connection details above")
    print("   3. Installed psycopg2-binary")
