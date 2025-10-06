#!/bin/bash

echo "🔄 Simple deployment for concentrate filter fix..."

# Check if we're on PythonAnywhere
if [[ "$HOME" == "/home/adamcordova" ]]; then
    echo "✅ Running on PythonAnywhere"
    PROJECT_DIR="/home/adamcordova/AGTDesigner"
    
    # Create project directory if it doesn't exist
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "📁 Creating project directory..."
        mkdir -p "$PROJECT_DIR"
    fi
    
    # Copy essential files
    echo "📂 Copying app.py with concentrate filter fix..."
    cp app.py "$PROJECT_DIR/"
    
    echo "📂 Copying configuration files..."
    cp config.py "$PROJECT_DIR/" 2>/dev/null || echo "⚠️  config.py not found, skipping"
    cp config_production.py "$PROJECT_DIR/" 2>/dev/null || echo "⚠️  config_production.py not found, skipping"
    
    # Copy requirements if exists
    if [ -f "requirements.txt" ]; then
        echo "📂 Copying requirements.txt..."
        cp requirements.txt "$PROJECT_DIR/"
    fi
    
    echo "✅ Concentrate filter fix deployed to PythonAnywhere"
    echo "🔄 Please reload your web app in the PythonAnywhere dashboard"
    
else
    echo "❌ This script should be run on PythonAnywhere"
    echo "💡 Upload this script to PythonAnywhere and run it there"
fi