#!/usr/bin/env python3
"""
Test script for fast Excel upload functionality
"""

import requests
import os
import time
import pandas as pd
import tempfile

def create_test_excel():
    """Create a test Excel file"""
    # Create test data
    data = {
        'Product Name*': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
        'Product Type*': ['Flower', 'Concentrate', 'Edible'],
        'Vendor/Supplier*': ['Test Vendor', 'Test Vendor', 'Test Vendor'],
        'Product Brand': ['Test Brand', 'Test Brand', 'Test Brand'],
        'Weight*': ['3.5g', '1g', '100mg'],
        'Price': ['25.00', '40.00', '15.00'],
        'Description': ['Test description 1', 'Test description 2', 'Test description 3']
    }
    
    df = pd.DataFrame(data)
    
    # Create temporary Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        df.to_excel(tmp_file.name, index=False)
        return tmp_file.name

def test_fast_upload():
    """Test the fast upload endpoint"""
    print("Testing fast Excel upload...")
    
    # Create test file
    test_file_path = create_test_excel()
    
    try:
        # Test upload
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            start_time = time.time()
            response = requests.post('http://localhost:8000/upload-fast', files=files)
            upload_time = time.time() - start_time
        
        print(f"Upload response: {response.status_code}")
        print(f"Upload time: {upload_time:.3f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Upload successful: {result}")
            
            # Test status endpoint
            if 'upload_id' in result:
                upload_id = result['upload_id']
                status_response = requests.get(f'http://localhost:8000/upload-status/{upload_id}')
                print(f"Status response: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"Status: {status_result}")
        
        else:
            print(f"Upload failed: {response.text}")
    
    except Exception as e:
        print(f"Error testing upload: {e}")
    
    finally:
        # Cleanup
        try:
            os.unlink(test_file_path)
        except:
            pass

def test_regular_upload():
    """Test the regular upload endpoint for comparison"""
    print("\nTesting regular Excel upload...")
    
    # Create test file
    test_file_path = create_test_excel()
    
    try:
        # Test upload
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            start_time = time.time()
            response = requests.post('http://localhost:8000/upload', files=files)
            upload_time = time.time() - start_time
        
        print(f"Regular upload response: {response.status_code}")
        print(f"Regular upload time: {upload_time:.3f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Regular upload successful: {result}")
        else:
            print(f"Regular upload failed: {response.text}")
    
    except Exception as e:
        print(f"Error testing regular upload: {e}")
    
    finally:
        # Cleanup
        try:
            os.unlink(test_file_path)
        except:
            pass

if __name__ == "__main__":
    print("Fast Excel Upload Test")
    print("=" * 50)
    
    # Test fast upload
    test_fast_upload()
    
    # Test regular upload for comparison
    test_regular_upload()
    
    print("\nTest completed!")
