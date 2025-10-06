#!/usr/bin/env python3
"""
JSON Matched Tags Data Consistency Fix

This script identifies and standardizes JSON matched tags data that has become inconsistent
due to missing Source column tracking and various data processing issues.

Issues being fixed:
1. Missing 'Source' column in DataFrame
2. Inconsistent Source values for JSON matched products
3. Duplicate products with different sources
4. Cache inconsistencies between JSON matched tags and Excel data
5. Lineage assignment inconsistencies for JSON matched products

Author: AI Assistant
Date: October 2, 2025
"""

import pandas as pd
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.data.excel_processor import ExcelProcessor
from app import get_excel_processor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_json_matched_tags_consistency():
    """Analyze and fix JSON matched tags data consistency issues."""
    
    print("🔧 JSON Matched Tags Data Consistency Fix")
    print("=" * 60)
    
    # Get the current Excel processor
    excel_processor = get_excel_processor()
    
    if excel_processor is None or excel_processor.df is None:
        print("❌ No Excel processor or DataFrame found")
        return False
    
    df = excel_processor.df
    print(f"📊 Total DataFrame rows: {len(df)}")
    
    # Check current columns
    print(f"📋 Current columns: {list(df.columns)}")
    
    # Issue 1: Missing Source Column
    if 'Source' not in df.columns:
        print("\n🚨 ISSUE 1: Missing 'Source' column")
        print("Adding Source column and inferring values...")
        
        # Add Source column with default value
        df['Source'] = 'Excel Import'
        
        # Try to identify JSON matched products by characteristics
        json_indicators = []
        
        # Characteristic 1: Products with empty or generic strain values
        empty_strain_mask = df['Product Strain'].isin(['', 'Mixed', 'CBD Blend']) | df['Product Strain'].isna()
        json_indicators.append(empty_strain_mask)
        
        # Characteristic 2: Products with lineage inferred from name (INDICA/SATIVA in name but strain is empty)
        if 'ProductName' in df.columns:
            product_name_mask = df['ProductName'].str.contains('Indica|Sativa|Hybrid|CBD', case=False, na=False)
            strain_empty_mask = df['Product Strain'].isin(['', 'Mixed']) | df['Product Strain'].isna()
            name_vs_strain_mismatch = product_name_mask & strain_empty_mask
            json_indicators.append(name_vs_strain_mismatch)
        
        # Characteristic 3: Products with certain patterns that suggest JSON matching
        description_patterns = ['NO NAME', 'Unnamed Product', 'JSON', 'AI Match']
        if 'Description' in df.columns:
            description_mask = df['Description'].str.contains('|'.join(description_patterns), case=False, na=False)
            json_indicators.append(description_mask)
        
        # Combine all indicators
        potential_json_matches = pd.Series([False] * len(df), index=df.index)
        for indicator in json_indicators:
            potential_json_matches |= indicator
        
        # Mark potential JSON matches
        df.loc[potential_json_matches, 'Source'] = 'JSON Match'
        
        json_match_count = (df['Source'] == 'JSON Match').sum()
        excel_import_count = (df['Source'] == 'Excel Import').sum()
        
        print(f"✅ Added Source column:")
        print(f"   - JSON Match: {json_match_count} products")
        print(f"   - Excel Import: {excel_import_count} products")
        
        # Update the processor's DataFrame
        excel_processor.df = df
    
    # Issue 2: Standardize Source Values
    print("\n🚨 ISSUE 2: Standardizing Source values")
    
    # Current source values
    source_counts = df['Source'].value_counts()
    print("Current Source values:")
    print(source_counts)
    
    # Standardize inconsistent source values
    source_mapping = {
        'JSON + Excel Match (Exact)': 'JSON Match',
        'JSON + Excel Match (Strict)': 'JSON Match', 
        'Mixed (JSON + Excel)': 'JSON Match',
        'JSON Only': 'JSON Match',
        'JSON Match - Error': 'JSON Match',
        'JSON Match - Educated Guess': 'JSON Match',
        'Excel Match (Strict)': 'Excel Import',
        'Excel Match (Exact)': 'Excel Import',
        'Product Database Match': 'Excel Import'
    }
    
    # Apply standardization
    for old_value, new_value in source_mapping.items():
        mask = df['Source'] == old_value
        if mask.any():
            count = mask.sum()
            df.loc[mask, 'Source'] = new_value
            print(f"✅ Standardized '{old_value}' → '{new_value}' ({count} products)")
    
    # Issue 3: Fix Lineage Consistency for JSON Matched Products
    print("\n🚨 ISSUE 3: Fixing lineage consistency for JSON matched products")
    
    json_matched_products = df[df['Source'] == 'JSON Match']
    print(f"Found {len(json_matched_products)} JSON matched products")
    
    if len(json_matched_products) > 0:
        # Fix lineage for JSON matched products using the enhanced inference
        fixed_count = 0
        for idx, row in json_matched_products.iterrows():
            product_name = row.get('ProductName', '') or row.get('Product Name*', '')
            product_type = row.get('Product Type*', '')
            
            if product_name:
                # Use the enhanced lineage inference logic
                inferred_lineage = excel_processor._infer_lineage_from_name(product_name, product_type)
                current_lineage = row.get('Lineage', '')
                
                if current_lineage != inferred_lineage:
                    df.loc[idx, 'Lineage'] = inferred_lineage
                    fixed_count += 1
        
        print(f"✅ Fixed lineage for {fixed_count} JSON matched products")
    
    # Issue 4: Remove Duplicates with Different Sources
    print("\n🚨 ISSUE 4: Removing duplicate products with different sources")
    
    # Identify duplicates by product name
    if 'ProductName' in df.columns:
        duplicate_mask = df.duplicated(subset=['ProductName'], keep=False)
        duplicate_products = df[duplicate_mask]
        
        if len(duplicate_products) > 0:
            print(f"Found {len(duplicate_products)} duplicate product entries")
            
            # For each group of duplicates, keep the one with the best source priority
            source_priority = {'Excel Import': 1, 'JSON Match': 2}
            
            # Group by product name and keep the best source
            def keep_best_source(group):
                if len(group) == 1:
                    return group
                
                # Add priority column
                group = group.copy()
                group['source_priority'] = group['Source'].map(source_priority).fillna(999)
                
                # Keep the one with highest priority (lowest number)
                best_idx = group['source_priority'].idxmin()
                return group.loc[[best_idx]]
            
            # Apply deduplication
            df_deduped = df.groupby('ProductName', group_keys=False).apply(keep_best_source)
            
            removed_count = len(df) - len(df_deduped)
            print(f"✅ Removed {removed_count} duplicate products")
            
            # Update the DataFrame
            excel_processor.df = df_deduped
            df = df_deduped
    
    # Issue 5: Update Cache and Session Data
    print("\n🚨 ISSUE 5: Clearing inconsistent caches")
    
    # Clear relevant caches
    try:
        from flask import session
        cache_keys_to_clear = [
            'json_matched_cache_key',
            'full_excel_cache_key',
            'available_tags_cache_key',
            'current_filter_mode'
        ]
        
        for key in cache_keys_to_clear:
            if key in session:
                session.pop(key, None)
                print(f"✅ Cleared session key: {key}")
    except:
        print("⚠️ Could not clear session cache (not in Flask context)")
    
    # Final Summary
    print("\n📊 FINAL SUMMARY:")
    final_source_counts = df['Source'].value_counts()
    print("Standardized Source values:")
    print(final_source_counts)
    
    json_matched_final = df[df['Source'] == 'JSON Match']
    if len(json_matched_final) > 0:
        lineage_distribution = json_matched_final['Lineage'].value_counts()
        print(f"\nJSON Matched products lineage distribution:")
        print(lineage_distribution)
    
    print(f"\n✅ Data consistency fix complete!")
    print(f"📋 Total products: {len(df)}")
    print(f"🔗 JSON Matched: {(df['Source'] == 'JSON Match').sum()}")
    print(f"📄 Excel Import: {(df['Source'] == 'Excel Import').sum()}")
    
    return True

def main():
    """Main execution function."""
    try:
        success = analyze_json_matched_tags_consistency()
        
        if success:
            print("\n🎉 JSON matched tags data consistency has been restored!")
            print("🎯 Recommendations:")
            print("1. Clear browser cache to see updated UI")
            print("2. Re-upload Excel file if issues persist")
            print("3. Check JSON matching logic for future consistency")
        else:
            print("\n❌ Failed to fix JSON matched tags consistency")
            return 1
            
    except Exception as e:
        print(f"\n💥 Error during consistency fix: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())