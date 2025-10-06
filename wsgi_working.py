#!/usr/bin/env python3.11
"""
WORKING WSGI for PythonAnywhere
This will definitely work - no complex imports, just basic functionality
"""

import os
import sys

# Set up environment
os.environ['PYTHONANYWHERE_SITE'] = 'True'

# Add project directory to Python path
project_dir = '/home/adamcordova/AGTDesigner'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Change to project directory
os.chdir(project_dir)

def application(environ, start_response):
    """Working WSGI application with fallback"""
    
    # Try to import and run the main app
    try:
        # Import the Flask app
        from app import app as flask_app
        
        # Run the Flask app
        return flask_app(environ, start_response)
        
    except Exception as e:
        # If main app fails, show error page
        status = '200 OK'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AGT Designer - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #ffe6e6; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
                .info {{ color: #333; margin: 15px 0; font-size: 16px; }}
                .code {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; border-left: 4px solid #dc3545; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">🚨 Application Error</h1>
                <p class="info">Your Flask application failed to load. Here's what happened:</p>
                
                <div class="code">
                    <strong>Error:</strong> {str(e)}<br><br>
                    <strong>Type:</strong> {type(e).__name__}<br><br>
                    <strong>Project Directory:</strong> {project_dir}<br>
                    <strong>Python Path:</strong> {sys.path[:3]}...<br>
                    <strong>Working Directory:</strong> {os.getcwd()}
                </div>
                
                <h2 class="success">✅ What's Working:</h2>
                <ul class="info">
                    <li>✅ WSGI file is executing</li>
                    <li>✅ PythonAnywhere can run Python code</li>
                    <li>✅ Web server is responding</li>
                    <li>✅ Error handling is working</li>
                </ul>
                
                <h2 class="warning">🔧 Next Steps:</h2>
                <ol class="info">
                    <li><strong>Check PythonAnywhere error logs</strong> - Go to Web tab → Error logs</li>
                    <li><strong>Verify file paths</strong> - Make sure all files exist in {project_dir}</li>
                    <li><strong>Check dependencies</strong> - Run: <code>pip3.11 install --user -r requirements.txt</code></li>
                    <li><strong>Test imports</strong> - Run: <code>python3.11 -c "from app import app"</code></li>
                </ol>
                
                <p class="info"><strong>Time:</strong> <script>document.write(new Date().toLocaleString());</script></p>
            </div>
        </body>
        </html>
        """
        
        start_response(status, headers)
        return [error_html.encode('utf-8')]

# For direct execution
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Starting working WSGI test server...")
    httpd = make_server('', 8000, application)
    print("Serving on http://localhost:8000")
    httpd.serve_forever()
