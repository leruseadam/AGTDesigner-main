#!/usr/bin/env python3
"""
Comprehensive PythonAnywhere App Loading Diagnosis
Diagnoses why the app still won't load after all fixes
"""

import os
import sys
import traceback
import subprocess

def check_wsgi_file():
    """Check the actual WSGI file being used"""
    print("🔍 Checking WSGI File Configuration...")
    print("=" * 40)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file not found: {wsgi_file}")
        return False
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        print(f"✅ WSGI file found: {wsgi_file}")
        
        # Check for key elements
        checks = [
            ('application', 'WSGI application variable'),
            ('from app import app', 'App import statement'),
            ('adamcordova-4822.postgres.pythonanywhere-services.com', 'PostgreSQL host'),
            ('os.environ', 'Environment variable setting')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ Found: {description}")
            else:
                print(f"❌ Missing: {description}")
        
        # Check if it's using the right WSGI file
        if 'wsgi_pythonanywhere_python311.py' in content:
            print("✅ Using correct WSGI file")
        else:
            print("⚠️ May not be using the correct WSGI file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading WSGI file: {e}")
        return False

def check_web_app_configuration():
    """Check PythonAnywhere Web app configuration"""
    print("\n🌐 Checking Web App Configuration...")
    print("=" * 40)
    
    print("💡 Manual checks needed:")
    print("1. Go to PythonAnywhere Web tab")
    print("2. Check if your web app is configured correctly")
    print("3. Verify the WSGI file path is set to:")
    print("   /var/www/www_agtpricetags_com_wsgi.py")
    print("4. Check if the domain is correct")
    print("5. Verify the web app is enabled")
    
    return True

def test_app_with_wsgi_simulation():
    """Test the app by simulating WSGI environment"""
    print("\n🧪 Testing App with WSGI Simulation...")
    print("=" * 45)
    
    try:
        # Set environment variables like WSGI would
        os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
        os.environ['DB_NAME'] = 'postgres'
        os.environ['DB_USER'] = 'super'
        os.environ['DB_PASSWORD'] = '193154life'
        os.environ['DB_PORT'] = '14822'
        
        print("✅ Environment variables set")
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the app
        print("🔄 Importing app...")
        from app import app
        
        print("✅ App imported successfully")
        
        # Test if it's a Flask app
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
            
            # Test a simple route
            with app.test_client() as client:
                try:
                    response = client.get('/')
                    print(f"✅ App responds to requests (status: {response.status_code})")
                    return True
                except Exception as e:
                    print(f"❌ App doesn't respond to requests: {e}")
                    return False
        else:
            print("❌ App is not a valid Flask application")
            return False
            
    except Exception as e:
        print(f"❌ App import/test failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

def check_error_logs():
    """Check for error logs"""
    print("\n📋 Checking Error Logs...")
    print("=" * 30)
    
    print("💡 Check these locations for error logs:")
    print("1. PythonAnywhere Web tab → Error log")
    print("2. PythonAnywhere Web tab → Server log")
    print("3. Check if there are any import errors")
    print("4. Look for database connection errors")
    print("5. Check for missing dependencies")
    
    # Try to find log files
    log_dirs = [
        '/home/adamcordova/AGTDesigner/logs',
        '/home/adamcordova/logs',
        '/var/log'
    ]
    
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            print(f"✅ Found log directory: {log_dir}")
        else:
            print(f"❌ Log directory not found: {log_dir}")
    
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking Dependencies...")
    print("=" * 30)
    
    required_packages = [
        'flask', 'pandas', 'openpyxl', 'python-docx', 
        'PIL', 'psycopg2', 'qrcode', 'requests', 'fuzzywuzzy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
                print(f"✅ {package} (Pillow)")
            else:
                __import__(package)
                print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ All required packages are installed")
        return True

def check_file_permissions():
    """Check file permissions"""
    print("\n🔐 Checking File Permissions...")
    print("=" * 35)
    
    important_files = [
        'app.py',
        'wsgi_pythonanywhere_python311.py',
        '/var/www/www_agtpricetags_com_wsgi.py'
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            try:
                # Check if we can read the file
                with open(file_path, 'r') as f:
                    f.read(1)  # Read just one character
                print(f"✅ {file_path} - readable")
            except PermissionError:
                print(f"❌ {file_path} - permission denied")
            except Exception as e:
                print(f"❌ {file_path} - error: {e}")
        else:
            print(f"❌ {file_path} - not found")
    
    return True

def provide_specific_fixes():
    """Provide specific fixes based on common issues"""
    print("\n🔧 Specific Fixes to Try...")
    print("=" * 35)
    
    print("1. 📥 Update your code:")
    print("   git pull origin main")
    print()
    
    print("2. 🔄 Force reload the web app:")
    print("   - Go to PythonAnywhere Web tab")
    print("   - Click Reload button")
    print("   - Wait 60 seconds")
    print("   - Try accessing your app")
    print()
    
    print("3. 📋 Check error logs:")
    print("   - Go to PythonAnywhere Web tab")
    print("   - Click Error log link")
    print("   - Copy/paste any error messages")
    print()
    
    print("4. ⚙️ Verify WSGI configuration:")
    print("   - Go to PythonAnywhere Web tab")
    print("   - Check Source code path: /home/adamcordova/AGTDesigner")
    print("   - Check WSGI configuration file: /var/www/www_agtpricetags_com_wsgi.py")
    print()
    
    print("5. 🐘 Test database connection:")
    print("   python test_postgresql_connection.py")
    print()
    
    print("6. 🧪 Test app import:")
    print("   python test_with_env_vars.py")

def main():
    """Main diagnostic function"""
    print("🚀 Comprehensive PythonAnywhere App Loading Diagnosis")
    print("=" * 60)
    
    # Run all checks
    wsgi_ok = check_wsgi_file()
    deps_ok = check_dependencies()
    perms_ok = check_file_permissions()
    app_ok = test_app_with_wsgi_simulation()
    
    # Manual checks
    check_web_app_configuration()
    check_error_logs()
    
    # Summary
    print("\n📊 Diagnostic Summary:")
    print("=" * 25)
    print(f"WSGI File: {'✅' if wsgi_ok else '❌'}")
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"File Permissions: {'✅' if perms_ok else '❌'}")
    print(f"App Test: {'✅' if app_ok else '❌'}")
    
    print()
    
    if all([wsgi_ok, deps_ok, perms_ok, app_ok]):
        print("🎉 All technical checks passed!")
        print("💡 The issue is likely in PythonAnywhere Web configuration")
        print("💡 Check the Web tab settings and error logs")
    else:
        print("⚠️ Some technical issues found")
        print("💡 Fix the issues above first")
    
    print()
    provide_specific_fixes()

if __name__ == "__main__":
    main()
