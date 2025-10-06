#!/usr/bin/env python3
"""
Database initialization script for PythonAnywhere deployment
Creates the product database with proper schema
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_database_path():
    """Get the database path for PythonAnywhere"""
    # Try multiple possible locations
    possible_paths = [
        "product_database.db",  # Current directory
        "uploads/product_database.db",  # uploads subdirectory
        os.path.expanduser("~/AGTDesigner/product_database.db"),  # Full path
        os.path.expanduser("~/AGTDesigner/uploads/product_database.db"),  # uploads path
    ]
    
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir, exist_ok=True)
        print(f"📁 Created directory: {uploads_dir}")
    
    # Use uploads/product_database.db as default
    return "uploads/product_database.db"

def create_products_table(db_path):
    """Create the products table with the full schema"""
    
    try:
        print(f"🔧 Initializing database: {db_path}")
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 Created directory: {db_dir}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create products table with full schema
        create_products_sql = '''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                "Product Name*" TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                strain_id INTEGER,
                "Product Type*" TEXT NOT NULL,
                "Vendor/Supplier*" TEXT,
                "Product Brand" TEXT,
                "Description" TEXT,
                "Weight*" TEXT,
                "Units" TEXT,
                "Price" TEXT,
                "Lineage" TEXT,
                first_seen_date TEXT NOT NULL,
                last_seen_date TEXT NOT NULL,
                total_occurrences INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                "Product Strain" TEXT,
                "Quantity*" TEXT,
                "DOH" TEXT,
                "Concentrate Type" TEXT,
                "Ratio" TEXT,
                "JointRatio" TEXT,
                "THC test result" TEXT,
                "CBD test result" TEXT,
                "Test result unit (% or mg)" TEXT,
                "State" TEXT,
                "Is Sample? (yes/no)" TEXT,
                "Is MJ product?(yes/no)" TEXT,
                "Discountable? (yes/no)" TEXT,
                "Room*" TEXT,
                "Batch Number" TEXT,
                "Lot Number" TEXT,
                "Barcode*" TEXT,
                "Medical Only (Yes/No)" TEXT,
                "Med Price" TEXT,
                "Expiration Date(YYYY-MM-DD)" TEXT,
                "Is Archived? (yes/no)" TEXT,
                "THC Per Serving" TEXT,
                "Allergens" TEXT,
                "Solvent" TEXT,
                "Accepted Date" TEXT,
                "Internal Product Identifier" TEXT,
                "Product Tags (comma separated)" TEXT,
                "Image URL" TEXT,
                "Ingredients" TEXT,
                "Total THC" TEXT,
                "THCA" TEXT,
                "CBDA" TEXT,
                "CBN" TEXT,
                "THC" TEXT,
                "CBD" TEXT,
                "Total CBD" TEXT,
                "CBGA" TEXT,
                "CBG" TEXT,
                "Total CBG" TEXT,
                "CBC" TEXT,
                "CBDV" TEXT,
                "THCV" TEXT,
                "CBGV" TEXT,
                "CBNV" TEXT,
                "CBGVA" TEXT,
                FOREIGN KEY (strain_id) REFERENCES strains (id),
                UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
            )
        '''
        
        print("➕ Creating products table...")
        cursor.execute(create_products_sql)
        
        # Create strains table if it doesn't exist
        create_strains_sql = '''
            CREATE TABLE IF NOT EXISTS strains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                lineage TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        '''
        
        print("➕ Creating strains table...")
        cursor.execute(create_strains_sql)
        
        conn.commit()
        print("✅ Database tables created successfully!")
        
        # Verify the tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📊 Created tables: {', '.join(tables)}")
        
        # Verify products table has the right columns
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📊 Products table has {len(columns)} columns")
        
        if "Test result unit (% or mg)" in columns:
            print("✅ Required column 'Test result unit (% or mg)' exists!")
        else:
            print("❌ Missing 'Test result unit (% or mg)' column!")
            return False
        
        # Test basic operations
        try:
            now = datetime.now().isoformat()
            
            # Test insert
            test_data = (
                "Test Product",  # Product Name*
                "test_product",  # normalized_name
                "Flower",       # Product Type*
                now,            # first_seen_date
                now,            # last_seen_date
                now,            # created_at
                now,            # updated_at
                "%"             # Test result unit (% or mg)
            )
            
            cursor.execute('''
                INSERT OR IGNORE INTO products 
                ("Product Name*", normalized_name, "Product Type*", first_seen_date, last_seen_date, created_at, updated_at, "Test result unit (% or mg)") 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', test_data)
            
            conn.commit()
            
            # Test query
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            print(f"📊 Products in database: {count}")
            
            # Clean up test data
            cursor.execute("DELETE FROM products WHERE \"Product Name*\" = 'Test Product'")
            conn.commit()
            print("🧹 Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️  Database operations test failed: {e}")
            return False
        
        conn.close()
        print(f"✅ Database initialized successfully at: {os.path.abspath(db_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def add_sample_data(db_path):
    """Add some sample data to test the database"""
    try:
        print("➕ Adding sample data...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        sample_products = [
            ("Blue Dream - 3.5g", "blue_dream_35g", "Flower", "A Greener Today", "High End Farms", "3.5", "g", "$45.00", "HYBRID", "Blue Dream"),
            ("Wedding Cake - 1g", "wedding_cake_1g", "Flower", "A Greener Today", "Thunder Chief", "1", "g", "$15.00", "INDICA", "Wedding Cake"),
            ("Sour Diesel - 1g Pre-Roll", "sour_diesel_1g_preroll", "Pre-Roll", "A Greener Today", "Various", "1", "g", "$12.00", "SATIVA", "Sour Diesel"),
            ("Mixed Strain Gummies - 10mg", "mixed_strain_gummies_10mg", "Edible (Solid)", "A Greener Today", "Kellys", "10", "mg", "$8.00", "MIXED", "Mixed"),
            ("CBD Tincture - 30ml", "cbd_tincture_30ml", "Tincture", "A Greener Today", "Various", "30", "ml", "$35.00", "CBD", "CBD Blend"),
        ]
        
        for product in sample_products:
            cursor.execute('''
                INSERT OR IGNORE INTO products 
                ("Product Name*", normalized_name, "Product Type*", "Vendor/Supplier*", "Product Brand", "Weight*", "Units", "Price", "Lineage", "Product Strain", first_seen_date, last_seen_date, created_at, updated_at, "Test result unit (% or mg)") 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product + (now, now, now, now, "%"))
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"✅ Sample data added. Total products: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        return False

if __name__ == "__main__":
    print("🗃️  PythonAnywhere Database Initialization")
    print("=" * 50)
    
    db_path = get_database_path()
    print(f"📍 Database location: {db_path}")
    
    success = create_products_table(db_path)
    
    if success:
        print("\n🎉 Database initialization completed successfully!")
        
        # Ask if user wants sample data
        add_samples = input("\nWould you like to add sample data for testing? (y/n): ").lower().startswith('y')
        if add_samples:
            add_sample_data(db_path)
        
        print(f"\n📍 Database created at: {os.path.abspath(db_path)}")
        print("The products table is now ready for use.")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)