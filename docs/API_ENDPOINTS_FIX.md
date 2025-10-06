# API Endpoints Fix Summary

## Problem Identified

The application was experiencing several API errors:

1. **400 Bad Request** errors for `/api/selected-tags` and `/api/available-tags`
2. **500 Internal Server Error** for unspecified endpoints
3. **Empty filter options** (all arrays were empty)
4. **No data loaded** by default on startup

## Root Cause Analysis

The main issues were:

1. **Duplicate Excel Processor Instances**: Two separate Excel processor instances were being created, causing confusion
2. **No Default File Loading**: The application wasn't automatically loading the default "A Greener Today" file on startup
3. **Poor Error Handling**: API endpoints weren't providing clear error messages when data wasn't loaded
4. **Inconsistent Data State**: The Excel processor state wasn't being properly managed

## Fixes Implemented

### 1. Unified Excel Processor Initialization

**Before**: Two separate Excel processor instances
```python
# Global instance
excel_processor = ExcelProcessor()

# Lazy-loaded instance
def get_excel_processor():
    global _excel_processor
    if _excel_processor is None:
        _excel_processor = ExcelProcessor()
    return _excel_processor
```

**After**: Single unified initialization with default file loading
```python
def initialize_excel_processor():
    """Initialize Excel processor and load default data."""
    try:
        excel_processor = get_excel_processor()
        excel_processor.logger.setLevel(logging.WARNING)
        
        # Try to load default file
        from src.core.data.excel_processor import get_default_upload_file
        default_file = get_default_upload_file()
        
        if default_file and os.path.exists(default_file):
            logging.info(f"Loading default file on startup: {default_file}")
            success = excel_processor.load_file(default_file)
            if success:
                excel_processor._last_loaded_file = default_file
                logging.info(f"Default file loaded successfully with {len(excel_processor.df)} records")
            else:
                logging.warning("Failed to load default file")
        else:
            logging.info("No default file found, waiting for user upload")
            
    except Exception as e:
        logging.error(f"Error initializing Excel processor: {e}")

# Initialize on startup
initialize_excel_processor()
```

### 2. Improved API Endpoint Error Handling

**Enhanced `/api/available-tags` endpoint**:
- Better error messages when no data is loaded
- Automatic fallback to default file loading
- Detailed logging for debugging
- Proper error responses with meaningful messages

**Enhanced `/api/selected-tags` endpoint**:
- Consistent error handling
- Clear error messages for missing data
- Better logging

**Enhanced `/api/filter-options` endpoint**:
- Automatic default file loading when no data is present
- Graceful handling of missing data
- Detailed logging

### 3. Added Status Endpoint

New `/api/status` endpoint to check server and data status:
```python
@app.route('/api/status', methods=['GET'])
def api_status():
    """Check API server status and data loading status."""
    try:
        excel_processor = get_excel_processor()
        
        status = {
            'server': 'running',
            'data_loaded': excel_processor.df is not None and not excel_processor.df.empty,
            'data_shape': excel_processor.df.shape if excel_processor.df is not None else None,
            'last_loaded_file': getattr(excel_processor, '_last_loaded_file', None),
            'selected_tags_count': len(excel_processor.selected_tags) if hasattr(excel_processor, 'selected_tags') else 0
        }
        
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error in status endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### 4. Test Script

Created `test_api_fix.py` to verify the fixes:
- Tests all API endpoints
- Verifies default file loading
- Provides clear feedback on what's working/failing

## Files Modified

1. **`app.py`** - Main fixes for API endpoints and initialization
2. **`test_api_fix.py`** - New test script (created)
3. **`API_ENDPOINTS_FIX.md`** - This documentation (created)

## Expected Results

After these fixes:

1. ✅ **API endpoints should return 200 status codes** when data is loaded
2. ✅ **Default file should load automatically** on startup if available
3. ✅ **Clear error messages** when no data is available
4. ✅ **Filter options should populate** with actual data
5. ✅ **Better debugging information** in logs
6. ✅ **Consistent data state** across all endpoints

## Testing

To test the fixes:

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Run the test script**:
   ```bash
   python test_api_fix.py
   ```

3. **Check the browser console** - should see successful API calls instead of 400/500 errors

4. **Verify filter dropdowns** - should populate with actual data instead of being empty

## Troubleshooting

If issues persist:

1. **Check if default file exists**: Look for "A Greener Today" Excel files in uploads/ or Downloads/
2. **Check server logs**: Look for initialization messages
3. **Use the status endpoint**: `GET /api/status` to check data loading status
4. **Upload a file manually**: If no default file exists, upload an Excel file through the UI

## Next Steps

1. **Monitor the application** to ensure the fixes resolve the issues
2. **Test with different file types** to ensure robustness
3. **Consider adding more comprehensive error handling** for edge cases
4. **Add automated tests** for the API endpoints 