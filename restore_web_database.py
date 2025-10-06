#!/usr/bin/env python3
"""
Restore web database with sample data
"""
import sqlite3
import os
import json

def create_database():
    """Create and populate the main product database"""
    print("Creating product_database.db...")
    
    conn = sqlite3.connect('product_database.db')
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            vendor TEXT,
            brand TEXT,
            product_type TEXT,
            weight TEXT,
            weight_units TEXT,
            thc_content TEXT,
            cbd_content TEXT,
            lineage TEXT,
            doh_status TEXT,
            price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample products
    sample_products = [
        ('Blue Raspberry Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Grape Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Peach Mango Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Pineapple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Green Apple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Orange Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Island Punch Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'SATIVA', 'DOH', '$25.00'),
        ('Raspberry Lemonade Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'SATIVA', 'DOH', '$25.00'),
        ('Grape Dream Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'INDICA', 'DOH', '$25.00'),
        ('Strawberry Banana Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'HYBRID', 'DOH', '$25.00'),
    ]
    
    for product in sample_products:
        cursor.execute('''
            INSERT INTO products (product_name, vendor, brand, product_type, weight, weight_units, 
                                thc_content, cbd_content, lineage, doh_status, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print("✅ product_database.db created with sample data")

def create_agt_bothell_database():
    """Create and populate the AGT Bothell database"""
    print("Creating product_database_AGT_Bothell.db...")
    
    conn = sqlite3.connect('product_database_AGT_Bothell.db')
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            vendor TEXT,
            brand TEXT,
            product_type TEXT,
            weight TEXT,
            weight_units TEXT,
            thc_content TEXT,
            cbd_content TEXT,
            lineage TEXT,
            doh_status TEXT,
            price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert AGT Bothell specific products
    agt_products = [
        ('Blue Raspberry Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Grape Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Peach Mango Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Pineapple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Green Apple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Orange Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
    ]
    
    for product in agt_products:
        cursor.execute('''
            INSERT INTO products (product_name, vendor, brand, product_type, weight, weight_units, 
                                thc_content, cbd_content, lineage, doh_status, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print("✅ product_database_AGT_Bothell.db created with sample data")

def main():
    print("🔧 RESTORING WEB DATABASE")
    print("=" * 50)
    
    # Remove existing databases if they exist
    for db_file in ['product_database.db', 'product_database_AGT_Bothell.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Removed existing {db_file}")
    
    # Create new databases
    create_database()
    create_agt_bothell_database()
    
    print("\n" + "=" * 50)
    print("✅ Database restoration complete!")
    print("📊 Both databases now contain sample product data")

if __name__ == "__main__":
    main()