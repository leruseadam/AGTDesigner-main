#!/usr/bin/env python3
"""
CodeRunner script to run the labelMaker app with the venv_fresh virtual environment.
This script ensures we use the correct Python interpreter with all dependencies installed.
"""

import sys
import os
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, 'app.py')
    
    # Use the system Python that has all dependencies installed
    python_path = '/usr/bin/python3'
    
    # Verify the Python interpreter exists
    if not os.path.exists(python_path):
        print(f"Error: Python interpreter not found at {python_path}")
        print("Please ensure Python 3 is installed on the system.")
        sys.exit(1)
    
    print(f"Running app from: {app_path}")
    print(f"Using Python: {python_path}")
    print("=" * 50)
    
    try:
        # Run the app with the virtual environment Python
        # Use Popen for non-blocking execution
        process = subprocess.Popen([python_path, app_path], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, 
                                 universal_newlines=True,
                                 bufsize=1)
        
        print("🚀 Flask app started successfully!")
        print("🌐 Server should be available at: http://127.0.0.1:5001")
        print("📝 Check the terminal for any error messages")
        print("⏹️  To stop the app, close this terminal or press Ctrl+C")
        print("=" * 60)
        
        # Stream output in real-time
        for line in process.stdout:
            print(line.rstrip())
            
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
        if 'process' in locals():
            process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
