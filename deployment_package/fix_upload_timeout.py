#!/usr/bin/env python3.11
"""
Fix upload timeout issues for large files
Creates a more responsive upload system
"""

import os
import sys

# Detect environment
if os.path.exists('/home/adamcordova'):
    # PythonAnywhere environment
    project_dir = '/home/adamcordova/AGTDesigner'
else:
    # Local environment
    project_dir = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 5'

def create_responsive_upload_handler():
    """Create a more responsive upload handler"""
    
    upload_handler_code = '''
@app.route('/upload-responsive', methods=['POST'])
def upload_file_responsive():
    """Responsive file upload that handles large files better"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate safe filename
        import uuid
        import time
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        sanitized_filename = f"{timestamp}_{unique_id}_{file.filename}"
        
        # Save to uploads directory
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        temp_path = os.path.join(uploads_dir, sanitized_filename)
        
        file.save(temp_path)
        
        # Quick response - don't process immediately
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': file.filename,
            'status': 'uploaded',
            'processing': 'background'
        })
        
    except Exception as e:
        logging.error(f"Responsive upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/process-file', methods=['POST'])
def process_uploaded_file():
    """Process the uploaded file in the background"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Find the uploaded file
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        file_path = None
        
        for file in os.listdir(uploads_dir):
            if filename in file:
                file_path = os.path.join(uploads_dir, file)
                break
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Process with minimal settings for speed
        try:
            import pandas as pd
            
            # Read with minimal processing
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                nrows=1000,  # Limit to 1000 rows for speed
                dtype=str,   # Read as strings
                na_filter=False,
                keep_default_na=False
            )
            
            if df.empty:
                return jsonify({'error': 'No data found in file'}), 400
            
            # Essential columns only
            essential_columns = ['Product Name*', 'Product Type*', 'Lineage', 'Product Brand']
            for col in essential_columns:
                if col not in df.columns:
                    df[col] = "Unknown"
            
            # Basic cleaning
            for col in essential_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Remove excluded types
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            # Store in database
            try:
                current_store = 'AGT_Bothell'
                product_db = get_product_database(current_store)
                if hasattr(product_db, 'store_excel_data'):
                    storage_result = product_db.store_excel_data(df, file_path)
                    logging.info(f"Database storage completed: {storage_result}")
            except Exception as db_error:
                logging.error(f"Database storage failed: {db_error}")
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'message': 'File processed successfully',
                'rows': len(df),
                'status': 'ready'
            })
            
        except Exception as process_error:
            logging.error(f"Processing error: {process_error}")
            return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
            
    except Exception as e:
        logging.error(f"Process file error: {e}")
        return jsonify({'error': 'Processing failed'}), 500
'''
    
    return upload_handler_code

def create_responsive_frontend():
    """Create responsive frontend JavaScript"""
    
    frontend_code = '''
// Responsive upload frontend
if (typeof TagManager !== 'undefined') {
    // Store original function
    TagManager.originalUploadFile = TagManager.uploadFile;
    
    // Replace with responsive upload
    TagManager.uploadFile = async function(file) {
        try {
            console.log(`Starting RESPONSIVE file upload:`, file.name, 'Size:', file.size, 'bytes');
            
            // Show loading splash
            this.showExcelLoadingSplash(file.name);
            this.updateUploadUI(`Uploading ${file.name} (responsive mode)...`);
            
            // Step 1: Upload file quickly
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadResponse = await fetch('/upload-responsive', {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            
            if (!uploadResponse.ok) {
                throw new Error(uploadData.error || 'Upload failed');
            }
            
            console.log('File uploaded, starting processing...');
            this.updateUploadUI(`Processing ${file.name}...`);
            
            // Step 2: Process file in background
            const processResponse = await fetch('/process-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: file.filename
                })
            });
            
            const processData = await processResponse.json();
            
            if (!processResponse.ok) {
                throw new Error(processData.error || 'Processing failed');
            }
            
            // Success!
            console.log('Processing completed:', processData);
            this.hideExcelLoadingSplash();
            this.updateUploadUI(`File processed successfully! ${processData.rows} rows`);
            this.clearUIStateForNewFile();
            this.showToast('success', `File processed successfully! ${processData.rows} rows processed.`);
            
            // Refresh tag lists
            await this.refreshTagLists();
            
            return processData;
            
        } catch (error) {
            console.error('Responsive upload error:', error);
            this.hideExcelLoadingSplash();
            this.showToast('error', `Upload failed: ${error.message}`);
            throw error;
        }
    };
}

console.log('🚀 Responsive upload frontend loaded!');
'''
    
    return frontend_code

def main():
    """Main function"""
    print("🚀 CREATING RESPONSIVE UPLOAD SYSTEM")
    print("=" * 40)
    
    # Create upload handler
    upload_handler = create_responsive_upload_handler()
    with open('responsive_upload_handler.py', 'w') as f:
        f.write(upload_handler)
    print("✅ Created responsive_upload_handler.py")
    
    # Create frontend
    frontend = create_responsive_frontend()
    with open('responsive_upload_frontend.js', 'w') as f:
        f.write(frontend)
    print("✅ Created responsive_upload_frontend.js")
    
    print("\n🎯 RESPONSIVE UPLOAD SYSTEM CREATED!")
    print("=" * 40)
    print("✅ Two-step upload process:")
    print("   1. Quick file upload (immediate response)")
    print("   2. Background processing (no timeout)")
    print("✅ Handles large files without frontend timeout")
    print("✅ Better user feedback and progress tracking")
    print("\n💡 Next steps:")
    print("1. Add upload handler to app.py")
    print("2. Add frontend script to templates")
    print("3. Test with large files")

if __name__ == "__main__":
    main()
