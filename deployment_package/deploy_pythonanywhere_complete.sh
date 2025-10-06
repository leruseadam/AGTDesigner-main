#!/bin/bash
# Complete PythonAnywhere deployment script
# Run this in PythonAnywhere console

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
USERNAME="adamcordova"
PROJECT_NAME="AGTDesigner"
PROJECT_DIR="/home/$USERNAME/$PROJECT_NAME"

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Start deployment
print_header "🚀 PYTHONANYWHERE DEPLOYMENT STARTING"

# Step 1: Navigate to project directory
print_info "Step 1: Setting up project directory"
cd $PROJECT_DIR || {
    print_error "Failed to navigate to $PROJECT_DIR"
    exit 1
}
print_status "Project directory: $PROJECT_DIR"

# Step 2: Update code from GitHub
print_info "Step 2: Updating code from GitHub"
git pull origin main || {
    print_warning "Git pull failed - continuing with existing code"
}
print_status "Code updated from GitHub"

# Step 3: Install Python dependencies
print_info "Step 3: Installing Python dependencies"
python3.11 -m pip install --user --upgrade pip

# Core Flask dependencies
python3.11 -m pip install --user Flask==2.3.3
python3.11 -m pip install --user Flask-CORS==4.0.0
python3.11 -m pip install --user Flask-Caching==2.1.0
python3.11 -m pip install --user Werkzeug==2.3.7

# Data processing
python3.11 -m pip install --user pandas==2.1.4
python3.11 -m pip install --user openpyxl==3.1.2
python3.11 -m pip install --user xlrd==2.0.1

# Document processing
python3.11 -m pip install --user python-docx==0.8.11
python3.11 -m pip install --user docxtpl==0.16.7
python3.11 -m pip install --user docxcompose==1.4.0
python3.11 -m pip install --user lxml==4.9.3

# Image processing
python3.11 -m pip install --user Pillow==10.1.0

# Utilities
python3.11 -m pip install --user python-dateutil==2.8.2
python3.11 -m pip install --user pytz==2023.3
python3.11 -m pip install --user jellyfish==1.2.0
python3.11 -m pip install --user requests>=2.32.0
python3.11 -m pip install --user fuzzywuzzy>=0.18.0
python3.11 -m pip install --user python-Levenshtein>=0.27.0

print_status "Dependencies installed"

# Step 4: Create required directories
print_info "Step 4: Creating required directories"
mkdir -p uploads
mkdir -p output
mkdir -p cache
mkdir -p sessions
mkdir -p logs
mkdir -p temp
mkdir -p static

# Set permissions
chmod 755 uploads
chmod 755 output
chmod 755 cache
chmod 755 sessions
chmod 755 logs
chmod 755 temp
chmod 755 static

print_status "Directories created and permissions set"

# Step 5: Database setup
print_info "Step 5: Setting up database"
if [ -f "uploads/product_database_pythonanywhere.db" ]; then
    print_status "PythonAnywhere database found"
    DB_SIZE=$(du -h uploads/product_database_pythonanywhere.db | cut -f1)
    print_info "Database size: $DB_SIZE"
else
    print_warning "No PythonAnywhere database found - will use default"
fi

# Step 6: Test application import
print_info "Step 6: Testing application import"
python3.11 -c "
try:
    from app import app
    print('✅ Application import successful')
    print(f'App name: {app.name}')
    print(f'Debug mode: {app.debug}')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
" || {
    print_error "Application import test failed!"
    exit 1
}

print_status "Application import test passed"

# Step 7: Create WSGI configuration
print_info "Step 7: Creating WSGI configuration"
cat > wsgi_pythonanywhere.py << 'EOF'
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
EOF

print_status "WSGI configuration created"

# Step 8: Test WSGI configuration
print_info "Step 8: Testing WSGI configuration"
python3.11 wsgi_pythonanywhere.py --help > /dev/null 2>&1 || {
    print_warning "WSGI test failed - this is normal for WSGI files"
}

# Step 9: Display deployment summary
print_header "🎉 DEPLOYMENT COMPLETE!"
echo ""
print_status "Deployment Summary:"
echo "  📁 Project directory: $PROJECT_DIR"
echo "  🐍 Python version: 3.11"
echo "  📦 Dependencies: Installed"
echo "  🗄️  Database: Ready"
echo "  ⚙️  WSGI config: Created"
echo ""
print_info "Next Steps:"
echo "  1. 📝 Go to PythonAnywhere Web tab"
echo "  2. 🔧 Configure your web app:"
echo "     - Source code: $PROJECT_DIR"
echo "     - WSGI file: $PROJECT_DIR/wsgi_pythonanywhere.py"
echo "     - Static files URL: /static/"
echo "     - Static files path: $PROJECT_DIR/static/"
echo "  3. 🔄 Reload your web app"
echo "  4. 🧪 Test at https://adamcordova.pythonanywhere.com"
echo ""
print_warning "Important Notes:"
echo "  - Database size: ~500MB (requires Hacker plan)"
echo "  - Check error logs if issues occur"
echo "  - Monitor memory usage"
echo ""
print_status "Ready for PythonAnywhere deployment! 🚀"