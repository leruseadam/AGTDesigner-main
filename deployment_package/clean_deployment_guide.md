# Clean PythonAnywhere Deployment Guide

## 🚀 Fresh Start Deployment (No Web Deployment Directory)

This guide will help you deploy your Flask application cleanly to PythonAnywhere without the complexity of separate web deployment files.

## Prerequisites
- PythonAnywhere account
- Git repository with your code
- Python 3.11

## Step 1: Clean Up PythonAnywhere

### 1.1 Remove Old Files
```bash
# SSH into PythonAnywhere
ssh adamcordova@ssh.pythonanywhere.com

# Remove old project directory
rm -rf ~/AGTDesigner

# Remove old web app configuration
# (Do this in PythonAnywhere Web tab - delete the old web app)
```

### 1.2 Clean Python Environment
```bash
# Remove old virtual environments
rm -rf ~/venv*
rm -rf ~/env*

# Clean pip cache
pip3.11 cache purge
```

## Step 2: Fresh Clone and Setup

### 2.1 Clone Repository
```bash
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
```

### 2.2 Install Dependencies
```bash
# Install Python packages
pip3.11 install --user -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip3.11 install --user flask pandas openpyxl python-docx docxcompose
```

### 2.3 Test Application
```bash
# Test the application
python3.11 test_method_signature.py
python3.11 test_web_loading.py
```

## Step 3: Create Clean WSGI File

### 3.1 Create Simple WSGI File
Create a new file called `wsgi.py` in your project root:

```python
#!/usr/bin/env python3.11
"""
Clean WSGI configuration for PythonAnywhere
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

# Import and configure Flask app
from app import app as application

# Production settings
application.config.update(
    DEBUG=False,
    TESTING=False,
    TEMPLATES_AUTO_RELOAD=False
)

# For direct execution
if __name__ == "__main__":
    application.run(debug=False)
```

## Step 4: Configure Web App

### 4.1 Create New Web App
1. Go to PythonAnywhere **Web** tab
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.11**

### 4.2 Configure Web App Settings
- **Source code**: `/home/adamcordova/AGTDesigner`
- **Working directory**: `/home/adamcordova/AGTDesigner`
- **WSGI file**: `/home/adamcordova/AGTDesigner/wsgi.py`

### 4.3 Reload Web App
1. Click **"Reload"** for your web app
2. Wait for reload to complete
3. Test your website

## Step 5: Test Deployment

### 5.1 Test Backend
```bash
cd ~/AGTDesigner
python3.11 test_method_signature.py
python3.11 test_web_loading.py
```

### 5.2 Test Web Interface
- Open your website URL
- Check if the page loads
- Test basic functionality

## Troubleshooting

### If Web App Still Doesn't Load

1. **Check Error Logs**
   - Go to Web tab → Your domain → Error log
   - Look for specific error messages

2. **Test WSGI File**
   ```bash
   cd ~/AGTDesigner
   python3.11 wsgi.py
   ```

3. **Check File Permissions**
   ```bash
   chmod +x wsgi.py
   ```

4. **Verify Dependencies**
   ```bash
   python3.11 -c "import flask, pandas, openpyxl; print('All dependencies OK')"
   ```

## Benefits of This Approach

✅ **Single source of truth** - No duplicate files
✅ **Easy maintenance** - Changes in one place
✅ **Clean deployment** - No web_deployment directory confusion
✅ **Direct git workflow** - Pull changes directly to production
✅ **Simple debugging** - All files in one location

## Next Steps

After successful deployment:
1. Test all functionality
2. Set up automatic deployments (optional)
3. Configure domain name (if needed)
4. Set up monitoring (optional)
