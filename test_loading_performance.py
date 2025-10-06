#!/usr/bin/env python3
"""
Quick Loading Test for PythonAnywhere
Tests the loading performance of key endpoints
"""

import requests
import time
import sys

def test_loading_performance():
    """Test the loading performance of key endpoints"""
    
    print("🚀 Testing PythonAnywhere Loading Performance...")
    print("=" * 50)
    
    # Replace with your actual PythonAnywhere URL
    base_url = "https://adamcordova.pythonanywhere.com"
    
    endpoints_to_test = [
        ("/", "Main page"),
        ("/api/database-stats", "Database stats"),
        ("/api/database-vendor-stats", "Vendor stats"),
        ("/api/initial-data", "Initial data"),
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        url = base_url + endpoint
        print(f"🔍 Testing {description}...")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            end_time = time.time()
            
            load_time = (end_time - start_time) * 1000  # Convert to milliseconds
            status = "✅" if response.status_code == 200 else "❌"
            
            print(f"{status} {description}: {load_time:.2f}ms (Status: {response.status_code})")
            
            results.append({
                'endpoint': description,
                'time': load_time,
                'status': response.status_code,
                'success': response.status_code == 200
            })
            
        except requests.exceptions.Timeout:
            print(f"⏰ {description}: Timeout (>30s)")
            results.append({
                'endpoint': description,
                'time': 30000,
                'status': 'timeout',
                'success': False
            })
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            results.append({
                'endpoint': description,
                'time': 0,
                'status': 'error',
                'success': False
            })
    
    # Summary
    print("\n📊 Performance Summary:")
    print("=" * 30)
    
    successful_tests = [r for r in results if r['success']]
    if successful_tests:
        avg_time = sum(r['time'] for r in successful_tests) / len(successful_tests)
        print(f"⚡ Average load time: {avg_time:.2f}ms")
        
        fastest = min(successful_tests, key=lambda x: x['time'])
        slowest = max(successful_tests, key=lambda x: x['time'])
        
        print(f"🚀 Fastest: {fastest['endpoint']} ({fastest['time']:.2f}ms)")
        print(f"🐌 Slowest: {slowest['endpoint']} ({slowest['time']:.2f}ms)")
    
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   - {test['endpoint']}: {test['status']}")
    
    # Performance recommendations
    print("\n💡 Performance Recommendations:")
    if any(r['time'] > 5000 for r in successful_tests):
        print("⚠️ Some endpoints are slow (>5s). Consider:")
        print("   - Running the performance optimization script")
        print("   - Checking database indexes")
        print("   - Reducing initial data load")
    elif any(r['time'] > 2000 for r in successful_tests):
        print("⚡ Performance is acceptable but could be improved")
        print("   - Consider running the optimization script")
    else:
        print("🎉 Performance looks good!")
    
    return results

if __name__ == "__main__":
    test_loading_performance()
