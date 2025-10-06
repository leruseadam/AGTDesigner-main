#!/usr/bin/env python3
"""
Ultra-Optimized WSGI for Custom PythonAnywhere Plan
Maximizes performance with 6 web workers, 20GB disk, 7000 CPU seconds/day
"""

import os
import sys
import logging
import gc
import threading
import multiprocessing

# Custom plan environment setup
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['PYTHONANYWHERE_CUSTOM_PLAN'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Aggressive memory optimization for custom plan
gc.set_threshold(100, 10, 10)  # More aggressive garbage collection
gc.enable()

# Configure the project directory
USERNAME = 'adamcordova'
project_dir = f'/home/{USERNAME}/AGTDesigner'

# Ensure we're in the right directory
if os.path.exists(project_dir):
    os.chdir(project_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

# Add user site-packages for custom plan
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Ultra-aggressive logging optimization for custom plan
logging.getLogger().setLevel(logging.ERROR)  # Only show errors
for logger_name in [
    'werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'xlrd', 
    'docxtpl', 'python-docx', 'flask', 'sqlalchemy', 'psutil'
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
    logging.getLogger(logger_name).disabled = False  # Keep minimal logging

# Custom plan specific optimizations
try:
    # Import and apply custom plan optimizations
    try:
        from pythonanywhere_custom_plan_optimizations import apply_custom_plan_optimizations
        apply_custom_plan_optimizations()
        logging.info("Custom plan optimizations applied")
    except ImportError:
        logging.warning("Custom plan optimizations not available")
    
    # Import the Flask application
    from app import app as application
    
    # Apply enhanced handlers for custom plan
    try:
        from custom_plan_upload_handler import create_custom_plan_upload_handler
        from fast_tag_generator import create_fast_tag_generator
        from fast_docx_generator import create_fast_generator_routes
        
        application = create_custom_plan_upload_handler(application)
        application = create_fast_tag_generator(application)
        create_fast_generator_routes(application)
        
        logging.info("Custom plan handlers applied")
    except ImportError:
        logging.warning("Custom plan handlers not available")
    
    # Custom plan configuration - optimized for 6 web workers
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=1200,  # 20 minutes (maximized)
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max (custom plan limit)
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour (maximized)
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=None,
        
        # Custom plan specific settings
        MAX_CONCURRENT_UPLOADS=6,  # Match web workers
        ENABLE_BACKGROUND_PROCESSING=True,
        ENABLE_ADVANCED_CACHING=True,
        CACHE_TTL=1200,  # 20 minutes
        ENABLE_MULTI_THREADING=True,
        MAX_THREADS_PER_WORKER=4,
        
        # Database optimizations for custom plan
        SQLALCHEMY_ENGINE_OPTIONS={
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 20
        },
        
        # File handling optimizations
        UPLOAD_FOLDER='/home/adamcordova/AGTDesigner/uploads',
        MAX_UPLOAD_SIZE=50 * 1024 * 1024,  # 50MB
        ALLOWED_EXTENSIONS={'xlsx', 'xls', 'docx'},
        
        # Performance optimizations
        COMPRESS_MIMETYPES=[
            'text/html', 'text/css', 'text/javascript', 'application/javascript',
            'application/json', 'application/xml', 'image/svg+xml'
        ],
        COMPRESS_LEVEL=6,
        COMPRESS_MIN_SIZE=500,
    )
    
    # Force garbage collection and memory optimization
    gc.collect()
    
    # Custom plan startup logging
    logging.info("Custom Plan WSGI Configuration Complete")
    logging.info("Optimized for: 6 Web Workers, 20GB Disk Space, 7000 CPU Seconds/Day, 4 Always-On Tasks, Postgres Enabled, Enhanced Performance Mode")
    
except ImportError as e:
    logging.critical(f"Failed to import Flask app: {e}")
    raise
except Exception as e:
    logging.critical(f"Error configuring Flask app: {e}")
    raise

# For direct execution (development)
if __name__ == "__main__":
    application.run(
        debug=False, 
        threaded=True,
        host='0.0.0.0',
        port=5000,
        processes=1  # Let PythonAnywhere handle multiple workers
    )