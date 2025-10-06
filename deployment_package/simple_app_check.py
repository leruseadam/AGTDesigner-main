#!/usr/bin/env python3
"""
Simple PythonAnywhere App Check
Basic checks to see what's wrong
"""

import os
import sys

def main():
    print("🔍 Simple PythonAnywhere App Check")
    print("=" * 40)
    
    # Check 1: Are we in the right directory?
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check 2: Does app.py exist?
    if os.path.exists('app.py'):
        print("✅ app.py exists")
    else:
        print("❌ app.py NOT FOUND")
        return
    
    # Check 3: Does WSGI file exist?
    wsgi_file = 'wsgi_pythonanywhere_python311.py'
    if os.path.exists(wsgi_file):
        print(f"✅ {wsgi_file} exists")
    else:
        print(f"❌ {wsgi_file} NOT FOUND")
        return
    
    # Check 4: Can we import Flask?
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return
    
    # Check 5: Can we import psycopg2?
    try:
        import psycopg2
        print("✅ psycopg2 imported successfully")
    except ImportError as e:
        print(f"❌ psycopg2 import failed: {e}")
        return
    
    # Check 6: Environment variables
    print("\n🔧 Environment Variables:")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'DB_PASSWORD':
            value = '*' * len(value) if value != 'NOT SET' else 'NOT SET'
        print(f"   {var}: {value}")
    
    # Check 7: Try to import the app
    print("\n🧪 Testing app import...")
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        print("✅ App imported successfully")
        
        # Check if it's a Flask app
        if hasattr(app, 'route'):
            print("✅ App is a valid Flask application")
        else:
            print("❌ App is not a valid Flask application")
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        print("\n🔍 Full error:")
        import traceback
        traceback.print_exc()
    
    print("\n💡 Next steps:")
    print("1. If app import failed, check the error above")
    print("2. If environment variables are missing, they need to be set")
    print("3. If Flask/psycopg2 failed, run: pip install -r requirements.txt")
    print("4. Check your PythonAnywhere Web tab error logs")

if __name__ == "__main__":
    main()
