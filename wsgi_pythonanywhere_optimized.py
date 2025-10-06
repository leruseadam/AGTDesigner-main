#!/usr/bin/env python3.11
"""
PythonAnywhere WSGI configuration for Label Maker application
Optimized for production deployment with large database
"""

import os
import sys
import logging
import site

# Configure the project directory
project_dir = '/home/adamcordova/AGTDesigner'

# Add project to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Add user site-packages for --user installed packages
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables for PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure minimal logging for production
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s - %(message)s'
)

# Suppress verbose logging from libraries
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'docxcompose']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

try:
    # Import the Flask application
    from app import app as application
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year cache for static files
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max file size
        SECRET_KEY=os.environ.get('SECRET_KEY', 'production-secret-key-change-me'),
    )
    
    print("✅ WSGI application loaded successfully")
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📦 Python path: {sys.path[:3]}...")  # Show first 3 paths
    
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    raise
except Exception as e:
    print(f"❌ Error configuring Flask app: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False, host='0.0.0.0', port=5000)
