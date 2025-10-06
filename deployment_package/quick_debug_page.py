#!/usr/bin/env python3.11
"""
Quick debug for page not loading issue
"""

import os
import sys
import time

def quick_debug():
    print("🔍 Quick page loading debug...")
    
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
        # Test 1: Check if we can import the app
        print("1. Testing app import...")
        from app import app
        print("   ✅ App imported successfully")
        
        # Test 2: Check app configuration
        print("2. Checking app configuration...")
        print(f"   📁 Upload folder: {app.config.get('UPLOAD_FOLDER', 'Not set')}")
        print(f"   🔑 Secret key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        print(f"   🐛 Debug mode: {app.debug}")
        
        # Test 3: Test with test client
        print("3. Testing home page...")
        with app.test_client() as client:
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            print(f"   📊 Status: {response.status_code}")
            print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
            print(f"   📏 Size: {len(response.data)} bytes")
            
            if response.status_code == 200:
                print("   ✅ Home page works")
                content = response.data.decode('utf-8')
                if '<html' in content.lower():
                    print("   ✅ Returns HTML")
                else:
                    print("   ❌ Not returning HTML")
                    print(f"   First 200 chars: {content[:200]}")
            else:
                print(f"   ❌ Home page failed: {response.status_code}")
                print(f"   Error: {response.data[:200]}")
        
        # Test 4: Check WSGI file
        print("4. Checking WSGI file...")
        wsgi_path = os.path.join(project_dir, 'wsgi.py')
        if os.path.exists(wsgi_path):
            print(f"   ✅ WSGI file exists: {wsgi_path}")
            # Check permissions
            stat = os.stat(wsgi_path)
            permissions = oct(stat.st_mode)[-3:]
            print(f"   📋 Permissions: {permissions}")
            
            if 'x' in permissions:
                print("   ✅ WSGI file is executable")
            else:
                print("   ❌ WSGI file is not executable")
        else:
            print(f"   ❌ WSGI file missing: {wsgi_path}")
        
        # Test 5: Check uploads directory
        print("5. Checking uploads directory...")
        uploads_dir = os.path.join(project_dir, 'uploads')
        if os.path.exists(uploads_dir):
            print(f"   ✅ Uploads directory exists: {uploads_dir}")
        else:
            print(f"   ❌ Uploads directory missing: {uploads_dir}")
        
        print("\n🎉 Quick debug completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_pythonanywhere_logs():
    """Check for any obvious issues"""
    print("\n📋 Checking for common issues...")
    
    # Check if we're on PythonAnywhere
    current_dir = os.getcwd()
    if 'pythonanywhere' in current_dir.lower() or '/home/' in current_dir:
        print("   ✅ Running on PythonAnywhere")
    else:
        print("   ⚠️  Not running on PythonAnywhere")
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024**3)
        print(f"   💾 Free space: {free_gb:.1f} GB")
        
        if free_gb < 1:
            print("   ⚠️  WARNING: Low disk space!")
        else:
            print("   ✅ Sufficient disk space")
    except:
        print("   ❌ Could not check disk space")

def main():
    print("🚀 Quick Page Loading Debug")
    print("=" * 40)
    
    # Run quick debug
    success = quick_debug()
    
    # Check for common issues
    check_pythonanywhere_logs()
    
    if success:
        print("\n✅ App appears to be working!")
        print("💡 If page still won't load:")
        print("1. Check PythonAnywhere Web tab error logs")
        print("2. Reload your web app")
        print("3. Verify WSGI file path in web app configuration")
        print("4. Check if there are any JavaScript errors in browser")
    else:
        print("\n❌ App has issues!")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
