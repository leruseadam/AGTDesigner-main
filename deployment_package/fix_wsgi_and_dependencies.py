#!/usr/bin/env python3
"""
Fix PythonAnywhere WSGI File Configuration
Ensures the WSGI file is using the correct configuration
"""

import os
import shutil

def fix_wsgi_file():
    """Fix the WSGI file to use the correct configuration"""
    
    print("🔧 Fixing PythonAnywhere WSGI File Configuration...")
    print("=" * 55)
    
    # Source WSGI file (our correct one)
    source_wsgi = "/home/adamcordova/AGTDesigner/wsgi_pythonanywhere_python311.py"
    
    # Target WSGI file (the one PythonAnywhere uses)
    target_wsgi = "/var/www/www_agtpricetags_com_wsgi.py"
    
    print(f"📁 Source WSGI: {source_wsgi}")
    print(f"📁 Target WSGI: {target_wsgi}")
    
    # Check if source file exists
    if not os.path.exists(source_wsgi):
        print(f"❌ Source WSGI file not found: {source_wsgi}")
        return False
    
    # Check if target file exists
    if not os.path.exists(target_wsgi):
        print(f"❌ Target WSGI file not found: {target_wsgi}")
        return False
    
    try:
        # Create backup of target file
        backup_file = target_wsgi + '.backup'
        shutil.copy2(target_wsgi, backup_file)
        print(f"✅ Created backup: {backup_file}")
        
        # Copy our correct WSGI file to the target location
        shutil.copy2(source_wsgi, target_wsgi)
        print("✅ WSGI file updated successfully!")
        
        # Verify the update
        with open(target_wsgi, 'r') as f:
            content = f.read()
        
        # Check for key elements
        checks = [
            ('adamcordova-4822.postgres.pythonanywhere-services.com', 'PostgreSQL host'),
            ('os.environ[\'DB_HOST\']', 'Database host environment variable'),
            ('os.environ[\'DB_NAME\']', 'Database name environment variable'),
            ('os.environ[\'DB_USER\']', 'Database user environment variable'),
            ('os.environ[\'DB_PASSWORD\']', 'Database password environment variable'),
            ('os.environ[\'DB_PORT\']', 'Database port environment variable'),
            ('from app import app', 'App import statement'),
            ('application = app', 'WSGI application assignment')
        ]
        
        print("\n🔍 Verifying WSGI file content:")
        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_good = False
        
        if all_good:
            print("\n🎉 WSGI file is correctly configured!")
            return True
        else:
            print("\n⚠️ Some elements are missing from WSGI file")
            return False
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {target_wsgi}")
        print("💡 You may need to run this with sudo")
        return False
    except Exception as e:
        print(f"❌ Error updating WSGI file: {e}")
        return False

def install_missing_dependencies():
    """Install missing dependencies"""
    print("\n📦 Installing Missing Dependencies...")
    print("=" * 40)
    
    try:
        import subprocess
        
        # Install python-docx
        print("🔄 Installing python-docx...")
        result = subprocess.run(['pip', 'install', 'python-docx'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ python-docx installed successfully")
            return True
        else:
            print(f"❌ Error installing python-docx: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_app_after_fixes():
    """Test the app after applying fixes"""
    print("\n🧪 Testing App After Fixes...")
    print("=" * 35)
    
    try:
        import sys
        sys.path.insert(0, os.getcwd())
        
        # Set environment variables
        os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
        os.environ['DB_NAME'] = 'postgres'
        os.environ['DB_USER'] = 'super'
        os.environ['DB_PASSWORD'] = '193154life'
        os.environ['DB_PORT'] = '14822'
        
        # Test imports
        print("🔄 Testing imports...")
        import flask
        import pandas
        import openpyxl
        import docx  # This should work now
        import PIL
        import psycopg2
        import qrcode
        import requests
        import fuzzywuzzy
        
        print("✅ All imports successful")
        
        # Test app import
        print("🔄 Testing app import...")
        from app import app
        
        print("✅ App imported successfully")
        
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            return True
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 PythonAnywhere WSGI and Dependencies Fix")
    print("=" * 50)
    
    # Install missing dependencies
    deps_ok = install_missing_dependencies()
    
    # Fix WSGI file
    wsgi_ok = fix_wsgi_file()
    
    # Test app
    app_ok = test_app_after_fixes()
    
    # Summary
    print("\n📊 Fix Summary:")
    print("=" * 20)
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"WSGI File: {'✅' if wsgi_ok else '❌'}")
    print(f"App Test: {'✅' if app_ok else '❌'}")
    
    print("\n💡 Next Steps:")
    if deps_ok and wsgi_ok and app_ok:
        print("🎉 All fixes applied successfully!")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click Reload button")
        print("3. Wait 60 seconds")
        print("4. Test your app")
    else:
        print("⚠️ Some fixes failed")
        print("1. Check the error messages above")
        print("2. Try running the fixes manually")
        print("3. Check PythonAnywhere error logs")

if __name__ == "__main__":
    main()
