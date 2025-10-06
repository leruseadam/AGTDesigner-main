#!/usr/bin/env python3.11
"""
FAST UPLOAD OPTIMIZER FOR PYTHONANYWHERE
Optimizes Excel file uploads for speed and performance
"""

import os
import sys
import pandas as pd
import logging
from typing import Optional, Dict, Any

# Add project directory to path
project_dir = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 5'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

def create_ultra_fast_upload_handler():
    """Create an ultra-fast upload handler for PythonAnywhere"""
    
    upload_handler_code = '''
@app.route('/upload-fast', methods=['POST'])
def upload_file_ultra_fast():
    """Ultra-fast file upload optimized for PythonAnywhere"""
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
        
        # ULTRA-FAST PROCESSING
        try:
            # Use pandas directly for maximum speed
            df = pd.read_excel(
                temp_path,
                engine='openpyxl',
                nrows=5000,  # Limit to 5000 rows for speed
                dtype=str,   # Read everything as strings for speed
                na_filter=False,  # Don't filter NA values
                keep_default_na=False  # Don't use default NA values
            )
            
            if df.empty:
                return jsonify({'error': 'No data found in file'}), 400
            
            # Minimal processing - only essential columns
            essential_columns = ['Product Name*', 'Product Type*', 'Lineage', 'Product Brand']
            
            # Ensure essential columns exist
            for col in essential_columns:
                if col not in df.columns:
                    df[col] = "Unknown"
            
            # Basic string cleaning (minimal)
            for col in essential_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Remove excluded product types (minimal check)
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            # Create minimal ExcelProcessor
            from src.core.data.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            processor.df = df
            
            # Store in global processor
            global excel_processor
            excel_processor = processor
            
            # Update session
            session['file_path'] = temp_path
            session['selected_tags'] = []
            
            # Clean up temp file immediately
            try:
                os.remove(temp_path)
            except:
                pass
            
            return jsonify({
                'message': 'File uploaded and processed successfully (ultra-fast mode)',
                'filename': file.filename,
                'rows': len(df),
                'status': 'ready',
                'processing_time': 'ultra-fast'
            })
            
        except Exception as process_error:
            logging.error(f"Ultra-fast processing error: {process_error}")
            return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
            
    except Exception as e:
        logging.error(f"Ultra-fast upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500
'''
    
    return upload_handler_code

def optimize_excel_processor():
    """Optimize the ExcelProcessor for faster loading"""
    
    optimization_code = '''
# Add this method to ExcelProcessor class for ultra-fast loading
def ultra_fast_load(self, file_path: str) -> bool:
    """Ultra-fast loading with minimal processing for PythonAnywhere"""
    try:
        self.logger.info(f"[ULTRA-FAST] Loading file: {file_path}")
        
        # Clear previous data efficiently
        if hasattr(self, 'df') and self.df is not None:
            del self.df
            import gc
            gc.collect()
        
        # Read with minimal settings for maximum speed
        df = pd.read_excel(
            file_path,
            engine='openpyxl',
            nrows=5000,  # Limit rows for speed
            dtype=str,   # Read as strings for speed
            na_filter=False,  # Don't filter NA values
            keep_default_na=False  # Don't use default NA values
        )
        
        if df is None or df.empty:
            self.logger.error("No data found in Excel file")
            return False
        
        self.logger.info(f"[ULTRA-FAST] Successfully read {len(df)} rows, {len(df.columns)} columns")
        
        # Handle duplicate columns efficiently
        df = handle_duplicate_columns(df)
        
        # Remove duplicates efficiently
        initial_count = len(df)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        final_count = len(df)
        
        if initial_count != final_count:
            self.logger.info(f"[ULTRA-FAST] Removed {initial_count - final_count} duplicate rows")
        
        # Apply ultra-minimal processing
        df = self._ultra_minimal_processing(df)
        
        self.df = df
        self.logger.info(f"[ULTRA-FAST] Processing complete: {len(df)} rows")
        return True
        
    except Exception as e:
        self.logger.error(f"[ULTRA-FAST] Error loading file: {e}")
        return False

def _ultra_minimal_processing(self, df: pd.DataFrame) -> pd.DataFrame:
    """Ultra-minimal processing for maximum speed"""
    try:
        if len(df) == 0:
            return df
        
        # Only essential processing
        essential_columns = ['Product Name*', 'Product Type*', 'Lineage', 'Product Brand']
        
        # Ensure required columns exist
        for col in essential_columns:
            if col not in df.columns:
                df[col] = "Unknown"
        
        # Basic string cleaning for key columns only
        for col in essential_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Remove excluded product types (minimal check)
        if 'Product Type*' in df.columns:
            excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
            df = df[~df['Product Type*'].isin(excluded_types)]
            df.reset_index(drop=True, inplace=True)
        
        self.logger.info(f"[ULTRA-FAST] Ultra-minimal processing completed: {len(df)} rows remaining")
        return df
        
    except Exception as e:
        self.logger.error(f"[ULTRA-FAST] Error in ultra-minimal processing: {e}")
        return df
'''
    
    return optimization_code

def create_performance_config():
    """Create performance configuration for faster uploads"""
    
    config_code = '''
# Performance optimization flags for ultra-fast uploads
ENABLE_ULTRA_FAST_MODE = True
ENABLE_MINIMAL_PROCESSING = True
ENABLE_FAST_LOADING = True
ENABLE_LAZY_PROCESSING = False
ENABLE_BATCH_OPERATIONS = False
ENABLE_VECTORIZED_OPERATIONS = False
ENABLE_LINEAGE_PERSISTENCE = False
ENABLE_STRAIN_SIMILARITY_PROCESSING = False  # Disable for speed

# Ultra-fast constants
ULTRA_FAST_BATCH_SIZE = 500
ULTRA_FAST_MAX_ROWS = 5000
ULTRA_FAST_CACHE_SIZE = 64
'''
    
    return config_code

def main():
    """Main function to create optimization files"""
    print("🚀 Creating ultra-fast upload optimizations...")
    
    # Create upload handler
    upload_handler = create_ultra_fast_upload_handler()
    with open('ultra_fast_upload_handler.py', 'w') as f:
        f.write(upload_handler)
    print("✅ Created ultra_fast_upload_handler.py")
    
    # Create Excel processor optimizations
    processor_optimizations = optimize_excel_processor()
    with open('excel_processor_optimizations.py', 'w') as f:
        f.write(processor_optimizations)
    print("✅ Created excel_processor_optimizations.py")
    
    # Create performance config
    performance_config = create_performance_config()
    with open('performance_config.py', 'w') as f:
        f.write(performance_config)
    print("✅ Created performance_config.py")
    
    print("\n🎯 OPTIMIZATION SUMMARY:")
    print("=" * 30)
    print("✅ Ultra-fast upload handler created")
    print("✅ Excel processor optimizations created")
    print("✅ Performance configuration created")
    print("\n💡 Next steps:")
    print("1. Add the upload handler to your app.py")
    print("2. Add the processor optimizations to ExcelProcessor class")
    print("3. Use the performance config to optimize processing")
    print("4. Test with /upload-fast endpoint")

if __name__ == "__main__":
    main()
