#!/usr/bin/env python3
import sys
import os

# This WSGI file will help us debug and find the correct path
print("🔍 DEBUGGING PYTHONANYWHERE WSGI CONFIGURATION")
print("=" * 50)

# Get the current WSGI file location
wsgi_file = os.path.abspath(__file__)
wsgi_dir = os.path.dirname(wsgi_file)
print(f"📁 WSGI file location: {wsgi_file}")
print(f"📂 WSGI directory: {wsgi_dir}")

# List all files in the WSGI directory
try:
    files_in_wsgi_dir = os.listdir(wsgi_dir)
    print(f"📄 Files in WSGI directory: {files_in_wsgi_dir[:10]}")
except Exception as e:
    print(f"❌ Cannot list WSGI directory: {e}")

# Check if app.py exists in WSGI directory
app_path_in_wsgi = os.path.join(wsgi_dir, 'app.py')
if os.path.exists(app_path_in_wsgi):
    print(f"✅ Found app.py in WSGI directory: {app_path_in_wsgi}")
    project_home = wsgi_dir
else:
    print(f"❌ No app.py in WSGI directory")
    
    # Try to find app.py in common locations
    print("🔍 Searching for app.py in common locations...")
    
    # Get the home directory
    home_dir = os.path.expanduser('~')
    print(f"🏠 Home directory: {home_dir}")
    
    # Search in home directory and subdirectories
    found_app = False
    for root, dirs, files in os.walk(home_dir):
        if 'app.py' in files:
            app_location = os.path.join(root, 'app.py')
            print(f"✅ Found app.py at: {app_location}")
            project_home = root
            found_app = True
            break
        # Limit search depth to avoid too much scanning
        if root.count(os.sep) - home_dir.count(os.sep) > 2:
            dirs[:] = []  # Don't go deeper
    
    if not found_app:
        print("❌ Could not find app.py anywhere!")
        print("💡 You need to upload your app.py file to PythonAnywhere")
        # Use a default location
        project_home = wsgi_dir
        print(f"⚠️  Using WSGI directory as fallback: {project_home}")

print(f"🎯 Using project home: {project_home}")

# Add the project directory to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)
    print(f"✅ Added to Python path: {project_home}")

# Change to the project directory
try:
    os.chdir(project_home)
    print(f"✅ Successfully changed to: {project_home}")
    
    # List files in the project directory
    project_files = os.listdir('.')
    print(f"📄 Files in project directory: {project_files[:10]}")
    
except Exception as e:
    print(f"❌ Failed to change directory: {e}")

# Try to import the Flask app
print("🔄 Attempting to import Flask app...")
try:
    from app import app as application
    print("✅ Successfully imported Flask app!")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    print("💡 Make sure app.py exists and contains a Flask app instance named 'app'")
    raise e

print("🎉 WSGI configuration completed successfully!")
