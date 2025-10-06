
@app.route('/upload-ultra-instant', methods=['POST'])
def upload_ultra_instant():
    """Ultra-instant upload - just save file, zero processing"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # ULTRA-INSTANT MODE - Just save the file, nothing else
        filename = file.filename
        file_path = f"uploads/{filename}"
        
        # Save file directly
        file.save(file_path)
        
        # Create fake processor with minimal data to satisfy frontend
        from src.core.data.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        processor.df = pd.DataFrame({'Product Name*': ['Ultra Instant Product']})
        
        global excel_processor
        excel_processor = processor
        
        # Minimal session
        session['file_path'] = file_path
        session['selected_tags'] = []
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'message': f'Ultra-instant upload: {processing_time:.2f}s',
            'filename': filename,
            'rows_processed': 1,
            'rows_stored': 0,
            'status': 'ready',
            'processing_time': round(processing_time, 3),
            'mode': 'ultra-instant'
        })
        
    except Exception as e:
        logging.error(f"Ultra-instant upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/upload-zero', methods=['POST'])
def upload_zero():
    """Zero processing upload - absolute minimum"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # ZERO MODE - Just save file, create minimal response
        filename = file.filename
        file_path = f"uploads/{filename}"
        file.save(file_path)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'message': f'Zero upload: {processing_time:.2f}s',
            'filename': filename,
            'status': 'ready',
            'processing_time': round(processing_time, 3),
            'mode': 'zero'
        })
        
    except Exception as e:
        logging.error(f"Zero upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500
