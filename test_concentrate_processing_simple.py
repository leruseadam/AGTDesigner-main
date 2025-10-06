#!/usr/bin/env python3
"""
Simpler test to check actual concentrate processing
"""

import sys
import os
sys.path.append('.')

# Import the app functions
from app import process_database_product_for_api

def test_concentrate_processing_simple():
    """Test concentrate processing directly"""
    
    print("🔍 Testing concentrate processing directly...")
    
    # Get a real concentrate record from database
    import sqlite3
    
    try:
        conn = sqlite3.connect('uploads/product_database_AGT_Bothell.db')
        cursor = conn.cursor()
        
        # Get one concentrate record
        cursor.execute("""
            SELECT "Product Name*", Description, "Weight*", Units, "Product Type*", "Product Brand"
            FROM products 
            WHERE "Product Type*" = 'Concentrate' 
            AND "Weight*" IS NOT NULL 
            AND Units IS NOT NULL 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print("❌ No concentrate products found")
            return False
            
        # Create a record dict like what the system uses
        product_name, description, weight, units, product_type, brand = row
        
        record = {
            'Product Name*': product_name,
            'ProductName': product_name,  # Some systems use this
            'Description': description,
            'Weight*': weight,
            'Units': units,
            'Product Type*': product_type,
            'Product Brand': brand or '',
            'Price': '12.00',
            'Lineage': 'Hybrid'
        }
        
        print(f"📋 Real concentrate record:")
        print(f"   Product Name: {product_name}")
        print(f"   Description: {description}")
        print(f"   Weight*: {weight}")
        print(f"   Units: {units}")
        
        # Test processing
        print(f"\n🧪 Testing process_database_product_for_api:")
        
        processed = process_database_product_for_api(record)
        
        print(f"✅ Processed fields:")
        print(f"   CombinedWeight: '{processed.get('CombinedWeight', 'MISSING')}'")
        print(f"   DescAndWeight: '{processed.get('DescAndWeight', 'MISSING')}'")
        
        # Check if DescAndWeight has weight
        desc_and_weight = processed.get('DescAndWeight', '')
        if weight and units and f"{weight}{units}" in desc_and_weight:
            print(f"   ✅ Weight found in DescAndWeight!")
            return True
        elif weight and units and "1g" in desc_and_weight:
            print(f"   ✅ Formatted weight found in DescAndWeight!")
            return True
        else:
            print(f"   ❌ Weight NOT found in DescAndWeight")
            print(f"       Expected to contain: {weight}{units}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_concentrate_processing_simple()
    sys.exit(0 if success else 1)