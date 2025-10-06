#!/usr/bin/env python3
"""
Debug WSGI configuration for PythonAnywhere
Provides detailed error information and diagnostics
"""

import os
import sys
import logging
import traceback
from datetime import datetime

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def debug_environment():
    """Print detailed environment information"""
    logger.info("=" * 60)
    logger.info("WSGI DEBUG INFORMATION")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # User information
    logger.info(f"User: {os.environ.get('USER', 'unknown')}")
    logger.info(f"Home directory: {os.path.expanduser('~')}")
    
    # Environment variables
    logger.info("Environment variables:")
    for key in ['PYTHONANYWHERE_DOMAIN', 'PYTHONANYWHERE_SITE', 'FLASK_ENV', 'PATH']:
        value = os.environ.get(key, 'NOT SET')
        logger.info(f"  {key}: {value}")

def debug_paths():
    """Debug Python path setup"""
    logger.info("Python path setup:")
    
    # Project directory
    project_dir = '/home/adamcordova/AGTDesigner'
    logger.info(f"Target project directory: {project_dir}")
    logger.info(f"Project directory exists: {os.path.exists(project_dir)}")
    
    if os.path.exists(project_dir):
        logger.info(f"Project directory contents: {os.listdir(project_dir)[:10]}")
        
        # Check for key files
        key_files = ['app.py', 'requirements.txt', 'src/__init__.py']
        for file in key_files:
            file_path = os.path.join(project_dir, file)
            logger.info(f"  {file}: {'EXISTS' if os.path.exists(file_path) else 'MISSING'}")
    
    # Python path
    logger.info(f"Current sys.path ({len(sys.path)} entries):")
    for i, path in enumerate(sys.path[:10]):
        logger.info(f"  [{i}] {path}")
    if len(sys.path) > 10:
        logger.info(f"  ... and {len(sys.path) - 10} more entries")

def test_imports():
    """Test critical imports"""
    logger.info("Testing critical imports:")
    
    imports_to_test = [
        'flask',
        'pandas', 
        'openpyxl',
        'docxtpl',
        'src',
        'src.core',
        'src.core.data',
        'app'
    ]
    
    for module in imports_to_test:
        try:
            if module == 'app':
                from app import app
                logger.info(f"  ✅ {module}: SUCCESS")
            else:
                __import__(module)
                logger.info(f"  ✅ {module}: SUCCESS")
        except ImportError as e:
            logger.error(f"  ❌ {module}: IMPORT ERROR - {e}")
        except Exception as e:
            logger.error(f"  ⚠️  {module}: OTHER ERROR - {e}")

# Configure the project directory
project_dir = '/home/adamcordova/AGTDesigner'

# Run diagnostics
debug_environment()
debug_paths()

# Set up Python path
if os.path.exists(project_dir):
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
        logger.info(f"Added project directory to Python path: {project_dir}")
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    logger.error(f"Project directory {project_dir} not found, using {current_dir}")

# Add user site-packages
try:
    import site
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
        logger.info(f"Added user site-packages to Python path: {user_site}")
except Exception as e:
    logger.error(f"Error adding user site-packages: {e}")

# Test imports
test_imports()

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

try:
    logger.info("Attempting to import Flask application...")
    from app import app as application
    logger.info("✅ Flask application imported successfully!")
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    
    logger.info("✅ Flask application configured successfully!")
    logger.info("=" * 60)
    
except ImportError as e:
    logger.error("=" * 60)
    logger.error("IMPORT ERROR DETAILS")
    logger.error("=" * 60)
    logger.error(f"Import error: {e}")
    logger.error(f"Full traceback:")
    logger.error(traceback.format_exc())
    
    logger.error("Debug information:")
    logger.error(f"Current directory: {os.getcwd()}")
    logger.error(f"Directory contents: {os.listdir('.')}")
    logger.error(f"Python path: {sys.path}")
    
    raise
    
except Exception as e:
    logger.error("=" * 60)
    logger.error("GENERAL ERROR DETAILS")
    logger.error("=" * 60)
    logger.error(f"Error: {e}")
    logger.error(f"Full traceback:")
    logger.error(traceback.format_exc())
    raise

# For direct execution
if __name__ == "__main__":
    logger.info("Running Flask application directly...")
    application.run(debug=True, host='0.0.0.0', port=5000)