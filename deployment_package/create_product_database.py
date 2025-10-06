#!/usr/bin/env python3.11
"""
Simple script to create the missing product_database.py file
Run this directly on PythonAnywhere
"""

import os

def create_product_database_file():
    """Create the missing product_database.py file"""
    
    # Ensure the directory exists
    data_dir = 'src/core/data'
    os.makedirs(data_dir, exist_ok=True)
    
    # Create the file
    file_path = os.path.join(data_dir, 'product_database.py')
    
    content = '''#!/usr/bin/env python3
"""
Minimal ProductDatabase for PythonAnywhere deployment
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

def get_database_path(store_name=None):
    """Get the correct database path for ProductDatabase instances."""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    uploads_dir = os.path.join(current_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    if store_name:
        db_filename = f'product_database_{store_name}.db'
        return os.path.join(uploads_dir, db_filename)
    else:
        return os.path.join(uploads_dir, 'product_database.db')

class ProductDatabase:
    """Minimal database for storing and managing product information."""
    
    def __init__(self, db_path: str = None, store_name: str = None):
        if db_path is None:
            self.db_path = get_database_path(store_name)
        else:
            self.db_path = db_path
        self._initialized = False
    
    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables."""
        if self._initialized:
            return True
            
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create strains table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strain_name TEXT UNIQUE NOT NULL,
                    normalized_name TEXT NOT NULL,
                    canonical_lineage TEXT,
                    first_seen_date TEXT NOT NULL,
                    last_seen_date TEXT NOT NULL,
                    total_occurrences INTEGER DEFAULT 1,
                    lineage_confidence REAL DEFAULT 0.0,
                    sovereign_lineage TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create products table
            cursor.execute("""
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
            """)
            
            conn.commit()
            conn.close()
            self._initialized = True
            print(f"Database initialized at: {self.db_path}")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
        
        return True
    
    def get_products(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get products from the database."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("SELECT * FROM products LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM products")
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return products
            
        except Exception as e:
            print(f"Error getting products: {e}")
            return []
    
    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """Add a product to the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build INSERT statement dynamically
            columns = list(product_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join([f'"{col}"' for col in columns])
            
            sql = f"""
                INSERT OR REPLACE INTO products 
                ({column_names})
                VALUES ({placeholders})
            """
            
            values = [product_data[col] for col in columns]
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding product: {e}")
            return False

def get_product_database(store_name=None):
    """Get a ProductDatabase instance for the specified store."""
    return ProductDatabase(store_name=store_name)

if __name__ == "__main__":
    # Test the database
    db = ProductDatabase()
    db.init_database()
    products = db.get_products()
    print(f"Database has {len(products)} products")
'''
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Created {file_path}")
        print(f"📁 File size: {os.path.getsize(file_path)} bytes")
        
        # Test the import
        import sys
        sys.path.insert(0, '.')
        from src.core.data.product_database import ProductDatabase
        print("✅ Import test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating file: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Creating product_database.py file...")
    success = create_product_database_file()
    
    if success:
        print("\n🎉 File created successfully!")
        print("You can now test the application import:")
        print("python3.11 -c 'from app import app'")
    else:
        print("\n❌ File creation failed!")
