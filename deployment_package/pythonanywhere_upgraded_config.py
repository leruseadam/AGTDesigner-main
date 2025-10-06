"""
Ultra-Optimized Configuration for Upgraded PythonAnywhere Plan
Maximizes performance with 5 web workers and 8000 CPU seconds
"""

import os
import logging
import gc

# Set environment variables for maximum performance
os.environ['PYTHONANYWHERE_UPGRADED'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'
os.environ['PYTHONANYWHERE_OPTIMIZATION'] = 'True'

# Aggressive memory management for upgraded plan
gc.set_threshold(50, 5, 5)  # More aggressive garbage collection

# Disable verbose logging completely
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'xlrd', 'docxtpl', 'python-docx']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).disabled = True

# Performance constants for upgraded PythonAnywhere
UPGRADED_MAX_CHUNK_SIZE = 50  # Increased from 25
UPGRADED_MAX_PROCESSING_TIME = 30  # Increased from 15
UPGRADED_MAX_TOTAL_TIME = 300  # Increased from 120
UPGRADED_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max (doubled)
UPGRADED_UPLOAD_CHUNK_SIZE = 16384  # 16KB chunks (doubled)

# Enable all optimizations
LAZY_IMPORTS = True
DISABLE_STARTUP_FILE_LOADING = False  # Can enable with more resources
LAZY_LOADING_ENABLED = True
ENABLE_BACKGROUND_PROCESSING = True
ENABLE_ADVANCED_CACHING = True

# Upgraded plan specific settings
UPGRADED_CONFIG = {
    'debug': False,
    'testing': False,
    'max_content_length': 10 * 1024 * 1024,  # 10MB
    'chunk_size_limit': 50,
    'max_processing_time_per_chunk': 30,
    'max_total_processing_time': 300,
    'enable_compression': True,
    'enable_caching': True,
    'cache_ttl': 600,  # 10 minutes (doubled)
    'enable_background_processing': True,
    'max_concurrent_uploads': 3,  # Can handle more with 5 web workers
    'enable_product_db_integration': True,  # Can re-enable with more resources
    'enable_advanced_search': True,
    'enable_real_time_updates': True
}

def get_upgraded_config():
    """Get upgraded PythonAnywhere configuration"""
    return UPGRADED_CONFIG

def apply_upgraded_optimizations():
    """Apply all optimizations for upgraded plan"""
    
    # Force garbage collection
    gc.collect()
    
    # Set memory limits
    import resource
    try:
        # Increase memory limits if possible
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, -1))  # 1GB
    except:
        pass  # Continue if not possible
    
    print("✅ Upgraded PythonAnywhere optimizations applied")
    print(f"   Max file size: {UPGRADED_MAX_FILE_SIZE / (1024*1024):.1f}MB")
    print(f"   Max processing time: {UPGRADED_MAX_TOTAL_TIME}s")
    print(f"   Cache TTL: {UPGRADED_CONFIG['cache_ttl']}s")
    print(f"   Background processing: {UPGRADED_CONFIG['enable_background_processing']}")

# Auto-apply optimizations
apply_upgraded_optimizations()
