#!/usr/bin/env python3.11
"""
Simple WSGI test for PythonAnywhere debugging
This is a minimal WSGI application to test if the basic setup works
"""

import os
import sys

# Add project directory to Python path
project_dir = '/home/adamcordova/AGTDesigner'
if os.path.exists(project_dir):
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
            body { font-family: Arial, sans-serif; margin: 40px; }
            .success { color: green; font-size: 24px; }
            .info { color: blue; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1 class="success">✅ WSGI Test Successful!</h1>
        <div class="info">
            <p><strong>Python Version:</strong> {python_version}</p>
            <p><strong>Project Directory:</strong> {project_dir}</p>
            <p><strong>Python Path:</strong> {python_path}</p>
            <p><strong>Environment:</strong> {environment}</p>
        </div>
        <p>If you can see this page, your WSGI configuration is working correctly!</p>
        <p>Now you can switch back to your main application.</p>
    </body>
    </html>
    """.format(
        python_version=sys.version,
        project_dir=project_dir,
        python_path='<br>'.join(sys.path[:5]),
        environment=dict(os.environ)
    )
    
    start_response(status, headers)
    return [html.encode('utf-8')]

# This is what PythonAnywhere will use
application = simple_app

# For testing
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Starting simple WSGI test server...")
    httpd = make_server('', 8000, application)
    print("Serving on http://localhost:8000")
    httpd.serve_forever()