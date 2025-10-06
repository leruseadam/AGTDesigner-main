#!/usr/bin/env python3.11
"""
Test app import to identify what's causing the failure
"""

import os
import sys
import traceback

def test_app_import():
    print("🔍 Testing app import step by step...")
    
    # Set up paths
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Add user site-packages
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
    
    # Set environment variables
    os.environ['PYTHONANYWHERE_SITE'] = 'True'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Change to project directory
    os.chdir(project_dir)
    
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📋 Python path: {sys.path[:3]}")
    
    # Test 1: Check if app.py exists
    print("\n1. Checking app.py file...")
    app_file = os.path.join(project_dir, 'app.py')
    if os.path.exists(app_file):
        print(f"   ✅ app.py exists: {app_file}")
        stat = os.stat(app_file)
        print(f"   📏 File size: {stat.st_size} bytes")
        print(f"   📋 Permissions: {oct(stat.st_mode)[-3:]}")
    else:
        print(f"   ❌ app.py missing: {app_file}")
        return False
    
    # Test 2: Try importing basic modules first
    print("\n2. Testing basic imports...")
    try:
        import flask
        print("   ✅ Flask imported")
    except Exception as e:
        print(f"   ❌ Flask import failed: {e}")
        return False
    
    try:
        import pandas
        print("   ✅ Pandas imported")
    except Exception as e:
        print(f"   ❌ Pandas import failed: {e}")
        return False
    
    try:
        import openpyxl
        print("   ✅ OpenPyXL imported")
    except Exception as e:
        print(f"   ❌ OpenPyXL import failed: {e}")
        return False
    
    # Test 3: Try importing app step by step
    print("\n3. Testing app import...")
    try:
        # First, try to import just the module
        import app
        print("   ✅ app module imported")
        
        # Then try to get the app object
        app_obj = app.app
        print("   ✅ app.app object accessed")
        
        # Test app configuration
        print(f"   📁 Upload folder: {app_obj.config.get('UPLOAD_FOLDER', 'Not set')}")
        print(f"   🔑 Secret key: {'Set' if app_obj.config.get('SECRET_KEY') else 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ App import failed: {e}")
        print("   📋 Full traceback:")
        traceback.print_exc()
        return False

def test_wsgi_simple():
    """Test simple WSGI functionality"""
    print("\n🧪 Testing simple WSGI...")
    
    try:
        from wsgiref.simple_server import make_server
        
        def simple_app(environ, start_response):
            status = '200 OK'
            headers = [('Content-Type', 'text/html')]
            start_response(status, headers)
            return [b'<h1>Simple WSGI Test</h1><p>WSGI is working!</p>']
        
        print("   ✅ Simple WSGI app created")
        return True
        
    except Exception as e:
        print(f"   ❌ Simple WSGI test failed: {e}")
        return False

def main():
    print("🚀 App Import Diagnostic Tool")
    print("=" * 50)
    
    # Test app import
    app_ok = test_app_import()
    
    # Test simple WSGI
    wsgi_ok = test_wsgi_simple()
    
    print("\n📋 Summary:")
    print(f"App import: {'✅' if app_ok else '❌'}")
    print(f"Simple WSGI: {'✅' if wsgi_ok else '❌'}")
    
    if app_ok and wsgi_ok:
        print("\n🎉 All tests passed!")
        print("💡 The issue might be with the WSGI file configuration")
        print("💡 Try using wsgi_minimal.py as your WSGI file")
    else:
        print("\n❌ Some tests failed!")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
