#!/usr/bin/env python3
"""
Simple test for the JSON endpoint to see what fields are actually returned
"""

import requests
import json
import base64

def create_test_json():
    """Create a simple test JSON with realistic data"""
    test_data = {
        "from_license_name": "Grow Op Farms",
        "inventory": [{
            "product_name": "Blue Dream Premium 1/8oz",
            "vendor": "Grow Op Farms",
            "brand": "House Brand",
            "product_type": "flower",
            "strain": "Blue Dream",
            "weight": "3.5",
            "unit_weight_uom": "g", 
            "thc_percentage": "22.5",
            "cbd_percentage": "0.3",
            "price": "35.00",
            "description": "Premium Blue Dream flower with excellent terpene profile",
            "sku": "BD-35-001",
            "batch_number": "BD220924",
            "harvest_date": "2024-09-15",
            "package_date": "2024-09-24",
            "lab_result_data": {
                "thc": "22.5%",
                "cbd": "0.3%",
                "total_cannabinoids": "24.1%",
                "terpenes": ["Myrcene", "Limonene", "Pinene"]
            },
            "lineage": "Blueberry x Haze",
            "quantity": "1",
            "room": "Flower Room A"
        }]
    }
    
    # Convert to base64 data URL
    json_str = json.dumps(test_data)
    json_b64 = base64.b64encode(json_str.encode()).decode()
    return f"data:application/json;base64,{json_b64}"

def test_json_endpoint():
    """Test the JSON endpoint and examine the response"""
    
    # Create test data
    test_url = create_test_json()
    
    # Prepare request
    payload = {"url": test_url}
    
    print("Testing JSON endpoint...")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        # Make request
        response = requests.post(
            "http://localhost:8000/api/json-match",
            json=payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            print("=== RESPONSE DATA ANALYSIS ===")
            print(f"Response type: {type(response_data)}")
            print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            print()
            
            # Check if it's a successful match response
            if 'status' in response_data:
                print(f"Status: {response_data['status']}")
                
                if 'matched_products' in response_data:
                    products = response_data['matched_products']
                    print(f"Number of matched products: {len(products)}")
                    
                    if products:
                        print("\n=== FIRST PRODUCT FIELD ANALYSIS ===")
                        first_product = products[0]
                        print(f"Product keys: {list(first_product.keys())}")
                        print()
                        
                        # Check each field
                        important_fields = [
                            'ProductName', 'Description', 'Product Type*', 'Product Brand',
                            'Product Strain', 'Lineage', 'Weight*', 'Units', 'THC test result',
                            'CBD test result', 'Vendor', 'Price', 'Lot Number', 'Barcode*',
                            'Room*', 'Batch Number', 'Quantity*'
                        ]
                        
                        print("=== FIELD VALUE ANALYSIS ===")
                        for field in important_fields:
                            value = first_product.get(field, "*** MISSING ***")
                            print(f"{field:20}: {value}")
                        
                        print("\n=== ALL FIELDS WITH VALUES ===")
                        for key, value in first_product.items():
                            if value and str(value).strip():
                                print(f"{key:30}: {value}")
                        
                        print("\n=== EMPTY OR MISSING FIELDS ===")
                        for key, value in first_product.items():
                            if not value or not str(value).strip():
                                print(f"{key:30}: {repr(value)}")
                    
                else:
                    print("No 'matched_products' in response")
            else:
                print("No 'status' in response")
                print(f"Full response: {json.dumps(response_data, indent=2)}")
                
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_json_endpoint()