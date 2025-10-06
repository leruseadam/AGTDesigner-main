#!/usr/bin/env python3

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

def create_database_tables(db_path):
    """Create database tables directly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create strains table
    cursor.execute('''
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
    ''')
    
    # Create products table with all Excel columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Product Name*" TEXT NOT NULL,
            "Brand*" TEXT,
            "Size*" TEXT,
            "Total THC" REAL,
            "Total CBD" REAL,
            "Category*" TEXT,
            "Sub-Category*" TEXT,
            "Product Type*" TEXT,
            "Batch Number" TEXT,
            "Product UPC" TEXT,
            "Product Strain" TEXT,
            "Indica, Sativa, Hybrid, or N/A (CBD products)*" TEXT,
            "Flower Type" TEXT,
            "Net Weight (Grams)" TEXT,
            "Units per package" TEXT,
            "Weight" REAL,
            "Units" TEXT,
            "Created" TEXT,
            "Price" TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Create other tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lineage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strain_id INTEGER,
            old_lineage TEXT,
            new_lineage TEXT,
            changed_at TEXT NOT NULL,
            FOREIGN KEY (strain_id) REFERENCES strains (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strain_brand_lineage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strain_name TEXT NOT NULL,
            brand_name TEXT NOT NULL,
            lineage TEXT,
            confidence REAL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully")

def rebuild_database_direct():
    """Rebuild the database using direct SQL approach"""
    
    print("Starting direct database rebuild...")
    
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
        # Create database and tables directly
        print("Creating database tables...")
        create_database_tables(database_path)
        
        # Verify tables were created
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Created tables: {[t[0] for t in tables]}")
        conn.close()
        
        if not tables:
            print("ERROR: No tables were created!")
            return False
        
        print("Loading Excel file...")
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} products from Excel")
        
        # Show sample of Product Strain data from Excel
        strain_sample = df['Product Strain'].dropna().value_counts().head(10)
        print("Top Product Strain values in Excel:")
        for strain, count in strain_sample.items():
            print(f"  '{strain}': {count} products")
        
        # Import products directly to database
        print("Importing products to database...")
        conn = sqlite3.connect(database_path)
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        success_count = 0
        for index, row in df.iterrows():
            if index % 100 == 0:
                print(f"Processing product {index + 1}/{len(df)}")
            
            try:
                # Insert product directly 
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (
                        "Product Name*", "Brand*", "Size*", "Total THC", "Total CBD",
                        "Category*", "Sub-Category*", "Product Type*", "Batch Number", "Product UPC",
                        "Product Strain", "Indica, Sativa, Hybrid, or N/A (CBD products)*", "Flower Type",
                        "Net Weight (Grams)", "Units per package", "Weight", "Units", 
                        "Created", "Price", created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('Product Name*', ''),
                    row.get('Brand*', ''),  
                    row.get('Size*', ''),
                    row.get('Total THC', None),
                    row.get('Total CBD', None),
                    row.get('Category*', ''),
                    row.get('Sub-Category*', ''),
                    row.get('Product Type*', ''),
                    row.get('Batch Number', ''),
                    row.get('Product UPC', ''),
                    row.get('Product Strain', ''),  # This is the key field!
                    row.get('Indica, Sativa, Hybrid, or N/A (CBD products)*', ''),
                    row.get('Flower Type', ''),
                    row.get('Net Weight (Grams)', ''),
                    row.get('Units per package', ''),
                    row.get('Weight', None),
                    row.get('Units', ''),
                    row.get('Created', ''),
                    row.get('Price', ''),
                    now,
                    now
                ))
                
                success_count += 1
                
                # Commit every 100 records
                if success_count % 100 == 0:
                    conn.commit()
                    
            except Exception as e:
                print(f"Error inserting product {index + 1}: {e}")
                continue
        
        # Final commit
        conn.commit()
        print(f"Successfully imported {success_count} products")
        
        # Final verification
        print("\n=== FINAL DATABASE VERIFICATION ===")
        cursor = conn.cursor()
        
        # Check products count
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        print(f"Database now contains {products_count} products")
        
        # Check Product Strain values in database
        cursor.execute('SELECT "Product Strain", COUNT(*) FROM products WHERE "Product Strain" IS NOT NULL AND "Product Strain" != "" AND "Product Strain" != " " GROUP BY "Product Strain" ORDER BY COUNT(*) DESC LIMIT 10')
        strain_samples = cursor.fetchall()
        print("Top Product Strain values in database:")
        for strain, count in strain_samples:
            print(f"  '{strain}': {count} products")
        
        # Test specific products mentioned in the issue
        print("\nTesting specific products:")
        test_products = ['Green Apple Moonshot', 'Orange Moonshot', 'Cherry Moonshot']
        
        for product_name in test_products:
            cursor.execute('SELECT "Product Strain" FROM products WHERE "Product Name*" LIKE ?', (f'%{product_name}%',))
            results = cursor.fetchall()
            if results:
                strain = results[0][0] if results[0][0] else 'Empty/NULL'
                print(f"  {product_name}: strain='{strain}'")
            else:
                print(f"  {product_name}: Product not found in database")
        
        conn.close()
        
        if products_count > 0:
            print(f"\n✅ Database rebuild completed successfully! {products_count} products imported.")
            return True
        else:
            print(f"\n❌ Database rebuild failed - no products imported.")
            return False
        
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild_database_direct()
    sys.exit(0 if success else 1)