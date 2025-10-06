#!/usr/bin/env python3.11
"""
Debug web loading issues on PythonAnywhere
"""

import os
import sys
import time
import requests
from urllib.parse import urljoin

def test_web_loading():
    print("🌐 Testing web loading on PythonAnywhere...")
    
    # Set up paths
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Add user site-packages
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
    
    try:
        # Test 1: Import Flask app
        print("1. Testing Flask app import...")
        from app import app
        print("   ✅ Flask app imported successfully")
        
        # Test 2: Test with test client
        print("2. Testing with Flask test client...")
        with app.test_client() as client:
            print("   ✅ Test client created")
            
            # Test home page
            print("3. Testing home page...")
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            print(f"   ✅ Response status: {response.status_code}")
            print(f"   ✅ Response time: {end_time - start_time:.2f} seconds")
            print(f"   ✅ Content length: {len(response.data)} bytes")
            
            if response.status_code == 200:
                print("   ✅ Home page loads successfully")
                
                # Check if it's HTML
                content = response.data.decode('utf-8')
                if '<html' in content.lower():
                    print("   ✅ Response contains HTML")
                else:
                    print("   ❌ Response doesn't contain HTML")
                    print(f"   First 200 chars: {content[:200]}")
                
                # Check for common issues
                if 'error' in content.lower():
                    print("   ⚠️  Response contains 'error' text")
                if 'exception' in content.lower():
                    print("   ⚠️  Response contains 'exception' text")
                if 'traceback' in content.lower():
                    print("   ⚠️  Response contains 'traceback' text")
                    
            else:
                print(f"   ❌ Home page failed with status: {response.status_code}")
                print(f"   Response: {response.data[:200]}")
        
        # Test 3: Test other routes
        print("4. Testing other routes...")
        with app.test_client() as client:
            routes_to_test = ['/api/status', '/test']
            for route in routes_to_test:
                try:
                    response = client.get(route)
                    print(f"   ✅ {route}: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ {route}: {e}")
        
        print("\n🎉 Web loading tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Web loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_permissions():
    """Check file permissions and structure"""
    print("\n📁 Checking file structure and permissions...")
    
    project_dir = '/home/adamcordova/AGTDesigner'
    
    # Check if directory exists
    if os.path.exists(project_dir):
        print(f"✅ Project directory exists: {project_dir}")
    else:
        print(f"❌ Project directory missing: {project_dir}")
        return False
    
    # Check key files
    key_files = ['app.py', 'wsgi.py', 'requirements.txt']
    for file in key_files:
        file_path = os.path.join(project_dir, file)
        if os.path.exists(file_path):
            print(f"✅ {file} exists")
            # Check permissions
            stat = os.stat(file_path)
            print(f"   Permissions: {oct(stat.st_mode)[-3:]}")
        else:
            print(f"❌ {file} missing")
    
    # Check if wsgi.py is executable
    wsgi_path = os.path.join(project_dir, 'wsgi.py')
    if os.path.exists(wsgi_path):
        if os.access(wsgi_path, os.X_OK):
            print("✅ wsgi.py is executable")
        else:
            print("❌ wsgi.py is not executable")
            print("   Run: chmod +x wsgi.py")
    
    return True

def main():
    print("🔍 PythonAnywhere Web Loading Debug Tool")
    print("=" * 50)
    
    # Check file structure
    check_file_permissions()
    
    # Test web loading
    test_web_loading()
    
    print("\n💡 If tests pass but page doesn't load:")
    print("1. Check PythonAnywhere Web tab error logs")
    print("2. Verify WSGI file path in web app configuration")
    print("3. Try accessing the page directly")
    print("4. Check if there are any JavaScript errors in browser console")

if __name__ == "__main__":
    main()
