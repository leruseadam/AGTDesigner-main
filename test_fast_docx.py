#!/usr/bin/env python3
"""
Test script for fast DOCX generation functionality
"""

import requests
import time
import json

def test_fast_docx_generation():
    """Test the fast DOCX generation endpoint"""
    print("Testing fast DOCX generation...")
    
    try:
        # Test data
        test_data = {
            'template_type': 'vertical',
            'scale_factor': 1.0,
            'selected_tags': ['Test Product 1', 'Test Product 2', 'Test Product 3']
        }
        
        start_time = time.time()
        
        # Make request to fast generation endpoint
        response = requests.post(
            'http://localhost:8000/api/generate-fast',
            json=test_data,
            timeout=60
        )
        
        generation_time = time.time() - start_time
        
        print(f"Response status: {response.status_code}")
        print(f"Generation time: {generation_time:.3f}s")
        
        if response.status_code == 200:
            # Check if it's a file response
            content_type = response.headers.get('content-type', '')
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print("✅ Fast DOCX generation successful!")
                print(f"Content-Type: {content_type}")
                print(f"Content-Length: {len(response.content)} bytes")
                
                # Save the file for inspection
                with open('test_fast_output.docx', 'wb') as f:
                    f.write(response.content)
                print("File saved as 'test_fast_output.docx'")
            else:
                print(f"❌ Unexpected content type: {content_type}")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Generation failed: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>60s)")
    except Exception as e:
        print(f"❌ Error testing fast generation: {e}")

def test_regular_docx_generation():
    """Test the regular DOCX generation for comparison"""
    print("\nTesting regular DOCX generation...")
    
    try:
        # Test data
        test_data = {
            'template_type': 'vertical',
            'scale_factor': 1.0,
            'selected_tags': ['Test Product 1', 'Test Product 2', 'Test Product 3']
        }
        
        start_time = time.time()
        
        # Make request to regular generation endpoint
        response = requests.post(
            'http://localhost:8000/api/generate',
            json=test_data,
            timeout=180  # 3 minutes timeout
        )
        
        generation_time = time.time() - start_time
        
        print(f"Response status: {response.status_code}")
        print(f"Generation time: {generation_time:.3f}s")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print("✅ Regular DOCX generation successful!")
                print(f"Content-Type: {content_type}")
                print(f"Content-Length: {len(response.content)} bytes")
                
                # Save the file for inspection
                with open('test_regular_output.docx', 'wb') as f:
                    f.write(response.content)
                print("File saved as 'test_regular_output.docx'")
            else:
                print(f"❌ Unexpected content type: {content_type}")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Generation failed: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>180s)")
    except Exception as e:
        print(f"❌ Error testing regular generation: {e}")

if __name__ == "__main__":
    print("Fast DOCX Generation Test")
    print("=" * 50)
    
    # Test fast generation
    test_fast_docx_generation()
    
    # Test regular generation for comparison
    test_regular_docx_generation()
    
    print("\nTest completed!")
