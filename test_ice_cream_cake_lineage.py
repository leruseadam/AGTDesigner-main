#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/src')

from core.data.excel_processor import ExcelProcessor

def test_ice_cream_cake_lineage():
    processor = ExcelProcessor()
    
    # Initialize and load data
    print("🔄 Loading Excel data...")
    # Use the Excel file loading method
    excel_file = None
    import glob
    possible_files = glob.glob("uploads/*.xlsx")
    if possible_files:
        excel_file = possible_files[0]
        print(f"📁 Using Excel file: {excel_file}")
        result = processor.load_file(excel_file)
        print(f"📊 Load result: {result}")
    else:
        print("❌ No Excel file found in uploads/")
        return
    
    if not hasattr(processor, 'current_data') or processor.current_data is None:
        print("❌ Failed to load data")
        return
    
    product_name = "Ice Cream Cake Wax by Huster's Ambition - 1g"
    
    # Find the product
    matches = processor.current_data[processor.current_data['ProductName'].str.contains('Ice Cream Cake Wax.*Ambition', case=False, na=False)]
    
    if len(matches) == 0:
        # Try alternative search
        matches = processor.current_data[processor.current_data['ProductName'].str.contains('Ice Cream Cake Wax', case=False, na=False)]
        print(f"🔍 Found {len(matches)} Ice Cream Cake Wax products:")
        for idx, row in matches.iterrows():
            print(f"  - {row['ProductName']}: Lineage='{row['Lineage']}'")
        
        if len(matches) == 0:
            print("❌ No Ice Cream Cake Wax products found")
            return
        
        # Use the first match
        product_name = matches.iloc[0]['ProductName']
    else:
        product_name = matches.iloc[0]['ProductName']
    
    print(f"🎯 Testing lineage update for: '{product_name}'")
    
    # Check current lineage
    current_record = processor.current_data[processor.current_data['ProductName'] == product_name]
    if len(current_record) > 0:
        current_lineage = current_record.iloc[0]['Lineage']
        print(f"📊 Current lineage: '{current_lineage}'")
    else:
        print("❌ Product not found in current data")
        return
    
    # Update lineage to INDICA
    print(f"🔄 Updating lineage to: 'INDICA'")
    result = processor.update_lineage_in_current_data(product_name, 'INDICA')
    print(f"✅ Update result: {result}")
    
    # Check updated lineage in DataFrame
    updated_record = processor.current_data[processor.current_data['ProductName'] == product_name]
    if len(updated_record) > 0:
        updated_lineage = updated_record.iloc[0]['Lineage']
        print(f"📊 Updated lineage in DataFrame: '{updated_lineage}'")
    
    # Test get_selected_records to see if it returns the updated lineage
    print(f"🏷️ Testing get_selected_records...")
    selected_tags = [product_name]
    records = processor.get_selected_records(selected_tags)
    
    if records and len(records) > 0:
        record_lineage = records[0].get('Lineage', 'NOT_FOUND')
        print(f"📋 Retrieved record lineage: '{record_lineage}'")
        
        if record_lineage == 'INDICA':
            print("✅ SUCCESS: Lineage update is working correctly!")
        else:
            print(f"❌ PROBLEM: Expected 'INDICA', got '{record_lineage}'")
            
            # Check if there's a database override
            if 'db_lineage' in records[0]:
                print(f"🗄️ Database lineage: '{records[0]['db_lineage']}'")
    else:
        print("❌ No records returned from get_selected_records")

if __name__ == '__main__':
    test_ice_cream_cake_lineage()