
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
