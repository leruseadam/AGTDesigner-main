#!/usr/bin/env python3
"""
Fix PythonAnywhere BlockingIOError Logging Issue
Updates WSGI file to use production logging configuration
"""

import os

def fix_logging_in_wsgi():
    """Fix the BlockingIOError logging issue in WSGI file"""
    
    print("🔧 Fixing PythonAnywhere BlockingIOError Logging Issue...")
    print("=" * 60)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file not found: {wsgi_file}")
        return False
    
    try:
        # Read the current WSGI file
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        print("✅ WSGI file found and readable")
        
        # Check if production logging is already configured
        if 'configure_production_logging' in content:
            print("✅ Production logging already configured")
            return True
        
        print("🔧 Adding production logging configuration...")
        
        # Production logging configuration to add
        logging_config = '''
# Configure production logging to prevent BlockingIOError
try:
    from pythonanywhere_logging_config import configure_production_logging
    configure_production_logging()
    print("✅ Production logging configured successfully")
except ImportError:
    # Fallback logging configuration
    import logging
    import sys
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    print("✅ Fallback logging configured")

# Suppress verbose logging from libraries
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'psycopg2']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
'''
        
        # Find where to insert the logging configuration
        # Look for the import section
        lines = content.split('\n')
        insert_line = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_line = i
        
        if insert_line == -1:
            print("❌ Could not find suitable place to insert logging configuration")
            return False
        
        # Insert logging configuration after the last import
        insert_line += 1
        
        # Add the logging configuration
        logging_lines = logging_config.strip().split('\n')
        for logging_line in logging_lines:
            lines.insert(insert_line, logging_line)
            insert_line += 1
        
        # Write the updated content
        updated_content = '\n'.join(lines)
        
        # Create backup first
        backup_file = wsgi_file + '.backup.logging'
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✅ Created backup: {backup_file}")
        
        # Write the updated file
        with open(wsgi_file, 'w') as f:
            f.write(updated_content)
        
        print("✅ WSGI file updated with production logging configuration!")
        
        # Verify the change
        with open(wsgi_file, 'r') as f:
            new_content = f.read()
        
        if 'configure_production_logging' in new_content:
            print("✅ Production logging configuration verified")
            return True
        else:
            print("❌ Production logging configuration not found after update")
            return False
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {wsgi_file}")
        print("💡 You may need to run this with sudo")
        return False
    except Exception as e:
        print(f"❌ Error updating WSGI file: {e}")
        return False

def check_logging_config_file():
    """Check if the logging configuration file exists"""
    print("\n📋 Checking Logging Configuration File...")
    print("=" * 45)
    
    logging_file = "/home/adamcordova/AGTDesigner/pythonanywhere_logging_config.py"
    
    if os.path.exists(logging_file):
        print(f"✅ Logging config file found: {logging_file}")
        return True
    else:
        print(f"❌ Logging config file not found: {logging_file}")
        print("💡 The file should exist in your project directory")
        return False

def test_wsgi_file():
    """Test the WSGI file to make sure it's valid"""
    print("\n🧪 Testing Updated WSGI File...")
    print("=" * 35)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'from app import app',
            'application = app',
            'configure_production_logging',
            'os.environ[\'DB_HOST\']',
            'adamcordova-4822.postgres.pythonanywhere-services.com'
        ]
        
        all_good = True
        for element in required_elements:
            if element in content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                all_good = False
        
        if all_good:
            print("\n🎉 WSGI file is correctly configured with logging!")
            return True
        else:
            print("\n⚠️ Some elements are missing from WSGI file")
            return False
        
    except Exception as e:
        print(f"❌ Error testing WSGI file: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 Fix PythonAnywhere BlockingIOError Logging Issue")
    print("=" * 55)
    
    # Check logging config file
    config_exists = check_logging_config_file()
    
    # Fix the WSGI file
    wsgi_fixed = fix_logging_in_wsgi()
    
    # Test the WSGI file
    wsgi_tested = test_wsgi_file()
    
    # Summary
    print("\n📊 Fix Summary:")
    print("=" * 20)
    print(f"Logging Config File: {'✅' if config_exists else '❌'}")
    print(f"WSGI Logging Fixed: {'✅' if wsgi_fixed else '❌'}")
    print(f"WSGI File Valid: {'✅' if wsgi_tested else '❌'}")
    
    print("\n💡 Next Steps:")
    if wsgi_fixed and wsgi_tested:
        print("🎉 WSGI file is now configured with production logging!")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click Reload button")
        print("3. Wait 60 seconds")
        print("4. Test your app - BlockingIOError should be fixed!")
    else:
        print("⚠️ Logging fix failed")
        print("1. Check the error messages above")
        print("2. Try running with sudo if permission denied")
        print("3. Check PythonAnywhere error logs")

if __name__ == "__main__":
    main()
