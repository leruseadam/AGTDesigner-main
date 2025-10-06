#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL
Optimized for Label Maker application
"""

import sqlite3
import psycopg2
import json
import os
from datetime import datetime

def migrate_sqlite_to_postgresql():
    """Migrate from SQLite to PostgreSQL"""
    
    # Database connections
    sqlite_path = 'uploads/product_database.db'
    postgres_config = {
        'host': 'localhost',
        'database': 'labelmaker',
        'user': 'labelmaker',
        'password': 'your_password_here'
    }
    
    # Connect to databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        postgres_conn = psycopg2.connect(**postgres_config)
        postgres_conn.autocommit = False
        postgres_cursor = postgres_conn.cursor()
        
        print("✅ Connected to both databases")
        
        # Create PostgreSQL schema
        create_postgres_schema(postgres_cursor)
        
        # Migrate products table
        migrate_products_table(sqlite_conn, postgres_cursor)
        
        # Migrate other tables
        migrate_other_tables(sqlite_conn, postgres_cursor)
        
        # Create indexes for performance
        create_performance_indexes(postgres_cursor)
        
        postgres_conn.commit()
        print("✅ Migration completed successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'postgres_conn' in locals():
            postgres_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        if 'postgres_conn' in locals():
            postgres_conn.close()

def create_postgres_schema(cursor):
    """Create optimized PostgreSQL schema"""
    
    schema_sql = """
    -- Products table with JSON support
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        strain VARCHAR(100),
        thc_percentage DECIMAL(5,2),
        cbd_percentage DECIMAL(5,2),
        price DECIMAL(10,2),
        weight_unit VARCHAR(20),
        product_type VARCHAR(50),
        vendor VARCHAR(100),
        lineage TEXT,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        id VARCHAR(255) PRIMARY KEY,
        data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Uploads tracking
    CREATE TABLE IF NOT EXISTS uploads (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255),
        file_path TEXT,
        file_size INTEGER,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        metadata JSONB
    );
    
    -- Performance optimization
    CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
    CREATE INDEX IF NOT EXISTS idx_products_strain ON products(strain);
    CREATE INDEX IF NOT EXISTS idx_products_metadata ON products USING GIN(metadata);
    CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type);
    CREATE INDEX IF NOT EXISTS idx_products_vendor ON products(vendor);
    """
    
    cursor.execute(schema_sql)
    print("✅ PostgreSQL schema created")

def migrate_products_table(sqlite_conn, postgres_cursor):
    """Migrate products with JSON optimization"""
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM products")
    
    products = sqlite_cursor.fetchall()
    print(f"📦 Migrating {len(products)} products...")
    
    for product in products:
        # Convert SQLite row to dict
        product_dict = dict(product)
        
        # Prepare metadata as JSONB
        metadata = {}
        for key, value in product_dict.items():
            if key not in ['id', 'name', 'strain', 'thc_percentage', 'cbd_percentage', 
                          'price', 'weight_unit', 'product_type', 'vendor', 'lineage']:
                if value is not None:
                    metadata[key] = value
        
        # Insert into PostgreSQL
        insert_sql = """
        INSERT INTO products (
            name, strain, thc_percentage, cbd_percentage, price,
            weight_unit, product_type, vendor, lineage, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        postgres_cursor.execute(insert_sql, (
            product_dict.get('name'),
            product_dict.get('strain'),
            product_dict.get('thc_percentage'),
            product_dict.get('cbd_percentage'),
            product_dict.get('price'),
            product_dict.get('weight_unit'),
            product_dict.get('product_type'),
            product_dict.get('vendor'),
            product_dict.get('lineage'),
            json.dumps(metadata) if metadata else None
        ))
    
    print("✅ Products migrated successfully")

def migrate_other_tables(sqlite_conn, postgres_cursor):
    """Migrate other tables"""
    
    # Migrate sessions if they exist
    try:
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        if 'sessions' in tables:
            sqlite_cursor.execute("SELECT * FROM sessions")
            sessions = sqlite_cursor.fetchall()
            
            for session in sessions:
                insert_sql = "INSERT INTO sessions (id, data) VALUES (%s, %s)"
                postgres_cursor.execute(insert_sql, (session[0], json.dumps(session[1])))
            
            print(f"✅ Migrated {len(sessions)} sessions")
            
    except Exception as e:
        print(f"⚠️ Sessions migration skipped: {e}")

def create_performance_indexes(cursor):
    """Create performance indexes"""
    
    indexes_sql = """
    -- Full-text search index
    CREATE INDEX IF NOT EXISTS idx_products_name_search 
    ON products USING GIN(to_tsvector('english', name));
    
    -- Composite indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_products_type_strain 
    ON products(product_type, strain);
    
    -- Price range index
    CREATE INDEX IF NOT EXISTS idx_products_price 
    ON products(price) WHERE price IS NOT NULL;
    
    -- Updated at index for recent products
    CREATE INDEX IF NOT EXISTS idx_products_updated 
    ON products(updated_at);
    """
    
    cursor.execute(indexes_sql)
    print("✅ Performance indexes created")

def create_postgresql_config():
    """Create PostgreSQL configuration for the app"""
    
    config_content = '''
# PostgreSQL Configuration for Label Maker
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

class PostgreSQLDatabase:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'labelmaker'),
            'user': os.getenv('DB_USER', 'labelmaker'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def get_connection(self):
        """Get database connection with optimized settings"""
        conn = psycopg2.connect(**self.config)
        conn.autocommit = False
        return conn
    
    def search_products(self, query, limit=50):
        """Full-text search with PostgreSQL"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT *, ts_rank(to_tsvector('english', name), plainto_tsquery('english', %s)) as rank
                    FROM products 
                    WHERE to_tsvector('english', name) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC, name
                    LIMIT %s
                """, (query, query, limit))
                return cursor.fetchall()
    
    def get_products_by_metadata(self, key, value):
        """Query products by JSON metadata"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE metadata->>%s = %s
                    ORDER BY name
                """, (key, value))
                return cursor.fetchall()
    
    def update_product_metadata(self, product_id, metadata_updates):
        """Update product metadata efficiently"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE products 
                    SET metadata = metadata || %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(metadata_updates), product_id))
                conn.commit()

# Global database instance
db = PostgreSQLDatabase()
'''
    
    with open('postgresql_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ PostgreSQL configuration created")

if __name__ == "__main__":
    print("🚀 Starting SQLite to PostgreSQL migration...")
    migrate_sqlite_to_postgresql()
    create_postgresql_config()
    print("🎉 Migration complete! Update your app to use PostgreSQL.")
