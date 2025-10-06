#!/usr/bin/env python3
"""
Web Deployment Verification Tool
Quick check to see if the concentrate weight fix is working on web
"""

import requests
import json

def test_web_deployment():
    """Test if the web version has the concentrate weight fix"""
    
    print("🔍 Testing Web Deployment for Concentrate Weight Fix")
    print("=" * 60)
    
    # Test the exact products from Word document
    test_products = [
        "Grape Slurpee Wax by Hustler's Ambition - 1g",
        "Afghani Kush Wax by Hustler's Ambition - 1g", 
        "Bruce Banner Wax by Hustler's Ambition - 1g"
    ]
    
    # Try to call web API endpoints to test
    base_url = "http://localhost:5000"  # Adjust if different
    
    print(f"Testing against: {base_url}")
    print()
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print("✅ Server is responding")
    except requests.exceptions.RequestException as e:
        print("❌ Server not responding:", e)
        print("\n💡 Next Steps:")
        print("1. Make sure the web server is running")
        print("2. Check if it's on a different port")
        print("3. Restart the web server to pick up code changes")
        return
    
    # Test 2: Try to get available tags (should include concentrates)
    try:
        response = requests.get(f"{base_url}/api/available-tags", timeout=10)
        if response.status_code == 200:
            tags = response.json()
            concentrate_tags = [tag for tag in tags if 'concentrate' in tag.lower() or 'wax' in tag.lower()]
            print(f"✅ Found {len(concentrate_tags)} concentrate-related tags")
            if concentrate_tags:
                print(f"   Sample tags: {concentrate_tags[:3]}")
        else:
            print(f"❌ API call failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print()
    print("🔧 Troubleshooting Steps:")
    print("1. Restart the web server to pick up latest code changes")
    print("2. Clear any application cache")
    print("3. Check server logs for errors")
    print("4. Verify the deployed code includes the sqlite3.Row fix")
    print()
    print("🎯 Expected Result:")
    print("After restart, concentrate labels should show:")
    for product in test_products:
        expected = product.split(" by ")[0] + " - 1g"
        print(f"   '{expected}'")

if __name__ == "__main__":
    test_web_deployment()