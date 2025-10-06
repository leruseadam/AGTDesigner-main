#!/bin/bash
# Simple PythonAnywhere Deployment Script
# Run this script on PythonAnywhere after cloning your repository

set -e  # Exit on any error

echo "🚀 PythonAnywhere Deployment Fix"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Get the username
USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

echo "👤 User: $USERNAME"
echo "📁 Project Directory: $PROJECT_DIR"
echo ""

# Step 1: Check if we're in the right directory
if [ ! -f "app.py" ]; then
    print_error "app.py not found. Please run this script from the project directory."
    echo "Current directory contents:"
    ls -la
    exit 1
fi

print_status "Found app.py - we're in the right directory"

# Step 2: Create required directories
print_info "Creating required directories..."
mkdir -p uploads output cache sessions logs temp src src/core src/core/data src/utils src/gui
print_status "Directories created"

# Step 3: Create missing __init__.py files
print_info "Creating missing __init__.py files..."
touch src/__init__.py src/core/__init__.py src/core/data/__init__.py src/utils/__init__.py src/gui/__init__.py
print_status "__init__.py files created"

# Step 4: Install dependencies
print_info "Installing Python dependencies..."
python3.11 -m pip install --user --upgrade pip setuptools wheel

# Install packages in order
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0
python3.11 -m pip install --user pandas==2.1.4 python-dateutil==2.8.2 pytz==2023.3
python3.11 -m pip install --user openpyxl==3.1.2 xlrd==2.0.1
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3
python3.11 -m pip install --user Pillow==10.1.0
python3.11 -m pip install --user jellyfish==1.2.0 fuzzywuzzy>=0.18.0 requests>=2.32.0

# Try to install python-Levenshtein (may fail on free accounts)
python3.11 -m pip install --user python-Levenshtein>=0.27.0 || print_warning "python-Levenshtein installation failed - will use fallback"

print_status "Dependencies installed"

# Step 5: Fix database issues
print_info "Fixing database issues..."

# Remove any corrupted database files
if ls *.db >/dev/null 2>&1; then
    for db_file in *.db; do
        if ! sqlite3 "$db_file" "SELECT 1;" >/dev/null 2>&1; then
            print_warning "Removing corrupted database: $db_file"
            mv "$db_file" "${db_file}.corrupted_backup"
        fi
    done
fi

# Initialize fresh database
print_info "Initializing fresh database..."
python3.11 -c "
import sqlite3
import os
from datetime import datetime

# Create uploads directory
os.makedirs('uploads', exist_ok=True)

# Create database
conn = sqlite3.connect('uploads/product_database.db')
cursor = conn.cursor()

# Create products table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        \"Product Name*\" TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        strain_id INTEGER,
        \"Product Type*\" TEXT NOT NULL,
        \"Vendor/Supplier*\" TEXT,
        \"Product Brand\" TEXT,
        \"Description\" TEXT,
        \"Weight*\" TEXT,
        \"Units\" TEXT,
        \"Price\" TEXT,
        \"Lineage\" TEXT,
        first_seen_date TEXT NOT NULL,
        last_seen_date TEXT NOT NULL,
        total_occurrences INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        \"Product Strain\" TEXT,
        \"Quantity*\" TEXT,
        \"DOH\" TEXT,
        \"Concentrate Type\" TEXT,
        \"Ratio\" TEXT,
        \"JointRatio\" TEXT,
        \"THC test result\" TEXT,
        \"CBD test result\" TEXT,
        \"Test result unit (% or mg)\" TEXT,
        \"State\" TEXT,
        \"Is Sample? (yes/no)\" TEXT,
        \"Is MJ product?(yes/no)\" TEXT,
        \"Discountable? (yes/no)\" TEXT,
        \"Room*\" TEXT,
        \"Batch Number\" TEXT,
        \"Lot Number\" TEXT,
        \"Barcode*\" TEXT,
        \"Medical Only (Yes/No)\" TEXT,
        \"Med Price\" TEXT,
        \"Expiration Date(YYYY-MM-DD)\" TEXT,
        \"Is Archived? (yes/no)\" TEXT,
        \"THC Per Serving\" TEXT,
        \"Allergens\" TEXT,
        \"Solvent\" TEXT,
        \"Accepted Date\" TEXT,
        \"Internal Product Identifier\" TEXT,
        \"Product Tags (comma separated)\" TEXT,
        \"Image URL\" TEXT,
        \"Ingredients\" TEXT,
        \"Total THC\" TEXT,
        \"THCA\" TEXT,
        \"CBDA\" TEXT,
        \"CBN\" TEXT,
        \"THC\" TEXT,
        \"CBD\" TEXT,
        \"Total CBD\" TEXT,
        \"CBGA\" TEXT,
        \"CBG\" TEXT,
        \"Total CBG\" TEXT,
        \"CBC\" TEXT,
        \"CBDV\" TEXT,
        \"THCV\" TEXT,
        \"CBGV\" TEXT,
        \"CBNV\" TEXT,
        \"CBGVA\" TEXT,
        FOREIGN KEY (strain_id) REFERENCES strains (id),
        UNIQUE(\"Product Name*\", \"Vendor/Supplier*\", \"Product Brand\")
    )
''')

# Create strains table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS strains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        lineage TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
''')

# Add sample data
now = datetime.now().isoformat()
sample_products = [
    ('Blue Dream - 3.5g', 'blue_dream_35g', 'Flower', 'A Greener Today', 'High End Farms', '3.5', 'g', '\$45.00', 'HYBRID', 'Blue Dream', now, now, now, now, '%'),
    ('Wedding Cake - 1g', 'wedding_cake_1g', 'Flower', 'A Greener Today', 'Thunder Chief', '1', 'g', '\$15.00', 'INDICA', 'Wedding Cake', now, now, now, now, '%'),
    ('Sour Diesel - 1g Pre-Roll', 'sour_diesel_1g_preroll', 'Pre-Roll', 'A Greener Today', 'Various', '1', 'g', '\$12.00', 'SATIVA', 'Sour Diesel', now, now, now, now, '%'),
    ('Mixed Strain Gummies - 10mg', 'mixed_strain_gummies_10mg', 'Edible (Solid)', 'A Greener Today', 'Kellys', '10', 'mg', '\$8.00', 'MIXED', 'Mixed', now, now, now, now, '%')
]

for product in sample_products:
    cursor.execute('''
        INSERT OR IGNORE INTO products 
        (\"Product Name*\", normalized_name, \"Product Type*\", \"Vendor/Supplier*\", \"Product Brand\", 
         \"Weight*\", \"Units\", \"Price\", \"Lineage\", \"Product Strain\", 
         first_seen_date, last_seen_date, created_at, updated_at, \"Test result unit (% or mg)\") 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', product)

conn.commit()
conn.close()
print('Database initialized successfully')
"

print_status "Database initialized"

# Step 6: Test application import
print_info "Testing application import..."
if python3.11 -c "from app import app; print('✅ Application imported successfully')"; then
    print_status "Application import test passed"
else
    print_error "Application import test failed"
    echo "Check the error messages above for details"
fi

# Step 7: Create WSGI configuration
print_info "Creating WSGI configuration..."
cat > wsgi_simple.py << EOF
#!/usr/bin/env python3.11
"""
Simple WSGI configuration for PythonAnywhere
"""

import os
import sys
import logging

# Configure the project directory
project_dir = '$PROJECT_DIR'

# Add project to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Add user site-packages for --user installed packages
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure minimal logging
logging.basicConfig(level=logging.ERROR)

# Import the Flask application
from app import app as application

# Production configuration
application.config.update(
    DEBUG=False,
    TESTING=False,
    TEMPLATES_AUTO_RELOAD=False,
    SEND_FILE_MAX_AGE_DEFAULT=31536000,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
)

if __name__ == "__main__":
    application.run(debug=False)
EOF

print_status "WSGI configuration created"

# Step 8: Display next steps
echo ""
print_status "🎉 Deployment preparation complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo ""
echo "1. 📝 Go to your PythonAnywhere Web tab"
echo ""
echo "2. 🔧 Configure your web app:"
echo "   - Source code: $PROJECT_DIR"
echo "   - WSGI file: $PROJECT_DIR/wsgi_simple.py"
echo "   - Static files URL: /static/"
echo "   - Static files path: $PROJECT_DIR/static/"
echo ""
echo "3. 🔄 Reload your web app"
echo ""
echo "4. 📋 Check error logs if there are issues"
echo ""
echo "5. 🧪 Test your application"
echo ""
echo "📊 Database Status:"
echo "   - Location: $PROJECT_DIR/uploads/product_database.db"
echo "   - Sample data: 4 products added"
echo ""
echo "🔧 If you encounter issues:"
echo "   - Check error logs in the Web tab"
echo "   - Verify dependencies: python3.11 -m pip list --user"
echo "   - Test import: python3.11 -c 'from app import app'"
echo ""
print_status "Deployment script completed!"
