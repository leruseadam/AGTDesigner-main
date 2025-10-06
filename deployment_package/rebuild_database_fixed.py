#!/usr/bin/env python3

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.data.product_database import ProductDatabase

def rebuild_database():
    """Rebuild the database from Excel file with proper initialization"""
    
    print("Starting database rebuild...")
    
    # Store name for AGT Bothell 
    store_name = "AGT_Bothell"
    
    # Excel file path
    excel_path = "/Users/adamcordova/Downloads/A Greener Today - Bothell_inventory_09-26-2025  4_51 PM.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"ERROR: Excel file not found: {excel_path}")
        return False
    
    # Database path
    database_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(database_dir, exist_ok=True)
    database_path = os.path.join(database_dir, f"product_database_{store_name}.db")
    
    # Remove existing database to start fresh
    if os.path.exists(database_path):
        print(f"Removing existing database: {database_path}")
        os.remove(database_path)
    
    try:
        # Initialize ProductDatabase - this will create all tables
        print("Initializing database...")
        db = ProductDatabase(store_name)
        db.init_database()  # Explicitly call initialization
        
        # Verify tables were created
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Created tables: {[t[0] for t in tables]}")
        conn.close()
        
        print("Loading Excel file...")
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} products from Excel")
        
        # Import products using ProductDatabase method
        print("Importing products...")
        success_count = 0
        
        for index, row in df.iterrows():
            if index % 100 == 0:
                print(f"Processing product {index + 1}/{len(df)}")
            
            try:
                # Convert row to dictionary
                product_data = row.to_dict()
                
                # Add/update product using ProductDatabase method
                result = db.add_or_update_product(product_data)
                if result:
                    success_count += 1
            except Exception as e:
                print(f"Error processing product {index + 1}: {e}")
                continue
        
        print(f"Successfully imported {success_count} products")
        
        # Verify database contents
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Check products count
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        print(f"Database now contains {products_count} products")
        
        # Check strain data
        cursor.execute('SELECT COUNT(*) FROM strains')
        strains_count = cursor.fetchone()[0]
        print(f"Database now contains {strains_count} strains")
        
        # Sample some Product Strain values
        cursor.execute('SELECT "Product Strain", COUNT(*) FROM products WHERE "Product Strain" IS NOT NULL AND "Product Strain" != "" AND "Product Strain" != " " GROUP BY "Product Strain" ORDER BY COUNT(*) DESC LIMIT 10')
        strain_samples = cursor.fetchall()
        print("Top Product Strain values:")
        for strain, count in strain_samples:
            print(f"  '{strain}': {count} products")
        
        conn.close()
        
        # Test specific products mentioned in the issue
        print("\nTesting specific products:")
        test_products = ['Green Apple Moonshot', 'Orange Moonshot', 'Cherry Moonshot']
        
        for product_name in test_products:
            product_info = db.get_product_by_name(product_name)
            if product_info:
                strain = product_info.get('Product Strain', 'Not found')
                print(f"  {product_name}: strain='{strain}'")
            else:
                print(f"  {product_name}: Product not found")
        
        print("\nDatabase rebuild completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild_database()
    sys.exit(0 if success else 1)