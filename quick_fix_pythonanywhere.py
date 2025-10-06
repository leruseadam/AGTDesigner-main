#!/usr/bin/env python3
"""
Quick Fix Script for PythonAnywhere App Loading Issues
Automatically fixes common problems
"""

import os
import sys
import subprocess

def fix_environment_variables():
    """Fix environment variables"""
    print("🔧 Fixing environment variables...")
    
    # Set required environment variables
    env_vars = {
        'DB_HOST': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'DB_NAME': 'postgres',
        'DB_USER': 'super',
        'DB_PASSWORD': '193154life',
        'DB_PORT': '14822'
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value
        print(f"✅ Set {var}")
    
    print("✅ Environment variables fixed")

def install_missing_dependencies():
    """Install missing dependencies"""
    print("📦 Installing missing dependencies...")
    
    try:
        # Install from requirements.txt
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Error installing dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def fix_wsgi_file():
    """Ensure WSGI file has correct configuration"""
    print("⚙️ Checking WSGI file...")
    
    wsgi_file = 'wsgi_pythonanywhere_python311.py'
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file {wsgi_file} not found")
        return False
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Check if environment variables are set
        if 'DB_HOST' in content and 'adamcordova-4822.postgres.pythonanywhere-services.com' in content:
            print("✅ WSGI file has correct database configuration")
            return True
        else:
            print("❌ WSGI file missing database configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error reading WSGI file: {e}")
        return False

def test_basic_imports():
    """Test basic imports"""
    print("🧪 Testing basic imports...")
    
    try:
        import flask
        import pandas
        import psycopg2
        import qrcode
        print("✅ All basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 PythonAnywhere Quick Fix")
    print("=" * 30)
    print()
    
    # Fix environment variables
    fix_environment_variables()
    print()
    
    # Install dependencies
    deps_ok = install_missing_dependencies()
    print()
    
    # Check WSGI file
    wsgi_ok = fix_wsgi_file()
    print()
    
    # Test imports
    imports_ok = test_basic_imports()
    print()
    
    # Summary
    print("📊 Fix Summary:")
    print("=" * 15)
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"WSGI Config: {'✅' if wsgi_ok else '❌'}")
    print(f"Imports: {'✅' if imports_ok else '❌'}")
    
    print()
    
    if deps_ok and wsgi_ok and imports_ok:
        print("🎉 Quick fix completed successfully!")
        print("💡 Next steps:")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click Reload button")
        print("3. Wait 30-60 seconds")
        print("4. Test your app")
    else:
        print("⚠️ Some issues remain. Run the full troubleshooting script:")
        print("python troubleshoot_pythonanywhere_app.py")

if __name__ == "__main__":
    main()
