#!/usr/bin/env python3
"""
Quick script to rebuild the database from the latest inventory file with strain data.
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.data.product_database import ProductDatabase

def rebuild_database():
    """Rebuild the database from the latest inventory file."""
    try:
        # Source file with strain data
        excel_file = 'uploads/A Greener Today - Bothell_inventory_09-26-2025  4_51 PM.xlsx'
        
        if not os.path.exists(excel_file):
            print(f"Excel file not found: {excel_file}")
            return False
            
        print(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file)
        print(f"Excel file contains {len(df)} products")
        
        # Check strain data in Excel file
        if 'Product Strain' in df.columns:
            valid_strains = df['Product Strain'].dropna()
            valid_strains = valid_strains[valid_strains.str.strip() != '']
            print(f"Excel file contains {len(valid_strains)} products with valid strain data")
            print("Sample strains:", valid_strains.value_counts().head(5).to_dict())
        else:
            print("WARNING: No 'Product Strain' column found in Excel file")
            
        # Initialize ProductDatabase and import data
        store_name = "AGT_Bothell"  # This should match what the app uses
        db_path = f"uploads/product_database_{store_name}.db"
        
        print(f"Rebuilding database: {db_path}")
        
        # Remove existing database to start fresh
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database")
            
        # Create ProductDatabase instance
        product_db = ProductDatabase(store_name=store_name)
        
        # Import the Excel data
        print("Importing Excel data into database...")
        
        # Process each row and add to database
        for index, row in df.iterrows():
            if index % 500 == 0:
                print(f"Processed {index} / {len(df)} products...")
            
            # Convert row to dictionary
            product_data = row.to_dict()
            
            # Add to database
            try:
                product_db.add_or_update_product(product_data)
            except Exception as e:
                if index < 10:  # Only print first 10 errors to avoid spam
                    print(f"Error processing product {index}: {e}")
        
        print(f"Import completed. Checking database...")
        
        # Verify the import
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        print(f"Database now contains {total_products} products")
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE "Product Strain" IS NOT NULL AND "Product Strain" != ""')
        products_with_strain = cursor.fetchone()[0]
        print(f"Products with strain data: {products_with_strain}")
        
        # Check specific products
        test_products = ['Green Apple Moonshot', 'Orange Moonshot', 'Berry Lemonade Shot']
        for product_name in test_products:
            cursor.execute('SELECT "Product Name*", "Product Strain" FROM products WHERE "Product Name*" LIKE ?', (f'%{product_name}%',))
            results = cursor.fetchall()
            if results:
                for name, strain in results:
                    print(f"✓ Found: {name} -> Strain: {repr(strain)}")
            else:
                print(f"✗ NOT found: {product_name}")
                
        conn.close()
        print("Database rebuild completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild_database()
    sys.exit(0 if success else 1)