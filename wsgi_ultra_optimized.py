#!/usr/bin/env python3
"""
Ultra-optimized WSGI configuration for PythonAnywhere
Includes aggressive performance optimizations for file upload and document generation
"""

import os
import sys
import logging

# Aggressive performance setup
os.environ['PYTHONANYWHERE_OPTIMIZATION'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Memory optimization
import gc
gc.set_threshold(100, 10, 10)

# Configure the project directory
USERNAME = 'adamcordova'  # Update this if needed
project_dir = f'/home/{USERNAME}/AGTDesigner'

# Add to Python path
if os.path.exists(project_dir):
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

# Add user site-packages
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Disable all logging for maximum performance
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'xlrd', 'docxtpl', 'python-docx']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).disabled = True

try:
    # Import performance optimizations first
    try:
        from pythonanywhere_optimizations import *
        from apply_optimizations import apply_optimizations_to_app
        apply_optimizations_to_app()
    except ImportError:
        pass  # Continue without optimizations if not available
    
    # Import the Flask application
    from app import app as application
    
    # Apply ultra-fast handlers if available
    try:
        from fast_upload_handler import create_fast_upload_handler
        from fast_docx_generator import create_fast_generator_routes
        
        application = create_fast_upload_handler(application)
        create_fast_generator_routes(application)
        
        print("✅ Fast handlers applied")
    except ImportError:
        print("⚠️ Fast handlers not available")
    
    # Ultra-aggressive production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=300,  # 5 minutes
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB max
        PERMANENT_SESSION_LIFETIME=900,  # 15 minutes
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=None,
    )
    
    # Force garbage collection
    gc.collect()
    
except ImportError as e:
    logging.critical(f"Failed to import Flask app: {e}")
    raise
except Exception as e:
    logging.critical(f"Error configuring Flask app: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False, threaded=True)
