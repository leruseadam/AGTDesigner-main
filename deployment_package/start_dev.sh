#!/bin/bash

# Development startup script for Label Maker
echo "🚀 Starting Label Maker in DEVELOPMENT mode..."
echo "📝 Auto-reloading enabled - no more manual restarts!"
echo "🌐 Server will be available at: http://127.0.0.1:5002"
echo "⏹️  Press Ctrl+C to stop the server"
echo "-" * 60

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "venv_pythonanywhere" ]; then
    echo "🔧 Activating PythonAnywhere virtual environment..."
    source venv_pythonanywhere/bin/activate
fi

# Run the development script
python run_dev.py
