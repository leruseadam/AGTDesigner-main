#!/usr/bin/env python3
"""
Test script to check what details are returned by JSON matching
using the Flask app approach to directly call the endpoint.
"""

import json
import requests
import base64

def create_test_json():
    """Create test JSON with detailed product information"""
    return {
        "from_license_name": "Grow Op Farms",
        "inventory": [
            {
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
            }
        ]
    }

def test_json_endpoint():
    """Test the JSON matching endpoint to see what details are returned"""
    print("=== Testing JSON Endpoint for Tag Details ===\n")
    
    # Create test data
    test_data = create_test_json()
    json_str = json.dumps(test_data)
    
    # Encode as base64 data URL (like the test does)
    encoded_data = base64.b64encode(json_str.encode()).decode()
    data_url = f"data:application/json;base64,{encoded_data}"
    
    try:
        # Test with local Flask app if running
        response = requests.post(
            'http://localhost:8000/api/json-match',
            json={'url': data_url},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            products = result.get('products', [])
            
            if products:
                print(f"✓ Got {len(products)} matched products\n")
                
                # Analyze first product in detail
                product = products[0]
                print("=== PRODUCT DETAILS ANALYSIS ===")
                print(f"Source: {product.get('Source', 'MISSING')}")
                print(f"Product Name: {product.get('Product Name*', 'MISSING')}")
                print(f"Product Type: {product.get('Product Type*', 'MISSING')}")
                print(f"Vendor: {product.get('Vendor', 'MISSING')}")
                print(f"Brand: {product.get('Product Brand', 'MISSING')}")
                print(f"Strain: {product.get('Product Strain', 'MISSING')}")
                print(f"Weight: {product.get('Weight*', 'MISSING')}")
                print(f"Price: {product.get('Price', 'MISSING')}")
                print(f"THC: {product.get('THC test result', 'MISSING')}")
                print(f"CBD: {product.get('CBD test result', 'MISSING')}")
                print(f"Description: {product.get('Description', 'MISSING')}")
                print(f"Quantity: {product.get('Quantity*', 'MISSING')}")
                print()
                
                # Check for missing details
                expected_fields = [
                    'Product Name*', 'Description', 'Product Type*', 'Vendor', 
                    'Product Brand', 'Product Strain', 'Weight*', 'Price',
                    'THC test result', 'CBD test result', 'Quantity*',
                    'sku', 'batch_number', 'harvest_date', 'package_date',
                    'Lineage', 'Units'
                ]
                
                print("=== FIELD ANALYSIS ===")
                missing_fields = []
                present_fields = []
                
                for field in expected_fields:
                    value = product.get(field)
                    if value and str(value).strip() and str(value) != 'Unknown Strain':
                        present_fields.append(field)
                        print(f"✓ {field}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                    else:
                        missing_fields.append(field)
                        print(f"❌ {field}: {value or 'MISSING'}")
                
                print(f"\n=== SUMMARY ===")
                print(f"Present fields: {len(present_fields)}/{len(expected_fields)}")
                print(f"Missing/Empty fields: {len(missing_fields)}")
                
                if missing_fields:
                    print(f"\nMissing: {', '.join(missing_fields)}")
                
                # Show all fields
                print(f"\n=== ALL AVAILABLE FIELDS ({len(product)} total) ===")
                for key, value in sorted(product.items()):
                    if value:
                        print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                
            else:
                print("❌ No products returned from endpoint")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Is it running on localhost:8000?")
        print("\nTo test manually, run: python app.py")
        print("Then run this script again.")
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

if __name__ == "__main__":
    test_json_endpoint()