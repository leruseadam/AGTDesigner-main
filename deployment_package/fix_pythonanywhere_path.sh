#!/bin/bash
# Quick fix for PythonAnywhere directory path error

echo "🔧 Fixing PythonAnywhere directory path error..."

# Check current directory structure
echo "📁 Current directory structure:"
ls -la ~/ | grep -E "(AGT|label|fresh)"

# Verify correct directory exists
if [ -d "/home/$(whoami)/AGTDesigner" ]; then
    echo "✅ Found correct directory: /home/$(whoami)/AGTDesigner"
else
    echo "❌ AGTDesigner directory not found!"
    echo "Available directories:"
    ls -la ~/
    exit 1
fi

# Update WSGI file if needed
cd ~/AGTDesigner

# Pull latest fixes
echo "📥 Pulling latest fixes..."
git pull origin main

# Check if wsgi.py exists and has correct path
if [ -f "wsgi.py" ]; then
    echo "🔍 Checking WSGI file..."
    if grep -q "labelMaker_fresh" wsgi.py; then
        echo "🔧 Fixing WSGI file path..."
        sed -i "s|labelMaker_fresh|AGTDesigner|g" wsgi.py
        echo "✅ WSGI file path fixed"
    else
        echo "✅ WSGI file path already correct"
    fi
else
    echo "⚠️  wsgi.py not found, using wsgi_pythonanywhere_python311.py"
fi

# Test the Flask app import
echo "🧪 Testing Flask app import..."
python3.11 -c "
import sys
import os
sys.path.insert(0, '/home/$(whoami)/AGTDesigner')
os.chdir('/home/$(whoami)/AGTDesigner')
try:
    from app import app
    print('✅ Flask app imports successfully')
except Exception as e:
    print(f'❌ Flask app import error: {e}')
    print(f'Current directory: {os.getcwd()}')
    print(f'Python path: {sys.path[:3]}')
    print(f'Directory contents: {os.listdir(\".\")[:10]}')
"

echo ""
echo "🎯 Next steps:"
echo "1. In PythonAnywhere Web tab, set your WSGI file to:"
echo "   /home/$(whoami)/AGTDesigner/wsgi.py"
echo "   OR"
echo "   /home/$(whoami)/AGTDesigner/wsgi_pythonanywhere_python311.py"
echo ""
echo "2. Click 'Reload' on your web app"
echo ""
echo "3. If still having issues, use the ultra-optimized WSGI:"
echo "   /home/$(whoami)/AGTDesigner/wsgi_ultra_optimized.py"