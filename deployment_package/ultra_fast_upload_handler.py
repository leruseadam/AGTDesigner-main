
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
