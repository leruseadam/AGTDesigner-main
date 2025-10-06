#!/usr/bin/env python3
"""
PythonAnywhere WSGI configuration for Label Maker application
Updated for Python 3.11 deployment with robust database connection handling
"""

import os
import sys
import logging

# Configure the project directory - UPDATE THIS WITH YOUR USERNAME
# Replace 'yourusername' with your actual PythonAnywhere username
project_dir = '/home/adamcordova/AGTDesigner'

# Verify directory exists and add to Python path
if os.path.exists(project_dir):
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
else:
    # Fallback to current directory if project_dir doesn't exist
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    logging.error(f"Project directory {project_dir} not found, using {current_dir}")

# Add user site-packages to Python path for --user installed packages
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables for PythonAnywhere FIRST
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# PostgreSQL Database Configuration - MUST be set before any imports
os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
os.environ['DB_NAME'] = 'postgres'
os.environ['DB_USER'] = 'super'
os.environ['DB_PASSWORD'] = '193154life'
os.environ['DB_PORT'] = '14822'

# Verify environment variables are set
print(f"DB_HOST: {os.environ.get('DB_HOST', 'NOT SET')}")
print(f"DB_NAME: {os.environ.get('DB_NAME', 'NOT SET')}")
print(f"DB_USER: {os.environ.get('DB_USER', 'NOT SET')}")
print(f"DB_PORT: {os.environ.get('DB_PORT', 'NOT SET')}")

# Configure production logging to prevent BlockingIOError
import logging
import logging.handlers

# CRITICAL: Disable all console logging to prevent BlockingIOError
logging.getLogger().handlers.clear()

# Create a null handler to prevent any logging to stdout/stderr
null_handler = logging.NullHandler()
logging.getLogger().addHandler(null_handler)

# Set all loggers to CRITICAL level to minimize output
logging.getLogger().setLevel(logging.CRITICAL)

# Suppress all library logging
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl', 'psycopg2', 'flask', 'sqlalchemy']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).handlers.clear()
    logging.getLogger(logger_name).addHandler(null_handler)

# Optional: Create file logging (only if needed)
try:
    log_dir = os.path.join(project_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a file handler for critical errors only
    log_file = os.path.join(log_dir, 'critical_errors.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=1024*1024,  # 1MB max file size
        backupCount=2,       # Keep 2 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.CRITICAL)
    
    # Add file handler to root logger
    logging.getLogger().addHandler(file_handler)
    
    print("✅ Production logging configured - critical errors only")
except Exception as e:
    print(f"⚠️ Could not configure file logging: {e}")
    print("✅ Console logging disabled - no BlockingIOError")

try:
    # Test database connection before importing app
    import psycopg2
    print("Testing database connection...")
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ['DB_PORT']
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products;')
    count = cursor.fetchone()[0]
    print(f"✅ Database connection successful! Products: {count}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    # Don't raise here - let the app handle it gracefully
    print("⚠️ Continuing without database connection test...")

try:
    # Import the Flask application
    from app import app
    application = app
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year cache for static files
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max file size
    )
    
    logging.info("WSGI application loaded successfully")
    
except ImportError as e:
    logging.error(f"Failed to import Flask app: {e}")
    logging.error(f"Python path: {sys.path}")
    logging.error(f"Current working directory: {os.getcwd()}")
    logging.error(f"Directory contents: {os.listdir('.')}")
    raise
except Exception as e:
    logging.error(f"Error configuring Flask app: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False)
