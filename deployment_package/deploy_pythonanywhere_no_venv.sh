#!/bin/bash
# PythonAnywhere Deployment Script for Label Maker (No Virtual Environment)
# Run this script in your PythonAnywhere Bash console after cloning the repository

set -e  # Exit on any error

echo "🚀 Starting PythonAnywhere deployment for Label Maker (No Virtual Environment)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get the username
USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

print_status "Deployment starting for user: ${USERNAME}"
print_status "Project directory: ${PROJECT_DIR}"

# Step 1: Verify we're in the right directory
if [ ! -f "app.py" ]; then
    print_error "app.py not found. Please run this script from the project directory."
    exit 1
fi

print_status "Project files verified"

# Step 2: Verify Python 3.11 is available
PYTHON_VERSION=$(python3.11 --version 2>/dev/null || echo "not found")
if [[ "$PYTHON_VERSION" == "not found" ]]; then
    print_error "Python 3.11 not found. Please contact PythonAnywhere support."
    exit 1
fi

print_status "Using: ${PYTHON_VERSION}"

# Step 3: Install dependencies globally for user
print_status "Installing dependencies for Python 3.11 (no virtual environment)..."

# Upgrade pip first
python3.11 -m pip install --user --upgrade pip setuptools wheel

# Install packages in order to avoid conflicts
echo "Installing Flask and core dependencies..."
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0

echo "Installing data processing libraries..."
python3.11 -m pip install --user pandas==2.1.4 python-dateutil==2.8.2 pytz==2023.3

echo "Installing Excel processing libraries..."
python3.11 -m pip install --user openpyxl==3.1.2 xlrd==2.0.1

echo "Installing document processing libraries..."
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3

echo "Installing image processing..."
python3.11 -m pip install --user Pillow==10.1.0

echo "Installing utility libraries..."
python3.11 -m pip install --user jellyfish==1.2.0 fuzzywuzzy>=0.18.0 requests>=2.32.0

# Try to install python-Levenshtein, but don't fail if it doesn't work
echo "Attempting to install python-Levenshtein (may fail on free accounts)..."
python3.11 -m pip install --user python-Levenshtein>=0.27.0 || print_warning "python-Levenshtein installation failed - will use fallback"

print_status "Dependencies installed successfully"

# Step 4: Create required directories
print_status "Creating required directories..."
mkdir -p uploads output cache sessions logs temp
chmod 755 uploads output cache sessions

# Step 5: Update WSGI file with correct username and Python path
print_status "Creating WSGI configuration for no virtual environment..."
cat > wsgi_configured_no_venv.py << EOF
#!/usr/bin/env python3
"""
PythonAnywhere WSGI configuration for Label Maker application
Updated for Python 3.11 deployment (No Virtual Environment)
"""

import os
import sys
import logging

# Configure the project directory
project_dir = '/home/${USERNAME}/AGTDesigner'

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
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables for PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging to prevent verbose output
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Suppress verbose logging from libraries
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl']:
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
EOF

# Step 6: Initialize database
print_status "Initializing database..."
if [ -f "init_pythonanywhere_database.py" ]; then
    python3.11 init_pythonanywhere_database.py
else
    print_warning "init_pythonanywhere_database.py not found - skipping database init"
fi

# Step 6.5: Import data if available
if [ -f "database_export.json" ] && [ -f "import_pythonanywhere_database.py" ]; then
    print_status "Importing database data..."
    python3.11 import_pythonanywhere_database.py || print_warning "Database import failed - will use empty database"
fi

# Step 7: Test the application
print_status "Testing application import..."
python3.11 -c "from app import app; print('✅ Application imported successfully')" || {
    print_error "Application import failed. Check the error messages above."
    exit 1
}

# Step 8: Display next steps
echo ""
print_status "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Go to your PythonAnywhere Web tab"
echo "2. Create a new web app (Manual configuration, Python 3.11)"
echo "3. Set the WSGI file to: ${PROJECT_DIR}/wsgi_configured_no_venv.py"
echo "4. Set static files:"
echo "   - URL: /static/"
echo "   - Directory: ${PROJECT_DIR}/static/"
echo "5. Reload your web app"
echo ""
echo "Your WSGI file has been configured for username: ${USERNAME}"
echo "Project directory: ${PROJECT_DIR}"
echo "Python packages installed to user directory (no virtual environment)"
echo ""
echo "If you encounter issues:"
echo "- Check error logs in the Web tab"
echo "- Verify all dependencies are installed: python3.11 -m pip list --user"
echo "- Test import: python3.11 -c 'from app import app'"
echo ""
print_status "Deployment script completed successfully!"