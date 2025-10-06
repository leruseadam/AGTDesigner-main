#!/usr/bin/env python3
"""
Test script to verify the 502 Bad Gateway fix
This script tests the /api/generate endpoint with various tag counts
"""

import requests
import json
import time
import sys

def test_generation_endpoint(base_url, tag_count=50):
    """Test the generation endpoint with a specific number of tags"""
    
    # Create test tags
    test_tags = [f"Test Product {i+1}" for i in range(tag_count)]
    
    payload = {
        "selected_tags": test_tags,
        "template_type": "vertical",
        "scale_factor": 1.0
    }
    
    print(f"Testing with {tag_count} tags...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=60,  # 60 second timeout
            headers={'Content-Type': 'application/json'}
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {duration:.2f} seconds")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Generation completed successfully")
            return True
        elif response.status_code == 408:
            print("⚠️  TIMEOUT: Request timed out (expected for large tag counts)")
            return False
        elif response.status_code == 502:
            print("❌ 502 ERROR: Bad Gateway (this should be fixed)")
            return False
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response text: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Run tests with different tag counts"""
    
    # Default to localhost if no URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    print(f"Testing 502 fix against: {base_url}")
    print("=" * 50)
    
    # Test with different tag counts
    test_cases = [
        (10, "Small tag set"),
        (50, "Medium tag set"),
        (100, "Large tag set"),
        (200, "Very large tag set"),
        (352, "Original problematic tag count")
    ]
    
    results = []
    
    for tag_count, description in test_cases:
        print(f"\n{description} ({tag_count} tags):")
        print("-" * 30)
        
        success = test_generation_endpoint(base_url, tag_count)
        results.append((tag_count, success))
        
        # Wait between tests to avoid rate limiting
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print("=" * 50)
    
    for tag_count, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{tag_count:3d} tags: {status}")
    
    # Check if fix is working
    small_success = any(success for count, success in results if count <= 50)
    large_failure = any(not success for count, success in results if count >= 200)
    
    if small_success and not large_failure:
        print("\n🎉 FIX VERIFIED: 502 errors should be resolved!")
        print("   - Small tag sets work correctly")
        print("   - Large tag sets fail gracefully with timeout (not 502)")
    else:
        print("\n⚠️  ISSUES DETECTED: Fix may need additional work")
        if not small_success:
            print("   - Even small tag sets are failing")
        if large_failure:
            print("   - Large tag sets still causing 502 errors")

if __name__ == "__main__":
    main()
