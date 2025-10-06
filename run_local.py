#!/usr/bin/env python3
"""
Local development runner for Label Maker application
Sets up local database environment and runs the app
"""

import os
import sys

def setup_local_environment():
    """Set up environment variables for local development"""
    print("🔧 Setting up local development environment...")
    
    # Set local database environment variables
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_NAME'] = 'agt_designer'
    os.environ['DB_USER'] = 'adamcordova'
    os.environ['DB_PASSWORD'] = ''
    os.environ['DB_PORT'] = '5432'
    
    # Set Flask environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'True'
    
    print("✅ Local environment configured:")
    print(f"   Database: {os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}")
    print(f"   User: {os.environ['DB_USER']}")
    print(f"   Flask Environment: {os.environ['FLASK_ENV']}")

def run_app():
    """Run the Flask application"""
    print("\n🚀 Starting Label Maker application...")
    
    try:
        from app import app
        print("✅ App imported successfully")
        
        # Run the app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_local_environment()
    run_app()
