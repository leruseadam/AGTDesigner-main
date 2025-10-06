#!/usr/bin/env python3.11
"""
Test the concentrated weight fix specifically for filtered label generation
"""

import sys
import os

# Add project directory to path (for PythonAnywhere)
project_dir = '/home/adamcordova/AGTDesigner'
if os.path.exists(project_dir):
    sys.path.insert(0, project_dir)

try:
    from app import process_database_product_for_api, _create_desc_and_weight
    
    print("🔧 Testing Concentrate Weight Fix for Filtered Labels")
    print("=" * 60)
    
    # Test the core function that was fixed
    test_db_record = {
        'Product Name*': 'Grape Slurpee Wax',
        'Product Type*': 'Solventless Concentrate',
        'Weight*': '1.0',
        'Units': 'g',
        'Description': 'Premium concentrate wax'
    }
    
    print("Testing process_database_product_for_api function:")
    print(f"Input record: {test_db_record['Product Name*']}")
    print(f"Weight*: {test_db_record['Weight*']}, Units: {test_db_record['Units']}")
    
    # This is the function that was being bypassed in generate_labels
    processed = process_database_product_for_api(test_db_record)
    
    print("\n✅ OUTPUT from process_database_product_for_api:")
    print(f"   CombinedWeight: {processed.get('CombinedWeight', 'MISSING')}")
    print(f"   DescAndWeight: {processed.get('DescAndWeight', 'MISSING')}")
    
    # Test what the manual creation was doing before
    manual_combined = f"{test_db_record.get('Weight*', '1')}{test_db_record.get('Units', 'g')}"
    manual_desc_and_weight = _create_desc_and_weight(test_db_record.get('Product Name*', ''), manual_combined)
    
    print("\n📋 What manual creation was doing before:")
    print(f"   Manual CombinedWeight: {manual_combined}")
    print(f"   Manual DescAndWeight: {manual_desc_and_weight}")
    
    # Check if they match
    if (processed.get('CombinedWeight') == manual_combined and 
        processed.get('DescAndWeight') == manual_desc_and_weight):
        print("\n✅ SUCCESS: Both methods produce identical results!")
        print("   The fix ensures consistency by using the same function.")
    else:
        print("\n⚠️  WARNING: Methods produce different results")
        print("   This indicates the fix will change behavior")
    
    print("\n" + "=" * 60)
    print("🎯 THE FIX:")
    print("   Before: generate_labels manually created DescAndWeight field")
    print("   After: generate_labels uses process_database_product_for_api")
    print("   Result: Consistent DescAndWeight creation for concentrate filters")
    print("\n🔄 NEXT STEPS:")
    print("   1. Update web deployment with latest code")
    print("   2. Test concentrate filter in web interface")
    print("   3. Verify weights appear in generated labels")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the correct directory")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()