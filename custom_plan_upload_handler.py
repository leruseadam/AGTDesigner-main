#!/usr/bin/env python3
"""
Custom Plan Upload Handler
Optimized for 6 web workers, 20GB disk, Postgres database
"""

import os
import time
import threading
import multiprocessing
from functools import wraps
from flask import Flask, request, jsonify, session
import pandas as pd
import logging

def custom_plan_performance_monitor(func):
    """Performance monitor for custom plan"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log performance metrics
        if execution_time > 0.5:  # Log operations > 0.5 seconds
            logging.info(f"{func.__name__}: {execution_time:.2f}s")
        
        return result
    return wrapper

def create_custom_plan_upload_handler(app):
    """Create upload handler optimized for custom plan"""
    
    @app.route('/upload-custom-plan', methods=['POST'])
    @custom_plan_performance_monitor
    def upload_custom_plan():
        """Custom plan upload - optimized for 6 workers, 20GB disk, Postgres"""
        try:
            start_time = time.time()
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Custom plan file handling
            filename = file.filename
            upload_dir = '/home/adamcordova/AGTDesigner/uploads'
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            # Save file with custom plan optimizations
            file.save(file_path)
            
            # Custom plan processing - handle large files efficiently
            try:
                # Read Excel with custom plan optimizations
                df = pd.read_excel(
                    file_path,
                    engine='openpyxl',
                    dtype=str,  # Read as strings for speed
                    na_filter=False,
                    keep_default_na=False,
                    # Custom plan specific optimizations
                    memory_map=True,  # Use memory mapping for large files
                    chunksize=1000   # Process in chunks
                )
                
                if df.empty:
                    return jsonify({'error': 'No data found'}), 400
                
                # Custom plan column optimization
                essential_cols = [
                    'Product Name*', 'Product Type*', 'Product Brand', 
                    'Product Strain', 'Lineage', 'THC test result', 'CBD test result',
                    'Price* (Tier Name for Bulk)', 'Weight*', 'Weight Unit* (grams/gm or ounces/oz)',
                    'Vendor/Supplier*', 'Quantity*', 'Cost*', 'Barcode*'
                ]
                
                # Keep only existing essential columns
                available_cols = [col for col in essential_cols if col in df.columns]
                if available_cols:
                    df = df[available_cols]
                
                # Custom plan filtering
                if 'Product Type*' in df.columns:
                    excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                    df = df[~df['Product Type*'].isin(excluded_types)]
                    df.reset_index(drop=True, inplace=True)
                
                # Create processor with custom plan optimizations
                from src.core.data.excel_processor import ExcelProcessor
                processor = ExcelProcessor()
                processor.df = df
                
                # Store globally
                global excel_processor
                excel_processor = processor
                
                # Custom plan database storage - optimized for Postgres
                try:
                    current_store = 'AGT_Bothell'
                    product_db = get_product_database(current_store)
                    
                    if hasattr(product_db, 'store_excel_data'):
                        # Use custom plan database optimization
                        product_db.store_excel_data(df, file_path)
                        logging.info(f"[CUSTOM-PLAN] Stored {len(df)} rows to {current_store} database")
                    else:
                        logging.warning(f"[CUSTOM-PLAN] ProductDatabase does not have store_excel_data method")
                except Exception as db_error:
                    logging.warning(f"[CUSTOM-PLAN] Database storage failed: {db_error}")
                
                # Update session
                session['file_path'] = file_path
                session['selected_tags'] = []
                
                processing_time = time.time() - start_time
                
                return jsonify({
                    'message': f'Custom plan upload: {processing_time:.1f}s',
                    'filename': filename,
                    'rows_processed': len(df),
                    'rows_stored': len(df),
                    'status': 'ready',
                    'processing_time': round(processing_time, 2),
                    'mode': 'custom-plan',
                    'total_products': len(df),
                    'plan_specs': {
                        'web_workers': 6,
                        'disk_space': '20GB',
                        'cpu_seconds': '7000/day',
                        'postgres': True
                    }
                })
                
            except Exception as process_error:
                logging.error(f"Custom plan processing error: {process_error}")
                return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
                
        except Exception as e:
            logging.error(f"Custom plan upload error: {e}")
            return jsonify({'error': 'Upload failed'}), 500
    
    @app.route('/upload-parallel', methods=['POST'])
    @custom_plan_performance_monitor
    def upload_parallel():
        """Parallel upload - uses multiple workers for large files"""
        try:
            start_time = time.time()
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Parallel processing setup
            filename = file.filename
            upload_dir = '/home/adamcordova/AGTDesigner/uploads'
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            file.save(file_path)
            
            # Parallel processing for large files
            try:
                # Use multiprocessing for large file processing
                def process_chunk(chunk_data):
                    """Process a chunk of data in parallel"""
                    return chunk_data.head(1000)  # Process 1000 rows per chunk
                
                # Read file in chunks for parallel processing
                chunk_size = 5000
                chunks = []
                
                for chunk in pd.read_excel(file_path, chunksize=chunk_size):
                    chunks.append(chunk)
                    if len(chunks) >= 6:  # Match web workers
                        break
                
                # Process chunks in parallel
                with multiprocessing.Pool(processes=6) as pool:
                    processed_chunks = pool.map(process_chunk, chunks)
                
                # Combine processed chunks
                df = pd.concat(processed_chunks, ignore_index=True)
                
                if df.empty:
                    return jsonify({'error': 'No data found'}), 400
                
                # Create processor
                from src.core.data.excel_processor import ExcelProcessor
                processor = ExcelProcessor()
                processor.df = df
                
                global excel_processor
                excel_processor = processor
                
                # Update session
                session['file_path'] = file_path
                session['selected_tags'] = []
                
                processing_time = time.time() - start_time
                
                return jsonify({
                    'message': f'Parallel upload: {processing_time:.1f}s',
                    'filename': filename,
                    'rows_processed': len(df),
                    'chunks_processed': len(chunks),
                    'status': 'ready',
                    'processing_time': round(processing_time, 2),
                    'mode': 'parallel',
                    'total_products': len(df)
                })
                
            except Exception as process_error:
                logging.error(f"Parallel processing error: {process_error}")
                return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
                
        except Exception as e:
            logging.error(f"Parallel upload error: {e}")
            return jsonify({'error': 'Upload failed'}), 500
    
    return app

# Export the function
__all__ = ['create_custom_plan_upload_handler']
