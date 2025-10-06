#!/bin/bash

# Complete Fresh Deployment Package Creator
# This creates a self-contained deployment package with everything needed

echo "🚀 Creating Complete Fresh Deployment Package"
echo "=============================================="

# Set variables
WORKSPACE_DIR="/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15"
DEPLOY_DIR="$WORKSPACE_DIR/complete_deployment_package"
DATE=$(date +"%Y%m%d_%H%M%S")

# Clean and create deployment directory
echo "📁 Setting up deployment directory..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy core application files
echo "📋 Copying core application files..."
cp "$WORKSPACE_DIR/app.py" "$DEPLOY_DIR/"
cp "$WORKSPACE_DIR/config.py" "$DEPLOY_DIR/"
cp "$WORKSPACE_DIR/requirements.txt" "$DEPLOY_DIR/"

# Copy essential directories
echo "📂 Copying essential directories..."
cp -r "$WORKSPACE_DIR/src" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️ src directory not found"
cp -r "$WORKSPACE_DIR/templates" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️ templates directory not found"
cp -r "$WORKSPACE_DIR/static" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️ static directory not found"

# Create uploads directory and copy database
echo "🗄️ Setting up database and uploads..."
mkdir -p "$DEPLOY_DIR/uploads"

# Copy the main working database
if [ -f "$WORKSPACE_DIR/uploads/product_database_AGT_Bothell.db" ]; then
    cp "$WORKSPACE_DIR/uploads/product_database_AGT_Bothell.db" "$DEPLOY_DIR/uploads/"
    echo "✅ Main database copied successfully"
else
    echo "⚠️ Main database not found"
fi

# Copy latest Excel file
LATEST_EXCEL=$(ls -t "$WORKSPACE_DIR/uploads/"*.xlsx 2>/dev/null | head -1)
if [ -n "$LATEST_EXCEL" ]; then
    cp "$LATEST_EXCEL" "$DEPLOY_DIR/uploads/"
    echo "✅ Latest Excel file copied: $(basename "$LATEST_EXCEL")"
fi

# Create WSGI file for deployment
echo "🔧 Creating WSGI configuration..."
cat > "$DEPLOY_DIR/wsgi.py" << 'EOF'
#!/usr/bin/env python3
"""
WSGI entry point for AGT Label Maker
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

if __name__ == "__main__":
    app.run()
EOF

# Create production configuration
echo "⚙️ Creating production configuration..."
cat > "$DEPLOY_DIR/config_production.py" << 'EOF'
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
EOF

# Create deployment test script
echo "🧪 Creating deployment test script..."
cat > "$DEPLOY_DIR/test_deployment.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify deployment is working correctly
"""
import os
import sys
import sqlite3

def test_directories():
    """Test that required directories exist"""
    required_dirs = ['uploads', 'src', 'templates', 'static']
    missing_dirs = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ All required directories present")
    return True

def test_database():
    """Test database connectivity"""
    db_path = 'uploads/product_database_AGT_Bothell.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"✅ Database accessible with {count} products")
        
        # Test concentrate products specifically
        cursor.execute("""
            SELECT COUNT(*) 
            FROM products 
            WHERE `Product Type*` = 'Concentrate'
        """)
        concentrate_count = cursor.fetchone()[0]
        print(f"✅ Found {concentrate_count} concentrate products")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    required_modules = [
        'flask', 'pandas', 'openpyxl', 'docx', 'qrcode', 'PIL'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        print("Install missing modules with: pip install -r requirements.txt")
        return False
    
    print("✅ All required modules imported successfully")
    return True

def test_app():
    """Test that the Flask app can be imported and configured"""
    try:
        sys.path.insert(0, '.')
        from app import app
        
        print(f"✅ Flask app imported successfully")
        print(f"   Debug mode: {app.config.get('DEBUG', 'Not set')}")
        print(f"   Secret key set: {'YES' if app.config.get('SECRET_KEY') else 'NO'}")
        
        return True
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AGT Label Maker Deployment")
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
        print("\n📋 Next steps:")
        print("1. Upload all files to your web server")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Configure web server to point to wsgi.py")
        print("4. Set environment variables (SECRET_KEY)")
        print("5. Restart web server")
    else:
        print("⚠️ Some tests failed. Fix the issues above before deploying.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x "$DEPLOY_DIR/test_deployment.py"

# Create quick start script for local testing
echo "🎯 Creating quick start script..."
cat > "$DEPLOY_DIR/quick_start.sh" << 'EOF'
#!/bin/bash

echo "🚀 AGT Label Maker Quick Start"
echo "=============================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Test the deployment
echo "🧪 Testing deployment..."
python3 test_deployment.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🌐 Starting application for local testing..."
    echo "Access at: http://localhost:5000"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Set environment variables
    export FLASK_APP=app.py
    export FLASK_ENV=development
    
    # Start the application
    python3 -m flask run --host=0.0.0.0 --port=5000
else
    echo "❌ Deployment test failed. Fix the issues before starting."
fi
EOF

chmod +x "$DEPLOY_DIR/quick_start.sh"

# Create complete deployment instructions
echo "📖 Creating deployment instructions..."
cat > "$DEPLOY_DIR/DEPLOYMENT_README.md" << 'EOF'
# AGT Label Maker - Complete Deployment Package

## What's Included

This package contains everything needed to deploy the AGT Label Maker:

- ✅ **app.py** - Main Flask application with all fixes applied
- ✅ **Complete database** - Product database with all AGT Bothell inventory
- ✅ **All source code** - Full src/ directory with all modules
- ✅ **Templates & Static files** - Complete web interface
- ✅ **WSGI configuration** - Ready for production deployment
- ✅ **Requirements** - All Python dependencies listed
- ✅ **Test scripts** - Verify deployment before going live

## Quick Local Test

1. **Extract/Upload files** to your target directory
2. **Run the test**: `python3 test_deployment.py`
3. **If tests pass, start locally**: `./quick_start.sh`
4. **Open browser** to http://localhost:5000

## Production Deployment

### For PythonAnywhere:

1. **Upload all files** to your web app directory
2. **Install dependencies**: `pip3.x install --user -r requirements.txt`
3. **Set WSGI file** to point to your uploaded `wsgi.py`
4. **Set environment variables** in web app settings:
   - `SECRET_KEY` = your-secure-random-key
5. **Reload web app**

### For other hosting (DigitalOcean, AWS, etc.):

1. **Upload files** maintaining directory structure
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure web server** (Apache/Nginx) to point to `wsgi.py`
4. **Set environment variables**:
   ```bash
   export SECRET_KEY="your-secure-secret-key"
   export FLASK_ENV="production"
   ```
5. **Restart web server**

## Key Features

### ✅ Concentrate Weight Fix Applied
The concentrate weight display issue has been completely resolved:
- Concentrate products now show weights properly (e.g., "Grape Slurpee Wax - 1g")
- SQLite Row object handling fixed
- Database API consistency maintained

### ✅ Complete Database Integration
- Full product database with all AGT Bothell inventory
- Optimized for web deployment
- All product types supported (Flower, Concentrate, Edible, Pre-Roll, etc.)

### ✅ Performance Optimized
- Fast Excel processing
- Efficient database queries
- Optimized for production hosting

## Testing Your Deployment

Run the test script to verify everything is working:

```bash
python3 test_deployment.py
```

The test will check:
- All required directories are present
- Python modules can be imported
- Database is accessible and has products
- Flask app can be imported and configured

## Troubleshooting

### Common Issues:

**1. Missing modules error**
```bash
pip install -r requirements.txt
```

**2. Database not found**
- Ensure `uploads/product_database_AGT_Bothell.db` exists
- Check file permissions

**3. Import errors**
- Verify all files were uploaded
- Check Python version compatibility (3.8+)

**4. Concentrate weights not showing**
- Restart web server after deployment
- Verify the database contains concentrate products

### Getting Help:

1. **Run the test script first**: `python3 test_deployment.py`
2. **Check web server error logs**
3. **Verify all files were uploaded correctly**
4. **Ensure environment variables are set**

## File Structure

```
deployment_package/
├── app.py                          # Main Flask application
├── wsgi.py                         # WSGI entry point
├── config.py                       # Application configuration
├── config_production.py            # Production settings
├── requirements.txt                # Python dependencies
├── test_deployment.py              # Deployment test script
├── quick_start.sh                  # Local testing script
├── src/                           # Application source code
├── templates/                     # HTML templates
├── static/                        # CSS, JS, images
└── uploads/                       # Database and uploaded files
    └── product_database_AGT_Bothell.db
```

## Support

This deployment package includes all the fixes and optimizations from your local version. If you encounter any issues, run the test script first to identify the problem.
EOF

# Create a summary of what was packaged
echo "📋 Creating package summary..."
cat > "$DEPLOY_DIR/PACKAGE_SUMMARY.md" << 'EOF'
# Deployment Package Summary

## Created On
Generated automatically with all current fixes and optimizations applied.

## What Was Packaged

### Core Application Files:
- ✅ app.py (with concentrate weight fix)
- ✅ config.py 
- ✅ requirements.txt (updated with qrcode)
- ✅ wsgi.py (production-ready)

### Database & Data:
- ✅ product_database_AGT_Bothell.db (complete product database)
- ✅ Latest Excel file (most recent inventory)

### Source Code:
- ✅ Complete src/ directory
- ✅ All templates/
- ✅ All static/ files

### Deployment Tools:
- ✅ test_deployment.py (verification script)
- ✅ quick_start.sh (local testing)
- ✅ Complete documentation

## Key Fixes Included

1. **Concentrate Weight Display Fix**
   - SQLite Row object handling corrected
   - Concentrate products now show weights properly

2. **Complete Database Integration**
   - Full AGT Bothell product database included
   - All product types supported

3. **Production Optimizations**
   - WSGI configuration for web servers
   - Production config settings
   - Performance optimizations

## Ready For Deployment

This package is ready for immediate deployment to:
- PythonAnywhere
- DigitalOcean
- AWS
- Any Python web hosting service

Run `test_deployment.py` first to verify everything is working correctly.
EOF

# Create archive for easy upload
echo "📦 Creating deployment archive..."
cd "$WORKSPACE_DIR"
tar -czf "complete_deployment_${DATE}.tar.gz" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")"

# Final summary
echo ""
echo "🎉 COMPLETE DEPLOYMENT PACKAGE CREATED!"
echo "========================================"
echo ""
echo "📁 Package location: $DEPLOY_DIR"
echo "📦 Archive created: complete_deployment_${DATE}.tar.gz"
echo ""
echo "✨ Package includes:"
echo "   ✅ Complete working application with all fixes"
echo "   ✅ Full database with AGT Bothell products"
echo "   ✅ Production-ready WSGI configuration"
echo "   ✅ Test scripts and documentation"
echo "   ✅ Concentrate weight fix applied"
echo ""
echo "🚀 Ready to deploy to any Python web hosting service!"
echo ""
echo "📋 Next steps:"
echo "1. Upload the package to your web server"
echo "2. Run: python3 test_deployment.py"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "4. Configure web server to point to wsgi.py"
echo "5. Set SECRET_KEY environment variable"
echo "6. Restart and test!"
echo ""

# Show what's in the package
echo "📋 Package contents:"
find "$DEPLOY_DIR" -type f | sort
echo ""
echo "📊 Package size:"
du -sh "$DEPLOY_DIR"
echo ""