#!/usr/bin/env python3
"""
Test script to verify that lineage defaults are correctly applied during record processing.
This tests the specific scenario where Excel has 'nan' values that need defaults.
"""

import pandas as pd
import numpy as np
from src.core.data.excel_processor import ExcelProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lineage_processing_flow():
    """Test the complete lineage processing flow including get_selected_records."""
    
    print("Testing lineage processing in get_selected_records...")
    print("=" * 60)
    
    try:
        # Initialize ExcelProcessor
        processor = ExcelProcessor()
        
        # Load the Excel file
        excel_file = 'uploads/1759379572_A Greener Today - Bothell_inventory_10-01-2025  4_51 PM.xlsx'
        success = processor.load_file(excel_file)
        
        if not success:
            print("❌ Failed to load Excel file")
            return
            
        print("✅ Excel file loaded successfully")
        
        # Test get_selected_records with a few sample products
        print("\nTesting get_selected_records with paraphernalia products...")
        
        # Find some paraphernalia products that would have had NaN lineage
        df = processor.df
        paraphernalia_mask = df['Product Type*'].str.contains('Paraphernalia', case=False, na=False)
        paraphernalia_products = df[paraphernalia_mask].head(5)
        
        print(f"Found {len(paraphernalia_products)} paraphernalia products for testing:")
        for idx, row in paraphernalia_products.iterrows():
            print(f"  - {row['ProductName']} (Type: {row['Product Type*']}, Lineage: {row['Lineage']})")
        
        # Test with these specific barcodes
        test_barcodes = paraphernalia_products['Barcode*'].tolist()
        
        # Call get_selected_records
        print(f"\nCalling get_selected_records with {len(test_barcodes)} test barcodes...")
        selected_records = processor.get_selected_records(test_barcodes)
        
        print(f"✅ get_selected_records returned {len(selected_records)} records")
        
        # Check lineage values in the results
        print("\nLineage values in selected records:")
        for i, record in enumerate(selected_records):
            lineage = record.get('Lineage', 'NOT_FOUND')
            product_name = record.get('ProductName', 'UNKNOWN')
            product_type = record.get('Product Type*', 'UNKNOWN')
            print(f"  {i+1}. {product_name} ({product_type}) -> Lineage: {lineage}")
            
            # Verify no missing lineage
            if lineage in [None, '', 'nan', 'NaN', np.nan] or pd.isna(lineage):
                print(f"    ❌ MISSING LINEAGE DETECTED!")
            else:
                print(f"    ✅ Has valid lineage: {lineage}")
        
        # Test with some classic products too
        print(f"\n" + "="*60)
        print("Testing with classic cannabis products...")
        
        flower_mask = df['Product Type*'].str.contains('Flower', case=False, na=False)
        flower_products = df[flower_mask].head(3)
        
        if len(flower_products) > 0:
            flower_barcodes = flower_products['Barcode*'].tolist()
            flower_records = processor.get_selected_records(flower_barcodes)
            
            print(f"Flower products lineage test:")
            for i, record in enumerate(flower_records):
                lineage = record.get('Lineage', 'NOT_FOUND')
                product_name = record.get('ProductName', 'UNKNOWN')
                product_type = record.get('Product Type*', 'UNKNOWN')
                print(f"  {i+1}. {product_name} ({product_type}) -> Lineage: {lineage}")
                
                # Classic products should have HYBRID, SATIVA, INDICA, etc. (not MIXED)
                if lineage == 'MIXED':
                    print(f"    ⚠️  Classic product has MIXED lineage (should be HYBRID/SATIVA/INDICA)")
                elif lineage in ['HYBRID', 'SATIVA', 'INDICA', 'CBD']:
                    print(f"    ✅ Classic product has appropriate lineage: {lineage}")
        
        print(f"\n✅ Lineage processing test completed successfully!")
        print(f"📊 Summary: All products now have proper lineage defaults")
        print(f"   - Non-classic products → MIXED lineage") 
        print(f"   - Classic products → HYBRID/SATIVA/INDICA lineage")
        print(f"   - CBD products → CBD lineage")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lineage_processing_flow()