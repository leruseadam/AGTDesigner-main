#!/usr/bin/env python3
import sys
import os

# First, let's find the correct directory
# Try common PythonAnywhere directory patterns
possible_paths = [
    '/home/yourusername',
    '/home/yourusername/AGTDesigner', 
    '/home/yourusername/AGTDesigner_deployment',
    '/home/yourusername/mysite',
    '/home/yourusername/web',
    os.path.dirname(os.path.abspath(__file__))  # Current WSGI file directory
]

print("🔍 Searching for the correct project directory...")

project_home = None
for path in possible_paths:
    if os.path.exists(path):
        # Check if app.py exists in this directory
        app_path = os.path.join(path, 'app.py')
        if os.path.exists(app_path):
            project_home = path
            print(f"✅ Found app.py in: {path}")
            break
        else:
            print(f"📁 Directory exists but no app.py: {path}")

if not project_home:
    # If we can't find it, use the current directory
    project_home = os.path.dirname(os.path.abspath(__file__))
    print(f"⚠️  Using current directory: {project_home}")

# Add the project directory to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory
try:
    os.chdir(project_home)
    print(f"✅ Successfully changed to: {project_home}")
except Exception as e:
    print(f"❌ Failed to change directory: {e}")
    # Don't change directory if it fails

# Debug information
print(f"📁 Project home: {project_home}")
print(f"🐍 Python path: {sys.path[:3]}")
print(f"📂 Current working directory: {os.getcwd()}")
print(f"📄 Files in current directory: {os.listdir('.')[:10]}")

# Import the Flask app
try:
    from app import app as application
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    # Try alternative import methods
    try:
        import app
        application = app.app
        print("✅ Successfully imported Flask app (alternative method)")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        # Try importing from the current directory
        try:
            sys.path.insert(0, os.getcwd())
            from app import app as application
            print("✅ Successfully imported Flask app (from current directory)")
        except ImportError as e3:
            print(f"❌ All import methods failed: {e3}")
            raise e3
