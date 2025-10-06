#!/bin/bash
# Quick deployment script for PythonAnywhere
# Save this and run in PythonAnywhere console

echo "🚀 Starting PythonAnywhere deployment..."

# Update code
cd /home/adamcordova/AGTDesigner
git pull origin main

# Install dependencies
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0
python3.11 -m pip install --user pandas==2.1.4 openpyxl==3.1.2
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7
python3.11 -m pip install --user Pillow==10.1.0 jellyfish==1.2.0

# Test configuration
python3.11 test_pythonanywhere_config.py

echo "✅ Deployment complete! Don't forget to:"
echo "1. Upload the optimized database"
echo "2. Reload your web app in the Web tab"
echo "3. Test at https://adamcordova.pythonanywhere.com"