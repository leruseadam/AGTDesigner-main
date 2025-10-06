#!/usr/bin/env python3.11
"""
Debug WSGI loading issues on PythonAnywhere
"""

import os
import sys
import subprocess

def test_wsgi_directly():
    """Test WSGI file directly"""
    print("🧪 Testing WSGI file directly...")
    
    wsgi_path = '/home/adamcordova/AGTDesigner/wsgi.py'
    
    if not os.path.exists(wsgi_path):
        print(f"❌ WSGI file not found: {wsgi_path}")
        return False
    
    # Check permissions
    stat = os.stat(wsgi_path)
    permissions = oct(stat.st_mode)[-3:]
    print(f"📋 WSGI permissions: {permissions}")
    
    if 'x' not in permissions:
        print("❌ WSGI file is not executable")
        return False
    else:
        print("✅ WSGI file is executable")
    
    # Try to run the WSGI file directly
    try:
        print("🚀 Testing WSGI file execution...")
        result = subprocess.run([sys.executable, wsgi_path], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ WSGI file runs successfully")
            return True
        else:
            print(f"❌ WSGI file failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  WSGI file timed out (this might be normal)")
        return True
    except Exception as e:
        print(f"❌ Error running WSGI file: {e}")
        return False

def check_wsgi_content():
    """Check WSGI file content"""
    print("\n📄 Checking WSGI file content...")
    
    wsgi_path = '/home/adamcordova/AGTDesigner/wsgi.py'
    
    try:
        with open(wsgi_path, 'r') as f:
            content = f.read()
        
        print(f"📏 File size: {len(content)} characters")
        
        # Check for key elements
        if 'from app import app as application' in content:
            print("✅ Contains 'from app import app as application'")
        else:
            print("❌ Missing 'from app import app as application'")
        
        if 'application =' in content:
            print("✅ Contains 'application ='")
        else:
            print("❌ Missing 'application ='")
        
        if '/home/adamcordova/AGTDesigner' in content:
            print("✅ Contains correct project path")
        else:
            print("❌ Missing correct project path")
        
        # Show first few lines
        lines = content.split('\n')[:10]
        print("📄 First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {line}")
            
    except Exception as e:
        print(f"❌ Error reading WSGI file: {e}")
        return False
    
    return True

def test_app_import():
    """Test if we can import the app"""
    print("\n🔍 Testing app import...")
    
    # Add project directory to path
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Add user site-packages
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
    
    try:
        from app import app
        print("✅ App imported successfully")
        
        # Test app configuration
        print(f"📁 Upload folder: {app.config.get('UPLOAD_FOLDER', 'Not set')}")
        print(f"🔑 Secret key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_pythonanywhere_config():
    """Check PythonAnywhere specific configuration"""
    print("\n🌐 Checking PythonAnywhere configuration...")
    
    # Check if we're on PythonAnywhere
    current_dir = os.getcwd()
    if 'pythonanywhere' in current_dir.lower() or '/home/' in current_dir:
        print("✅ Running on PythonAnywhere")
    else:
        print("⚠️  Not running on PythonAnywhere")
    
    # Check environment variables
    pythonanywhere_site = os.environ.get('PYTHONANYWHERE_SITE')
    if pythonanywhere_site:
        print(f"✅ PYTHONANYWHERE_SITE: {pythonanywhere_site}")
    else:
        print("❌ PYTHONANYWHERE_SITE not set")
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if we can access the project directory
    project_dir = '/home/adamcordova/AGTDesigner'
    if os.path.exists(project_dir):
        print(f"✅ Project directory exists: {project_dir}")
        
        # Check key files
        key_files = ['app.py', 'wsgi.py', 'requirements.txt']
        for file in key_files:
            file_path = os.path.join(project_dir, file)
            if os.path.exists(file_path):
                print(f"✅ {file} exists")
            else:
                print(f"❌ {file} missing")
    else:
        print(f"❌ Project directory missing: {project_dir}")

def main():
    print("🚀 WSGI Loading Debug Tool")
    print("=" * 50)
    
    # Test WSGI file directly
    wsgi_ok = test_wsgi_directly()
    
    # Check WSGI content
    content_ok = check_wsgi_content()
    
    # Test app import
    app_ok = test_app_import()
    
    # Check PythonAnywhere config
    check_pythonanywhere_config()
    
    print("\n📋 Summary:")
    print(f"WSGI file execution: {'✅' if wsgi_ok else '❌'}")
    print(f"WSGI content: {'✅' if content_ok else '❌'}")
    print(f"App import: {'✅' if app_ok else '❌'}")
    
    if wsgi_ok and content_ok and app_ok:
        print("\n🎉 All tests passed! WSGI should be working.")
        print("💡 If page still won't load:")
        print("1. Check PythonAnywhere Web tab error logs")
        print("2. Verify WSGI file path in web app configuration")
        print("3. Try reloading the web app")
        print("4. Check if there are any JavaScript errors in browser")
    else:
        print("\n❌ Some tests failed!")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
