#!/usr/bin/env python3
"""
Test to verify what the actual issue is with JSON matched tags missing details
"""

import requests
import json
import base64

def create_simple_test():
    """Create a very simple test"""
    # Test with the GET endpoint first to see if basic Flask is working
    print("=== Testing GET endpoint ===")
    try:
        response = requests.get("http://localhost:8000/api/stats", timeout=10)
        print(f"GET /api/stats status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Stats response keys: {list(data.keys())}")
            print(f"Total products: {data.get('total_products', 'N/A')}")
        else:
            print(f"GET error: {response.text}")
    except Exception as e:
        print(f"GET request failed: {e}")
    
    print("\n" + "="*50)
    print("=== Testing minimal JSON endpoint ===")
    
    # Test with a very simple JSON payload
    simple_data = {
        "from_license_name": "Test Vendor",
        "inventory": [{
            "product_name": "Test Product",
            "vendor": "Test Vendor",
            "product_type": "flower"
        }]
    }
    
    json_str = json.dumps(simple_data)
    json_b64 = base64.b64encode(json_str.encode()).decode()
    test_url = f"data:application/json;base64,{json_b64}"
    
    payload = {"url": test_url}
    
    try:
        response = requests.post(
            "http://localhost:8000/api/json-match",
            json=payload,
            timeout=30
        )
        
        print(f"POST status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response analysis:")
            print(f"  - Success: {data.get('success')}")
            print(f"  - Message: {data.get('message')}")
            print(f"  - Matched count: {data.get('matched_count')}")
            print(f"  - Available tags: {len(data.get('available_tags', []))}")
            print(f"  - JSON matched tags: {len(data.get('json_matched_tags', []))}")
            
            if data.get('json_matched_tags'):
                print("\n=== JSON Matched Tag Analysis ===")
                tag = data['json_matched_tags'][0]
                print(f"First tag keys: {list(tag.keys())}")
                print(f"Product Name: {tag.get('ProductName', 'MISSING')}")
                print(f"Vendor: {tag.get('Vendor', 'MISSING')}")
                print(f"Product Type: {tag.get('Product Type*', 'MISSING')}")
                
        else:
            print(f"POST error: {response.text}")
            
    except Exception as e:
        print(f"POST request failed: {e}")

if __name__ == "__main__":
    create_simple_test()