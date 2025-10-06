#!/bin/bash
# Quick PythonAnywhere Setup Script
# Run this directly in PythonAnywhere console

echo "🚀 PythonAnywhere Quick Setup"
echo "============================="

# Get current directory
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Check if we're in the right directory
if [[ ! -f "app.py" ]]; then
    echo "❌ app.py not found. Please run this from your project directory."
    echo "Expected: /home/yourusername/AGTDesigner"
    exit 1
fi

echo "✅ Project directory confirmed"

# Step 1: Set up virtual environment
echo ""
echo "🐍 Setting up virtual environment..."
if ! command -v mkvirtualenv &> /dev/null; then
    echo "Installing virtualenvwrapper..."
    pip3 install --user virtualenvwrapper
    echo "Please add 'source ~/.local/bin/virtualenvwrapper.sh' to your ~/.bashrc"
    echo "Then run 'source ~/.bashrc' and re-run this script"
    exit 1
fi

# Create or activate virtual environment
if ! workon labelmaker-env &> /dev/null; then
    echo "Creating virtual environment..."
    mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env
else
    echo "Virtual environment already exists"
fi

workon labelmaker-env
echo "✅ Virtual environment ready"

# Step 2: Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel

# Install core dependencies
pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0
pip install pandas==2.1.4 openpyxl==3.1.2 xlrd==2.0.1
pip install python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3
pip install Pillow==10.1.0 python-dateutil==2.8.2 pytz==2023.3
pip install jellyfish==1.2.0 requests>=2.32.0 fuzzywuzzy>=0.18.0 python-Levenshtein>=0.27.0

echo "✅ Dependencies installed"

# Step 3: Create directories
echo ""
echo "📁 Creating required directories..."
mkdir -p uploads output cache sessions logs temp
chmod 755 uploads output cache sessions logs temp
echo "✅ Directories created"

# Step 4: Database setup
echo ""
echo "🗄️  Setting up database..."
if [ -f "product_database.db" ]; then
    echo "Database file found"
    DB_SIZE=$(du -h product_database.db | cut -f1)
    echo "Database size: $DB_SIZE"
    
    # Test database
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('product_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    print(f'Database OK - Products: {count}')
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
" || echo "⚠️  Database test failed"
    
elif [ -f "products_dump.sql" ]; then
    echo "SQL dump found, restoring database..."
    python3 -c "
import sqlite3
import os
if os.path.exists('product_database.db'):
    os.remove('product_database.db')
conn = sqlite3.connect('product_database.db')
with open('products_dump.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Database restored from SQL dump')
" || echo "⚠️  Database restoration failed"
    
else
    echo "No database found, initializing..."
    python3 init_database.py || echo "⚠️  Database initialization failed"
fi

# Step 5: Test application
echo ""
echo "🧪 Testing application..."
python3 -c "
try:
    from app import app
    print('✅ Application import successful')
    print(f'App name: {app.name}')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    import traceback
    traceback.print_exc()
" || echo "⚠️  Application test failed"

# Step 6: Show next steps
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo "1. Go to PythonAnywhere Web tab"
echo "2. Create/configure your web app:"
echo "   - Choose 'Manual configuration'"
echo "   - Select Python 3.11"
echo "   - Don't use framework template"
echo "3. Configure WSGI file with this content:"
echo ""
cat << 'EOF'
#!/usr/bin/env python3
import os
import sys
import logging

# Project directory
project_dir = '/home/adamcordova/AGTDesigner'  # Replace with your username

# Add to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging
logging.basicConfig(level=logging.ERROR)
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

try:
    from app import app as application
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    print("WSGI application loaded successfully")
except Exception as e:
    print(f"Error: {e}")
    raise
EOF
echo ""
echo "4. Configure static files:"
echo "   - URL: /static/"
echo "   - Directory: /home/adamcordova/AGTDesigner/static/  # Replace with your username"
echo "5. Reload your web app"
echo "6. Test at: https://adamcordova.pythonanywhere.com  # Replace with your username"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check error logs in Web tab if issues occur"
echo "- Verify virtual environment: workon labelmaker-env"
echo "- Test database: python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); print('OK')\""
echo "- Test app: python3 -c \"from app import app; print('OK')\""
echo ""
echo "✅ Ready for deployment!"
