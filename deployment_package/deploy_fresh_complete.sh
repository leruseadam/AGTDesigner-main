#!/bin/bash

# =============================================================================
# 🚀 FRESH LABEL MAKER DEPLOYMENT SCRIPT
# =============================================================================
# This script will:
# 1. Clean up any existing deployment
# 2. Clone fresh repository from GitHub
# 3. Set up virtual environment
# 4. Install dependencies
# 5. Set up database with all data
# 6. Configure WSGI for production
# 7. Test the deployment
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting Fresh Label Maker Deployment..."
echo "============================================="

# Configuration
PROJECT_NAME="labelMaker"
REPO_URL="https://github.com/leruseadam/AGTDesigner.git"
PYTHON_VERSION="3.11"
VENV_NAME="labelmaker-env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're on PythonAnywhere
check_pythonanywhere() {
    if [[ "$HOSTNAME" == *"pythonanywhere"* ]] || [[ -d "/home/$USER" ]]; then
        log_info "Detected PythonAnywhere environment"
        return 0
    else
        log_info "Detected local development environment"
        return 1
    fi
}

# Step 1: Clean up existing deployment
log_info "Step 1: Cleaning up existing deployment..."

# Remove old project directory if it exists
if [ -d "$HOME/$PROJECT_NAME" ]; then
    log_warning "Removing existing project directory: $HOME/$PROJECT_NAME"
    rm -rf "$HOME/$PROJECT_NAME"
fi

# Remove old virtual environment if it exists
if [ -d "$HOME/.virtualenvs/$VENV_NAME" ]; then
    log_warning "Removing existing virtual environment: $VENV_NAME"
    rm -rf "$HOME/.virtualenvs/$VENV_NAME"
fi

log_success "Cleanup completed"

# Step 2: Clone fresh repository
log_info "Step 2: Cloning fresh repository..."

cd "$HOME"
if git clone "$REPO_URL" "$PROJECT_NAME"; then
    log_success "Repository cloned successfully"
else
    log_error "Failed to clone repository"
    exit 1
fi

cd "$HOME/$PROJECT_NAME"

# Step 3: Set up virtual environment
log_info "Step 3: Setting up virtual environment..."

# Check if we're on PythonAnywhere
if check_pythonanywhere; then
    # PythonAnywhere setup
    if command -v mkvirtualenv >/dev/null 2>&1; then
        log_info "Creating virtual environment using mkvirtualenv..."
        mkvirtualenv --python=python$PYTHON_VERSION $VENV_NAME
    else
        log_info "mkvirtualenv not available, using python -m venv..."
        mkdir -p "$HOME/.virtualenvs"
        python$PYTHON_VERSION -m venv "$HOME/.virtualenvs/$VENV_NAME"
    fi
    
    # Activate virtual environment
    source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
else
    # Local development setup
    log_info "Creating virtual environment locally..."
    python$PYTHON_VERSION -m venv venv
    source venv/bin/activate
fi

log_success "Virtual environment created and activated"

# Step 4: Install dependencies
log_info "Step 4: Installing dependencies..."

# Upgrade pip first
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    log_info "Installing from requirements.txt..."
    pip install -r requirements.txt
else
    log_warning "requirements.txt not found, installing basic dependencies..."
    pip install Flask==2.3.3 Flask-CORS==4.0.0 pandas==2.1.4 openpyxl==3.1.2 python-docx==0.8.11 docxtpl==0.16.7 Pillow==10.1.0
fi

log_success "Dependencies installed"

# Step 5: Set up directories
log_info "Step 5: Setting up directories..."

# Create necessary directories
mkdir -p uploads
mkdir -p temp
mkdir -p sessions
mkdir -p logs
mkdir -p static/fonts
mkdir -p templates

# Set permissions
chmod 755 uploads temp sessions logs

log_success "Directories created"

# Step 6: Set up database
log_info "Step 6: Setting up database..."

# Check if database files exist from the repository
if [ -f "uploads/product_database.db" ]; then
    log_success "Main database file already exists"
elif [ -f "uploads/product_database_AGT_Bothell.db" ]; then
    # Copy AGT Bothell database as main database
    cp "uploads/product_database_AGT_Bothell.db" "uploads/product_database.db"
    log_success "AGT Bothell database copied as main database"
else
    log_info "Creating new database..."
    
    # Create database initialization script
    cat > init_database_fresh.py << 'EOF'
#!/usr/bin/env python3
"""
Initialize fresh database for Label Maker
"""
import os
import sys
import sqlite3
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def create_database():
    """Create a fresh database with proper schema"""
    db_path = os.path.join('uploads', 'product_database.db')
    
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create products table with all necessary columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductName TEXT,
            "Product Name*" TEXT,
            Vendor TEXT,
            "Product Brand" TEXT,
            "Product Type*" TEXT,
            "Product Strain" TEXT,
            Lineage TEXT,
            Description TEXT,
            "Price*" REAL,
            "Weight*" REAL,
            Units TEXT,
            "Quantity*" INTEGER,
            "THC test result" REAL,
            "CBD test result" REAL,
            "Test result unit (% or mg)" TEXT,
            "Room*" TEXT,
            State TEXT,
            "Is Sample? (yes/no)" TEXT,
            "Is MJ product?(yes/no)" TEXT,
            "Discountable? (yes/no)" TEXT,
            "Medical Only (Yes/No)" TEXT,
            DOH TEXT,
            Ratio TEXT,
            source TEXT DEFAULT 'excel',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_name ON products(ProductName)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_name_star ON products("Product Name*")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor ON products(Vendor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_brand ON products("Product Brand")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_strain ON products("Product Strain")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_type ON products("Product Type*")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lineage ON products(Lineage)')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created successfully: {db_path}")
    return True

if __name__ == "__main__":
    create_database()
EOF

    # Run database initialization
    python init_database_fresh.py
    log_success "Database initialized"
fi

# Step 7: Create WSGI configuration
log_info "Step 7: Creating WSGI configuration..."

cat > wsgi.py << 'EOF'
#!/usr/bin/env python3
"""
WSGI configuration for Label Maker application
Optimized for PythonAnywhere deployment
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the project directory to the Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add the src directory to the Python path
src_path = os.path.join(project_home, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # Set environment variables for production
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('PYTHONANYWHERE_MODE', 'true')
    os.environ.setdefault('DISABLE_STARTUP_FILE_LOADING', 'true')
    
    # Import and create the Flask application
    from app import app as application
    
    # Ensure necessary directories exist
    uploads_dir = os.path.join(project_home, 'uploads')
    temp_dir = os.path.join(project_home, 'temp')
    sessions_dir = os.path.join(project_home, 'sessions')
    logs_dir = os.path.join(project_home, 'logs')
    
    for directory in [uploads_dir, temp_dir, sessions_dir, logs_dir]:
        os.makedirs(directory, exist_ok=True)
    
    logging.info("✅ WSGI application loaded successfully")
    logging.info(f"✅ Project home: {project_home}")
    logging.info(f"✅ Python paths: {sys.path[:3]}...")
    
except Exception as e:
    logging.error(f"❌ Failed to load WSGI application: {e}")
    import traceback
    logging.error(traceback.format_exc())
    raise

# For debugging - this will be logged in the error log
if __name__ == "__main__":
    logging.info("WSGI module loaded successfully")
EOF

log_success "WSGI configuration created"

# Step 8: Create production config
log_info "Step 8: Creating production configuration..."

cat > config_production.py << 'EOF'
import os
from config import Config

class ProductionConfig(Config):
    """Production configuration for PythonAnywhere"""
    DEBUG = False
    DEVELOPMENT_MODE = False
    TEMPLATES_AUTO_RELOAD = False
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache
    
    # Production secret key - change this in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'label-maker-production-2024-secure-change-me')
    
    # Production optimizations
    PYTHONANYWHERE_MODE = True
    DISABLE_STARTUP_FILE_LOADING = True
    
    # Reduce memory usage for PythonAnywhere
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # Shorter session lifetime for production
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'product_database.db')
EOF

log_success "Production configuration created"

# Step 9: Create startup script for easy maintenance
log_info "Step 9: Creating maintenance scripts..."

cat > test_deployment.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify deployment is working correctly
"""
import os
import sys

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flask
        import pandas
        import openpyxl
        import docx
        from PIL import Image
        print("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connectivity"""
    db_path = 'uploads/product_database.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"✅ Database accessible with {count} products")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_app():
    """Test that the app can be imported and configured"""
    try:
        sys.path.insert(0, '.')
        sys.path.insert(0, 'src')
        from app import app
        print("✅ Flask app imported successfully")
        print(f"✅ Debug mode: {app.config.get('DEBUG', 'Not set')}")
        print(f"✅ Upload folder: {app.config.get('UPLOAD_FOLDER', 'Not set')}")
        return True
    except Exception as e:
        print(f"❌ App test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_directories():
    """Test that all required directories exist"""
    required_dirs = ['uploads', 'temp', 'sessions', 'logs', 'static', 'templates', 'src']
    all_exist = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("🧪 Testing Label Maker Deployment")
    print("=" * 40)
    
    tests = [
        ("Directories", test_directories),
        ("Module Imports", test_imports),
        ("Database", test_database),
        ("Flask App", test_app)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Deployment is ready.")
        exit(0)
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        exit(1)
EOF

chmod +x test_deployment.py

log_success "Maintenance scripts created"

# Step 10: Test the application
log_info "Step 10: Testing the application..."

# Test import
if python test_deployment.py; then
    log_success "Application test passed"
else
    log_error "Application test failed"
    exit 1
fi

# Step 11: Create deployment summary
log_info "Step 11: Creating deployment summary..."

cat > DEPLOYMENT_SUMMARY.md << EOF
# 🚀 Fresh Deployment Summary

## ✅ Deployment Completed Successfully!

**Deployed on:** $(date)
**Project Location:** $HOME/$PROJECT_NAME
**Virtual Environment:** $HOME/.virtualenvs/$VENV_NAME
**Repository:** $REPO_URL

## 📁 Directory Structure:
- **Application Code:** $HOME/$PROJECT_NAME/
- **Database:** $HOME/$PROJECT_NAME/uploads/product_database.db
- **Static Files:** $HOME/$PROJECT_NAME/static/
- **Templates:** $HOME/$PROJECT_NAME/templates/
- **Uploads:** $HOME/$PROJECT_NAME/uploads/
- **Logs:** $HOME/$PROJECT_NAME/logs/
- **Source Code:** $HOME/$PROJECT_NAME/src/

## � Configuration Files:
- **WSGI:** wsgi.py (Production-ready)
- **Config:** config_production.py
- **Requirements:** requirements.txt
- **Test Script:** test_deployment.py

## 📊 Next Steps for PythonAnywhere:

### 1. Web App Configuration:
1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app** (or **Delete** and recreate existing)
3. Choose **Manual configuration**
4. Select **Python 3.11**

### 2. Set Configuration:
- **Source code:** \`$HOME/$PROJECT_NAME\`
- **WSGI file:** \`$HOME/$PROJECT_NAME/wsgi.py\`
- **Virtual environment:** \`$HOME/.virtualenvs/$VENV_NAME\`

### 3. Static Files Mapping:
- **URL:** \`/static/\`
- **Directory:** \`$HOME/$PROJECT_NAME/static/\`

### 4. Environment Variables (Optional):
- **FLASK_ENV:** production
- **PYTHONANYWHERE_MODE:** true
- **SECRET_KEY:** your-secure-secret-key

### 5. Reload and Test:
- Click **Reload** button
- Visit: \`https://yourusername.pythonanywhere.com\`
- Test with: \`cd $HOME/$PROJECT_NAME && python test_deployment.py\`

## 🔍 Troubleshooting:
- **Error logs:** PythonAnywhere **Web** tab → **Error log**
- **Test deployment:** \`cd $HOME/$PROJECT_NAME && python test_deployment.py\`
- **Activate venv:** \`workon $VENV_NAME\`
- **Check imports:** \`cd $HOME/$PROJECT_NAME && python -c "from app import app; print('OK')"\`

## 📋 What's Included:
✅ Complete Flask application with all routes and features
✅ Database setup with proper schema
✅ Excel file upload and processing functionality
✅ Label generation with QR codes
✅ Product matching and filtering
✅ Responsive web interface
✅ Session management
✅ File handling and cleanup
✅ Error handling and logging
✅ Production-optimized configuration

## 🎯 Key Features:
- **Label Generation:** QR codes, multiple templates, bulk processing
- **Product Management:** Database integration, Excel upload, filtering
- **Data Processing:** JSON matching, strain categorization, validation
- **User Interface:** Modern responsive design, real-time feedback
- **Performance:** Optimized for PythonAnywhere deployment

## 🔄 Update Process:
To update the deployment with new code:
\`\`\`bash
cd $HOME/$PROJECT_NAME
git pull origin main
workon $VENV_NAME
pip install -r requirements.txt
# In PythonAnywhere Web tab: click Reload
\`\`\`

Ready to go live! 🎉
EOF

# Create quick reference file
cat > QUICK_REFERENCE.md << 'EOF'
# 🚀 Label Maker - Quick Reference

## Essential Commands:
```bash
# Activate environment
workon labelmaker-env

# Test deployment
cd ~/labelMaker && python test_deployment.py

# Check application status
cd ~/labelMaker && python -c "from app import app; print('✅ App OK')"

# View error logs (PythonAnywhere)
# Go to Web tab → Error log

# Update from GitHub
cd ~/labelMaker && git pull origin main
```

## File Locations:
- **App:** `~/labelMaker/app.py`
- **WSGI:** `~/labelMaker/wsgi.py` 
- **Database:** `~/labelMaker/uploads/product_database.db`
- **Config:** `~/labelMaker/config_production.py`

## PythonAnywhere Settings:
- **Source code:** `/home/yourusername/labelMaker`
- **WSGI file:** `/home/yourusername/labelMaker/wsgi.py`
- **Virtual env:** `/home/yourusername/.virtualenvs/labelmaker-env`
- **Static files:** `/static/` → `/home/yourusername/labelMaker/static/`

## Common Issues:
- **Import errors:** Check virtual environment is active
- **Database errors:** Verify `uploads/product_database.db` exists
- **Static files:** Ensure static file mapping is configured
- **Memory errors:** Restart web app, check file sizes
EOF

# Final success message
echo ""
echo "============================================="
log_success "🎉 FRESH DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉"
echo "============================================="
echo ""
log_info "� Project Location: $HOME/$PROJECT_NAME"
log_info "� Virtual Environment: $HOME/.virtualenvs/$VENV_NAME"
log_info "� Database: $HOME/$PROJECT_NAME/uploads/product_database.db"
log_info "🌐 WSGI File: $HOME/$PROJECT_NAME/wsgi.py"
log_info "🔧 Test Script: $HOME/$PROJECT_NAME/test_deployment.py"
echo ""
log_info "📋 Next Steps:"
log_info "1. Configure your PythonAnywhere web app (see DEPLOYMENT_SUMMARY.md)"
log_info "2. Set WSGI file to: $HOME/$PROJECT_NAME/wsgi.py"
log_info "3. Set virtual environment to: $HOME/.virtualenvs/$VENV_NAME"
log_info "4. Add static files mapping: /static/ → $HOME/$PROJECT_NAME/static/"
log_info "5. Reload your web app"
log_info "6. Test with: python test_deployment.py"
echo ""
log_success "🚀 Your Label Maker is ready to deploy!"
echo ""
log_info "� Quick commands:"
log_info "   • Test: cd $HOME/$PROJECT_NAME && python test_deployment.py"
log_info "   • Update: cd $HOME/$PROJECT_NAME && git pull origin main"
log_info "   • Activate env: workon $VENV_NAME"
echo ""

# Deactivate virtual environment
deactivate || true

exit 0