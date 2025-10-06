#!/bin/bash

echo "=== PythonAnywhere Deployment Script ==="
echo ""

# Create a deployment package
echo "Creating deployment package..."
mkdir -p deployment_package

# Copy essential files (excluding large files)
echo "Copying essential files..."
cp -r src/ deployment_package/
cp -r static/ deployment_package/
cp -r templates/ deployment_package/
cp -r uploads/ deployment_package/ 2>/dev/null || echo "No uploads directory found"
cp app.py deployment_package/
cp wsgi.py deployment_package/
cp requirements.txt deployment_package/
cp *.py deployment_package/ 2>/dev/null || echo "No additional Python files"
cp *.md deployment_package/ 2>/dev/null || echo "No markdown files"
cp *.sh deployment_package/ 2>/dev/null || echo "No shell scripts"

# Remove large files from deployment package
echo "Removing large files from deployment package..."
find deployment_package/ -name "*.db" -delete
find deployment_package/ -name "*.db.gz" -delete
find deployment_package/ -name "*.tar.gz" -delete
find deployment_package/ -name "*.zip" -delete
find deployment_package/ -name "*.xlsx" -delete
find deployment_package/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find deployment_package/ -name "*.pyc" -delete
find deployment_package/ -name ".DS_Store" -delete

echo ""
echo "=== DEPLOYMENT PACKAGE READY ==="
echo "Location: ./deployment_package/"
echo ""
echo "Next steps for PythonAnywhere:"
echo "1. Zip the deployment_package folder"
echo "2. Upload to PythonAnywhere via Files tab"
echo "3. Extract in your project directory"
echo "4. Install requirements: pip3.10 install --user -r requirements.txt"
echo "5. Update your WSGI file to point to the new app.py"
echo "6. Reload your web app"
echo ""
echo "=== Weight Field Fixes Included ==="
echo "✅ Enhanced frontend weight field extraction"
echo "✅ Comprehensive backend weight field population"
echo "✅ Automatic weight extraction from product names"
echo "✅ Cache invalidation for immediate deployment"
echo "✅ Concentrate product weight display fixes"
echo ""

# Create a zip file for easy upload
echo "Creating zip file for upload..."
cd deployment_package
zip -r ../AGTDesigner_deployment.zip . -x "*.db" "*.db.gz" "*.tar.gz" "*.zip" "*.xlsx" "__pycache__/*" "*.pyc" ".DS_Store"
cd ..

echo ""
echo "✅ Deployment package created: AGTDesigner_deployment.zip"
echo "✅ Ready to upload to PythonAnywhere!"
