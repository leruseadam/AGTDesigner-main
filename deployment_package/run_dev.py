#!/usr/bin/env python3
"""
Development startup script for Label Maker app.
This script enables auto-reloading so you don't have to restart manually.
"""

import os
import sys

# Set development environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['DEVELOPMENT_MODE'] = 'true'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("🚀 Starting Label Maker in DEVELOPMENT mode with auto-reloading...")
    print("📝 Changes to Python files will automatically restart the server")
    print("🌐 Server will be available at: http://127.0.0.1:5002")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Import and run the app
    from app import LabelMakerApp
    
    try:
        app = LabelMakerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Development server stopped by user")
    except Exception as e:
        print(f"❌ Error starting development server: {e}")
        sys.exit(1) 