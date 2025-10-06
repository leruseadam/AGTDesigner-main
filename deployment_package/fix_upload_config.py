#!/usr/bin/env python3.11
"""
Fix upload configuration for PythonAnywhere persistence
"""

import os
from pathlib import Path

def fix_upload_config():
    print("🔧 Fixing upload configuration for PythonAnywhere...")
    
    # Get the current directory (should be /home/adamcordova/AGTDesigner)
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Create uploads directory
    uploads_dir = os.path.join(current_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Set proper permissions
    os.chmod(uploads_dir, 0o755)
    
    print(f"✅ Upload directory created: {uploads_dir}")
    
    # Test write permissions
    test_file = os.path.join(uploads_dir, 'test_write.txt')
    try:
        with open(test_file, 'w') as f:
            f.write('Test write successful')
        os.remove(test_file)
        print("✅ Write permissions working")
    except Exception as e:
        print(f"❌ Write permission error: {e}")
        return False
    
    # Check if we're on PythonAnywhere
    if 'pythonanywhere' in current_dir.lower() or '/home/' in current_dir:
        print("✅ Running on PythonAnywhere - using persistent directory")
        
        # Create a .gitkeep file
        gitkeep_file = os.path.join(uploads_dir, '.gitkeep')
        with open(gitkeep_file, 'w') as f:
            f.write('# This file ensures the uploads directory is tracked by git\n')
        print("✅ .gitkeep file created")
        
        # Show directory info
        files = os.listdir(uploads_dir)
        print(f"📁 Uploads directory contains {len(files)} files")
        
        if files:
            print("📄 Files in uploads directory:")
            for file in files[:10]:
                file_path = os.path.join(uploads_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path) / 1024  # KB
                    print(f"   - {file} ({size:.1f} KB)")
    
    return True

if __name__ == "__main__":
    fix_upload_config()
