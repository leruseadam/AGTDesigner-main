#!/usr/bin/env python3

"""
Simple test for upload persistence issue
"""

import requests
import pandas as pd

def test_basic_upload():
    """Test basic upload functionality"""
    print("Testing basic upload functionality...")
    
    # Create test Excel file
    test_data = pd.DataFrame({
        'Product Name*': ['Test Product'],
        'Price': [25.00],
        'Weight*': [3.5],
        'Product Type*': ['Flower'],
        'Vendor/Supplier*': ['Test Vendor']
    })
    
    test_file = 'simple_test.xlsx'
    test_data.to_excel(test_file, index=False)
    print(f"✅ Created test file: {test_file}")
    
    # Test with session
    session = requests.Session()
    
    try:
        # Upload file
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f)}
            response = session.post('http://localhost:8000/upload', files=files)
        
        print(f"Upload response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload success: {result.get('message')}")
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
        
        # Test if data persists - check available tags
        import time
        time.sleep(3)  # Wait for processing
        
        tags_response = session.get('http://localhost:8000/api/available-tags')
        print(f"Tags response: {tags_response.status_code}")
        
        if tags_response.status_code == 200:
            tags_data = tags_response.json()
            if tags_data.get('success') and tags_data.get('tags'):
                print(f"✅ Found {len(tags_data['tags'])} products")
                
                # Look for our test product
                test_found = False
                for tag in tags_data['tags'][:5]:
                    product_name = tag.get('Product Name*', '')
                    if 'Test Product' in product_name:
                        test_found = True
                        print(f"✅ Found test product: {product_name}")
                        break
                
                if test_found:
                    print("✅ Upload persisted successfully!")
                    return True
                else:
                    print("⚠️  Test product not found - might be default data")
                    return False
            else:
                print(f"❌ No products found: {tags_data}")
                return False
        else:
            print(f"❌ Failed to get tags: {tags_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        import os
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    print("Simple Upload Persistence Test")
    print("=" * 40)
    success = test_basic_upload()
    print("=" * 40)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED - Upload doesn't persist")