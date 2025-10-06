#!/usr/bin/env python3.11
"""
Minimal WSGI configuration for PythonAnywhere
This is the simplest possible WSGI file to test basic functionality
"""

import os
import sys

# Add project directory to Python path
project_dir = '/home/adamcordova/AGTDesigner'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Add user site-packages
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Change to project directory
os.chdir(project_dir)

# Simple test application first
def simple_app(environ, start_response):
    """Simple WSGI application for testing"""
    status = '200 OK'
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WSGI Test - Working!</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #28a745; font-size: 24px; margin-bottom: 20px; }
            .info { color: #333; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">🎉 WSGI Test Successful!</h1>
            <p class="info">If you can see this page, your WSGI configuration is working correctly!</p>
            <p class="info">Python version: """ + sys.version + """</p>
            <p class="info">Project directory: """ + project_dir + """</p>
            <p class="info">Current working directory: """ + os.getcwd() + """</p>
            <p class="info">Python path: """ + str(sys.path[:3]) + """</p>
            <p class="info">Now you can switch back to your main application.</p>
        </div>
    </body>
    </html>
    """
    
    start_response(status, headers)
    return [html.encode('utf-8')]

# Try to import the main app, fallback to simple app if it fails
try:
    from app import app as application
    print("✅ Main app imported successfully")
except Exception as e:
    print(f"❌ Main app import failed: {e}")
    print("Using simple test app instead")
    application = simple_app

# For direct execution
if __name__ == "__main__":
    if application == simple_app:
        print("Running simple test app...")
        from wsgiref.simple_server import make_server
        httpd = make_server('', 8000, application)
        print("Serving on http://localhost:8000")
        httpd.serve_forever()
    else:
        application.run(debug=False)
