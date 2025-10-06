#!/usr/bin/env python3
import sys
import os

# Add the project directory to Python path
project_home = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 23'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory
os.chdir(project_home)

# Import the Flask app
try:
    from app import app as application
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    # Try alternative import paths
    try:
        import app
        application = app.app
        print("✅ Successfully imported Flask app (alternative method)")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        raise e2

# Debug information
print(f"Project home: {project_home}")
print(f"Python path: {sys.path[:3]}")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')[:5]}")
