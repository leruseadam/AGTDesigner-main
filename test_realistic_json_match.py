#!/usr/bin/env python3
"""
Test script with realistic cannabis inventory JSON data
"""
import os
import sys
import logging
import json

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_json_data():
    """Create realistic cannabis inventory JSON data for testing"""
    test_data = {
        "from_license_name": "Grow Op Farms",
        "inventory_transfer_items": [
            {
                "product_name": "Blue Dream 1/8oz Pre-Pack",
                "inventory_name": "Blue Dream 1/8oz Pre-Pack",
                "vendor": "Grow Op Farms",
                "category": "flower",
                "strain": "Blue Dream",
                "weight": "3.5g",
                "thc_percentage": "22.5",
                "cbd_percentage": "0.8",
                "price": "45.00"
            },
            {
                "product_name": "OG Kush Cartridge 1g",
                "inventory_name": "OG Kush Cartridge 1g", 
                "vendor": "Grow Op Farms",
                "category": "vape_cartridge",
                "strain": "OG Kush",
                "weight": "1g",
                "thc_percentage": "85.2",
                "cbd_percentage": "1.2",
                "price": "65.00"
            },
            {
                "product_name": "Sour Diesel Pre-Roll Twin Pack",
                "inventory_name": "Sour Diesel Pre-Roll Twin Pack",
                "vendor": "Grow Op Farms", 
                "category": "pre_roll",
                "strain": "Sour Diesel",
                "weight": "2g",
                "thc_percentage": "19.8",
                "cbd_percentage": "0.5",
                "price": "28.00"
            },
            {
                "product_name": "GSC Edible Gummies 10mg x 10",
                "inventory_name": "GSC Edible Gummies 10mg x 10",
                "vendor": "Grow Op Farms",
                "category": "edible",
                "strain": "Girl Scout Cookies",
                "weight": "100mg",
                "thc_percentage": "10",
                "cbd_percentage": "0",
                "price": "35.00"
            },
            {
                "product_name": "Purple Haze Shatter 1g",
                "inventory_name": "Purple Haze Shatter 1g",
                "vendor": "Grow Op Farms",
                "category": "concentrate",
                "strain": "Purple Haze",
                "weight": "1g", 
                "thc_percentage": "78.9",
                "cbd_percentage": "2.1",
                "price": "55.00"
            }
        ]
    }
    return test_data

def test_json_matching_with_realistic_data():
    """Test JSON matching with realistic cannabis data"""
    print("=== Testing JSON Matching with Realistic Cannabis Data ===\n")
    
    try:
        # Create test data
        test_data = create_test_json_data()
        test_json = json.dumps(test_data, indent=2)
        
        print(f"Created test JSON with {len(test_data['inventory_transfer_items'])} products:")
        for item in test_data['inventory_transfer_items']:
            print(f"  - {item['product_name']} ({item['category']})")
        
        # Create enhanced JSON matcher
        from src.core.data.enhanced_json_matcher import EnhancedJSONMatcher
        from src.core.data.excel_processor import ExcelProcessor
        
        # Create empty Excel processor
        excel_processor = ExcelProcessor()
        json_matcher = EnhancedJSONMatcher(excel_processor)
        
        # Load database products
        db_products = json_matcher._get_database_products()
        if db_products:
            print(f"\\n✓ Loaded {len(db_products)} database products")
            
            # Populate excel processor and build ML models
            import pandas as pd
            json_matcher.excel_processor.df = pd.DataFrame(db_products)
            json_matcher._build_ml_models()
            print("✓ ML models built successfully")
            
            # Test direct matching with the JSON items
            json_items = test_data['inventory_transfer_items']
            print(f"\\nTesting matching with {len(json_items)} JSON items...")
            
            # Use the match_products method directly
            from src.core.data.enhanced_json_matcher import MatchStrategy
            match_results = json_matcher.match_products(json_items, strategy=MatchStrategy.HYBRID)
            
            print(f"\\n=== MATCHING RESULTS ===")
            print(f"Found {len(match_results)} matches:")
            
            for i, result in enumerate(match_results):
                product_name = result.match_data.get('Product Name*', 'Unknown')
                json_name = json_items[i]['product_name'] if i < len(json_items) else 'Unknown'
                print(f"  {i+1}. JSON: '{json_name}' -> DB: '{product_name}' (Score: {result.score:.3f}, Strategy: {result.strategy_used.value})")
                
                # Show match factors
                if result.match_factors:
                    factors_str = ", ".join([f"{k}={v:.2f}" for k, v in result.match_factors.items()])
                    print(f"     Factors: {factors_str}")
            
            # Test using the same method as the Flask app
            print(f"\\n=== TESTING FLASK APP METHOD ===")
            
            # Create a data URL with our test JSON
            import base64
            json_bytes = test_json.encode('utf-8')
            b64_encoded = base64.b64encode(json_bytes).decode('utf-8')
            data_url = f"data:application/json;base64,{b64_encoded}"
            
            # Use fetch_and_match (the same method called by Flask app)
            flask_results = json_matcher.fetch_and_match(data_url)
            
            print(f"Flask method returned {len(flask_results)} products:")
            for i, product in enumerate(flask_results):
                product_name = product.get('Product Name*', product.get('ProductName', 'Unknown'))
                print(f"  {i+1}. {product_name}")
            
        else:
            print("✗ No database products found")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_matching_with_realistic_data()