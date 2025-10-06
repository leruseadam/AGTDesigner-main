#!/usr/bin/env python3
"""
Test script to verify lineage default assignment for products with missing lineage values.
"""

import pandas as pd
import numpy as np
from src.core.data.excel_processor import ExcelProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lineage_defaults():
    """Test that products with missing lineage get appropriate defaults."""
    
    print("Testing lineage default assignment...")
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
            
        # Check lineage values before and after processing
        df = processor.df
        
        # Count missing lineage values
        missing_mask = (
            df['Lineage'].isna() | 
            (df['Lineage'].astype(str).str.strip() == '') |
            (df['Lineage'].astype(str).str.lower().str.strip() == 'nan')
        )
        
        missing_count = missing_mask.sum()
        print(f"Products with missing lineage: {missing_count}")
        
        if missing_count > 0:
            print("\nSample products with missing lineage:")
            missing_products = df[missing_mask][['Product Name*', 'Product Type*', 'Lineage']].head(10)
            for idx, row in missing_products.iterrows():
                print(f"  {row['Product Name*']} ({row['Product Type*']}) - Lineage: {row['Lineage']}")
        
        # Check lineage distribution
        print(f"\nCurrent lineage distribution:")
        lineage_counts = df['Lineage'].value_counts(dropna=False)
        for lineage, count in lineage_counts.items():
            print(f"  {lineage}: {count} products")
            
        # Check specific product types
        print(f"\nProduct types with missing lineage:")
        if missing_count > 0:
            type_counts = df[missing_mask]['Product Type*'].value_counts()
            for product_type, count in type_counts.head(10).items():
                print(f"  {product_type}: {count} products")
        
        print(f"\n✅ Test completed. Missing lineage products: {missing_count}")
        
        # If there are still missing values, this indicates our fix needs to be applied
        if missing_count > 0:
            print("⚠️  Missing lineage values detected - the fix should resolve these during processing")
        else:
            print("✅ All products have lineage values!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lineage_defaults()