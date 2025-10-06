
# PythonAnywhere WSGI Fix Instructions

## The Problem
The error "No module named 'app'" occurs because the WSGI file can't find your app.py file.

## The Solution

### 1. Upload the Fixed WSGI File
- Upload `wsgi_pythonanywhere_fixed.py` to your PythonAnywhere home directory
- Make sure it's in the same directory as your `app.py` file

### 2. Update PythonAnywhere WSGI Configuration
- Go to PythonAnywhere Dashboard → Web tab
- Click on your WSGI configuration file
- Replace the entire content with the content from `wsgi_pythonanywhere_fixed.py`

### 3. Alternative: Manual WSGI Configuration
If the above doesn't work, manually set your WSGI file to:

```python
#!/usr/bin/env python3
import sys
import os

# Add the project directory to Python path
project_home = '/home/yourusername/AGTDesigner_deployment'  # Update this path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory  
os.chdir(project_home)

# Import the Flask app
from app import app as application
```

### 4. Reload Your Web App
- Click the "Reload" button in the Web tab
- Check the error logs if there are still issues

## Troubleshooting

### If you still get "No module named 'app'":
1. Check that `app.py` exists in your project directory
2. Verify the path in the WSGI file matches your actual directory
3. Make sure you've uploaded all the necessary files
4. Check the PythonAnywhere error logs for more details

### If you get import errors:
1. Make sure you've installed all requirements: `pip3.10 install --user -r requirements.txt`
2. Check that all Python files are uploaded correctly
3. Verify the project structure is intact

## Expected Result
After fixing the WSGI configuration, your app should load successfully and the weight field fixes should be active.
