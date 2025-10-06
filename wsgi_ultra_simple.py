#!/usr/bin/env python3.11
"""
Ultra-simple WSGI for PythonAnywhere debugging
This is the absolute simplest WSGI file possible
"""

def application(environ, start_response):
    """Ultra-simple WSGI application"""
    status = '200 OK'
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultra-Simple WSGI Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #e8f5e8; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #28a745; font-size: 28px; margin-bottom: 20px; }
            .info { color: #333; margin: 15px 0; font-size: 16px; }
            .code { background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">🎉 ULTRA-SIMPLE WSGI WORKING!</h1>
            <p class="info">This is the simplest possible WSGI application.</p>
            <p class="info">If you can see this page, your PythonAnywhere WSGI setup is working correctly.</p>
            
            <div class="code">
                <strong>WSGI Test Results:</strong><br>
                ✅ WSGI file executed successfully<br>
                ✅ PythonAnywhere can run Python code<br>
                ✅ Web server is working<br>
                ✅ Basic HTML rendering works
            </div>
            
            <p class="info"><strong>Next Steps:</strong></p>
            <p class="info">1. This confirms WSGI is working</p>
            <p class="info">2. The issue is with your Flask application</p>
            <p class="info">3. Check PythonAnywhere error logs for Flask-specific errors</p>
            <p class="info">4. Try importing your Flask app step by step</p>
            
            <p class="info"><strong>Time:</strong> <script>document.write(new Date().toLocaleString());</script></p>
        </div>
    </body>
    </html>
    """
    
    start_response(status, headers)
    return [html.encode('utf-8')]

# For direct execution
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Starting ultra-simple WSGI test server...")
    httpd = make_server('', 8000, application)
    print("Serving on http://localhost:8000")
    httpd.serve_forever()
