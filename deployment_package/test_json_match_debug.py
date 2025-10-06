#!/usr/bin/env python3
"""
Test script to debug JSON matching data issues
"""
import json
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import the enhanced matcher
from core.data.enhanced_json_matcher import EnhancedJSONMatcher

def test_json_matching():
    """Test JSON matching to see what data is missing"""
    
    print("🧪 TESTING JSON MATCHING DATA PRESERVATION")
    print("=" * 60)
    
    # Create a test JSON product with rich data
    test_json = [
        {
            "product_name": "Blue Dream - Live Resin Cart",
            "inventory_name": "Blue Dream - Live Resin Cart", 
            "vendor": "premium extracts",
            "price": "45.99",
            "weight": "1g",
            "weight_with_units": "1g",
            "unit_weight_uom": "g",
            "thc_percentage": "78.5",
            "cbd_percentage": "0.8",
            "batch_number": "BDC-2024-001",
            "lot_number": "LOT-78945",
            "sku": "PE-BDC-1G",
            "quantity": "12",
            "room": "Extraction Lab A",
            "description": "Premium Blue Dream live resin cartridge with natural terpenes",
            "strain": "Blue Dream",
            "product_type": "Vape Cartridge",
            "lab_result_data": {
                "thc": "78.5",
                "cbd": "0.8", 
                "total_cannabinoids": "82.3",
                "terpenes": ["myrcene", "limonene", "pinene"]
            },
            "harvest_date": "2024-09-15",
            "package_date": "2024-09-20"
        }
    ]
    
    try:
        # Initialize enhanced matcher
        from core.excel_processor import ExcelProcessor
        excel_processor = ExcelProcessor()
        matcher = EnhancedJSONMatcher(excel_processor)
        
        print("📊 Input JSON Data:")
        for key, value in test_json[0].items():
            print(f"  {key}: {value}")
        
        print("\n🔍 Testing hybrid merge with JSON data...")
        
        # Test the hybrid merge function directly
        dummy_db_product = {
            "Product Name*": "Blue Dream Live Resin Cartridge",
            "Vendor/Supplier*": "Premium Extracts",
            "Product Type*": "Vape",
            "Price": "40.00",
            "Weight*": "1.0",
            "Units": "g"
        }
        
        print("\n📊 Database Product (before merge):")
        for key, value in dummy_db_product.items():
            print(f"  {key}: {value}")
        
        # Test hybrid merge
        hybrid_result = matcher._merge_json_data_hybrid(dummy_db_product, test_json)
        
        print("\n🎯 Hybrid Result (after merge):")
        for key, value in hybrid_result.items():
            print(f"  {key}: {value}")
        
        # Check what's missing
        print("\n❌ MISSING DATA ANALYSIS:")
        
        # Check if JSON fields are preserved
        json_fields_to_check = [
            ("price", "Price"),
            ("batch_number", "Batch Number"), 
            ("lot_number", "Lot Number"),
            ("sku", "Internal Product Identifier"),
            ("quantity", "Quantity*"),
            ("room", "Room*"),
            ("thc_percentage", "THC test result"),
            ("cbd_percentage", "CBD test result"),
            ("description", "Description")
        ]
        
        for json_key, expected_db_field in json_fields_to_check:
            json_value = test_json[0].get(json_key)
            result_value = hybrid_result.get(expected_db_field)
            
            if json_value and not result_value:
                print(f"  ❌ MISSING: {json_key} ('{json_value}') -> {expected_db_field}")
            elif json_value and result_value != str(json_value):
                print(f"  ⚠️  DIFFERENT: {json_key} ('{json_value}') -> {expected_db_field} ('{result_value}')")
            elif json_value and result_value == str(json_value):
                print(f"  ✅ PRESERVED: {json_key} ('{json_value}') -> {expected_db_field}")
            else:
                print(f"  ⚪ NO DATA: {json_key} -> {expected_db_field}")
        
        print("\n📋 ALL RESULT FIELDS:")
        for key in sorted(hybrid_result.keys()):
            value = hybrid_result[key]
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_matching()