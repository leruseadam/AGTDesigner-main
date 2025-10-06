#!/usr/bin/env python3.11
"""
Fix file upload persistence on PythonAnywhere
Creates persistent upload directory and ensures files survive restarts
"""

import os
import shutil
from pathlib import Path

def fix_file_persistence():
    print("🔧 Fixing file upload persistence on PythonAnywhere...")
    
    # Define paths
    home_dir = Path.home()
    project_dir = home_dir / 'AGTDesigner'
    uploads_dir = project_dir / 'uploads'
    
    # Create persistent uploads directory
    print(f"1. Creating persistent uploads directory...")
    uploads_dir.mkdir(exist_ok=True)
    print(f"   ✅ Created: {uploads_dir}")
    
    # Set proper permissions
    print("2. Setting proper permissions...")
    os.chmod(uploads_dir, 0o755)
    print("   ✅ Permissions set to 755")
    
    # Create a test file to verify persistence
    print("3. Creating test file...")
    test_file = uploads_dir / 'test_persistence.txt'
    test_file.write_text('This file should persist across restarts')
    print(f"   ✅ Test file created: {test_file}")
    
    # Check if we can write to the directory
    print("4. Testing write permissions...")
    try:
        test_write = uploads_dir / 'write_test.txt'
        test_write.write_text('Write test successful')
        test_write.unlink()  # Remove test file
        print("   ✅ Write permissions working")
    except Exception as e:
        print(f"   ❌ Write permission error: {e}")
        return False
    
    # Create a .gitkeep file to ensure directory is tracked
    print("5. Creating .gitkeep file...")
    gitkeep = uploads_dir / '.gitkeep'
    gitkeep.write_text('# This file ensures the uploads directory is tracked by git')
    print("   ✅ .gitkeep file created")
    
    # Check current uploads directory size
    print("6. Checking uploads directory...")
    try:
        files = list(uploads_dir.glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"   📁 Directory contains {len(files)} files")
        print(f"   📏 Total size: {total_size / (1024*1024):.2f} MB")
        
        if files:
            print("   📄 Files in uploads directory:")
            for file in files[:10]:  # Show first 10 files
                size = file.stat().st_size / 1024  # KB
                print(f"      - {file.name} ({size:.1f} KB)")
            if len(files) > 10:
                print(f"      ... and {len(files) - 10} more files")
    except Exception as e:
        print(f"   ❌ Error checking directory: {e}")
    
    print("\n🎉 File persistence fix completed!")
    print("\n💡 Additional recommendations:")
    print("1. Files in ~/AGTDesigner/uploads/ should now persist")
    print("2. Consider implementing file cleanup to prevent disk space issues")
    print("3. Monitor disk usage regularly")
    print("4. Files are stored in: /home/adamcordova/AGTDesigner/uploads/")
    
    return True

def check_disk_space():
    """Check available disk space"""
    print("\n💾 Checking disk space...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        
        print(f"   💽 Total space: {total_gb:.1f} GB")
        print(f"   📊 Used space: {used_gb:.1f} GB ({used/total*100:.1f}%)")
        print(f"   ✅ Free space: {free_gb:.1f} GB ({free/total*100:.1f}%)")
        
        if free_gb < 1:
            print("   ⚠️  WARNING: Less than 1GB free space!")
            return False
        else:
            print("   ✅ Sufficient disk space available")
            return True
            
    except Exception as e:
        print(f"   ❌ Error checking disk space: {e}")
        return False

def cleanup_old_files():
    """Clean up old files to free space"""
    print("\n🧹 Cleaning up old files...")
    
    uploads_dir = Path.home() / 'AGTDesigner' / 'uploads'
    
    if not uploads_dir.exists():
        print("   ❌ Uploads directory doesn't exist")
        return False
    
    try:
        files = list(uploads_dir.glob('*'))
        if not files:
            print("   ✅ No files to clean up")
            return True
        
        # Remove test files
        test_files = [f for f in files if f.name.startswith('test_')]
        for test_file in test_files:
            test_file.unlink()
            print(f"   🗑️  Removed test file: {test_file.name}")
        
        # Remove files older than 7 days (optional)
        import time
        current_time = time.time()
        old_files = []
        
        for file in files:
            if file.is_file() and not file.name.startswith('.'):
                file_age = current_time - file.stat().st_mtime
                if file_age > 7 * 24 * 3600:  # 7 days
                    old_files.append(file)
        
        if old_files:
            print(f"   📅 Found {len(old_files)} files older than 7 days")
            for old_file in old_files[:5]:  # Show first 5
                print(f"      - {old_file.name}")
            if len(old_files) > 5:
                print(f"      ... and {len(old_files) - 5} more")
            
            # Uncomment the next line to actually delete old files
            # for old_file in old_files: old_file.unlink()
            print("   ℹ️  Old files found but not deleted (uncomment code to delete)")
        else:
            print("   ✅ No old files to clean up")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error during cleanup: {e}")
        return False

def main():
    print("🚀 PythonAnywhere File Persistence Fix")
    print("=" * 50)
    
    # Check disk space first
    if not check_disk_space():
        print("\n⚠️  Low disk space detected!")
        cleanup_old_files()
    
    # Fix file persistence
    success = fix_file_persistence()
    
    if success:
        print("\n✅ File persistence fix completed successfully!")
        print("\n📋 Next steps:")
        print("1. Reload your web app on PythonAnywhere")
        print("2. Test file upload functionality")
        print("3. Verify files persist after web app reload")
    else:
        print("\n❌ File persistence fix failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
