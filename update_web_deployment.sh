#!/bin/bash
# Update Web Deployment with Latest Changes
# Run this script in your PythonAnywhere console to update the web version

set -e  # Exit on any error

echo "🔄 Updating web deployment with latest changes..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Get the username
USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

print_status "Starting deployment update for user: ${USERNAME}"

# Step 1: Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    print_error "Please run the full deployment script first"
    exit 1
fi

cd "$PROJECT_DIR"
print_status "Changed to project directory: $PROJECT_DIR"

# Step 2: Check current branch and status
print_status "Checking git status..."
git status

# Step 3: Pull latest changes
print_status "Pulling latest changes from GitHub..."
git fetch origin
git pull origin main

# Step 4: Check if there are new commits
LATEST_COMMIT=$(git log --oneline -1)
print_status "Latest commit: $LATEST_COMMIT"

# Step 5: Test the application
print_status "Testing application with latest changes..."
python3.11 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import process_database_product_for_api
    print('✅ Application import successful')
    print('✅ process_database_product_for_api function available')
    
    # Test the fix
    test_product = {
        'Product Name*': 'Test Concentrate',
        'Description': 'Test Description', 
        'Weight*': '1.0',
        'Units': 'g'
    }
    result = process_database_product_for_api(test_product)
    if 'DescAndWeight' in result and result['DescAndWeight']:
        print('✅ DescAndWeight field creation working!')
        print(f'   DescAndWeight: {result[\"DescAndWeight\"]}')
    else:
        print('❌ DescAndWeight field not created properly')
        
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Application test passed!"
else
    print_error "Application test failed!"
    exit 1
fi

# Step 6: Check web app status
echo ""
print_status "🎉 Code update complete!"
echo ""
echo "IMPORTANT: You must now reload your web app!"
echo ""
echo "Instructions to reload:"
echo "1. Go to https://www.pythonanywhere.com/user/$USERNAME/webapps/"
echo "2. Find your web app"
echo "3. Click the 'Reload' button"
echo "4. Wait for the reload to complete"
echo ""
echo "After reloading, the concentrate weight fix should be active on the web version!"
echo ""
print_warning "The web app reload is REQUIRED for changes to take effect!"