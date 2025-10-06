#!/usr/bin/env python3
"""
Fix Missing WSGI Application Assignment
Adds the missing 'application = app' line to the WSGI file
"""

import os

def fix_wsgi_application_assignment():
    """Fix the missing WSGI application assignment"""
    
    print("🔧 Fixing Missing WSGI Application Assignment...")
    print("=" * 50)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file not found: {wsgi_file}")
        return False
    
    try:
        # Read the current WSGI file
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        print("✅ WSGI file found and readable")
        
        # Check if application assignment already exists
        if 'application = app' in content:
            print("✅ WSGI application assignment already exists")
            return True
        
        # Check if 'from app import app' exists
        if 'from app import app' not in content:
            print("❌ 'from app import app' not found in WSGI file")
            return False
        
        print("✅ Found 'from app import app' statement")
        
        # Add the missing application assignment
        # Find where to add it (after the import)
        lines = content.split('\n')
        insert_line = -1
        
        for i, line in enumerate(lines):
            if 'from app import app' in line:
                insert_line = i + 1
                break
        
        if insert_line == -1:
            print("❌ Could not find suitable place to add application assignment")
            return False
        
        # Insert the application assignment
        lines.insert(insert_line, 'application = app')
        
        # Write the updated content
        updated_content = '\n'.join(lines)
        
        # Create backup first
        backup_file = wsgi_file + '.backup'
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✅ Created backup: {backup_file}")
        
        # Write the updated file
        with open(wsgi_file, 'w') as f:
            f.write(updated_content)
        
        print("✅ WSGI file updated with application assignment!")
        
        # Verify the change
        with open(wsgi_file, 'r') as f:
            new_content = f.read()
        
        if 'application = app' in new_content:
            print("✅ Application assignment verified")
            return True
        else:
            print("❌ Application assignment not found after update")
            return False
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {wsgi_file}")
        print("💡 You may need to run this with sudo")
        return False
    except Exception as e:
        print(f"❌ Error updating WSGI file: {e}")
        return False

def test_wsgi_file():
    """Test the WSGI file to make sure it's valid"""
    print("\n🧪 Testing WSGI File...")
    print("=" * 25)
    
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'from app import app',
            'application = app',
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
            print("\n🎉 WSGI file is correctly configured!")
            return True
        else:
            print("\n⚠️ Some elements are missing from WSGI file")
            return False
        
    except Exception as e:
        print(f"❌ Error testing WSGI file: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 Fix Missing WSGI Application Assignment")
    print("=" * 45)
    
    # Fix the WSGI file
    wsgi_fixed = fix_wsgi_application_assignment()
    
    # Test the WSGI file
    wsgi_tested = test_wsgi_file()
    
    # Summary
    print("\n📊 Fix Summary:")
    print("=" * 20)
    print(f"WSGI Assignment Fixed: {'✅' if wsgi_fixed else '❌'}")
    print(f"WSGI File Valid: {'✅' if wsgi_tested else '❌'}")
    
    print("\n💡 Next Steps:")
    if wsgi_fixed and wsgi_tested:
        print("🎉 WSGI file is now correctly configured!")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click Reload button")
        print("3. Wait 60 seconds")
        print("4. Test your app - it should work now!")
    else:
        print("⚠️ WSGI fix failed")
        print("1. Check the error messages above")
        print("2. Try running with sudo if permission denied")
        print("3. Check PythonAnywhere error logs")

if __name__ == "__main__":
    main()
