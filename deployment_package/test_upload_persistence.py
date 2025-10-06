#!/usr/bin/env python3

"""
Test Upload Persistence - Check if uploaded files persist across sessions
"""

import requests
import os
import time
import json

BASE_URL = "http://localhost:8000"

def test_upload_persistence():
    """Test that uploaded files persist across requests"""
    print("=== Testing Upload Persistence ===")
    
    # Test file - create a simple Excel file
    test_file_path = "test_upload.xlsx"
    
    # Create a simple Excel file for testing
    try:
        import pandas as pd
        test_data = pd.DataFrame({
            'Product Name*': ['Test Product 1', 'Test Product 2'],
            'Price': [10.00, 15.00],
            'Weight*': [1.0, 2.0],
            'Product Type*': ['Flower', 'Edible'],
            'Vendor/Supplier*': ['Test Vendor', 'Test Vendor'],
            'Product Strain': ['Test Strain', 'Other Strain']
        })
        test_data.to_excel(test_file_path, index=False)
        print(f"✅ Created test file: {test_file_path}")
    except Exception as e:
        print(f"❌ Failed to create test file: {e}")
        return False
    
    # Test upload
    session = requests.Session()
    
    try:
        print("\n1. Testing file upload...")
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = session.post(f"{BASE_URL}/upload", files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful: {result.get('message', 'No message')}")
                if 'filename' in result:
                    print(f"   Uploaded file: {result['filename']}")
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
        
        # Wait a moment for processing
        time.sleep(2)
        
        print("\n2. Testing if upload persists in same session...")
        # Test if the file persists in the same session
        tags_response = session.get(f"{BASE_URL}/api/available-tags")
        if tags_response.status_code == 200:
            tags_data = tags_response.json()
            if tags_data.get('success') and tags_data.get('tags'):
                print(f"✅ Found {len(tags_data['tags'])} products from uploaded file")
                print(f"   Sample product: {tags_data['tags'][0].get('Product Name*', 'No name')}")
            else:
                print(f"❌ No products found from uploaded file in same session")
                return False
        else:
            print(f"❌ Failed to get tags: {tags_response.status_code}")
            return False
        
        print("\n3. Testing if upload persists in new session...")
        # Create a new session to test persistence
        new_session = requests.Session()
        
        # Try to access the uploaded data with new session
        new_tags_response = new_session.get(f"{BASE_URL}/api/available-tags")
        if new_tags_response.status_code == 200:
            new_tags_data = new_tags_response.json()
            if new_tags_data.get('success') and new_tags_data.get('tags'):
                uploaded_products = len(new_tags_data['tags'])
                print(f"✅ Found {uploaded_products} products from uploaded file in new session")
                
                # Check if it's the uploaded data or default data
                test_product_found = False
                for tag in new_tags_data['tags'][:5]:  # Check first 5 products
                    if 'Test Product' in tag.get('Product Name*', ''):
                        test_product_found = True
                        break
                
                if test_product_found:
                    print("✅ Upload data persisted across sessions!")
                    return True
                else:
                    print("⚠️  New session loaded default data, not uploaded data")
                    print("   This suggests uploads don't persist across sessions")
                    return False
            else:
                print(f"❌ No products found in new session")
                return False
        else:
            print(f"❌ Failed to get tags in new session: {new_tags_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n🧹 Cleaned up test file: {test_file_path}")

def test_session_info():
    """Test session information endpoints"""
    print("\n=== Testing Session Information ===")
    
    session = requests.Session()
    
    try:
        # Test session status
        response = session.get(f"{BASE_URL}/api/session-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session status: {json.dumps(data, indent=2)}")
        else:
            print(f"⚠️  Session status endpoint not available: {response.status_code}")
        
        # Test debug info
        response = session.get(f"{BASE_URL}/api/debug-session")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug session info available")
            if 'file_path' in data:
                print(f"   File path in session: {data['file_path']}")
            if 'session_id' in data:
                print(f"   Session ID: {data['session_id']}")
        else:
            print(f"⚠️  Debug session endpoint not available: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Session info test failed: {e}")

if __name__ == "__main__":
    print("Upload Persistence Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server responded with {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("Please start the Flask app first: python app.py")
        exit(1)
    
    # Run tests
    test_session_info()
    
    success = test_upload_persistence()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ UPLOAD PERSISTENCE TEST PASSED")
    else:
        print("❌ UPLOAD PERSISTENCE TEST FAILED")
        print("\nPossible issues:")
        print("- Session configuration not preserving data across requests")
        print("- File uploads not being properly stored in session")
        print("- ExcelProcessor not loading session data correctly")
        print("- Cache clearing between requests")