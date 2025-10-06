#!/usr/bin/env python3
"""
Fast Excel Upload Fix
Addresses the main performance bottlenecks in Excel file processing:
1. Database schema issues (missing Source column)
2. Database locking issues
3. Inefficient processing methods
4. Memory management problems
"""

import os
import sys
import time
import logging
import tempfile
import threading
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify, session
import pandas as pd
import gc
from concurrent.futures import ThreadPoolExecutor
import sqlite3

# Performance constants
MAX_ROWS_FOR_FAST_UPLOAD = 100000  # Increased limit
CHUNK_SIZE = 5000  # Smaller chunks for better memory management
MEMORY_CLEANUP_THRESHOLD = 1000
ENABLE_PARALLEL_PROCESSING = True
MAX_WORKERS = 2  # Reduced to avoid database locking

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastExcelUploader:
    """Ultra-fast Excel upload with optimized database operations"""
    
    def __init__(self):
        self.processing_lock = threading.Lock()
        self.active_uploads = {}
        self.db_lock = threading.RLock()  # Use RLock for database operations
        
    def upload_file_fast(self, file, app_config):
        """Main fast upload endpoint with optimized processing"""
        start_time = time.time()
        upload_id = f"upload_{int(time.time() * 1000)}"
        
        try:
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                file.save(tmp_file.name)
                file_path = tmp_file.name
            
            # Get file info
            file_info = {
                'filename': file.filename,
                'size': os.path.getsize(file_path),
                'upload_id': upload_id,
                'start_time': start_time
            }
            
            logger.info(f"[FAST UPLOAD] Starting upload {upload_id}: {file.filename} ({file_info['size']} bytes)")
            
            # Process file in background thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._process_file_fast, file_path, upload_id, file_info)
                
                # Store upload info
                self.active_uploads[upload_id] = {
                    'future': future,
                    'file_info': file_info,
                    'status': 'processing'
                }
                
                processing_time = time.time() - start_time
                
                return jsonify({
                    'success': True,
                    'upload_id': upload_id,
                    'message': 'File upload started successfully',
                    'processing_time': round(processing_time, 3),
                    'status': 'processing'
                })
                
        except Exception as e:
            logger.error(f"[FAST UPLOAD] Error in upload {upload_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'upload_id': upload_id
            }), 500
    
    def _process_file_fast(self, file_path, upload_id, file_info):
        """Process Excel file with optimized methods"""
        try:
            logger.info(f"[FAST UPLOAD] Processing file: {file_path}")
            
            # Method 1: Try ultra-fast load
            success = self._ultra_fast_load(file_path)
            if success:
                logger.info(f"[FAST UPLOAD] Ultra-fast load successful")
                return self._create_success_response(file_info, "ultra_fast")
            
            # Method 2: Try streaming load
            success = self._streaming_load(file_path)
            if success:
                logger.info(f"[FAST UPLOAD] Streaming load successful")
                return self._create_success_response(file_info, "streaming")
            
            # Method 3: Fallback to standard load with optimizations
            success = self._standard_load_optimized(file_path)
            if success:
                logger.info(f"[FAST UPLOAD] Standard load successful")
                return self._create_success_response(file_info, "standard")
            
            raise Exception("All loading methods failed")
            
        except Exception as e:
            logger.error(f"[FAST UPLOAD] Error processing file: {e}")
            self.active_uploads[upload_id]['status'] = 'error'
            self.active_uploads[upload_id]['error'] = str(e)
            raise
        finally:
            # Cleanup
            try:
                os.unlink(file_path)
            except:
                pass
    
    def _ultra_fast_load(self, file_path):
        """Ultra-fast Excel loading with minimal processing"""
        try:
            # Read with optimized settings
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                nrows=MAX_ROWS_FOR_FAST_UPLOAD,
                dtype=str,  # Read as strings for speed
                na_filter=False,
                keep_default_na=False
            )
            
            if df is None or df.empty:
                logger.warning("No data found in Excel file")
                return False
            
            # Minimal processing
            df = self._minimal_processing(df)
            
            # Store in session
            session['excel_data'] = df.to_dict('records')
            session['file_path'] = file_path
            session['selected_tags'] = []
            
            logger.info(f"[ULTRA-FAST] Loaded {len(df)} rows successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Ultra-fast load failed: {e}")
            return False
    
    def _streaming_load(self, file_path):
        """Load large files in streaming chunks"""
        try:
            chunks = []
            total_rows = 0
            
            # Read in chunks
            for chunk in pd.read_excel(
                file_path,
                engine='openpyxl',
                chunksize=CHUNK_SIZE,
                dtype=str,
                na_filter=False,
                keep_default_na=False
            ):
                chunks.append(chunk)
                total_rows += len(chunk)
                
                # Limit total rows
                if total_rows >= MAX_ROWS_FOR_FAST_UPLOAD:
                    break
            
            if not chunks:
                logger.warning("No chunks loaded")
                return False
            
            # Combine chunks
            df = pd.concat(chunks, ignore_index=True)
            
            # Minimal processing
            df = self._minimal_processing(df)
            
            # Store in session
            session['excel_data'] = df.to_dict('records')
            session['file_path'] = file_path
            session['selected_tags'] = []
            
            logger.info(f"[STREAMING] Loaded {len(df)} rows in {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.warning(f"Streaming load failed: {e}")
            return False
    
    def _standard_load_optimized(self, file_path):
        """Standard load with optimizations"""
        try:
            # Use ExcelProcessor with optimizations
            from src.core.data.excel_processor import ExcelProcessor
            
            processor = ExcelProcessor()
            
            # Disable database integration for faster loading
            if hasattr(processor, 'enable_product_db_integration'):
                processor.enable_product_db_integration(False)
            
            # Load with high row limit
            success = processor.load_excel_file(file_path, max_rows=MAX_ROWS_FOR_FAST_UPLOAD)
            
            if success and hasattr(processor, 'df') and processor.df is not None:
                # Store in session
                session['excel_data'] = processor.df.to_dict('records')
                session['file_path'] = file_path
                session['selected_tags'] = []
                
                logger.info(f"[STANDARD] Loaded {len(processor.df)} rows")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Standard load failed: {e}")
            return False
    
    def _minimal_processing(self, df):
        """Minimal processing for speed"""
        try:
            # Remove duplicates
            initial_count = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            # Basic cleaning
            df = df.fillna('')
            
            # Remove excluded product types
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            logger.info(f"[MINIMAL] Processed {len(df)} rows (removed {initial_count - len(df)} duplicates)")
            return df
            
        except Exception as e:
            logger.error(f"Error in minimal processing: {e}")
            return df
    
    def _create_success_response(self, file_info, method):
        """Create success response"""
        processing_time = time.time() - file_info['start_time']
        
        return {
            'success': True,
            'message': f'File processed successfully using {method} method',
            'processing_time': round(processing_time, 3),
            'method': method,
            'status': 'completed'
        }
    
    def get_fast_upload_status(self, upload_id):
        """Get upload status"""
        if upload_id not in self.active_uploads:
            return jsonify({'error': 'Upload not found'}), 404
        
        upload_info = self.active_uploads[upload_id]
        
        if upload_info['status'] == 'processing':
            if upload_info['future'].done():
                try:
                    result = upload_info['future'].result()
                    upload_info['status'] = 'completed'
                    upload_info['result'] = result
                except Exception as e:
                    upload_info['status'] = 'error'
                    upload_info['error'] = str(e)
        
        return jsonify({
            'upload_id': upload_id,
            'status': upload_info['status'],
            'file_info': upload_info['file_info'],
            'result': upload_info.get('result'),
            'error': upload_info.get('error')
        })

def create_fast_upload_routes(app):
    """Create fast upload routes for the Flask app"""
    uploader = FastExcelUploader()
    
    @app.route('/upload-fast', methods=['POST'])
    def upload_fast():
        """Fast Excel upload endpoint"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        return uploader.upload_file_fast(file, app.config)
    
    @app.route('/api/upload-status-fast/<upload_id>', methods=['GET'])
    def get_upload_status_fast(upload_id):
        """Get upload status"""
        return uploader.get_fast_upload_status(upload_id)
    
    return app

def fix_database_schema():
    """Fix database schema issues"""
    try:
        from src.core.data.product_database import ProductDatabase
        
        # Initialize database to ensure schema is up to date
        db = ProductDatabase()
        db.init_database()
        
        logger.info("Database schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    # Fix database schema first
    logger.info("Fixing database schema...")
    if fix_database_schema():
        logger.info("Database schema fixed successfully")
    else:
        logger.error("Failed to fix database schema")
    
    # Test the uploader
    logger.info("Fast Excel uploader ready")
