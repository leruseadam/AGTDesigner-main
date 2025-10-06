#!/usr/bin/env python3
"""
Fix Excel upload issues on PythonAnywhere
This script creates a simple, working upload endpoint
"""

def create_simple_upload_fix():
    """Create a simple upload fix for PythonAnywhere"""
    
    fix_code = '''
# Add this to your app.py file to fix Excel upload issues

@app.route('/upload-debug', methods=['POST'])
def upload_debug():
    """Debug upload endpoint to test file uploads"""
    try:
        print("=== UPLOAD DEBUG START ===")
        print(f"Request method: {request.method}")
        print(f"Request files: {list(request.files.keys())}")
        print(f"Content-Type: {request.content_type}")
        print(f"Content-Length: {request.content_length}")
        
        if 'file' not in request.files:
            print("ERROR: No file in request.files")
            return jsonify({'error': 'No file uploaded', 'debug': 'No file in request.files'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        print(f"File content type: {file.content_type}")
        print(f"File size: {len(file.read()) if hasattr(file, 'read') else 'Unknown'}")
        
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'error': 'No file selected', 'debug': 'Empty filename'}), 400
        
        # Check file extension
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            print(f"ERROR: Invalid file type: {file.filename}")
            return jsonify({'error': 'Only Excel files allowed', 'debug': f'Invalid type: {file.filename}'}), 400
        
        # Create uploads directory
        import os
        os.makedirs('uploads', exist_ok=True)
        
        # Save file
        from werkzeug.utils import secure_filename
        import time
        
        timestamp = int(time.time())
        safe_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join('uploads', filename)
        
        print(f"Saving file to: {file_path}")
        file.save(file_path)
        
        # Test if file was saved
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"File saved successfully: {file_size} bytes")
            
            # Quick pandas test
            try:
                import pandas as pd
                df = pd.read_excel(file_path, nrows=5)
                print(f"Pandas test successful: {len(df)} rows")
                
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'filename': filename,
                    'size': file_size,
                    'debug': {
                        'file_path': file_path,
                        'pandas_rows': len(df),
                        'columns': list(df.columns)[:5] if len(df) > 0 else []
                    }
                })
                
            except Exception as e:
                print(f"Pandas test failed: {e}")
                return jsonify({
                    'success': True,
                    'message': 'File uploaded but pandas test failed',
                    'filename': filename,
                    'size': file_size,
                    'warning': str(e)
                })
        else:
            print("ERROR: File was not saved")
            return jsonify({'error': 'File save failed', 'debug': 'File not found after save'}), 500
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'debug': 'Exception in upload_debug'}), 500

@app.route('/upload-simple-fix', methods=['POST'])
def upload_simple_fix():
    """Simple, reliable upload for PythonAnywhere"""
    try:
        print("=== SIMPLE UPLOAD FIX START ===")
        
        # Check if file exists
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Only Excel files allowed'}), 400
        
        # Create uploads directory
        import os
        import time
        from werkzeug.utils import secure_filename
        
        os.makedirs('uploads', exist_ok=True)
        
        # Generate safe filename
        timestamp = int(time.time())
        safe_filename = secure_filename(file.filename)
        filename = f"upload_{timestamp}_{safe_filename}"
        file_path = os.path.join('uploads', filename)
        
        print(f"Saving file: {filename}")
        
        # Save file
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            return jsonify({'error': 'File save failed'}), 500
        
        file_size = os.path.getsize(file_path)
        print(f"File saved: {file_size} bytes")
        
        # Store in session
        session['file_path'] = file_path
        session['current_file'] = filename
        session['upload_time'] = time.time()
        
        # Return success
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'size': file_size,
            'path': file_path
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
'''
    
    return fix_code

def print_fix_instructions():
    """Print instructions for fixing the upload"""
    
    print("🔧 EXCEL UPLOAD FIX FOR PYTHONANYWHERE")
    print("=" * 50)
    print()
    print("The issue is likely one of these:")
    print("1. File size limits")
    print("2. Timeout issues")
    print("3. Memory limits")
    print("4. Directory permissions")
    print("5. Flask configuration")
    print()
    print("📋 QUICK FIXES TO TRY:")
    print()
    print("1. Add these routes to your app.py:")
    print("   (Copy the code from the fix_code above)")
    print()
    print("2. Test with the debug endpoint:")
    print("   POST /upload-debug")
    print()
    print("3. Use the simple fix endpoint:")
    print("   POST /upload-simple-fix")
    print()
    print("4. Check PythonAnywhere settings:")
    print("   - Web tab → Increase timeout to 300-600 seconds")
    print("   - Check MAX_CONTENT_LENGTH in Flask config")
    print("   - Verify uploads directory permissions")
    print()
    print("5. Alternative: Use Files tab upload")
    print("   - Upload Excel file via PythonAnywhere Files tab")
    print("   - Place in /home/adamcordova/AGTDesigner/uploads/")
    print("   - App will auto-detect the file")
    print()
    print("6. Check error logs:")
    print("   - Web tab → Error log link")
    print("   - Look for specific error messages")
    print()
    print("🚀 MOST LIKELY SOLUTION:")
    print("   Increase WSGI timeout in PythonAnywhere Web tab")
    print("   to 300-600 seconds for large Excel files.")

if __name__ == "__main__":
    fix_code = create_simple_upload_fix()
    print_fix_instructions()
    
    # Save the fix code
    with open('upload_fix_code.txt', 'w') as f:
        f.write(fix_code)
    
    print("\n✅ Fix code saved to: upload_fix_code.txt")
    print("Copy this code into your app.py file to fix uploads.")
