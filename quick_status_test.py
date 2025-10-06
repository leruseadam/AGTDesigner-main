#!/usr/bin/env python3
"""
Quick status test to demonstrate vendor restriction is working
"""

import json
from src.core.data.enhanced_json_matcher import EnhancedJSONMatcher
from src.core.data.product_database import ProductDatabase

def test_status():
    # Load cultivera data
    with open('test_49_products.json', 'r') as f:
        json_data = json.load(f)
    
    # Extract document vendor
    document_vendor = json_data.get('from_license_name', '')
    print(f"📋 Document vendor: {document_vendor}")
    
    # Test both scenarios
    from src.core.data.excel_processor import ExcelProcessor
    excel_processor = ExcelProcessor()
    matcher = EnhancedJSONMatcher(excel_processor)
    
    # 1. Without vendor restriction (pass empty vendor)
    for product in json_data.get('inventory_transfer_items', []):
        product['vendor'] = ''  # Clear individual vendor
    
    results_no_restriction = matcher.match_products(json_data)
    print(f"🔄 Matches WITHOUT vendor restriction: {len(results_no_restriction)}")
    
    # 2. With vendor restriction (assign document vendor)
    for product in json_data.get('inventory_transfer_items', []):
        product['vendor'] = document_vendor
    
    results_with_restriction = matcher.match_products(json_data)
    print(f"🎯 Matches WITH vendor restriction: {len(results_with_restriction)}")
    
    # Show vendor distribution in results
    if results_with_restriction:
        vendors = set()
        for result in results_with_restriction:
            if 'database_match' in result and result['database_match']:
                db_vendor = result['database_match'].get('vendor', 'Unknown')
                vendors.add(db_vendor)
        
        print(f"✅ All {len(results_with_restriction)} matches restricted to vendors: {list(vendors)}")
        
        # Check if all matches are from CERES
        ceres_matches = [r for r in results_with_restriction if 'database_match' in r and r['database_match'] and 'CERES' in str(r['database_match'].get('vendor', ''))]
        print(f"🏢 CERES-specific matches: {len(ceres_matches)}")

if __name__ == "__main__":
    test_status()