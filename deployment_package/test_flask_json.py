#!/usr/bin/env python3
"""
Test the Flask app JSON matching endpoint directly
"""
import os
import sys
import json
import base64
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_flask_json_endpoint():
    """Test the Flask app JSON matching endpoint"""
    try:
        # Import Flask app
        from app import app
        
        # Create test JSON data with a vendor that exists in the database
        test_data = {
            "from_license_name": "Grow Op Farms",  # This vendor exists in database
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
                }
            ]
        }
        
        # Convert to data URL
        test_json = json.dumps(test_data, indent=2)
        json_bytes = test_json.encode('utf-8')
        b64_encoded = base64.b64encode(json_bytes).decode('utf-8')
        data_url = f"data:application/json;base64,{b64_encoded}"
        
        print("=== Testing Flask JSON Matching Endpoint ===\\n")
        print(f"Test data has {len(test_data['inventory_transfer_items'])} products:")
        for item in test_data['inventory_transfer_items']:
            print(f"  - {item['product_name']} (vendor: {item['vendor']})")
        
        # Create test client
        with app.test_client() as client:
            # Test the JSON match endpoint
            response = client.post('/api/json-match', 
                                 json={'url': data_url},
                                 content_type='application/json')
            
            print(f"\\nFlask Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ Success: {data.get('success', False)}")
                print(f"✓ Matched Count: {data.get('matched_count', 0)}")
                print(f"✓ Message: {data.get('message', 'No message')}")
                
                matched_names = data.get('matched_names', [])
                print(f"\\nMatched products ({len(matched_names)}):")
                for i, name in enumerate(matched_names):
                    print(f"  {i+1}. {name}")
                    
                # Check if we have available_tags
                available_tags = data.get('available_tags', [])
                if available_tags:
                    print(f"\\nFirst matched product details:")
                    first_product = available_tags[0]
                    for key, value in first_product.items():
                        print(f"  {key}: {value}")
                
            else:
                print(f"✗ Error {response.status_code}: {response.get_json()}")
        
        print("\\n=== Test with Non-existent Vendor ===")
        
        # Test with original problematic vendor
        test_data2 = dict(test_data)
        test_data2["from_license_name"] = "LIFTED CANNABIS"  # Another real vendor
        for item in test_data2["inventory_transfer_items"]:
            item["vendor"] = "LIFTED CANNABIS"
        
        test_json2 = json.dumps(test_data2, indent=2)
        json_bytes2 = test_json2.encode('utf-8')
        b64_encoded2 = base64.b64encode(json_bytes2).decode('utf-8')
        data_url2 = f"data:application/json;base64,{b64_encoded2}"
        
        with app.test_client() as client:
            response2 = client.post('/api/json-match', 
                                  json={'url': data_url2},
                                  content_type='application/json')
            
            print(f"Response Status: {response2.status_code}")
            
            if response2.status_code == 200:
                data2 = response2.get_json()
                print(f"✓ Success: {data2.get('success', False)}")
                print(f"✓ Matched Count: {data2.get('matched_count', 0)}")
                print(f"✓ Message: {data2.get('message', 'No message')}")
                
                if data2.get('matched_count', 0) > 0:
                    print("\\n🎉 JSON matching works even with non-existent vendor!")
                    print("   This is expected behavior - it falls back to matching against all products.")
                else:
                    print("\\n⚠️  No matches found with non-existent vendor")
                    
            else:
                print(f"✗ Error {response2.status_code}: {response2.get_json()}")
                
    except Exception as e:
        print(f"Error testing Flask app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flask_json_endpoint()