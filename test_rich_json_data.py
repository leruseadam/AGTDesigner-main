#!/usr/bin/env python3
"""
Test JSON with rich data to check if hybrid merge preserves fields
"""
import json
import base64
import requests

# Create test JSON with rich field data
test_json = [
    {
        "product_name": "Blue Dream Cartridge",
        "inventory_name": "Blue Dream Cartridge", 
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
    },
    {
        "product_name": "OG Kush Flower",
        "inventory_name": "OG Kush Flower",
        "vendor": "top shelf farms",
        "price": "35.00", 
        "weight": "3.5g",
        "weight_with_units": "3.5g",
        "unit_weight_uom": "g",
        "thc_percentage": "24.2",
        "cbd_percentage": "0.3",
        "batch_number": "OGK-2024-002",
        "lot_number": "LOT-67890",
        "sku": "TSF-OGK-3.5G",
        "quantity": "25",
        "room": "Flowering Room B",
        "description": "Classic OG Kush with earthy pine aroma",
        "strain": "OG Kush",
        "product_type": "Flower",
        "lab_result_data": {
            "thc": "24.2",
            "cbd": "0.3",
            "total_cannabinoids": "28.1",
            "terpenes": ["myrcene", "limonene", "caryophyllene"]
        },
        "harvest_date": "2024-09-01",
        "package_date": "2024-09-10"
    }
]

print("🧪 TESTING ENHANCED JSON MATCHER WITH RICH DATA")
print("=" * 60)

# Encode to base64 data URL
json_str = json.dumps(test_json, indent=2)
encoded = base64.b64encode(json_str.encode()).decode()
data_url = f"data:application/json;base64,{encoded}"

print(f"📊 Input JSON contains {len(test_json)} products with rich field data")
print(f"🔗 Data URL length: {len(data_url)} characters")

# Test with the regular JSON match endpoint
print("\n🔍 Testing regular JSON match endpoint...")
response = requests.post('http://localhost:8000/api/json-match', 
                        json={'url': data_url},
                        timeout=30)

if response.status_code == 200:
    results = response.json()
    print(f"✅ Regular JSON match returned {len(results)} results")
else:
    print(f"❌ Regular JSON match failed: {response.status_code} - {response.text}")

# Check what's in available tags now
print("\n📋 Checking available tags after JSON matching...")
response = requests.get('http://localhost:8000/api/available-tags')
if response.status_code == 200:
    tags = response.json()
    if tags:
        first_tag = tags[0]
        print(f"🏷️  First tag keys: {sorted(first_tag.keys())[:20]}...")  # Show first 20 keys
        
        print("\n🔍 Checking specific fields in first matched product:")
        fields_to_check = [
            ("Product Name*", "Product Name"),
            ("Source", "Source"), 
            ("JSON_Source", "JSON Source"),
            ("Match_Score", "Match Score"),
            ("Price", "Price"),
            ("Batch Number", "Batch Number"),
            ("Lot Number", "Lot Number"), 
            ("Internal Product Identifier", "SKU"),
            ("Quantity*", "Quantity"),
            ("Room*", "Room"),
            ("THC test result", "THC"),
            ("CBD test result", "CBD"),
            ("JSON_Item_Name", "JSON Item Name"),
            ("JSON_Fields_Merged", "JSON Fields Merged")
        ]
        
        for key, label in fields_to_check:
            value = first_tag.get(key, "N/A")
            status = "✅" if value and str(value).strip() not in ["N/A", "None", "", "null"] else "❌"
            print(f"  {status} {label}: {value}")
            
    else:
        print("❌ No tags returned")
else:
    print(f"❌ Failed to get available tags: {response.status_code}")

print("\n" + "=" * 60)