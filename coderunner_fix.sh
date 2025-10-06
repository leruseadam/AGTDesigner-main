#!/bin/bash
# CodeRunner fix script - forces correct Python interpreter

echo "🔧 CodeRunner Fix Script"
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/app.py"

# Deactivate any virtual environment
deactivate 2>/dev/null || true

# Try multiple Python interpreters
PYTHON_PATHS=(
    "/usr/bin/python3"
    "/usr/local/bin/python3"
    "/opt/homebrew/bin/python3"
    "python3"
    "python"
)

WORKING_PYTHON=""

echo "Testing Python interpreters..."
for python_path in "${PYTHON_PATHS[@]}"; do
    echo "Testing: $python_path"
    if $python_path -c "import pandas, flask, docx, openpyxl; print('All dependencies available')" 2>/dev/null; then
        WORKING_PYTHON="$python_path"
        echo "✅ $python_path - All dependencies working"
        break
    else
        echo "❌ $python_path - Missing dependencies"
    fi
done

if [ -z "$WORKING_PYTHON" ]; then
    echo ""
    echo "❌ No working Python interpreter found!"
    echo "Please ensure Python 3 with all dependencies is installed."
    exit 1
fi

echo ""
echo "🚀 Using Python: $WORKING_PYTHON"
echo "📁 App location: $APP_PATH"
echo "========================================"

# Run the app
exec "$WORKING_PYTHON" "$APP_PATH"
