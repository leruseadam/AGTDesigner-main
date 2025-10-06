#!/usr/bin/env python3
"""
PythonAnywhere PostgreSQL Setup
Complete setup for PostgreSQL on PythonAnywhere
"""

import os
import sys
import subprocess

def setup_pythonanywhere_postgresql():
    """Set up PostgreSQL on PythonAnywhere"""
    
    print("🐘 Setting up PythonAnywhere PostgreSQL...")
    print("=" * 50)
    
    # Check if we're on PythonAnywhere
    if not is_pythonanywhere():
        print("❌ This script is designed for PythonAnywhere")
        print("💡 Run this on your PythonAnywhere account")
        return False
    
    print("📋 Step 1: Install PostgreSQL Client")
    install_postgresql_client()
    
    print("\\n📋 Step 2: Get Connection Details")
    get_connection_details()
    
    print("\\n📋 Step 3: Test Connection")
    test_connection()
    
    print("\\n📋 Step 4: Create Configuration")
    create_configuration()
    
    return True

def is_pythonanywhere():
    """Check if running on PythonAnywhere"""
    return 'pythonanywhere.com' in os.environ.get('HTTP_HOST', '') or 'PYTHONANYWHERE' in os.environ

def install_postgresql_client():
    """Install PostgreSQL client on PythonAnywhere"""
    
    print("📦 Installing PostgreSQL client...")
    
    try:
        # Install psycopg2-binary (works better on PythonAnywhere)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'psycopg2-binary'])
        print("✅ PostgreSQL client installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PostgreSQL client: {e}")
        print("💡 Try manually: pip3.11 install --user psycopg2-binary")
        return False

def get_connection_details():
    """Get PostgreSQL connection details from PythonAnywhere"""
    
    print("🔧 Getting PostgreSQL connection details...")
    print()
    print("📝 To get your PostgreSQL connection details:")
    print("1. Go to PythonAnywhere Dashboard")
    print("2. Click 'Databases' tab")
    print("3. Find your PostgreSQL database")
    print("4. Click on it to see connection details")
    print()
    print("📋 You'll need these details:")
    print("   • Host: (something like adamcordova.mysql.pythonanywhere-services.com)")
    print("   • Database name: (your database name)")
    print("   • Username: (your username)")
    print("   • Password: (your password)")
    print("   • Port: (usually 5432 for PostgreSQL)")
    print()
    print("💡 Copy these details - you'll need them for the next step!")

def test_connection():
    """Test PostgreSQL connection"""
    
    print("🧪 Testing PostgreSQL connection...")
    
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
        
        # Create a test configuration
        print("\\n📝 To test your connection, update these details:")
        print("   Host: [Your PostgreSQL host from PythonAnywhere]")
        print("   Database: [Your database name]")
        print("   User: [Your username]")
        print("   Password: [Your password]")
        print("   Port: 5432")
        print()
        print("💡 Then run: python test_pythonanywhere_postgresql.py")
        
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip3.11 install --user psycopg2-binary")

def create_configuration():
    """Create PythonAnywhere PostgreSQL configuration"""
    
    config_content = '''"""
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
'''
    
    with open('pythonanywhere_postgresql_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ PythonAnywhere PostgreSQL configuration created")

def create_test_script():
    """Create test script for PythonAnywhere PostgreSQL"""
    
    test_content = '''#!/usr/bin/env python3
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
        'host': os.getenv('DB_HOST', 'adamcordova.mysql.pythonanywhere-services.com'),
        'database': os.getenv('DB_NAME', 'adamcordova$labelmaker'),
        'user': os.getenv('DB_USER', 'adamcordova'),
        'password': os.getenv('DB_PASSWORD', 'YOUR_POSTGRESQL_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
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
        print("Run: python migrate_to_pythonanywhere_postgresql.py")
    else:
        print("\\n🔧 Fix connection issues first")
        print("Then run this test again")
'''
    
    with open('test_pythonanywhere_postgresql.py', 'w') as f:
        f.write(test_content)
    
    print("✅ PythonAnywhere PostgreSQL test script created")

def create_migration_script():
    """Create migration script for PythonAnywhere PostgreSQL"""
    
    migration_content = '''#!/usr/bin/env python3
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
    sqlite_path = '/Users/adamcordova/Desktop/product_database_AGT_Bothell.db'
    
    # PythonAnywhere PostgreSQL connection
    postgres_config = {
        'host': os.getenv('DB_HOST', 'adamcordova.mysql.pythonanywhere-services.com'),
        'database': os.getenv('DB_NAME', 'adamcordova$labelmaker'),
        'user': os.getenv('DB_USER', 'adamcordova'),
        'password': os.getenv('DB_PASSWORD', 'YOUR_POSTGRESQL_PASSWORD'),
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
    print("3. Test connection: python test_pythonanywhere_postgresql.py")
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
'''
    
    with open('migrate_to_pythonanywhere_postgresql.py', 'w') as f:
        f.write(migration_content)
    
    print("✅ PythonAnywhere PostgreSQL migration script created")

if __name__ == "__main__":
    print("🐘 PythonAnywhere PostgreSQL Setup")
    print("=" * 40)
    
    success = setup_pythonanywhere_postgresql()
    
    if success:
        create_test_script()
        create_migration_script()
        print("\\n🎉 PythonAnywhere PostgreSQL setup complete!")
        print("\\n📋 Next steps:")
        print("1. Get your PostgreSQL connection details from PythonAnywhere")
        print("2. Update connection details in the config files")
        print("3. Test connection: python test_pythonanywhere_postgresql.py")
        print("4. Migrate data: python migrate_to_pythonanywhere_postgresql.py")
        print("5. Update your app to use PostgreSQL")
    else:
        print("❌ Setup failed")
