#!/usr/bin/env python3
"""
Debug the concentrate filter issue step by step
"""

import sys
import os
sys.path.append('.')

# Import the app functions
from app import process_database_product_for_api, _create_desc_and_weight

def test_concentrate_processing():
    """Test the concentrate processing step by step"""
    
    print("🔍 Testing concentrate processing step by step...")
    
    # Sample concentrate record from database
    sample_concentrate = {
        'Product Name*': 'Bridesmaid + CBN Live Resin by Passion Flower - 1g',
        'ProductName': 'Bridesmaid + CBN Live Resin by Passion Flower - 1g',  # Both formats
        'Description': 'Bridesmaid + CBN Live Resin',
        'Weight*': '1.0',
        'Units': 'g',
        'Product Type*': 'Concentrate',
        'Product Brand': 'Passion Flower',
        'Product Strain': '',
        'Price': '12',
        'Lineage': 'Hybrid'
    }
    
    print(f"📋 Input record:")
    print(f"   ProductName: {sample_concentrate.get('ProductName', 'MISSING')}")
    print(f"   Description: {sample_concentrate.get('Description', 'MISSING')}")
    print(f"   Weight*: {sample_concentrate.get('Weight*', 'MISSING')}")
    print(f"   Units: {sample_concentrate.get('Units', 'MISSING')}")
    
    # Test the _create_desc_and_weight function directly
    print(f"\n🧪 Testing _create_desc_and_weight function:")
    
    weight = sample_concentrate.get('Weight*')
    units = sample_concentrate.get('Units')
    description = sample_concentrate.get('Description', '')
    
    try:
        # Combine weight and units for the function call
        combined_weight = f"{weight}{units}" if weight and units else ''
        desc_and_weight = _create_desc_and_weight(description, combined_weight)
        print(f"   ✅ Result: '{desc_and_weight}'")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test the full process_database_product_for_api function
    print(f"\n🧪 Testing process_database_product_for_api function:")
    
    try:
        processed = process_database_product_for_api(sample_concentrate)
        desc_and_weight_result = processed.get('DescAndWeight', 'MISSING')
        print(f"   ✅ DescAndWeight: '{desc_and_weight_result}'")
        
        if 'MISSING' in desc_and_weight_result:
            print(f"   ❌ DescAndWeight field is missing!")
            return False
            
        if '1g' not in desc_and_weight_result:
            print(f"   ⚠️  Weight '1g' not found in DescAndWeight")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎉 Concentrate processing test PASSED!")
    return True

if __name__ == "__main__":
    success = test_concentrate_processing()
    sys.exit(0 if success else 1)