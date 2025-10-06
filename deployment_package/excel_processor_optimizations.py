
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
