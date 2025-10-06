#!/bin/bash

# PythonAnywhere Git Deployment Script
# ====================================
# Run this script in a PythonAnywhere Bash console

echo "🚀 AGT Label Maker - PythonAnywhere Git Deployment"
echo "=================================================="

# Check if we're in the right place
if [ ! -f "/home/$USER/.bashrc" ]; then
    echo "❌ This script should be run in a PythonAnywhere Bash console"
    exit 1
fi

# Step 1: Clone the repository
echo "📥 Step 1: Cloning repository..."
if [ -d "AGTDesigner" ]; then
    echo "🔄 Repository already exists, updating..."
    cd AGTDesigner
    git pull origin main
else
    echo "📦 Cloning fresh repository..."
    git clone https://github.com/leruseadam/AGTDesigner.git
    cd AGTDesigner
fi

# Step 2: Install dependencies
echo "📦 Step 2: Installing dependencies..."
pip3.11 install --user -r requirements.txt

# Step 3: Test the installation
echo "🧪 Step 3: Testing installation..."
if python3 -c "import app; print('✅ App imports successfully')"; then
    echo "✅ Application test passed"
else
    echo "❌ Application test failed"
    exit 1
fi

# Step 4: Check database
echo "🗄️ Step 4: Checking database..."
if [ -f "uploads/product_database_AGT_Bothell.db" ]; then
    echo "✅ Database found"
else
    echo "⚠️ Database not found - will need to be uploaded separately"
fi

# Step 5: Instructions
echo ""
echo "🎉 Git deployment complete!"
echo "==========================="
echo ""
echo "📋 Next steps in PythonAnywhere Web tab:"
echo "1. Go to Web tab in your PythonAnywhere dashboard"
echo "2. Create a new web app (or edit existing)"
echo "3. Set these configurations:"
echo "   - Source code: /home/$USER/AGTDesigner"
echo "   - WSGI file: /home/$USER/AGTDesigner/wsgi.py"
echo "4. Add environment variables:"
echo "   - SECRET_KEY = your-secure-random-key"
echo "5. Reload your web app"
echo ""
echo "🔄 For future updates:"
echo "cd AGTDesigner && git pull origin main && pip3.11 install --user -r requirements.txt"
echo "Then reload your web app in the Web tab"
echo ""

# Display repository info
echo "📊 Repository Status:"
echo "- Current branch: $(git branch --show-current)"
echo "- Latest commit: $(git log -1 --oneline)"
echo "- Repository URL: https://github.com/leruseadam/AGTDesigner"
echo ""
echo "✅ Ready for PythonAnywhere deployment!"