#!/usr/bin/env python3.11
"""
Debug file upload stuck on initializing issue
"""

import os
import sys
import time
import logging
from pathlib import Path

def debug_upload_issue():
    print("🔍 Debugging file upload stuck on initializing...")
    
    # Set up paths
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Add user site-packages
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
    
    try:
        # Test 1: Check uploads directory
        print("1. Checking uploads directory...")
        uploads_dir = Path(project_dir) / 'uploads'
        if uploads_dir.exists():
            print(f"   ✅ Uploads directory exists: {uploads_dir}")
            print(f"   📁 Permissions: {oct(uploads_dir.stat().st_mode)[-3:]}")
            
            # Check if we can write
            test_file = uploads_dir / 'test_write.txt'
            try:
                test_file.write_text('test')
                test_file.unlink()
                print("   ✅ Write permissions working")
            except Exception as e:
                print(f"   ❌ Write permission error: {e}")
        else:
            print(f"   ❌ Uploads directory missing: {uploads_dir}")
            print("   🔧 Creating uploads directory...")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(uploads_dir, 0o755)
            print("   ✅ Uploads directory created")
        
        # Test 2: Check Flask app import
        print("2. Testing Flask app import...")
        from app import app
        print("   ✅ Flask app imported successfully")
        
        # Test 3: Check upload configuration
        print("3. Checking upload configuration...")
        upload_folder = app.config.get('UPLOAD_FOLDER')
        print(f"   📁 Upload folder: {upload_folder}")
        print(f"   📏 Max file size: {app.config.get('MAX_CONTENT_LENGTH', 0) / (1024*1024):.1f} MB")
        
        # Test 4: Test upload endpoint with test client
        print("4. Testing upload endpoint...")
        with app.test_client() as client:
            # Create a test file
            test_content = b"test,data\n1,2\n3,4"
            
            # Test upload
            response = client.post('/upload', data={
                'file': (io.BytesIO(test_content), 'test.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            })
            
            print(f"   📤 Upload response status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Upload endpoint working")
                try:
                    response_data = response.get_json()
                    print(f"   📄 Response: {response_data}")
                except:
                    print(f"   📄 Response text: {response.data[:200]}")
            else:
                print(f"   ❌ Upload failed: {response.status_code}")
                print(f"   📄 Error: {response.data[:200]}")
        
        # Test 5: Check for common issues
        print("5. Checking for common issues...")
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024**3)
        print(f"   💾 Free disk space: {free_gb:.1f} GB")
        
        if free_gb < 1:
            print("   ⚠️  WARNING: Low disk space!")
        else:
            print("   ✅ Sufficient disk space")
        
        # Check if we're on PythonAnywhere
        if 'pythonanywhere' in os.getcwd().lower() or '/home/' in os.getcwd():
            print("   ✅ Running on PythonAnywhere")
        else:
            print("   ⚠️  Not running on PythonAnywhere")
        
        # Check session configuration
        print("6. Checking session configuration...")
        secret_key = app.config.get('SECRET_KEY')
        if secret_key:
            print("   ✅ Secret key configured")
        else:
            print("   ❌ Secret key missing")
        
        session_type = app.config.get('SESSION_TYPE')
        print(f"   📋 Session type: {session_type}")
        
        print("\n🎉 Upload debugging completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Upload debugging failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_upload_logs():
    """Check for upload-related log messages"""
    print("\n📋 Checking for upload logs...")
    
    # Look for recent log files
    log_dirs = ['logs', 'log', '.']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            if log_files:
                print(f"   📄 Found log files in {log_dir}: {log_files}")
                
                # Check the most recent log file
                latest_log = max([os.path.join(log_dir, f) for f in log_files], 
                               key=os.path.getmtime)
                print(f"   📖 Latest log: {latest_log}")
                
                try:
                    with open(latest_log, 'r') as f:
                        lines = f.readlines()
                        # Look for upload-related messages
                        upload_lines = [line for line in lines[-50:] if 'upload' in line.lower()]
                        if upload_lines:
                            print("   🔍 Recent upload-related log entries:")
                            for line in upload_lines[-5:]:
                                print(f"      {line.strip()}")
                        else:
                            print("   ℹ️  No recent upload-related log entries")
                except Exception as e:
                    print(f"   ❌ Error reading log file: {e}")
                break
    else:
        print("   ℹ️  No log files found")

def main():
    print("🚀 File Upload Debug Tool")
    print("=" * 50)
    
    # Debug upload issue
    debug_upload_issue()
    
    # Check logs
    check_upload_logs()
    
    print("\n💡 Common solutions for 'stuck on initializing':")
    print("1. Check PythonAnywhere error logs in Web tab")
    print("2. Verify uploads directory exists and is writable")
    print("3. Check disk space (PythonAnywhere has limited storage)")
    print("4. Try uploading a smaller file first")
    print("5. Check if the upload endpoint is responding")
    print("6. Verify file type is .xlsx")
    print("7. Check browser console for JavaScript errors")

if __name__ == "__main__":
    import io
    main()
