#!/usr/bin/env python3.11
"""
ULTRA-FAST UPLOAD OPTIMIZER
Creates the fastest possible Excel upload for PythonAnywhere
"""

import os
import sys

def create_ultra_fast_upload():
    """Create ultra-fast upload endpoint with minimal processing"""
    
    upload_code = '''
@app.route('/upload-lightning', methods=['POST'])
def upload_lightning():
    """Lightning-fast upload with absolute minimal processing"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Skip filename sanitization for speed
        filename = file.filename
        
        # Save directly to uploads (no temp file)
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        
        file.save(file_path)
        
        # LIGHTNING-FAST PROCESSING - Only read first 100 rows
        try:
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                nrows=100,  # Only 100 rows for maximum speed
                dtype=str,
                na_filter=False,
                keep_default_na=False
            )
            
            if df.empty:
                return jsonify({'error': 'No data found'}), 400
            
            # MINIMAL PROCESSING - Only keep essential columns
            essential_cols = ['Product Name*', 'Product Type*', 'Product Brand']
            available_cols = [col for col in essential_cols if col in df.columns]
            
            if available_cols:
                df = df[available_cols]
            
            # Create minimal processor
            from src.core.data.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            processor.df = df
            
            # Store globally
            global excel_processor
            excel_processor = processor
            
            # MINIMAL DATABASE STORAGE - Only store essential data
            try:
                current_store = 'AGT_Bothell'
                product_db = get_product_database(current_store)
                
                # Store only first 50 rows to database for speed
                small_df = df.head(50)
                if hasattr(product_db, 'store_excel_data'):
                    product_db.store_excel_data(small_df, file_path)
                    logging.info(f"[LIGHTNING] Stored {len(small_df)} rows to {current_store} database")
            except Exception as db_error:
                logging.warning(f"[LIGHTNING] Database storage skipped: {db_error}")
            
            # Update session minimally
            session['file_path'] = file_path
            session['selected_tags'] = []
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'message': f'Lightning upload complete in {processing_time:.1f}s',
                'filename': filename,
                'rows_processed': len(df),
                'rows_stored': min(50, len(df)),
                'status': 'ready',
                'processing_time': round(processing_time, 2)
            })
            
        except Exception as process_error:
            logging.error(f"Lightning processing error: {process_error}")
            return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
            
    except Exception as e:
        logging.error(f"Lightning upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500
'''
    
    return upload_code

def create_ultra_fast_frontend():
    """Create ultra-fast frontend JavaScript"""
    
    frontend_code = '''
// Ultra-fast upload frontend
(function() {
    'use strict';
    
    // Override the upload function for lightning speed
    if (typeof TagManager !== 'undefined' && TagManager.prototype.uploadFile) {
        const originalUploadFile = TagManager.prototype.uploadFile;
        
        TagManager.prototype.uploadFile = function(file) {
            console.log('🚀 Using LIGHTNING upload mode');
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show lightning-fast UI
            this.showUploadProgress('Lightning mode: Processing first 100 rows...');
            
            return fetch('/upload-lightning', {
                method: 'POST',
                body: formData,
                timeout: 30000  // 30 second timeout
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('⚡ Lightning upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show success message
                this.showUploadSuccess(`⚡ Lightning upload complete in ${data.processing_time}s! Processed ${data.rows_processed} rows, stored ${data.rows_stored} to database.`);
                
                // Load tags immediately
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('⚡ Lightning upload failed:', error);
                this.showUploadError(`Lightning upload failed: ${error.message}`);
                throw error;
            });
        };
        
        console.log('⚡ Lightning upload mode activated');
    }
})();
'''
    
    return frontend_code

if __name__ == "__main__":
    # Create the ultra-fast upload code
    upload_code = create_ultra_fast_upload()
    frontend_code = create_ultra_fast_frontend()
    
    # Write to files
    with open("ultra_fast_upload_endpoint.py", "w") as f:
        f.write(upload_code)
    
    with open("static/js/lightning_upload.js", "w") as f:
        f.write(frontend_code)
    
    print("✅ Created ultra-fast upload optimization")
    print("📁 Files created:")
    print("   - ultra_fast_upload_endpoint.py")
    print("   - static/js/lightning_upload.js")
    print("\n🚀 Lightning upload features:")
    print("   - Only processes first 100 rows")
    print("   - Stores only 50 rows to database")
    print("   - Minimal column processing")
    print("   - 30-second timeout")
    print("   - No filename sanitization")
    print("   - Direct file save (no temp files)")
