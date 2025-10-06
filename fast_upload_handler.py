#!/usr/bin/env python3
"""
Fast upload handler for PythonAnywhere with aggressive optimizations
"""

from flask import Flask, request, jsonify, session
import os
import time
import tempfile
import pandas as pd
from werkzeug.utils import secure_filename

def create_fast_upload_handler(app):
    """Create optimized upload handler"""
    
    @app.route('/upload-ultra-fast', methods=['POST'])
    def upload_ultra_fast():
        """Ultra-fast upload with minimal processing"""
        start_time = time.time()
        
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Quick file validation
            if not file.filename.lower().endswith(('.xlsx', '.xls')):
                return jsonify({'error': 'Only Excel files allowed'}), 400
            
            # Save with minimal processing
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            
            # Ensure uploads directory exists
            os.makedirs('uploads', exist_ok=True)
            
            # Save file directly
            file.save(filepath)
            
            # Quick validation - just check if pandas can open it
            try:
                # Read only first 5 rows to validate
                df = pd.read_excel(filepath, nrows=5)
                row_count = len(pd.read_excel(filepath))  # Get full count
            except Exception as e:
                os.remove(filepath)  # Clean up on error
                return jsonify({'error': f'Invalid Excel file: {str(e)}'}), 400
            
            # Store minimal info in session
            session['current_file'] = filename
            session['file_path'] = filepath
            session['upload_time'] = time.time()
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'filename': filename,
                'rows': row_count,
                'columns': len(df.columns),
                'processing_time': round(processing_time, 2),
                'message': f'File uploaded successfully in {processing_time:.1f}s'
            })
            
        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @app.route('/process-ultra-fast', methods=['POST'])
    def process_ultra_fast():
        """Ultra-fast processing with minimal overhead"""
        start_time = time.time()
        
        try:
            if 'current_file' not in session:
                return jsonify({'error': 'No file uploaded'}), 400
            
            filepath = session.get('file_path')
            if not os.path.exists(filepath):
                return jsonify({'error': 'File not found'}), 400
            
            # Load with minimal processing
            df = pd.read_excel(filepath)
            
            # Basic processing only
            processed_data = []
            for index, row in df.iterrows():
                if index >= 100:  # Limit to first 100 rows for speed
                    break
                    
                processed_data.append({
                    'index': index,
                    'data': row.to_dict()
                })
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'processed_rows': len(processed_data),
                'data': processed_data[:20],  # Return first 20 for preview
                'processing_time': round(processing_time, 2),
                'total_rows': len(df)
            })
            
        except Exception as e:
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500

    return app

# Export the function
__all__ = ['create_fast_upload_handler']
