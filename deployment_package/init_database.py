#!/usr/bin/env python3

import sqlite3
import os
import sys

def create_products_table():
    """Create the products table with the full schema"""
    
    db_path = "/Users/adamcordova/Desktop/labelMaker_ QR copy 2/uploads/product_database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        print(f"🔧 Creating products table in: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create products table with full schema from ProductDatabase
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
        conn.commit()
        print("✅ Products table created successfully!")
        
        # Verify the table exists and has the right column
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📊 Products table has {len(columns)} columns")
        
        if "Test result unit (% or mg)" in columns:
            print("✅ Required column 'Test result unit (% or mg)' exists!")
        else:
            print("❌ Missing 'Test result unit (% or mg)' column!")
            return False
        
        # Test insert to verify it works
        try:
            from datetime import datetime
            now = datetime.now().isoformat()
            
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
            print("✅ Test insert successful")
            
            # Clean up test data
            cursor.execute("DELETE FROM products WHERE \"Product Name*\" = 'Test Product'")
            conn.commit()
            print("🧹 Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️  Test insert failed: {e}")
            return False
        
        conn.close()
        print("✅ Database initialization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    print("🗃️  Database Initialization Tool")
    print("=" * 40)
    
    success = create_products_table()
    
    if success:
        print("\n🎉 Database initialization completed successfully!")
        print("The products table is now ready for use.")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)