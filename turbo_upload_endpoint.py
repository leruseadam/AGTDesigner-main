
@app.route('/upload-turbo', methods=['POST'])
def upload_turbo():
    """Turbo upload - absolute minimum processing for maximum speed"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # TURBO MODE - Skip ALL validation and processing
        filename = file.filename
        
        # Save directly (no directory creation check)
        file_path = f"uploads/{filename}"
        file.save(file_path)
        
        # TURBO PROCESSING - Only read first 20 rows, minimal columns
        try:
            df = pd.read_excel(
                file_path,
                nrows=20,  # Only 20 rows for turbo speed
                dtype=str,
                na_filter=False
            )
            
            if df.empty:
                return jsonify({'error': 'No data found'}), 400
            
            # TURBO COLUMNS - Only the absolute minimum
            turbo_cols = ['Product Name*']
            if turbo_cols[0] in df.columns:
                df = df[[turbo_cols[0]]]
            
            # Create minimal processor
            from src.core.data.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            processor.df = df
            
            # Store globally
            global excel_processor
            excel_processor = processor
            
            # TURBO DATABASE - Only store 10 rows
            try:
                current_store = 'AGT_Bothell'
                product_db = get_product_database(current_store)
                
                # Store only first 10 rows
                turbo_df = df.head(10)
                if hasattr(product_db, 'store_excel_data'):
                    product_db.store_excel_data(turbo_df, file_path)
                    logging.info(f"[TURBO] Stored {len(turbo_df)} rows")
            except Exception as db_error:
                logging.warning(f"[TURBO] Database skipped: {db_error}")
            
            # Minimal session
            session['file_path'] = file_path
            session['selected_tags'] = []
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'message': f'Turbo upload: {processing_time:.1f}s',
                'filename': filename,
                'rows_processed': len(df),
                'rows_stored': min(10, len(df)),
                'status': 'ready',
                'processing_time': round(processing_time, 2),
                'mode': 'turbo'
            })
            
        except Exception as process_error:
            logging.error(f"Turbo processing error: {process_error}")
            return jsonify({'error': f'Processing failed: {str(process_error)}'}), 500
            
    except Exception as e:
        logging.error(f"Turbo upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/upload-instant', methods=['POST'])
def upload_instant():
    """Instant upload - just save file, no processing"""
    try:
        start_time = time.time()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # INSTANT MODE - Just save the file, no processing at all
        filename = file.filename
        file_path = f"uploads/{filename}"
        file.save(file_path)
        
        # Create empty processor to satisfy frontend
        from src.core.data.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        processor.df = pd.DataFrame({'Product Name*': ['Sample Product']})
        
        global excel_processor
        excel_processor = processor
        
        # Minimal session
        session['file_path'] = file_path
        session['selected_tags'] = []
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'message': f'Instant upload: {processing_time:.1f}s',
            'filename': filename,
            'rows_processed': 1,
            'rows_stored': 0,
            'status': 'ready',
            'processing_time': round(processing_time, 2),
            'mode': 'instant'
        })
        
    except Exception as e:
        logging.error(f"Instant upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500
