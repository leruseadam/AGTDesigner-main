#!/usr/bin/env python3.11
"""
Simple database fix that bypasses psutil issues
Uses pandas directly to avoid ExcelProcessor complications
"""

import os
import sys
import pandas as pd
import sqlite3
from datetime import datetime

# Detect environment
if os.path.exists('/home/adamcordova'):
    # PythonAnywhere environment
    project_dir = '/home/adamcordova/AGTDesigner'
else:
    # Local environment
    project_dir = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 5'

def create_simple_database():
    """Create a simple database with sample data"""
    print("🚀 Creating simple database with sample data...")
    
    # Database path
    db_path = os.path.join(project_dir, 'uploads', 'product_database_AGT_Bothell.db')
    
    # Ensure uploads directory exists
    os.makedirs(os.path.join(project_dir, 'uploads'), exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database: {db_path}")
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Product Name*" TEXT NOT NULL,
            "Product Type*" TEXT NOT NULL,
            "Vendor/Supplier*" TEXT,
            "Product Brand" TEXT,
            "Description" TEXT,
            "Weight*" TEXT,
            "Price" TEXT,
            "Lineage" TEXT,
            "Product Strain" TEXT,
            "THC test result" TEXT,
            "CBD test result" TEXT,
            "Test result unit (% or mg)" TEXT,
            "Quantity*" TEXT,
            "Weight Unit* (grams/gm or ounces/oz)" TEXT,
            "Lot Number" TEXT,
            "Barcode*" TEXT,
            "State" TEXT,
            "Room*" TEXT,
            "Batch Number" TEXT,
            "Product Tags (comma separated)" TEXT,
            "Internal Product Identifier" TEXT,
            "Expiration Date(YYYY-MM-DD)" TEXT,
            "Is Archived? (yes/no)" TEXT,
            "THC Per Serving" TEXT,
            "Allergens" TEXT,
            "Solvent" TEXT,
            "Accepted Date" TEXT,
            "Medical Only (Yes/No)" TEXT,
            "Med Price" TEXT,
            "Total THC" TEXT,
            "THCA" TEXT,
            "CBDA" TEXT,
            "CBN" TEXT,
            "Image URL" TEXT,
            "Ingredients" TEXT,
            "DOH Compliant (Yes/No)" TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Create strains table
    cursor.execute('''
        CREATE TABLE strains (
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
    
    # Insert sample data
    sample_products = [
        {
            'Product Name*': 'Blue Dream',
            'Product Type*': 'Flower',
            'Vendor/Supplier*': 'AGT Bothell',
            'Product Brand': 'AGT Premium',
            'Description': 'Classic sativa-dominant hybrid',
            'Weight*': '3.5',
            'Price': '45.00',
            'Lineage': 'SATIVA',
            'Product Strain': 'Blue Dream',
            'THC test result': '18.5',
            'CBD test result': '0.8',
            'Test result unit (% or mg)': '%',
            'Quantity*': '1',
            'Weight Unit* (grams/gm or ounces/oz)': 'grams',
            'Lot Number': 'BD001',
            'Barcode*': '1234567890123',
            'State': 'WA',
            'Room*': 'Flower Room A',
            'Batch Number': 'BD2025001',
            'Product Tags (comma separated)': 'premium, sativa, hybrid',
            'Internal Product Identifier': 'BD-001',
            'Expiration Date(YYYY-MM-DD)': '2025-12-31',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '18.5',
            'Allergens': 'None',
            'Solvent': '',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '40.00',
            'Total THC': '18.5',
            'THCA': '0.2',
            'CBDA': '0.1',
            'CBN': '0.1',
            'Image URL': '',
            'Ingredients': 'Cannabis',
            'DOH Compliant (Yes/No)': 'Yes',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'Product Name*': 'OG Kush',
            'Product Type*': 'Flower',
            'Vendor/Supplier*': 'AGT Bothell',
            'Product Brand': 'AGT Premium',
            'Description': 'Classic indica strain',
            'Weight*': '3.5',
            'Price': '50.00',
            'Lineage': 'INDICA',
            'Product Strain': 'OG Kush',
            'THC test result': '22.3',
            'CBD test result': '0.5',
            'Test result unit (% or mg)': '%',
            'Quantity*': '1',
            'Weight Unit* (grams/gm or ounces/oz)': 'grams',
            'Lot Number': 'OG001',
            'Barcode*': '1234567890124',
            'State': 'WA',
            'Room*': 'Flower Room B',
            'Batch Number': 'OG2025001',
            'Product Tags (comma separated)': 'premium, indica, classic',
            'Internal Product Identifier': 'OG-001',
            'Expiration Date(YYYY-MM-DD)': '2025-12-31',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '22.3',
            'Allergens': 'None',
            'Solvent': '',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '45.00',
            'Total THC': '22.3',
            'THCA': '0.3',
            'CBDA': '0.1',
            'CBN': '0.2',
            'Image URL': '',
            'Ingredients': 'Cannabis',
            'DOH Compliant (Yes/No)': 'Yes',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'Product Name*': 'CBD Tincture',
            'Product Type*': 'Tincture',
            'Vendor/Supplier*': 'AGT Bothell',
            'Product Brand': 'AGT Wellness',
            'Description': 'High CBD tincture for wellness',
            'Weight*': '30',
            'Price': '35.00',
            'Lineage': 'CBD',
            'Product Strain': 'CBD',
            'THC test result': '0.3',
            'CBD test result': '25.0',
            'Test result unit (% or mg)': '%',
            'Quantity*': '1',
            'Weight Unit* (grams/gm or ounces/oz)': 'ml',
            'Lot Number': 'CBD001',
            'Barcode*': '1234567890125',
            'State': 'WA',
            'Room*': 'Extract Room',
            'Batch Number': 'CBD2025001',
            'Product Tags (comma separated)': 'wellness, cbd, tincture',
            'Internal Product Identifier': 'CBD-001',
            'Expiration Date(YYYY-MM-DD)': '2026-01-01',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '0.3',
            'Allergens': 'None',
            'Solvent': 'MCT Oil',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '30.00',
            'Total THC': '0.3',
            'THCA': '0.0',
            'CBDA': '0.0',
            'CBN': '0.0',
            'Image URL': '',
            'Ingredients': 'CBD Extract, MCT Oil',
            'DOH Compliant (Yes/No)': 'Yes',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    ]
    
    # Insert products
    for product in sample_products:
        columns = list(product.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'"{col}"' for col in columns])
        
        sql = f'''
            INSERT INTO products 
            ({column_names})
            VALUES ({placeholders})
        '''
        
        values = [product[col] for col in columns]
        cursor.execute(sql, values)
    
    # Insert strains
    sample_strains = [
        {
            'strain_name': 'Blue Dream',
            'normalized_name': 'blue dream',
            'canonical_lineage': 'SATIVA',
            'first_seen_date': datetime.now().isoformat(),
            'last_seen_date': datetime.now().isoformat(),
            'total_occurrences': 1,
            'lineage_confidence': 0.9,
            'sovereign_lineage': 'SATIVA',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'strain_name': 'OG Kush',
            'normalized_name': 'og kush',
            'canonical_lineage': 'INDICA',
            'first_seen_date': datetime.now().isoformat(),
            'last_seen_date': datetime.now().isoformat(),
            'total_occurrences': 1,
            'lineage_confidence': 0.9,
            'sovereign_lineage': 'INDICA',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'strain_name': 'CBD',
            'normalized_name': 'cbd',
            'canonical_lineage': 'CBD',
            'first_seen_date': datetime.now().isoformat(),
            'last_seen_date': datetime.now().isoformat(),
            'total_occurrences': 1,
            'lineage_confidence': 0.9,
            'sovereign_lineage': 'CBD',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    ]
    
    for strain in sample_strains:
        columns = list(strain.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        sql = f'''
            INSERT INTO strains 
            ({column_names})
            VALUES ({placeholders})
        '''
        
        values = [strain[col] for col in columns]
        cursor.execute(sql, values)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"✅ Database created successfully: {db_path}")
    print(f"📊 Products: {len(sample_products)}")
    print(f"🌿 Strains: {len(sample_strains)}")
    
    return True

def main():
    """Main function"""
    print("🚀 SIMPLE DATABASE FIX (NO PSUTIL)")
    print("=" * 40)
    
    print(f"📍 Project directory: {project_dir}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    success = create_simple_database()
    
    if success:
        print("\n🎉 Database created successfully!")
        print("💡 Refresh your web page to see the products")
        return True
    else:
        print("\n❌ Failed to create database")
        return False

if __name__ == "__main__":
    main()
