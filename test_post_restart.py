#!/usr/bin/env python3
"""
Post-Restart Verification Test
Run this after restarting the web server to verify concentrate weights work
"""

import sys
import os
sys.path.append('/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15')

import sqlite3
from app import process_database_product_for_api

def test_post_restart():
    """Test the concentrate weight fix after server restart"""
    
    print("🧪 Post-Restart Concentrate Weight Test")
    print("=" * 50)
    
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
    
    all_passed = True
    
    for product_name in test_products:
        print(f"\n🔍 Testing: {product_name}")
        
        # Get the product from database
        cursor.execute('SELECT * FROM products WHERE "Product Name*" = ?', (product_name,))
        db_record = cursor.fetchone()
        
        if db_record:
            try:
                processed_record = process_database_product_for_api(db_record)
                desc_weight = processed_record.get('DescAndWeight', 'NOT FOUND')
                
                # Expected result
                expected_name = product_name.split(" by ")[0] + " - 1g"
                
                if desc_weight == expected_name:
                    print(f"✅ PASS: '{desc_weight}'")
                else:
                    print(f"❌ FAIL: Got '{desc_weight}', expected '{expected_name}'")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                all_passed = False
                
        else:
            print(f"❌ NOT FOUND in database")
            all_passed = False
    
    conn.close()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Concentrate weights are working correctly")
        print("✅ Web labels should now show weights properly")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Web server may need restart or code reload")
    
    print("\n🎯 Expected in generated labels:")
    print("- Grape Slurpee Wax - 1g")
    print("- Afghani Kush Wax - 1g") 
    print("- Bruce Banner Wax - 1g")

if __name__ == "__main__":
    test_post_restart()