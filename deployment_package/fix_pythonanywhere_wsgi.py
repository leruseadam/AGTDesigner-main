#!/usr/bin/env python3
"""
Simple script to fix PythonAnywhere web app
Run this on PythonAnywhere Bash console
"""

import os
import shutil

def fix_pythonanywhere_wsgi():
    """Fix the PythonAnywhere WSGI file"""
    print("🔧 Fixing PythonAnywhere WSGI File...")
    print("=" * 40)
    
    # Paths
    source_file = '/home/adamcordova/AGTDesigner/wsgi_pythonanywhere_python311.py'
    target_file = '/var/www/www_agtpricetags_com_wsgi.py'
    
    print(f"Source: {source_file}")
    print(f"Target: {target_file}")
    
    # Check if source exists
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        print("💡 Make sure you're in the right directory and the file exists")
        return False
    
    try:
        # Create backup
        if os.path.exists(target_file):
            backup_file = f"{target_file}.backup"
            shutil.copy2(target_file, backup_file)
            print(f"✅ Created backup: {backup_file}")
        
        # Copy the file
        shutil.copy2(source_file, target_file)
        print(f"✅ Successfully copied WSGI file!")
        
        # Verify the copy
        with open(target_file, 'r') as f:
            content = f.read()
        
        if "application = app" in content and "DB_HOST" in content:
            print("✅ WSGI file verification passed!")
            print("💡 Now go to PythonAnywhere Web tab and click 'Reload'")
            return True
        else:
            print("❌ WSGI file verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return False

if __name__ == "__main__":
    fix_pythonanywhere_wsgi()
