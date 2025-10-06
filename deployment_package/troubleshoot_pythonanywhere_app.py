#!/usr/bin/env python3
"""
PythonAnywhere App Troubleshooting Script
Diagnoses why the app won't load and provides fixes
"""

import os
import sys
import traceback
import importlib.util

def check_environment():
    """Check PythonAnywhere environment"""
    print("🔍 Checking PythonAnywhere Environment...")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if we're on PythonAnywhere
    is_pythonanywhere = 'pythonanywhere.com' in os.environ.get('HTTP_HOST', '') or 'PYTHONANYWHERE' in os.environ
    print(f"🌐 PythonAnywhere detected: {'✅' if is_pythonanywhere else '❌'}")
    
    # Check working directory
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check if app files exist
    app_files = ['app.py', 'wsgi_pythonanywhere_python311.py', 'requirements.txt']
    for file in app_files:
        exists = os.path.exists(file)
        print(f"📄 {file}: {'✅' if exists else '❌'}")
    
    print()

def check_dependencies():
    """Check if all dependencies are installed"""
    print("📦 Checking Dependencies...")
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
    else:
        print("\n✅ All required packages are installed")
    
    print()
    return missing_packages

def check_database_config():
    """Check database configuration"""
    print("🐘 Checking Database Configuration...")
    print("=" * 40)
    
    # Check environment variables
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    missing_env_vars = []
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if var == 'DB_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_env_vars.append(var)
    
    if missing_env_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_env_vars)}")
        print("💡 Set them in your WSGI file or run the database connection test")
    else:
        print("\n✅ All database environment variables are set")
    
    print()
    return missing_env_vars

def test_app_import():
    """Test if the app can be imported"""
    print("🧪 Testing App Import...")
    print("=" * 25)
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test importing the app
        print("🔄 Importing app...")
        from app import app
        print("✅ App imported successfully")
        
        # Test if app is a Flask app
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
        else:
            print("❌ App is not a valid Flask application")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

def test_wsgi_config():
    """Test WSGI configuration"""
    print("⚙️ Testing WSGI Configuration...")
    print("=" * 35)
    
    wsgi_file = 'wsgi_pythonanywhere_python311.py'
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file {wsgi_file} not found")
        return False
    
    try:
        # Read WSGI file
        with open(wsgi_file, 'r') as f:
            wsgi_content = f.read()
        
        # Check for required elements
        required_elements = [
            'application',
            'from app import app',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_PORT'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element in wsgi_content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                missing_elements.append(element)
        
        if missing_elements:
            print(f"\n⚠️ Missing WSGI elements: {', '.join(missing_elements)}")
            return False
        else:
            print("\n✅ WSGI configuration looks correct")
            return True
            
    except Exception as e:
        print(f"❌ Error reading WSGI file: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🔗 Testing Database Connection...")
    print("=" * 35)
    
    try:
        import psycopg2
        
        # Get database config
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'agt_designer'),
            'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        print("🔄 Attempting database connection...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT COUNT(*) FROM products;")
        count = cur.fetchone()[0]
        print(f"✅ Database connection successful - {count} products found")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def provide_fixes():
    """Provide specific fixes based on issues found"""
    print("🔧 Recommended Fixes...")
    print("=" * 25)
    
    print("1. 📥 Update your code:")
    print("   git pull origin main")
    print()
    
    print("2. 🔧 Install missing dependencies:")
    print("   pip install -r requirements.txt")
    print()
    
    print("3. 🐘 Fix database connection:")
    print("   python test_pythonanywhere_database_connection.py")
    print()
    
    print("4. ⚙️ Check WSGI file:")
    print("   - Ensure wsgi_pythonanywhere_python311.py is selected in Web tab")
    print("   - Check that environment variables are set")
    print()
    
    print("5. 🔄 Reload web app:")
    print("   - Go to PythonAnywhere Web tab")
    print("   - Click Reload button")
    print("   - Wait 30-60 seconds")
    print()
    
    print("6. 📋 Check error logs:")
    print("   - Go to PythonAnywhere Web tab")
    print("   - Click Error log link")
    print("   - Look for specific error messages")

def main():
    """Main troubleshooting function"""
    print("🚀 PythonAnywhere App Troubleshooting")
    print("=" * 50)
    print()
    
    # Run all checks
    env_ok = check_environment()
    deps_ok = len(check_dependencies()) == 0
    db_config_ok = len(check_database_config()) == 0
    app_import_ok = test_app_import()
    wsgi_ok = test_wsgi_config()
    db_connection_ok = test_database_connection()
    
    # Summary
    print("📊 Troubleshooting Summary:")
    print("=" * 30)
    print(f"Environment: {'✅' if env_ok else '❌'}")
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"Database Config: {'✅' if db_config_ok else '❌'}")
    print(f"App Import: {'✅' if app_import_ok else '❌'}")
    print(f"WSGI Config: {'✅' if wsgi_ok else '❌'}")
    print(f"Database Connection: {'✅' if db_connection_ok else '❌'}")
    
    print()
    
    if all([env_ok, deps_ok, db_config_ok, app_import_ok, wsgi_ok, db_connection_ok]):
        print("🎉 All checks passed! Your app should be working.")
        print("💡 If it's still not loading, try reloading the web app.")
    else:
        print("⚠️ Some issues found. Follow the recommended fixes below:")
        print()
        provide_fixes()

if __name__ == "__main__":
    main()
