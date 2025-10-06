#!/usr/bin/env python3
"""
Import database data from JSON export
Run this script on PythonAnywhere after uploading database_export.json
"""

import sqlite3
import json
import os
from datetime import datetime

def import_database_data():
    """Import data from JSON export"""
    
    export_file = "database_export.json"
    if not os.path.exists(export_file):
        print(f"❌ Export file not found: {export_file}")
        print("Please upload database_export.json to your PythonAnywhere directory first!")
        return False
    
    print(f"📂 Loading data from: {export_file}")
    
    try:
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        strains = data.get('strains', [])
        
        print(f"📊 Found {len(products)} products to import")
        print(f"📊 Found {len(strains)} strains to import")
        
        # Connect to database
        db_path = "uploads/product_database.db"
        if not os.path.exists("uploads"):
            os.makedirs("uploads", exist_ok=True)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Import strains first
        if strains:
            print("➕ Importing strains...")
            for strain in strains:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO strains 
                        (id, name, lineage, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        strain.get('id'),
                        strain.get('name'),
                        strain.get('lineage'),
                        strain.get('created_at'),
                        strain.get('updated_at')
                    ))
                except Exception as e:
                    print(f"⚠️  Error importing strain {strain.get('name', 'unknown')}: {e}")
        
        # Import products
        if products:
            print("➕ Importing products...")
            imported_count = 0
            
            for product in products:
                try:
                    # Build INSERT statement dynamically based on available columns
                    columns = list(product.keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    column_names = ', '.join([f'"{col}"' for col in columns])
                    
                    sql = f"""
                        INSERT OR REPLACE INTO products 
                        ({column_names})
                        VALUES ({placeholders})
                    """
                    
                    values = [product[col] for col in columns]
                    cursor.execute(sql, values)
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        print(f"   Imported {imported_count} products...")
                        
                except Exception as e:
                    print(f"⚠️  Error importing product {product.get('Product Name*', 'unknown')}: {e}")
            
            print(f"✅ Imported {imported_count} products")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database import completed successfully!")
        
        # Verify import
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"📊 Total products in database: {product_count}")
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing database: {e}")
        return False

if __name__ == "__main__":
    print("🗃️  Database Import Tool")
    print("=" * 40)
    
    success = import_database_data()
    
    if success:
        print("\n🎉 Import completed successfully!")
    else:
        print("\n❌ Import failed!")
