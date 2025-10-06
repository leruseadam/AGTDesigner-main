#!/bin/bash
# Simple Manual Installation for PythonAnywhere (No Virtual Environment)
# Use this if the main deployment script fails

echo "🔧 Manual installation starting..."

# Install essential packages only
echo "Installing core Flask application..."
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7

echo "Installing data processing..."
python3.11 -m pip install --user pandas==2.1.4 openpyxl==3.1.2

echo "Installing document processing..."  
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7

echo "Installing image processing..."
python3.11 -m pip install --user Pillow==10.1.0

echo "Installing utility libraries..."
python3.11 -m pip install --user fuzzywuzzy jellyfish

# Create directories
mkdir -p uploads output cache sessions logs temp

# Test
echo "Testing Flask import..."
python3.11 -c "from app import app; print('✅ Flask app imports successfully')"

echo "✅ Manual installation complete!"
echo ""
echo "Next: Use wsgi_configured_no_venv.py as your WSGI file"