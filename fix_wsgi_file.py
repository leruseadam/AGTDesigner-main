#!/usr/bin/env python3.11
"""
Script to help identify and fix the current WSGI file on PythonAnywhere
"""

import os
import sys

def find_wsgi_files():
    """Find all WSGI files in common locations"""
    print("🔍 Searching for WSGI files...")
    
    # Common WSGI file locations
    locations = [
        '/var/www',
        '/home/adamcordova',
        '/home/adamcordova/AGTDesigner'
    ]
    
    wsgi_files = []
    
    for location in locations:
        if os.path.exists(location):
            print(f"✅ Checking: {location}")
            try:
                for root, dirs, files in os.walk(location):
                    for file in files:
                        if file.endswith('.py') and ('wsgi' in file.lower() or 'app' in file.lower()):
                            full_path = os.path.join(root, file)
                            wsgi_files.append(full_path)
                            print(f"   📄 Found: {full_path}")
            except PermissionError:
                print(f"   ❌ Permission denied: {location}")
        else:
            print(f"❌ Not found: {location}")
    
    return wsgi_files

def check_wsgi_content(file_path):
    """Check the content of a WSGI file"""
    print(f"\n📋 Checking content of: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        print(f"   📏 File size: {len(content)} characters")
        
        # Check for key indicators
        if 'from app import app' in content:
            print("   ✅ Contains 'from app import app'")
        else:
            print("   ❌ Missing 'from app import app'")
            
        if 'application' in content:
            print("   ✅ Contains 'application' variable")
        else:
            print("   ❌ Missing 'application' variable")
            
        if '/home/adamcordova/AGTDesigner' in content:
            print("   ✅ Contains correct project path")
        else:
            print("   ❌ Missing correct project path")
            
        # Show first few lines
        lines = content.split('\n')[:10]
        print("   📄 First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"      {i:2d}: {line}")
            
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")

def create_fixed_wsgi():
    """Create a fixed WSGI file content"""
    print("\n🔧 Creating fixed WSGI content...")
    
    wsgi_content = '''#!/usr/bin/env python3.11
"""
Fixed WSGI configuration for PythonAnywhere
"""

import os
import sys
import logging

# Configure the project directory
project_dir = '/home/adamcordova/AGTDesigner'

# Verify directory exists and add to Python path
if os.path.exists(project_dir):
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    print(f"✅ Project directory found: {project_dir}")
else:
    print(f"❌ Project directory not found: {project_dir}")
    # Fallback to current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

# Add user site-packages to Python path
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging
logging.basicConfig(level=logging.ERROR)

try:
    # Import the Flask application
    from app import app as application
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False
    )
    
    print("✅ WSGI application loaded successfully")
    
except Exception as e:
    print(f"❌ Error loading WSGI application: {e}")
    import traceback
    traceback.print_exc()
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False)
'''
    
    return wsgi_content

def main():
    print("🚀 PythonAnywhere WSGI File Diagnostic Tool")
    print("=" * 50)
    
    # Find WSGI files
    wsgi_files = find_wsgi_files()
    
    if not wsgi_files:
        print("\n❌ No WSGI files found!")
        return
    
    # Check each WSGI file
    for wsgi_file in wsgi_files:
        check_wsgi_content(wsgi_file)
    
    # Create fixed content
    fixed_content = create_fixed_wsgi()
    
    print("\n📝 Fixed WSGI content:")
    print("=" * 50)
    print(fixed_content)
    
    print("\n💡 Instructions:")
    print("1. Copy the fixed WSGI content above")
    print("2. Go to your PythonAnywhere Web tab")
    print("3. Edit your WSGI file")
    print("4. Replace the entire content with the fixed version")
    print("5. Save and reload your web app")

if __name__ == "__main__":
    main()
