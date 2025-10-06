#!/usr/bin/env python3
"""
Debug script to examine the details returned in JSON matched tags.
Helps identify which specific fields might be missing.
"""

import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'web_deployment/src/core/data')

from json_matcher import EnhancedJSONMatcher
import json
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_json_data():
    """Create realistic cannabis inventory JSON data for testing"""
    return {
        "from_license_name": "Grow Op Farms",
        "inventory": [
            {
                "name": "Blue Dream 1/8oz Pre-Pack",
                "product_type": "flower",
                "strain": "Blue Dream",
                "brand": "House Brand",
                "weight": "3.5g",
                "thc_percentage": "22.5",
                "cbd_percentage": "0.3",
                "price": "35.00",
                "sku": "BD-35-001",
                "description": "Premium Blue Dream flower, indoor grown with excellent terpene profile",
                "batch_number": "BD220924",
                "harvest_date": "2024-09-15",
                "package_date": "2024-09-24",
                "lab_results": {
                    "thc": "22.5%",
                    "cbd": "0.3%",
                    "total_cannabinoids": "24.1%"
                }
            }
        ]
    }

def analyze_tag_details():
    """Analyze what details are present in JSON matched tags"""
    print("=== Analyzing JSON Tag Details ===\n")
    
    # Create test JSON
    json_data = create_test_json_data()
    json_str = json.dumps(json_data)
    
    # Initialize matcher
    matcher = EnhancedJSONMatcher('/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/uploads/product_database_AGT_Bothell.db')
    
    # Get matches
    products = matcher.fetch_and_match_with_product_db(f"data:application/json;base64,{json_str.encode().hex()}")
    
    if not products:
        print("❌ No products returned!")
        return
    
    print(f"✓ Got {len(products)} matched products\n")
    
    # Analyze first product in detail
    product = products[0]
    print("=== DETAILED PRODUCT ANALYSIS ===")
    print(f"Product Name: {product.get('Product Name', 'MISSING')}")
    print(f"Source: {product.get('Source', 'MISSING')}")
    print()
    
    # Check all fields systematically
    essential_fields = [
        'Product Name', 'Description', 'Product Type', 'Vendor', 'Brand', 
        'Strain', 'Weight', 'Price', 'THC Results', 'CBD Results',
        'SKU', 'Batch Number', 'Harvest Date', 'Package Date',
        'Lab Results', 'Total Cannabinoids', 'Terpene Profile'
    ]
    
    print("=== FIELD PRESENCE CHECK ===")
    missing_fields = []
    present_fields = []
    
    for field in essential_fields:
        if field in product and product[field]:
            present_fields.append(field)
            print(f"✓ {field}: {str(product[field])[:50]}{'...' if len(str(product[field])) > 50 else ''}")
        else:
            missing_fields.append(field)
            print(f"❌ {field}: MISSING")
    
    print(f"\n=== SUMMARY ===")
    print(f"Present fields: {len(present_fields)}")
    print(f"Missing fields: {len(missing_fields)}")
    
    if missing_fields:
        print(f"\nMissing: {', '.join(missing_fields)}")
    
    # Show all available fields
    print(f"\n=== ALL AVAILABLE FIELDS ===")
    for key, value in product.items():
        if value:  # Only show non-empty fields
            print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
    
    print(f"\nTotal fields in product: {len(product)}")
    print(f"Non-empty fields: {len([k for k, v in product.items() if v])}")

if __name__ == "__main__":
    analyze_tag_details()