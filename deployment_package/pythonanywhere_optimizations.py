
# PythonAnywhere Aggressive Performance Optimization
import os
import logging

# Set environment variables for maximum performance
os.environ['PYTHONANYWHERE_OPTIMIZATION'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Aggressive memory management
import gc
gc.set_threshold(100, 10, 10)  # More aggressive garbage collection

# Disable verbose logging completely
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'xlrd', 'docxtpl', 'python-docx']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).disabled = True

# Performance constants for PythonAnywhere
PYTHONANYWHERE_MAX_CHUNK_SIZE = 25  # Reduce from 50
PYTHONANYWHERE_MAX_PROCESSING_TIME = 15  # Reduce from 30
PYTHONANYWHERE_MAX_TOTAL_TIME = 120  # Reduce from 300
PYTHONANYWHERE_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max
PYTHONANYWHERE_UPLOAD_CHUNK_SIZE = 8192  # 8KB chunks

# Enable lazy imports
LAZY_IMPORTS = True

# Disable startup file loading
DISABLE_STARTUP_FILE_LOADING = True
LAZY_LOADING_ENABLED = True

print("✅ PythonAnywhere optimizations applied")
