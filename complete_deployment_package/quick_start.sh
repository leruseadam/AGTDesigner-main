#!/bin/bash

echo "🚀 AGT Label Maker Quick Start"
echo "=============================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Test the deployment
echo "🧪 Testing deployment..."
python3 test_deployment.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🌐 Starting application for local testing..."
    echo "Access at: http://localhost:5000"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Set environment variables
    export FLASK_APP=app.py
    export FLASK_ENV=development
    
    # Start the application
    python3 -m flask run --host=0.0.0.0 --port=5000
else
    echo "❌ Deployment test failed. Fix the issues before starting."
fi
