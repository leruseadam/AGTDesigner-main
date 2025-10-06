#!/bin/bash
# PythonAnywhere Deployment Script for Label Maker
# Run this script in your PythonAnywhere Bash console after cloning the repository

set -e  # Exit on any error

echo "🚀 Starting PythonAnywhere deployment for Label Maker..."

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

# Step 2: Create virtual environment with Python 3.11
print_status "Creating virtual environment with Python 3.11..."
if ! command -v mkvirtualenv &> /dev/null; then
    print_error "mkvirtualenv not found. Please install virtualenvwrapper first:"
    echo "pip3.11 install --user virtualenvwrapper"
    exit 1
fi

# Remove existing environment if it exists
if [ -d "$HOME/.virtualenvs/labelmaker-env" ]; then
    print_warning "Removing existing virtual environment..."
    rmvirtualenv labelmaker-env || true
fi

mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env
workon labelmaker-env

# Verify Python version
PYTHON_VERSION=$(python --version)
print_status "Using: ${PYTHON_VERSION}"

# Step 3: Upgrade pip and install dependencies
print_status "Installing dependencies..."
pip install --upgrade pip setuptools wheel

# Install packages in order to avoid conflicts
echo "Installing Flask and core dependencies..."
pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0

echo "Installing data processing libraries..."
pip install pandas==2.1.4 python-dateutil==2.8.2 pytz==2023.3

echo "Installing Excel processing libraries..."
pip install openpyxl==3.1.2 xlrd==2.0.1

echo "Installing document processing libraries..."
pip install python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3

echo "Installing image processing..."
pip install Pillow==10.1.0

echo "Installing utility libraries..."
pip install jellyfish==1.2.0 fuzzywuzzy>=0.18.0 requests>=2.32.0

# Try to install python-Levenshtein, but don't fail if it doesn't work
echo "Attempting to install python-Levenshtein (may fail on free accounts)..."
pip install python-Levenshtein>=0.27.0 || print_warning "python-Levenshtein installation failed - will use fallback"

print_status "Dependencies installed successfully"

# Step 4: Create required directories
print_status "Creating required directories..."
mkdir -p uploads output cache sessions logs temp
chmod 755 uploads output cache sessions

# Step 5: Update WSGI file with correct username
print_status "Updating WSGI configuration..."
sed "s/yourusername/${USERNAME}/g" wsgi_pythonanywhere_python311.py > wsgi_configured.py

# Step 6: Initialize database (if needed)
if [ -f "init_database.py" ]; then
    print_status "Initializing database..."
    python init_database.py || print_warning "Database initialization failed - may already exist"
fi

# Step 7: Test the application
print_status "Testing application import..."
python -c "from app import app; print('✅ Application imported successfully')" || {
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
echo "3. Set the WSGI file to: ${PROJECT_DIR}/wsgi_configured.py"
echo "4. Set static files:"
echo "   - URL: /static/"
echo "   - Directory: ${PROJECT_DIR}/static/"
echo "5. Reload your web app"
echo ""
echo "Your WSGI file has been configured for username: ${USERNAME}"
echo "Project directory: ${PROJECT_DIR}"
echo ""
echo "If you encounter issues:"
echo "- Check error logs in the Web tab"
echo "- Verify all dependencies are installed: workon labelmaker-env && pip list"
echo "- Test import: python -c 'from app import app'"
echo ""
print_status "Deployment script completed successfully!"