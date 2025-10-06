#!/usr/bin/env python3.11
"""
Test script to verify the concentrate weight fix is working on web deployment
"""

import sys
import os

# Add project directory to path (for PythonAnywhere)
project_dir = '/home/adamcordova/AGTDesigner'
if os.path.exists(project_dir):
    sys.path.insert(0, project_dir)

try:
    from app import process_database_product_for_api
    
    print("🧪 Testing Concentrate Weight Fix")
    print("=" * 50)
    
    # Test case 1: Concentrate with weight
    test_concentrate = {
        'Product Name*': 'Cascade Cream Classic Hashish by Sitka - 1g',
        'Product Type': 'Solventless Concentrate',
        'Description': 'Cascade Cream Classic Hashish',
        'Weight*': '1.0',
        'Units': 'g'
    }
    
    print("Test 1: Concentrate with weight data")
    print(f"Input: {test_concentrate['Product Name*']}")
    print(f"Weight*: {test_concentrate['Weight*']}, Units: {test_concentrate['Units']}")
    
    result = process_database_product_for_api(test_concentrate)
    
    print("\nOutput:")
    print(f"CombinedWeight: {result.get('CombinedWeight', 'MISSING')}")
    print(f"DescAndWeight: {result.get('DescAndWeight', 'MISSING')}")
    
    # Check if fix is working
    if 'DescAndWeight' in result and result['DescAndWeight'] and result['DescAndWeight'] != 'N/A':
        print("✅ SUCCESS: DescAndWeight field created correctly!")
        if "1g" in result['DescAndWeight']:
            print("✅ SUCCESS: Weight appears in DescAndWeight field!")
        else:
            print("⚠️  WARNING: Weight might not be formatted correctly")
    else:
        print("❌ FAILURE: DescAndWeight field missing or empty!")
        print("   This means the fix is NOT working on this deployment")
    
    print("\n" + "=" * 50)
    
    # Test case 2: Another concentrate
    test_concentrate_2 = {
        'Product Name*': 'Live Rosin Concentrate',
        'Description': 'Premium Live Rosin',
        'Weight*': '0.5',
        'Units': 'g'
    }
    
    print("Test 2: Another concentrate")
    result_2 = process_database_product_for_api(test_concentrate_2)
    print(f"DescAndWeight: {result_2.get('DescAndWeight', 'MISSING')}")
    
    if 'DescAndWeight' in result_2 and "0.5g" in result_2['DescAndWeight']:
        print("✅ SUCCESS: Second test also working!")
    else:
        print("❌ FAILURE: Second test failed")
    
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    
    if ('DescAndWeight' in result and result['DescAndWeight'] and 
        'DescAndWeight' in result_2 and result_2['DescAndWeight']):
        print("✅ CONCENTRATE WEIGHT FIX IS WORKING!")
        print("   The web deployment has been successfully updated.")
    else:
        print("❌ CONCENTRATE WEIGHT FIX IS NOT WORKING!")
        print("   The web deployment needs to be updated.")
        print("   Steps to fix:")
        print("   1. Pull latest code: git pull origin main")
        print("   2. Reload web app in PythonAnywhere dashboard")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the correct directory")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()