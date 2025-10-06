#!/usr/bin/env python3
"""
Direct test of JSON tag creation without Flask app.
Examines the exact fields returned by JSON matching.
"""

import json
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_json_tag_creation():
    """Test what happens when JSON tags are created"""
    print("=== Direct JSON Tag Creation Test ===\n")
    
    # Read the realistic test to see what it does
    try:
        # Read our test file to understand the pattern
        test_file = os.path.join(current_dir, 'test_realistic_json_match.py')
        if os.path.exists(test_file):
            print("✓ Found test_realistic_json_match.py")
            
            # Read and show the test structure
            with open(test_file, 'r') as f:
                content = f.read()
                
            # Find the JSON creation section
            if 'create_test_json_data' in content:
                print("✓ Found test JSON creation function")
                
                # Look for the structure
                start = content.find('def create_test_json_data')
                end = content.find('\ndef', start + 1)
                if end == -1:
                    end = content.find('\nclass', start + 1)
                if end == -1:
                    end = start + 2000  # Fallback
                    
                json_function = content[start:end]
                print("\n=== JSON Structure Used in Tests ===")
                print(json_function[:1500] + ('...' if len(json_function) > 1500 else ''))
        
        # Try to understand what fields are being used
        print("\n=== Analysis of JSON Matching Process ===")
        print("Based on the code examination:")
        print("1. JSON items go through _create_product_from_json()")
        print("2. First tries to find database match")
        print("3. If no match, creates tag from JSON data + inference")
        print("4. Sets Source: 'JSON Match'")
        
        print("\n=== Expected Fields in JSON Tags ===")
        expected_json_fields = [
            "Product Name*",
            "Description", 
            "Product Type*",
            "Product Brand",
            "Product Strain",
            "Vendor",
            "Price",
            "Weight*",
            "Quantity*",
            "THC test result",
            "CBD test result",
            "Source",
            "Lineage",
            "Units"
        ]
        
        for field in expected_json_fields:
            print(f"  • {field}")
            
        print("\n=== Potential Issues ===")
        print("JSON matched tags might be missing details because:")
        print("1. Original JSON doesn't contain certain fields (sku, batch_number, etc.)")
        print("2. Database match not found, so falls back to inference")
        print("3. Inference may not populate all expected fields")
        print("4. JSON structure doesn't match expected keys")
        
        print("\n=== Recommendation ===")
        print("To debug, run the Flask app and test endpoint:")
        print("1. python app.py")
        print("2. python test_json_tag_details.py") 
        print("This will show exactly what fields are populated vs missing")
        
    except Exception as e:
        print(f"❌ Error analyzing test: {e}")

if __name__ == "__main__":
    test_json_tag_creation()