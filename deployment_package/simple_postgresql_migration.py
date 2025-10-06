#!/usr/bin/env python3
"""
Simple PostgreSQL Migration Script
Migrates your SQLite database to any PostgreSQL setup
"""

import sqlite3
import psycopg2
import os
import json
from datetime import datetime

def migrate_to_postgresql():
    """Migrate SQLite to PostgreSQL"""
    
    print("🚀 Starting PostgreSQL Migration...")
    print("=" * 50)
    
    # Database paths
    sqlite_path = '/Users/adamcordova/Desktop/product_database_AGT_Bothell.db'
    
    # PostgreSQL connection (update these)
    postgres_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'labelmaker'),
        'user': os.getenv('DB_USER', 'labelmaker'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("📋 Connection Details:")
    print(f"   Host: {postgres_config['host']}")
    print(f"   Database: {postgres_config['database']}")
    print(f"   User: {postgres_config['user']}")
    print(f"   Port: {postgres_config['port']}")
    print()
    
    # Connect to SQLite
    print("📦 Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # Connect to PostgreSQL
        print("🐘 Connecting to PostgreSQL database...")
        postgres_conn = psycopg2.connect(**postgres_config)
        postgres_conn.autocommit = False
        postgres_cursor = postgres_conn.cursor()
        
        print("✅ Connected to both databases")
        
        # Create PostgreSQL schema
        create_postgres_schema(postgres_cursor)
        
        # Migrate products
        migrate_products(sqlite_cursor, postgres_cursor)
        
        # Migrate strains
        migrate_strains(sqlite_cursor, postgres_cursor)
        
        # Create indexes
        create_indexes(postgres_cursor)
        
        postgres_conn.commit()
        print("✅ Migration completed successfully")
        
        # Show stats
        show_migration_stats(postgres_cursor)
        
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
    """Create PostgreSQL schema"""
    
    print("🏗️ Creating PostgreSQL schema...")
    
    schema_sql = """
    -- Drop existing tables
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS strains CASCADE;
    
    -- Products table
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        product_name VARCHAR(255),
        product_type VARCHAR(100),
        product_brand VARCHAR(100),
        vendor_supplier VARCHAR(100),
        product_strain VARCHAR(100),
        lineage TEXT,
        description TEXT,
        weight VARCHAR(50),
        units VARCHAR(20),
        price DECIMAL(10,2),
        quantity VARCHAR(50),
        doh VARCHAR(50),
        concentrate_type VARCHAR(100),
        ratio VARCHAR(50),
        joint_ratio VARCHAR(50),
        state VARCHAR(50),
        is_sample VARCHAR(10),
        is_mj_product VARCHAR(10),
        discountable VARCHAR(10),
        room VARCHAR(50),
        batch_number VARCHAR(100),
        lot_number VARCHAR(100),
        barcode VARCHAR(100),
        medical_only VARCHAR(10),
        med_price DECIMAL(10,2),
        expiration_date DATE,
        is_archived VARCHAR(10),
        thc_per_serving VARCHAR(50),
        allergens TEXT,
        solvent VARCHAR(100),
        accepted_date DATE,
        internal_product_id VARCHAR(100),
        product_tags TEXT,
        image_url TEXT,
        ingredients TEXT,
        combined_weight VARCHAR(50),
        ratio_or_thc_cbd VARCHAR(50),
        description_complexity INTEGER,
        total_thc VARCHAR(50),
        thca VARCHAR(50),
        cbda VARCHAR(50),
        cbn VARCHAR(50),
        normalized_name VARCHAR(255),
        test_result_unit VARCHAR(20) DEFAULT '',
        thc VARCHAR(50) DEFAULT '',
        cbd VARCHAR(50) DEFAULT '',
        total_cbd VARCHAR(50) DEFAULT '',
        cbga VARCHAR(50) DEFAULT '',
        cbg VARCHAR(50) DEFAULT '',
        total_cbg VARCHAR(50) DEFAULT '',
        cbc VARCHAR(50) DEFAULT '',
        cbdv VARCHAR(50) DEFAULT '',
        thcv VARCHAR(50) DEFAULT '',
        cbgv VARCHAR(50) DEFAULT '',
        cbnv VARCHAR(50) DEFAULT '',
        cbgva VARCHAR(50) DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Strains table
    CREATE TABLE strains (
        id SERIAL PRIMARY KEY,
        strain_name VARCHAR(255) UNIQUE NOT NULL,
        normalized_name VARCHAR(255) NOT NULL,
        canonical_lineage TEXT,
        first_seen_date DATE NOT NULL,
        last_seen_date DATE NOT NULL,
        total_occurrences INTEGER DEFAULT 1,
        lineage_confidence DECIMAL(5,2) DEFAULT 0.0,
        sovereign_lineage TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(schema_sql)
    print("✅ Schema created")

def migrate_products(sqlite_cursor, postgres_cursor):
    """Migrate products table"""
    
    sqlite_cursor.execute("SELECT COUNT(*) FROM products")
    total_products = sqlite_cursor.fetchone()[0]
    print(f"📦 Migrating {total_products:,} products...")
    
    sqlite_cursor.execute("SELECT * FROM products")
    products = sqlite_cursor.fetchall()
    
    for i, product in enumerate(products):
        if i % 1000 == 0:
            print(f"   Processed {i:,}/{total_products:,} products...")
        
        product_dict = dict(product)
        
        # Clean price data
        def clean_price(value):
            if not value or value == '':
                return None
            try:
                cleaned = str(value).replace('$', '').replace(',', '').strip()
                return float(cleaned) if cleaned else None
            except:
                return None
        
        # Insert into PostgreSQL
        insert_sql = """
        INSERT INTO products (
            product_name, product_type, product_brand, vendor_supplier, product_strain,
            lineage, description, weight, units, price, quantity, doh, concentrate_type,
            ratio, joint_ratio, state, is_sample, is_mj_product, discountable, room,
            batch_number, lot_number, barcode, medical_only, med_price, expiration_date,
            is_archived, thc_per_serving, allergens, solvent, accepted_date,
            internal_product_id, product_tags, image_url, ingredients, combined_weight,
            ratio_or_thc_cbd, description_complexity, total_thc, thca, cbda, cbn,
            normalized_name, test_result_unit, thc, cbd, total_cbd, cbga, cbg,
            total_cbg, cbc, cbdv, thcv, cbgv, cbnv, cbgva
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        postgres_cursor.execute(insert_sql, (
            product_dict.get('Product Name*'),
            product_dict.get('Product Type*'),
            product_dict.get('Product Brand'),
            product_dict.get('Vendor/Supplier*'),
            product_dict.get('Product Strain'),
            product_dict.get('Lineage'),
            product_dict.get('Description'),
            product_dict.get('Weight*'),
            product_dict.get('Units'),
            clean_price(product_dict.get('Price')),
            product_dict.get('Quantity*'),
            product_dict.get('DOH'),
            product_dict.get('Concentrate Type'),
            product_dict.get('Ratio'),
            product_dict.get('JointRatio'),
            product_dict.get('State'),
            product_dict.get('Is Sample? (yes/no)'),
            product_dict.get('Is MJ product?(yes/no)'),
            product_dict.get('Discountable? (yes/no)'),
            product_dict.get('Room*'),
            product_dict.get('Batch Number'),
            product_dict.get('Lot Number'),
            product_dict.get('Barcode*'),
            product_dict.get('Medical Only (Yes/No)'),
            clean_price(product_dict.get('Med Price')),
            product_dict.get('Expiration Date(YYYY-MM-DD)'),
            product_dict.get('Is Archived? (yes/no)'),
            product_dict.get('THC Per Serving'),
            product_dict.get('Allergens'),
            product_dict.get('Solvent'),
            product_dict.get('Accepted Date'),
            product_dict.get('Internal Product Identifier'),
            product_dict.get('Product Tags (comma separated)'),
            product_dict.get('Image URL'),
            product_dict.get('Ingredients'),
            product_dict.get('CombinedWeight'),
            product_dict.get('Ratio_or_THC_CBD'),
            product_dict.get('Description_Complexity'),
            product_dict.get('Total THC'),
            product_dict.get('THCA'),
            product_dict.get('CBDA'),
            product_dict.get('CBN'),
            product_dict.get('normalized_name'),
            product_dict.get('Test result unit (% or mg)'),
            product_dict.get('THC'),
            product_dict.get('CBD'),
            product_dict.get('Total CBD'),
            product_dict.get('CBGA'),
            product_dict.get('CBG'),
            product_dict.get('Total CBG'),
            product_dict.get('CBC'),
            product_dict.get('CBDV'),
            product_dict.get('THCV'),
            product_dict.get('CBGV'),
            product_dict.get('CBNV'),
            product_dict.get('CBGVA')
        ))
    
    print("✅ Products migrated successfully")

def migrate_strains(sqlite_cursor, postgres_cursor):
    """Migrate strains table"""
    
    try:
        sqlite_cursor.execute("SELECT COUNT(*) FROM strains")
        total_strains = sqlite_cursor.fetchone()[0]
        print(f"🌿 Migrating {total_strains:,} strains...")
        
        sqlite_cursor.execute("SELECT * FROM strains")
        strains = sqlite_cursor.fetchall()
        
        for strain in strains:
            strain_dict = dict(strain)
            
            insert_sql = """
            INSERT INTO strains (
                strain_name, normalized_name, canonical_lineage, first_seen_date,
                last_seen_date, total_occurrences, lineage_confidence, sovereign_lineage
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            postgres_cursor.execute(insert_sql, (
                strain_dict.get('strain_name'),
                strain_dict.get('normalized_name'),
                strain_dict.get('canonical_lineage'),
                strain_dict.get('first_seen_date'),
                strain_dict.get('last_seen_date'),
                strain_dict.get('total_occurrences'),
                strain_dict.get('lineage_confidence'),
                strain_dict.get('sovereign_lineage')
            ))
        
        print("✅ Strains migrated successfully")
        
    except Exception as e:
        print(f"⚠️ Strains migration skipped: {e}")

def create_indexes(cursor):
    """Create performance indexes"""
    
    print("📊 Creating performance indexes...")
    
    indexes_sql = """
    -- Full-text search indexes
    CREATE INDEX idx_products_name_search ON products USING GIN(to_tsvector('english', product_name));
    CREATE INDEX idx_products_strain_search ON products USING GIN(to_tsvector('english', product_strain));
    CREATE INDEX idx_products_vendor_search ON products USING GIN(to_tsvector('english', vendor_supplier));
    
    -- Regular indexes
    CREATE INDEX idx_products_type ON products(product_type);
    CREATE INDEX idx_products_strain ON products(product_strain);
    CREATE INDEX idx_products_vendor ON products(vendor_supplier);
    CREATE INDEX idx_products_brand ON products(product_brand);
    CREATE INDEX idx_products_price ON products(price) WHERE price IS NOT NULL;
    
    -- Strains indexes
    CREATE INDEX idx_strains_name ON strains(strain_name);
    CREATE INDEX idx_strains_normalized ON strains(normalized_name);
    """
    
    cursor.execute(indexes_sql)
    print("✅ Indexes created")

def show_migration_stats(cursor):
    """Show migration statistics"""
    
    print("\\n📊 Migration Statistics:")
    print("=" * 30)
    
    # Products stats
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT product_type) FROM products")
    product_types = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT product_strain) FROM products WHERE product_strain IS NOT NULL")
    strains = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT vendor_supplier) FROM products WHERE vendor_supplier IS NOT NULL")
    vendors = cursor.fetchone()[0]
    
    print(f"Products: {total_products:,}")
    print(f"Product Types: {product_types}")
    print(f"Strains: {strains}")
    print(f"Vendors: {vendors}")
    
    # Strains stats
    try:
        cursor.execute("SELECT COUNT(*) FROM strains")
        total_strains = cursor.fetchone()[0]
        print(f"Strain Records: {total_strains}")
    except:
        print("Strain Records: 0")

def create_postgresql_app_config():
    """Create app configuration for PostgreSQL"""
    
    config_content = '''"""
PostgreSQL App Configuration
Update your app to use PostgreSQL instead of SQLite
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

class PostgreSQLApp:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'labelmaker'),
            'user': os.getenv('DB_USER', 'labelmaker'),
            'password': os.getenv('DB_PASSWORD', ''),
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

# Global PostgreSQL instance
pg_app = PostgreSQLApp()

# Test connection
if pg_app.get_connection():
    print("✅ PostgreSQL app configuration ready")
else:
    print("❌ PostgreSQL connection failed - check your configuration")
'''
    
    with open('postgresql_app_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ PostgreSQL app configuration created")

if __name__ == "__main__":
    print("🐘 Simple PostgreSQL Migration")
    print("=" * 35)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip install psycopg2-binary")
        exit(1)
    
    # Check connection details
    print("\\n📋 Before running migration:")
    print("1. Set up PostgreSQL database (Railway, DigitalOcean, etc.)")
    print("2. Set environment variables:")
    print("   export DB_HOST=your-postgres-host")
    print("   export DB_NAME=labelmaker")
    print("   export DB_USER=labelmaker")
    print("   export DB_PASSWORD=your-password")
    print("   export DB_PORT=5432")
    print("3. Test connection: python test_postgresql_connection.py")
    print()
    
    # Ask for confirmation
    response = input("Ready to migrate? (y/n): ").lower().strip()
    
    if response == 'y':
        migrate_to_postgresql()
        create_postgresql_app_config()
        print("\\n🎉 Migration complete!")
        print("\\n📋 Next steps:")
        print("1. Update your app to use postgresql_app_config.py")
        print("2. Test performance improvements")
        print("3. Enjoy faster searches!")
    else:
        print("Migration cancelled. Run when ready!")
