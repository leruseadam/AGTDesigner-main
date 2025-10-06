
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
