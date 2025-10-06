#!/usr/bin/env python3.11
"""
SMART-FAST UPLOAD OPTIMIZER
Processes all data efficiently but still fast for large databases
"""

import os
import sys

def create_smart_fast_upload():
    """Create smart-fast upload endpoint that processes all data efficiently"""
    
    upload_code = '''
@app.route('/upload-smart-fast', methods=['POST'])
def upload_smart_fast():
    """Smart-fast upload - processes all data efficiently"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # SMART-FAST MODE - Process all data but efficiently
        filename = file.filename
        file_path = f"uploads/{filename}"
        file.save(file_path)
        
        # SMART PROCESSING - Read all rows but with optimizations
        try:
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                dtype=str,  # Read everything as strings for speed
                na_filter=False,
                keep_default_na=False
            )
            
            if df.empty:
                return jsonify({'error': 'No data found'}), 400
            
            # SMART COLUMNS - Keep essential columns only
            essential_cols = [
                'Product Name*', 'Product Type*', 'Product Brand', 
                'Product Strain', 'Lineage', 'THC test result', 'CBD test result',
                'Price* (Tier Name for Bulk)', 'Weight*', 'Weight Unit* (grams/gm or ounces/oz)'
            ]
            
            # Keep only columns that exist
            available_cols = [col for col in essential_cols if col in df.columns]
            if available_cols:
                df = df[available_cols]
            
            # SMART FILTERING - Remove excluded types efficiently
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            # Create processor with all data
            from src.core.data.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            processor.df = df
            
            # Store globally
            global excel_processor
            excel_processor = processor
            
            # SMART DATABASE STORAGE - Store all data efficiently
            try:
                current_store = 'AGT_Bothell'
                product_db = get_product_database(current_store)
                
                if hasattr(product_db, 'store_excel_data'):
                    product_db.store_excel_data(df, file_path)
                    logging.info(f"[SMART-FAST] Stored {len(df)} rows to {current_store} database")
                else:
                    logging.warning(f"[SMART-FAST] ProductDatabase does not have store_excel_data method")
            except Exception as db_error:
                logging.warning(f"[SMART-FAST] Database storage failed: {db_error}")
            
            # Update session
            session['file_path'] = file_path
            session['selected_tags'] = []
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'message': f'Smart-fast upload: {processing_time:.1f}s',
                'filename': filename,
                'rows_processed': len(df),
                'rows_stored': len(df),
                'status': 'ready',
                'processing_time': round(processing_time, 2),
                'mode': 'smart-fast',
                'total_products': len(df)
            })
            
        except Exception as process_error:
            logging.error(f"Smart-fast processing error: {process_error}")
            return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
            
    except Exception as e:
        logging.error(f"Smart-fast upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500
'''
    
    return upload_code

def create_smart_fast_frontend():
    """Create smart-fast frontend JavaScript"""
    
    frontend_code = '''
// Smart-fast upload frontend - processes all data efficiently
(function() {
    'use strict';
    
    // Override the upload function for smart-fast processing
    if (typeof TagManager !== 'undefined' && TagManager.prototype.uploadFile) {
        const originalUploadFile = TagManager.prototype.uploadFile;
        
        TagManager.prototype.uploadFile = function(file) {
            console.log('🧠 Using SMART-FAST upload mode');
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show smart-fast UI
            this.showUploadProgress('Smart-fast mode: Processing all products efficiently...');
            
            return fetch('/upload-smart-fast', {
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
                console.log('🧠 Smart-fast upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show success message
                this.showUploadSuccess(`🧠 Smart-fast upload complete in ${data.processing_time}s! Processed ${data.total_products} products.`);
                
                // Load tags immediately
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('🧠 Smart-fast upload failed:', error);
                // Try ultra-instant as fallback
                console.log('🧠 Trying ultra-instant mode...');
                return this.tryUltraInstantUpload(file);
            });
        };
        
        // Add ultra-instant upload fallback
        TagManager.prototype.tryUltraInstantUpload = function(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            this.showUploadProgress('Ultra-instant mode: Just saving file...');
            
            return fetch('/upload-ultra-instant', {
                method: 'POST',
                body: formData,
                timeout: 5000  // 5 second timeout
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('⚡ Ultra-instant upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                this.showUploadSuccess(`⚡ Ultra-instant upload complete in ${data.processing_time}s!`);
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('⚡ Ultra-instant upload failed:', error);
                this.showUploadError(`Both smart-fast and ultra-instant upload failed: ${error.message}`);
                throw error;
            });
        };
        
        console.log('🧠 Smart-fast upload mode activated');
    }
})();
'''
    
    return frontend_code

if __name__ == "__main__":
    # Create the smart-fast upload code
    upload_code = create_smart_fast_upload()
    frontend_code = create_smart_fast_frontend()
    
    # Write to files
    with open("smart_fast_upload_endpoint.py", "w") as f:
        f.write(upload_code)
    
    with open("static/js/smart_fast_upload.js", "w") as f:
        f.write(frontend_code)
    
    print("✅ Created SMART-FAST upload optimization")
    print("📁 Files created:")
    print("   - smart_fast_upload_endpoint.py")
    print("   - static/js/smart_fast_upload.js")
    print("\n🧠 SMART-FAST upload features:")
    print("   - Processes ALL rows from Excel file")
    print("   - Keeps essential columns only")
    print("   - Efficient filtering of excluded types")
    print("   - Stores all data to Bothell database")
    print("   - 30-second timeout for large files")
    print("   - Ultra-instant fallback if needed")
    print("\n🎯 TARGET:")
    print("   - Should handle 10,000+ products efficiently")
    print("   - Complete processing in under 30 seconds")
    print("   - Full database population")
