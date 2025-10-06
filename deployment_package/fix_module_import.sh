#!/bin/bash
# Fix missing module 'src.core.data.product_database' on PythonAnywhere

echo "🚨 Fixing PythonAnywhere Module Import Error"
echo "============================================"

USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

cd "$PROJECT_DIR" || exit 1

echo "📁 Working directory: $PROJECT_DIR"
echo ""

# Step 1: Pull latest changes from GitHub
echo "🔄 Pulling latest changes from GitHub..."
git pull origin main

echo ""

# Step 2: Verify directory structure
echo "📂 Verifying directory structure..."

REQUIRED_DIRS=(
    "src"
    "src/core"
    "src/core/data"
    "src/core/formatting"
    "src/core/generation" 
    "src/core/utils"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "🔧 Creating directory: $dir"
        mkdir -p "$dir"
    else
        echo "✅ Directory exists: $dir"
    fi
done

echo ""

# Step 3: Create missing __init__.py files
echo "📄 Creating missing __init__.py files..."

INIT_FILES=(
    "src/__init__.py"
    "src/core/__init__.py"
    "src/core/data/__init__.py"
    "src/core/formatting/__init__.py"
    "src/core/generation/__init__.py"
    "src/core/utils/__init__.py"
)

for init_file in "${INIT_FILES[@]}"; do
    if [ ! -f "$init_file" ]; then
        echo "🔧 Creating: $init_file"
        echo "# Module initialization" > "$init_file"
    else
        echo "✅ Exists: $init_file"
    fi
done

echo ""

# Step 4: Verify critical files exist
echo "📋 Checking critical files..."

CRITICAL_FILES=(
    "app.py"
    "src/core/data/product_database.py"
    "src/core/data/json_matcher.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
    fi
done

echo ""

# Step 5: Test Python imports
echo "🐍 Testing Python imports..."

python3.11 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')

modules = [
    'src',
    'src.core', 
    'src.core.data',
    'src.core.data.product_database',
    'src.core.data.json_matcher'
]

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except Exception as e:
        print(f'❌ {module}: {e}')
"

echo ""

# Step 6: Test Flask app import
echo "🧪 Testing Flask app import..."

python3.11 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_DIR')
os.chdir('$PROJECT_DIR')

try:
    from app import app
    print('✅ Flask app imported successfully!')
    print(f'App name: {app.name}')
except Exception as e:
    print(f'❌ Flask app import failed: {e}')
    import traceback
    print('Full traceback:')
    traceback.print_exc()
"

echo ""
echo "🎯 NEXT STEPS:"
echo "=============="
echo "1. 🔄 Reload your web app in PythonAnywhere"
echo "2. 🔍 Check error logs for any remaining issues"
echo "3. ✅ If working, switch to optimized WSGI:"
echo "   /home/adamcordova/AGTDesigner/wsgi_ultra_optimized.py"
echo ""
echo "✅ Module fix complete!"