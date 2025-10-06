#!/usr/bin/env python3.11
"""
Simple upload test to isolate the issue
"""

import os
import sys
import io
from pathlib import Path

def test_simple_upload():
    print("🧪 Testing simple file upload...")
    
    # Set up paths
    project_dir = '/home/adamcordova/AGTDesigner'
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    try:
        # Import Flask app
        from app import app
        print("✅ Flask app imported")
        
        # Create a simple test file
        test_content = b"Product Name,Price\nTest Product,10.00"
        
        # Test with test client
        with app.test_client() as client:
            print("📤 Testing upload endpoint...")
            
            response = client.post('/upload', data={
                'file': (io.BytesIO(test_content), 'test.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            })
            
            print(f"📊 Response status: {response.status_code}")
            print(f"📄 Response data: {response.data[:200]}")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
                return True
            else:
                print("❌ Upload failed!")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_uploads_directory():
    """Check uploads directory status"""
    print("\n📁 Checking uploads directory...")
    
    uploads_dir = Path('/home/adamcordova/AGTDesigner/uploads')
    
    if uploads_dir.exists():
        print(f"✅ Directory exists: {uploads_dir}")
        
        # Check permissions
        stat = uploads_dir.stat()
        permissions = oct(stat.st_mode)[-3:]
        print(f"📋 Permissions: {permissions}")
        
        # Check if writable
        test_file = uploads_dir / 'test_write.txt'
        try:
            test_file.write_text('test')
            test_file.unlink()
            print("✅ Directory is writable")
        except Exception as e:
            print(f"❌ Directory not writable: {e}")
        
        # List files
        files = list(uploads_dir.glob('*'))
        print(f"📄 Files in directory: {len(files)}")
        for file in files[:5]:
            size = file.stat().st_size / 1024
            print(f"   - {file.name} ({size:.1f} KB)")
        
    else:
        print(f"❌ Directory missing: {uploads_dir}")
        print("🔧 Creating directory...")
        try:
            uploads_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(uploads_dir, 0o755)
            print("✅ Directory created")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")

def main():
    print("🚀 Simple Upload Test")
    print("=" * 30)
    
    # Check uploads directory
    check_uploads_directory()
    
    # Test simple upload
    success = test_simple_upload()
    
    if success:
        print("\n🎉 Upload test passed!")
        print("The issue might be with the frontend or file size.")
    else:
        print("\n❌ Upload test failed!")
        print("Check the error messages above for details.")

if __name__ == "__main__":
    main()
