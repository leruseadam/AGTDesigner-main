#!/bin/bash
# CodeRunner script to run the labelMaker app with venv_fresh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/app.py"

# Use the system Python that has all dependencies installed
PYTHON_PATH="/usr/bin/python3"

# Verify the Python interpreter exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python interpreter not found at $PYTHON_PATH"
    echo "Please ensure Python 3 is installed on the system."
    exit 1
fi

echo "Running app from: $APP_PATH"
echo "Using Python: $PYTHON_PATH"
echo "=================================================="

# Change to the app directory
cd "$SCRIPT_DIR"

# Run the app with the virtual environment Python
exec "$PYTHON_PATH" "$APP_PATH"
