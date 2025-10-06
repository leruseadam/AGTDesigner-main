#!/usr/bin/env python3

"""
End-to-End Concentrate Filter Test

Tests the complete concentrate filtering workflow including:
1. Database search for concentrate products
2. Label generation with proper weight display
3. Template processing with DescAndWeight field
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from app import get_excel_processor, process_database_product_for_api
from src.core.data.product_database import ProductDatabase

def test_concentrate_end_to_end():
    """Test the complete concentrate filtering and label generation process."""
    
    print("🔍 Testing concentrate filter end-to-end...")
    
    # Step 1: Initialize Excel processor (simulates Flask app startup)
    try:
        excel_processor = get_excel_processor()
        print("✅ Excel processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Excel processor: {e}")
        return False
    
    # Step 2: Find concentrate products in database
    try:
        product_db = ProductDatabase()
        
        # Search for concentrate products
        query = """
        SELECT "Product Name*", Description, "Weight*", Units, "Product Type*" 
        FROM products 
        WHERE "Product Type*" LIKE '%Concentrate%' 
           OR "Product Type*" LIKE '%RSO%' 
           OR "Product Type*" LIKE '%Tanker%'
           OR Description LIKE '%resin%' 
           OR Description LIKE '%rosin%'
        LIMIT 5
        """
        
        db_path = "/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/uploads/product_database_AGT_Bothell.db"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            concentrate_products = [dict(row) for row in cursor.fetchall()]
        
        print(f"✅ Found {len(concentrate_products)} concentrate products in database")
        
        if not concentrate_products:
            print("❌ No concentrate products found!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to search database: {e}")
        return False
    
    # Step 3: Test processing each concentrate product
    all_passed = True
    for i, product in enumerate(concentrate_products):
        print(f"\n📋 Testing product {i+1}: {product.get('Product Name*', 'UNKNOWN')}")
        print(f"   Type: {product.get('Product Type*', 'UNKNOWN')}")
        print(f"   Weight: {product.get('Weight*', 'MISSING')} {product.get('Units', 'MISSING')}")
        
        try:
            # Process the product through the API function
            processed = process_database_product_for_api(product)
            desc_and_weight = processed.get('DescAndWeight', 'MISSING')
            
            print(f"   ✅ Processed DescAndWeight: '{desc_and_weight}'")
            
            # Check if weight is included
            weight = product.get('Weight*')
            units = product.get('Units')
            
            if weight and units:
                expected_weight = f"{weight}{units}".replace('.0', '')  # Remove trailing zero
                if expected_weight in desc_and_weight:
                    print(f"   ✅ Weight '{expected_weight}' found in DescAndWeight")
                else:
                    print(f"   ⚠️  Expected weight '{expected_weight}' NOT found in DescAndWeight")
                    all_passed = False
            else:
                print(f"   ⚠️  Missing weight or units data")
                
        except Exception as e:
            print(f"   ❌ Error processing product: {e}")
            all_passed = False
    
    # Step 4: Test with a specific concentrate product that should have weight
    print(f"\n🧪 Testing specific concentrate with known weight...")
    
    try:
        # Find a specific concentrate product with weight
        query = """
        SELECT "Product Name*", Description, "Weight*", Units, "Product Type*" 
        FROM products 
        WHERE ("Product Name*" LIKE '%resin%' OR Description LIKE '%resin%')
           AND "Weight*" IS NOT NULL 
           AND Units IS NOT NULL
           AND "Weight*" != ''
           AND Units != ''
        LIMIT 1
        """
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            test_product = cursor.fetchone()
        
        if test_product:
            test_product = dict(test_product)
            print(f"   Product: {test_product.get('Product Name*')}")
            print(f"   Weight: {test_product.get('Weight*')} {test_product.get('Units')}")
            
            processed = process_database_product_for_api(test_product)
            desc_and_weight = processed.get('DescAndWeight', 'MISSING')
            
            print(f"   DescAndWeight: '{desc_and_weight}'")
            
            # Verify weight is in the result
            weight = str(test_product.get('Weight*', '')).replace('.0', '')
            units = test_product.get('Units', '')
            expected_weight = f"{weight}{units}"
            
            if expected_weight in desc_and_weight:
                print(f"   ✅ Weight '{expected_weight}' correctly included!")
            else:
                print(f"   ❌ Weight '{expected_weight}' MISSING from DescAndWeight!")
                all_passed = False
        else:
            print("   ⚠️  No concentrate products with weight found")
            
    except Exception as e:
        print(f"   ❌ Error in specific test: {e}")
        all_passed = False
    
    if all_passed:
        print(f"\n🎉 END-TO-END CONCENTRATE TEST PASSED!")
        print("The concentrate filter should now work correctly on the web version.")
    else:
        print(f"\n❌ END-TO-END CONCENTRATE TEST FAILED!")
        print("There are still issues with concentrate weight processing.")
    
    return all_passed

if __name__ == "__main__":
    success = test_concentrate_end_to_end()
    sys.exit(0 if success else 1)