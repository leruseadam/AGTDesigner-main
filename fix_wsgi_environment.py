#!/usr/bin/env python3
"""
Fix PythonAnywhere WSGI Environment Variables
Updates the WSGI file to include PostgreSQL environment variables
"""

import os

def fix_wsgi_file():
    """Fix the WSGI file to include environment variables"""
    
    print("🔧 Fixing PythonAnywhere WSGI Environment Variables...")
    print("=" * 55)
    
    # The actual WSGI file path
    wsgi_file = "/var/www/www_agtpricetags_com_wsgi.py"
    
    print(f"📁 WSGI file: {wsgi_file}")
    
    # Check if the file exists
    if not os.path.exists(wsgi_file):
        print(f"❌ WSGI file not found: {wsgi_file}")
        print("💡 Make sure you're running this on PythonAnywhere")
        return False
    
    try:
        # Read the current WSGI file
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        print("✅ WSGI file found and readable")
        
        # Check if environment variables are already set
        env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
        missing_vars = []
        
        for var in env_vars:
            if f"os.environ['{var}']" in content:
                print(f"✅ {var} already set")
            else:
                print(f"❌ {var} missing")
                missing_vars.append(var)
        
        if not missing_vars:
            print("\n🎉 All environment variables are already set!")
            return True
        
        print(f"\n🔧 Adding {len(missing_vars)} missing environment variables...")
        
        # Environment variables to add
        env_additions = [
            "# PostgreSQL Database Configuration",
            "os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'",
            "os.environ['DB_NAME'] = 'postgres'",
            "os.environ['DB_USER'] = 'super'",
            "os.environ['DB_PASSWORD'] = '193154life'",
            "os.environ['DB_PORT'] = '14822'",
            ""
        ]
        
        # Find where to insert the environment variables
        # Look for the import section
        import_section_end = content.find("import sys")
        if import_section_end == -1:
            import_section_end = content.find("import os")
        
        if import_section_end == -1:
            print("❌ Could not find import section to add environment variables")
            return False
        
        # Find the end of the import section
        lines = content.split('\n')
        insert_line = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_line = i
        
        if insert_line == -1:
            print("❌ Could not find suitable place to insert environment variables")
            return False
        
        # Insert environment variables after the last import
        insert_line += 1
        
        # Add the environment variables
        for env_line in env_additions:
            lines.insert(insert_line, env_line)
            insert_line += 1
        
        # Write the updated content
        updated_content = '\n'.join(lines)
        
        # Create a backup first
        backup_file = wsgi_file + '.backup'
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✅ Created backup: {backup_file}")
        
        # Write the updated file
        with open(wsgi_file, 'w') as f:
            f.write(updated_content)
        
        print("✅ WSGI file updated successfully!")
        
        # Verify the changes
        print("\n🔍 Verifying changes...")
        with open(wsgi_file, 'r') as f:
            new_content = f.read()
        
        for var in env_vars:
            if f"os.environ['{var}']" in new_content:
                print(f"✅ {var} now set")
            else:
                print(f"❌ {var} still missing")
        
        print("\n🎉 WSGI file fix completed!")
        print("\n💡 Next steps:")
        print("1. Go to PythonAnywhere Web tab")
        print("2. Click Reload button")
        print("3. Wait 30-60 seconds")
        print("4. Test your app")
        
        return True
        
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {wsgi_file}")
        print("💡 You may need to run this with sudo or contact PythonAnywhere support")
        return False
    except Exception as e:
        print(f"❌ Error fixing WSGI file: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are now set"""
    
    print("\n🧪 Testing Environment Variables...")
    print("=" * 40)
    
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    all_set = True
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if var == 'DB_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    if all_set:
        print("\n🎉 All environment variables are set!")
        return True
    else:
        print("\n⚠️ Some environment variables are missing")
        print("💡 The WSGI file may need to be reloaded")
        return False

def main():
    """Main function"""
    print("🚀 PythonAnywhere WSGI Environment Variables Fix")
    print("=" * 55)
    
    # Fix the WSGI file
    wsgi_fixed = fix_wsgi_file()
    
    if wsgi_fixed:
        # Test environment variables
        env_ok = test_environment_variables()
        
        print("\n📊 Fix Summary:")
        print("=" * 20)
        print(f"WSGI file updated: {'✅' if wsgi_fixed else '❌'}")
        print(f"Environment variables: {'✅' if env_ok else '❌'}")
        
        if wsgi_fixed:
            print("\n🎉 WSGI fix completed!")
            print("💡 Reload your web app to apply the changes")
        else:
            print("\n⚠️ WSGI fix failed")
            print("💡 Check the error messages above")
    else:
        print("\n❌ Could not fix WSGI file")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
