"""
Production configuration for AGT Label Maker
"""
import os

# Basic Flask settings
DEBUG = False
TESTING = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# File upload settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = 'uploads'

# Database configuration
DATABASE_PATH = 'uploads/product_database_AGT_Bothell.db'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Performance settings
SEND_FILE_MAX_AGE_DEFAULT = 300  # 5 minutes cache for static files
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes session timeout
