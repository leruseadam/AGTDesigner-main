#!/bin/bash
"""
Clean deployment script for PythonAnywhere
Removes old files and sets up fresh deployment
"""

echo "🚀 Starting clean PythonAnywhere deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Cleaning up old files...${NC}"

# Remove old project directory
if [ -d "~/AGTDesigner" ]; then
    echo "Removing old AGTDesigner directory..."
    rm -rf ~/AGTDesigner
fi

# Remove old virtual environments
echo "Cleaning up old virtual environments..."
rm -rf ~/venv*
rm -rf ~/env*

# Clean pip cache
echo "Cleaning pip cache..."
pip3.11 cache purge

echo -e "${GREEN}✅ Cleanup complete${NC}"

echo -e "${YELLOW}Step 2: Cloning fresh repository...${NC}"

# Clone repository
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner

echo -e "${GREEN}✅ Repository cloned${NC}"

echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"

# Install dependencies
if [ -f "requirements.txt" ]; then
    pip3.11 install --user -r requirements.txt
else
    echo "Installing core dependencies..."
    pip3.11 install --user flask pandas openpyxl python-docx docxcompose
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"

echo -e "${YELLOW}Step 4: Testing application...${NC}"

# Test the application
python3.11 test_method_signature.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Method signature test passed${NC}"
else
    echo -e "${RED}❌ Method signature test failed${NC}"
    exit 1
fi

python3.11 test_web_loading.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Web loading test passed${NC}"
else
    echo -e "${RED}❌ Web loading test failed${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Clean deployment setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Go to PythonAnywhere Web tab"
echo "2. Create new web app with Manual configuration"
echo "3. Set source code: /home/adamcordova/AGTDesigner"
echo "4. Set working directory: /home/adamcordova/AGTDesigner"
echo "5. Set WSGI file: /home/adamcordova/AGTDesigner/wsgi.py"
echo "6. Reload your web app"
echo "7. Test your website!"
