#!/usr/bin/env python3
"""
Create a fixed database with all necessary columns including ProductName
"""
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_fixed_database():
    """Create database with comprehensive schema including ProductName column"""
    try:
        # Connect to database
        conn = sqlite3.connect('product_database.db')
        cursor = conn.cursor()
        
        # Create strains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strain_name TEXT NOT NULL UNIQUE,
                normalized_name TEXT NOT NULL,
                lineage TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create products table with ALL needed columns
        cursor.execute('''
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
                -- Additional cannabinoid columns
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
                -- CRITICAL: Excel processor compatibility columns
                "ProductName" TEXT,
                "Units_Alt" TEXT,
                "Price_Alt" TEXT,
                "DOH Compliant (Yes/No)" TEXT,
                "Joint Ratio" TEXT,
                "Quantity Received*" TEXT,
                "qty" TEXT,
                FOREIGN KEY (strain_id) REFERENCES strains (id),
                UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
            )
        ''')
        
        # Create lineage_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lineage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strain_id INTEGER,
                old_lineage TEXT,
                new_lineage TEXT,
                change_date TEXT NOT NULL,
                change_reason TEXT,
                FOREIGN KEY (strain_id) REFERENCES strains (id)
            )
        ''')
        
        # Create strain-brand lineage overrides
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strain_brand_lineage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strain_name TEXT NOT NULL,
                brand TEXT NOT NULL,
                lineage TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(strain_name, brand)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strains_normalized ON strains(normalized_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_normalized ON products(normalized_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_strain ON products(strain_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_vendor_brand ON products("Vendor/Supplier*", "Product Brand")')
        
        # Create session management tables (if needed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                data TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database created successfully with ProductName column")
        
        # Verify the column exists
        conn = sqlite3.connect('product_database.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        
        product_name_exists = any(col[1] == 'ProductName' for col in columns)
        if product_name_exists:
            logger.info("✅ ProductName column confirmed to exist")
        else:
            logger.error("❌ ProductName column missing!")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

if __name__ == "__main__":
    create_fixed_database()