#!/bin/bash
# Comprehensive PythonAnywhere App Loading Troubleshooter

echo "🚨 PythonAnywhere App Loading Troubleshooter"
echo "=============================================="

USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

echo "👤 User: $USERNAME"
echo "📁 Project Directory: $PROJECT_DIR"
echo ""

# Step 1: Check directory structure
echo "📁 STEP 1: Directory Structure"
echo "-------------------------------"

if [ -d "$PROJECT_DIR" ]; then
    echo "✅ Project directory exists"
    echo "📂 Contents:"
    ls -la "$PROJECT_DIR" | head -15
else
    echo "❌ Project directory missing!"
    echo "Available directories in home:"
    ls -la ~/ | grep -E "(agt|label|designer|fresh)" || echo "No matching directories found"
    exit 1
fi

echo ""

# Step 2: Check critical files
echo "📄 STEP 2: Critical Files Check"
echo "--------------------------------"

cd "$PROJECT_DIR"

CRITICAL_FILES=("app.py" "requirements.txt" "src/__init__.py" "src/core/__init__.py" "src/core/data/__init__.py")

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file MISSING"
        
        # Try to create missing __init__.py files
        if [[ $file == *"__init__.py" ]]; then
            mkdir -p $(dirname "$file")
            touch "$file"
            echo "   🔧 Created empty $file"
        fi
    fi
done

echo ""

# Step 3: Test Python imports
echo "🐍 STEP 3: Python Import Test"
echo "------------------------------"

python3.11 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_DIR')
os.chdir('$PROJECT_DIR')

# Test imports
imports = ['flask', 'pandas', 'openpyxl', 'docxtpl', 'src', 'src.core', 'src.core.data']

for module in imports:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
    except Exception as e:
        print(f'⚠️  {module}: {e}')

# Test Flask app import
print('')
print('🧪 Flask App Import Test:')
try:
    from app import app
    print('✅ Flask app imported successfully')
    print(f'   App name: {app.name if hasattr(app, \"name\") else \"unknown\"}')
    print(f'   Debug mode: {app.debug if hasattr(app, \"debug\") else \"unknown\"}')
except Exception as e:
    print(f'❌ Flask app import failed: {e}')
    import traceback
    print('Full traceback:')
    traceback.print_exc()
"

echo ""

# Step 4: Check installed packages
echo "📦 STEP 4: Installed Packages"
echo "------------------------------"

echo "User-installed packages:"
python3.11 -m pip list --user | head -10

echo ""
echo "Key packages check:"
KEY_PACKAGES=("Flask" "pandas" "openpyxl" "python-docx" "docxtpl")

for package in "${KEY_PACKAGES[@]}"; do
    if python3.11 -m pip show "$package" >/dev/null 2>&1; then
        VERSION=$(python3.11 -m pip show "$package" | grep Version | cut -d' ' -f2)
        echo "✅ $package ($VERSION)"
    else
        echo "❌ $package (not installed)"
        echo "   💡 Install with: python3.11 -m pip install --user $package"
    fi
done

echo ""

# Step 5: Database check
echo "🗃️  STEP 5: Database Check"
echo "------------------------"

DB_PATHS=("$PROJECT_DIR/product_database.db" "$PROJECT_DIR/uploads/product_database.db")

for db_path in "${DB_PATHS[@]}"; do
    if [ -f "$db_path" ]; then
        SIZE=$(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path" 2>/dev/null)
        echo "✅ Database found: $db_path (${SIZE} bytes)"
        break
    fi
done

if ! ls "$PROJECT_DIR"/*database*.db >/dev/null 2>&1 && ! ls "$PROJECT_DIR"/uploads/*database*.db >/dev/null 2>&1; then
    echo "⚠️  No database found"
    echo "   💡 Run: python3.11 init_pythonanywhere_database.py"
fi

echo ""

# Step 6: WSGI file recommendations
echo "⚙️  STEP 6: WSGI Recommendations"
echo "--------------------------------"

WSGI_FILES=(
    "wsgi_debug.py"
    "wsgi_pythonanywhere_python311.py" 
    "wsgi_ultra_optimized.py"
    "wsgi.py"
)

echo "Available WSGI files:"
for wsgi_file in "${WSGI_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$wsgi_file" ]; then
        echo "✅ $wsgi_file"
    else
        echo "❌ $wsgi_file"
    fi
done

echo ""
echo "🎯 RECOMMENDED ACTIONS:"
echo "======================="

echo "1. 📝 In PythonAnywhere Web tab, set WSGI file to:"
echo "   $PROJECT_DIR/wsgi_debug.py"
echo ""

echo "2. 🔄 Reload your web app"
echo ""

echo "3. 📋 Check error logs for detailed debug information"
echo ""

echo "4. 🔧 If imports fail, install missing packages:"
echo "   python3.11 -m pip install --user flask pandas openpyxl python-docx docxtpl"
echo ""

echo "5. 🗃️  If database is missing, initialize it:"
echo "   python3.11 init_pythonanywhere_database.py"
echo ""

echo "6. ✅ Once working, switch to optimized WSGI:"
echo "   $PROJECT_DIR/wsgi_ultra_optimized.py"

echo ""
echo "🔍 For detailed diagnostics, run:"
echo "   python3.11 diagnose_pythonanywhere.py"