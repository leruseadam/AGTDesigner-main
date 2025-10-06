#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15')

import sqlite3
from app import process_database_product_for_api

def test_exact_wax_products():
    """Test the exact wax products from the Word document"""
    
    # Connect to database
    db_path = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/uploads/product_database_AGT_Bothell.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This makes rows accessible like dictionaries
    cursor = conn.cursor()
    
    # Test the exact products from Word document
    test_products = [
        "Grape Slurpee Wax by Hustler's Ambition - 1g",
        "Afghani Kush Wax by Hustler's Ambition - 1g", 
        "Bruce Banner Wax by Hustler's Ambition - 1g"
    ]
    
    print("Testing exact wax products from Word document:")
    print("=" * 60)
    
    for product_name in test_products:
        print(f"\nTesting: {product_name}")
        
        # Get the product from database
        cursor.execute('SELECT * FROM products WHERE "Product Name*" = ?', (product_name,))
        db_record = cursor.fetchone()
        
        if db_record:
            print(f"✓ Found in database")
            print(f"  Weight*: {db_record['Weight*']}")
            print(f"  Units: {db_record['Units']}")
            print(f"  Product Type*: {db_record['Product Type*']}")
            
            # Process through API function
            try:
                processed_record = process_database_product_for_api(db_record)
                print(f"✓ Processed successfully")
                print(f"  DescAndWeight: '{processed_record.get('DescAndWeight', 'NOT FOUND')}'")
                
                # Check if weight is in DescAndWeight
                desc_weight = processed_record.get('DescAndWeight', '')
                if '1g' in desc_weight or '1.0g' in desc_weight:
                    print(f"✓ Weight correctly included in DescAndWeight")
                else:
                    print(f"❌ Weight missing from DescAndWeight")
                    
            except Exception as e:
                print(f"❌ Processing failed: {e}")
                
        else:
            print(f"❌ Not found in database")
    
    conn.close()

if __name__ == "__main__":
    test_exact_wax_products()