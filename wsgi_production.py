#!/usr/bin/env python3
"""
Production WSGI for Custom PythonAnywhere Plan
No print statements - uses logging only
"""

import os
import sys
import logging

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['PYTHONANYWHERE_CUSTOM_PLAN'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging for production
logging.basicConfig(level=logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Set project directory
USERNAME = 'adamcordova'
project_dir = f'/home/{USERNAME}/AGTDesigner'

# Change to project directory
if os.path.exists(project_dir):
    os.chdir(project_dir)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

# Add user site-packages
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

try:
    # Import Flask app
    from app import app as application
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=1200,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
        PERMANENT_SESSION_LIFETIME=3600,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=None,
    )
    
    # Log successful configuration
    logging.info("Production WSGI configuration complete")
    
except ImportError as e:
    logging.critical(f"Failed to import Flask app: {e}")
    raise
except Exception as e:
    logging.critical(f"Error configuring Flask app: {e}")
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False, threaded=True)
