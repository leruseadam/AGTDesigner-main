#!/usr/bin/env python3.11
"""
Simple test Flask app to verify basic functionality
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test App - Working!</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #28a745; font-size: 24px; margin-bottom: 20px; }
            .info { color: #333; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">🎉 Test App is Working!</h1>
            <p class="info">If you can see this page, your PythonAnywhere setup is working correctly.</p>
            <p class="info">The issue might be with your main Flask application.</p>
            <p class="info">Time: <script>document.write(new Date().toLocaleString());</script></p>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return {'status': 'success', 'message': 'Test endpoint working'}

if __name__ == '__main__':
    app.run(debug=True)
