#!/usr/bin/env python3.11
"""
Test WSGI loading and Flask app initialization
"""

import os
import sys
import logging

print("=== WSGI Loading Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths

# Test directory structure
print("\n=== Directory Structure ===")
project_dir = '/home/adamcordova/AGTDesigner'
print(f"Project directory exists: {os.path.exists(project_dir)}")

if os.path.exists(project_dir):
    print(f"Project directory contents: {os.listdir(project_dir)[:10]}...")  # First 10 items
    
    # Check for app.py
    app_file = os.path.join(project_dir, 'app.py')
    print(f"app.py exists: {os.path.exists(app_file)}")
    
    # Check for src directory
    src_dir = os.path.join(project_dir, 'src')
    print(f"src directory exists: {os.path.exists(src_dir)}")
    
    if os.path.exists(src_dir):
        print(f"src contents: {os.listdir(src_dir)}")

# Test Python path setup
print("\n=== Python Path Setup ===")
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    print(f"Added project directory to Python path: {project_dir}")
else:
    print(f"Project directory already in Python path: {project_dir}")

# Test import
print("\n=== Import Test ===")
try:
    from app import app
    print("✅ Successfully imported app")
    
    # Test app configuration
    print(f"App name: {app.name}")
    print(f"App debug mode: {app.debug}")
    print(f"App testing mode: {app.testing}")
    
    # Test routes
    with app.app_context():
        print(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()][:5]}...")
    
    print("✅ Flask app is working correctly")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Available files: {os.listdir('.')}")
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
