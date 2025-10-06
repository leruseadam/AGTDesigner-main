#!/usr/bin/env python3
"""
Test lineage update flow to debug UI lineage changes not reflecting in output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.data.excel_processor import ExcelProcessor
import pandas as pd

def test_lineage_update_flow():
    """Test the complete lineage update flow"""
    print("🧪 Testing lineage update flow")
    print("=" * 50)
    
    # Initialize processor
    processor = ExcelProcessor()
    
    # Load the Excel file
    excel_file = 'uploads/1759379572_A Greener Today - Bothell_inventory_10-01-2025  4_51 PM.xlsx'
    print(f"📁 Loading Excel file: {excel_file}")
    
    success = processor.load_file(excel_file)
    if not success:
        print(f"❌ Failed to load Excel file")
        return
    
    print(f"✅ Loaded {len(processor.df)} products")
    
    # Find a product to test lineage update
    if 'ProductName' not in processor.df.columns:
        print(f"❌ ProductName column not found. Available columns: {list(processor.df.columns)}")
        return
    
    # Get a sample product
    sample_product_name = processor.df['ProductName'].iloc[0]
    original_lineage = processor.df[processor.df['ProductName'] == sample_product_name]['Lineage'].iloc[0]
    
    print(f"🎯 Test product: '{sample_product_name}'")
    print(f"📊 Original lineage: '{original_lineage}'")
    
    # Update lineage
    new_lineage = 'SATIVA' if original_lineage != 'SATIVA' else 'INDICA'
    print(f"🔄 Updating lineage to: '{new_lineage}'")
    
    success = processor.update_lineage_in_current_data(sample_product_name, new_lineage)
    if not success:
        print(f"❌ Failed to update lineage")
        return
    
    print(f"✅ Lineage update returned success")
    
    # Verify lineage was updated in DataFrame
    updated_lineage = processor.df[processor.df['ProductName'] == sample_product_name]['Lineage'].iloc[0]
    print(f"📊 Updated lineage in DataFrame: '{updated_lineage}'")
    
    if updated_lineage == new_lineage:
        print(f"✅ Lineage correctly updated in DataFrame")
    else:
        print(f"❌ Lineage NOT updated in DataFrame. Expected: '{new_lineage}', Got: '{updated_lineage}'")
        return
    
    # Simulate selecting this product for label generation
    processor.selected_tags = [sample_product_name]
    print(f"🏷️ Selected tags: {processor.selected_tags}")
    
    # Get selected records
    records = processor.get_selected_records()
    print(f"📋 Retrieved {len(records)} records")
    
    if not records:
        print(f"❌ No records returned from get_selected_records")
        return
    
    # Check lineage in returned record
    record = records[0]
    record_lineage = record.get('Lineage', 'NOT_FOUND')
    record_product_name = record.get('ProductName', record.get('Product Name*', 'NOT_FOUND'))
    
    print(f"🎯 Record product name: '{record_product_name}'")
    print(f"📊 Record lineage: '{record_lineage}'")
    
    if record_lineage == new_lineage:
        print(f"✅ SUCCESS: Lineage correctly returned in get_selected_records")
        print(f"🎉 Lineage update flow is working correctly!")
    else:
        print(f"❌ FAILURE: Lineage NOT correct in get_selected_records")
        print(f"   Expected: '{new_lineage}'")
        print(f"   Got: '{record_lineage}'")
        
        # Debug: Check if the record is coming from the updated DataFrame
        print(f"\n🔍 Debugging record source:")
        print(f"   Record keys: {list(record.keys())}")
        if 'Source' in record:
            print(f"   Record source: {record['Source']}")
        
        # Check if DataFrame still has correct lineage
        df_lineage_check = processor.df[processor.df['ProductName'] == sample_product_name]['Lineage'].iloc[0]
        print(f"   DataFrame lineage: '{df_lineage_check}'")

if __name__ == "__main__":
    test_lineage_update_flow()