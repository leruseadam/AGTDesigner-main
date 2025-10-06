#!/usr/bin/env python3.11
"""
Check PythonAnywhere error logs and common issues
"""

import os
import sys
import subprocess

def check_common_issues():
    """Check for common PythonAnywhere issues"""
    print("🔍 Checking common PythonAnywhere issues...")
    
    # Check if we're on PythonAnywhere
    current_dir = os.getcwd()
    if 'pythonanywhere' in current_dir.lower() or '/home/' in current_dir:
        print("✅ Running on PythonAnywhere")
    else:
        print("⚠️  Not running on PythonAnywhere")
        return
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if we can access common directories
    print("\n📁 Checking directory access...")
    
    home_dir = os.path.expanduser('~')
    print(f"   Home directory: {home_dir}")
    
    project_dir = '/home/adamcordova/AGTDesigner'
    if os.path.exists(project_dir):
        print(f"   ✅ Project directory exists: {project_dir}")
        
        # Check key files
        key_files = ['app.py', 'wsgi.py', 'wsgi_minimal.py', 'wsgi_ultra_simple.py']
        for file in key_files:
            file_path = os.path.join(project_dir, file)
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                permissions = oct(stat.st_mode)[-3:]
                print(f"   ✅ {file} exists (permissions: {permissions})")
            else:
                print(f"   ❌ {file} missing")
    else:
        print(f"   ❌ Project directory missing: {project_dir}")
    
    # Check environment variables
    print("\n🌐 Checking environment variables...")
    pythonanywhere_site = os.environ.get('PYTHONANYWHERE_SITE')
    if pythonanywhere_site:
        print(f"   ✅ PYTHONANYWHERE_SITE: {pythonanywhere_site}")
    else:
        print("   ❌ PYTHONANYWHERE_SITE not set")
    
    # Check disk space
    print("\n💾 Checking disk space...")
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024**3)
        print(f"   💽 Free space: {free_gb:.1f} GB")
        
        if free_gb < 1:
            print("   ⚠️  WARNING: Low disk space!")
        else:
            print("   ✅ Sufficient disk space")
    except Exception as e:
        print(f"   ❌ Error checking disk space: {e}")

def check_wsgi_files():
    """Check WSGI files and their content"""
    print("\n📄 Checking WSGI files...")
    
    wsgi_files = [
        '/home/adamcordova/AGTDesigner/wsgi.py',
        '/home/adamcordova/AGTDesigner/wsgi_minimal.py',
        '/home/adamcordova/AGTDesigner/wsgi_ultra_simple.py'
    ]
    
    for wsgi_file in wsgi_files:
        if os.path.exists(wsgi_file):
            print(f"\n📋 {wsgi_file}:")
            
            # Check permissions
            stat = os.stat(wsgi_file)
            permissions = oct(stat.st_mode)[-3:]
            print(f"   Permissions: {permissions}")
            
            if 'x' in permissions:
                print("   ✅ Executable")
            else:
                print("   ❌ Not executable")
            
            # Check content
            try:
                with open(wsgi_file, 'r') as f:
                    content = f.read()
                
                print(f"   Size: {len(content)} characters")
                
                if 'application' in content:
                    print("   ✅ Contains 'application'")
                else:
                    print("   ❌ Missing 'application'")
                
                if 'from app import' in content:
                    print("   ✅ Imports from app")
                else:
                    print("   ℹ️  Doesn't import from app (might be intentional)")
                    
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")

def test_simple_wsgi():
    """Test the ultra-simple WSGI"""
    print("\n🧪 Testing ultra-simple WSGI...")
    
    wsgi_path = '/home/adamcordova/AGTDesigner/wsgi_ultra_simple.py'
    
    if not os.path.exists(wsgi_path):
        print(f"   ❌ Ultra-simple WSGI not found: {wsgi_path}")
        return False
    
    try:
        # Try to import the WSGI file
        import importlib.util
        spec = importlib.util.spec_from_file_location("wsgi_ultra_simple", wsgi_path)
        wsgi_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wsgi_module)
        
        print("   ✅ Ultra-simple WSGI imported successfully")
        
        # Test the application function
        if hasattr(wsgi_module, 'application'):
            print("   ✅ Application function exists")
            return True
        else:
            print("   ❌ Application function missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing ultra-simple WSGI: {e}")
        return False

def main():
    print("🚀 PythonAnywhere Error Log Checker")
    print("=" * 50)
    
    # Check common issues
    check_common_issues()
    
    # Check WSGI files
    check_wsgi_files()
    
    # Test simple WSGI
    wsgi_ok = test_simple_wsgi()
    
    print("\n📋 Summary:")
    print(f"Ultra-simple WSGI: {'✅' if wsgi_ok else '❌'}")
    
    if wsgi_ok:
        print("\n🎉 Ultra-simple WSGI should work!")
        print("💡 Try using wsgi_ultra_simple.py as your WSGI file")
        print("💡 This will confirm if the issue is with your Flask app")
    else:
        print("\n❌ Even ultra-simple WSGI has issues!")
        print("💡 Check PythonAnywhere Web tab error logs")
        print("💡 Verify WSGI file path in web app configuration")

if __name__ == "__main__":
    main()
