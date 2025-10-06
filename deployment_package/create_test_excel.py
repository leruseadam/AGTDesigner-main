#!/usr/bin/env python3.11
"""
Create a proper test Excel file for upload testing
"""

import os
import sys
from pathlib import Path

def create_test_excel():
    print("📊 Creating proper test Excel file...")
    
    try:
        import pandas as pd
        
        # Create test data
        test_data = {
            'Product Name*': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
            'Product Type*': ['Flower', 'Edible', 'Concentrate'],
            'Price*': [25.00, 15.00, 45.00],
            'Weight*': [3.5, 1.0, 0.5],
            'Weight Unit* (grams/gm or ounces/oz)': ['grams', 'grams', 'grams'],
            'THC test result': [20.5, 10.0, 75.0],
            'CBD test result': [2.1, 5.0, 1.5],
            'Vendor/Supplier*': ['Test Vendor', 'Test Vendor', 'Test Vendor']
        }
        
        # Create DataFrame
        df = pd.DataFrame(test_data)
        
        # Save as Excel file
        test_file_path = Path('/home/adamcordova/AGTDesigner/uploads/test_proper.xlsx')
        df.to_excel(test_file_path, index=False)
        
        print(f"✅ Test Excel file created: {test_file_path}")
        print(f"📏 File size: {test_file_path.stat().st_size} bytes")
        
        return True
        
    except ImportError:
        print("❌ pandas not available, creating simple CSV instead")
        
        # Create simple CSV
        csv_content = """Product Name*,Product Type*,Price*,Weight*,Weight Unit* (grams/gm or ounces/oz),THC test result,CBD test result,Vendor/Supplier*
Test Product 1,Flower,25.00,3.5,grams,20.5,2.1,Test Vendor
Test Product 2,Edible,15.00,1.0,grams,10.0,5.0,Test Vendor
Test Product 3,Concentrate,45.00,0.5,grams,75.0,1.5,Test Vendor"""
        
        csv_file_path = Path('/home/adamcordova/AGTDesigner/uploads/test_proper.csv')
        csv_file_path.write_text(csv_content)
        
        print(f"✅ Test CSV file created: {csv_file_path}")
        print("ℹ️  Note: You'll need to convert this to .xlsx format for testing")
        
        return False
        
    except Exception as e:
        print(f"❌ Error creating test file: {e}")
        return False

def main():
    print("🚀 Test Excel File Creator")
    print("=" * 30)
    
    success = create_test_excel()
    
    if success:
        print("\n🎉 Test Excel file created successfully!")
        print("📋 Next steps:")
        print("1. Try uploading the test_proper.xlsx file")
        print("2. The upload should work without getting stuck")
        print("3. If it works, the issue was with the invalid test file")
    else:
        print("\n⚠️  Could not create proper Excel file")
        print("📋 Alternative:")
        print("1. Upload a real Excel file from your computer")
        print("2. The issue was that the test file wasn't a valid Excel file")

if __name__ == "__main__":
    main()
