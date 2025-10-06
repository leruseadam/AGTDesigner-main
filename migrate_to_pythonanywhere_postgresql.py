#!/usr/bin/env python3
"""
Migrate to PythonAnywhere PostgreSQL
Migrates your SQLite database to PythonAnywhere PostgreSQL
"""

import sqlite3
import psycopg2
import os
import json
from datetime import datetime

def migrate_to_pythonanywhere_postgresql():
    """Migrate SQLite to PythonAnywhere PostgreSQL"""
    
    print("🚀 Migrating to PythonAnywhere PostgreSQL...")
    print("=" * 50)
    
    # Database paths
    sqlite_path = '/home/adamcordova/AGTDesigner/uploads/product_database_AGT_Bothell.db'
    
    # PythonAnywhere PostgreSQL connection
    postgres_config = {
        'host': os.getenv('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'super'),
        'password': os.getenv('DB_PASSWORD', '193154life'),
        'port': os.getenv('DB_PORT', '14822')
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
        print("🐘 Connecting to PythonAnywhere PostgreSQL...")
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
        # Clean date data
        def clean_date(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                # Handle various date formats
                value_str = str(value).strip()
                if value_str == '' or value_str.lower() in ['none', 'null', 'n/a']:
                    return None
                return value_str
            except:
                return None
        
        # Clean numeric data
        def clean_numeric(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                cleaned = str(value).replace(',', '').strip()
                return float(cleaned) if cleaned else None
            except:
                return None
        
        # Clean text data
        def clean_text(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            return str(value).strip()
        
        # Clean boolean data
        def clean_boolean(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            value_str = str(value).strip().lower()
            if value_str in ['yes', 'true', '1', 'y']:
                return True
            elif value_str in ['no', 'false', '0', 'n']:
                return False
            return None

        
        # Clean date data
        def clean_date(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                # Handle various date formats
                value_str = str(value).strip()
                if value_str == '' or value_str.lower() in ['none', 'null', 'n/a']:
                    return None
                return value_str
            except:
                return None
        
        # Clean numeric data
        def clean_numeric(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                cleaned = str(value).replace(',', '').strip()
                return float(cleaned) if cleaned else None
            except:
                return None
        
        # Clean text data
        def clean_text(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            return str(value).strip()
        
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
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        postgres_cursor.execute(insert_sql, (
            clean_text(product_dict.get('Product Name*')),
            clean_text(product_dict.get('Product Type*')),
            clean_text(product_dict.get('Product Brand')),
            clean_text(product_dict.get('Vendor/Supplier*')),
            clean_text(product_dict.get('Product Strain')),
            clean_text(product_dict.get('Lineage')),
            clean_text(product_dict.get('Description')),
            clean_numeric(product_dict.get('Weight*')),
            clean_text(product_dict.get('Units')),
            clean_price(product_dict.get('Price')),
            clean_numeric(product_dict.get('Quantity*')),
            clean_text(product_dict.get('DOH')),
            clean_text(product_dict.get('Concentrate Type')),
            clean_text(product_dict.get('Ratio')),
            clean_text(product_dict.get('JointRatio')),
            clean_text(product_dict.get('State')),
            clean_boolean(product_dict.get('Is Sample? (yes/no)')),
            clean_boolean(product_dict.get('Is MJ product?(yes/no)')),
            clean_boolean(product_dict.get('Discountable? (yes/no)')),
            clean_text(product_dict.get('Room*')),
            clean_text(product_dict.get('Batch Number')),
            clean_text(product_dict.get('Lot Number')),
            clean_text(product_dict.get('Barcode*')),
            clean_boolean(product_dict.get('Medical Only (Yes/No)')),
            clean_price(product_dict.get('Med Price')),
            clean_date(product_dict.get('Expiration Date(YYYY-MM-DD)')),
            clean_boolean(product_dict.get('Is Archived? (yes/no)')),
            clean_text(product_dict.get('THC Per Serving')),
            clean_text(product_dict.get('Allergens')),
            clean_text(product_dict.get('Solvent')),
            clean_date(product_dict.get('Accepted Date')),
            clean_text(product_dict.get('Internal Product Identifier')),
            clean_text(product_dict.get('Product Tags (comma separated)')),
            clean_text(product_dict.get('Image URL')),
            clean_text(product_dict.get('Ingredients')),
            clean_numeric(product_dict.get('CombinedWeight')),
            clean_text(product_dict.get('Ratio_or_THC_CBD')),
            clean_text(product_dict.get('Description_Complexity')),
            clean_numeric(product_dict.get('Total THC')),
            clean_numeric(product_dict.get('THCA')),
            clean_numeric(product_dict.get('CBDA')),
            clean_numeric(product_dict.get('CBN')),
            clean_text(product_dict.get('normalized_name')),
            clean_text(product_dict.get('Test result unit (% or mg)')),
            clean_numeric(product_dict.get('THC')),
            clean_numeric(product_dict.get('CBD')),
            clean_numeric(product_dict.get('Total CBD')),
            clean_numeric(product_dict.get('CBGA')),
            clean_numeric(product_dict.get('CBG')),
            clean_numeric(product_dict.get('Total CBG')),
            clean_numeric(product_dict.get('CBC')),
            clean_numeric(product_dict.get('CBDV')),
            clean_numeric(product_dict.get('THCV')),
            clean_numeric(product_dict.get('CBGV')),
            clean_numeric(product_dict.get('CBNV')),
            clean_numeric(product_dict.get('CBGVA'))
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

if __name__ == "__main__":
    print("🐘 PythonAnywhere PostgreSQL Migration")
    print("=" * 40)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip3.11 install --user psycopg2-binary")
        exit(1)
    
    # Check connection details
    print("\\n📋 Before running migration:")
    print("1. Get your PostgreSQL connection details from PythonAnywhere")
    print("2. Set environment variables:")
    print("   export DB_HOST=your-postgres-host")
    print("   export DB_NAME=your-database-name")
    print("   export DB_USER=your-username")
    print("   export DB_PASSWORD=your-password")
    print("   export DB_PORT=5432")
    print("3. Test connection: python3.11 test_pythonanywhere_postgresql.py")
    print()
    
    # Ask for confirmation
    response = input("Ready to migrate? (y/n): ").lower().strip()
    
    if response == 'y':
        migrate_to_pythonanywhere_postgresql()
        print("\\n🎉 Migration complete!")
        print("\\n📋 Next steps:")
        print("1. Update your app to use pythonanywhere_postgresql_config.py")
        print("2. Test performance improvements")
        print("3. Enjoy faster searches!")
    else:
        print("Migration cancelled. Run when ready!")
