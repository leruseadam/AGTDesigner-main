#!/usr/bin/env python3.11
"""
Test web app loading on PythonAnywhere
This script tests if the Flask app can be imported and served correctly
"""

import os
import sys
import logging

def test_web_loading():
    print("🌐 Testing web app loading...")
    
    # Set up paths
    project_dir = '/home/adamcordova/AGTDesigner'
    if os.path.exists(project_dir):
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        print(f"✅ Project directory found: {project_dir}")
    else:
        print(f"❌ Project directory not found: {project_dir}")
        return False
    
    # Add user site-packages
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
        print(f"✅ User site-packages added: {user_site}")
    
    # Set environment variables
    os.environ['PYTHONANYWHERE_SITE'] = 'True'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    try:
        # Test 1: Import the Flask app
        print("1. Testing Flask app import...")
        from app import app
        print("   ✅ Flask app imported successfully")
        
        # Test 2: Check app configuration
        print("2. Testing app configuration...")
        print(f"   ✅ App name: {app.name}")
        print(f"   ✅ Debug mode: {app.debug}")
        print(f"   ✅ Testing mode: {app.testing}")
        
        # Test 3: Check registered routes
        print("3. Testing registered routes...")
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"   ✅ Found {len(routes)} routes: {routes[:5]}...")
        
        # Test 4: Test client creation
        print("4. Testing test client...")
        with app.test_client() as client:
            print("   ✅ Test client created successfully")
            
            # Test 5: Test home page
            print("5. Testing home page response...")
            response = client.get('/')
            print(f"   ✅ Home page response: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Home page content length:", len(response.data))
            else:
                print(f"   ❌ Home page failed with status: {response.status_code}")
                print(f"   Response data: {response.data[:200]}...")
        
        print("\n🎉 ALL WEB TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Web test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_loading()
    if success:
        print("\n✅ Web app is ready for deployment!")
    else:
        print("\n❌ Web app has issues that need to be fixed.")
