# PythonAnywhere Deployment from Scratch - Complete Guide

## Overview
This guide will deploy your Label Maker application to PythonAnywhere from scratch, including handling the large database migration.

## Prerequisites
- PythonAnywhere account (Free tier works, but Paid recommended for better performance)
- Your GitHub repository: `https://github.com/leruseadam/AGTDesigner.git`
- Local project working correctly

## Step 1: PythonAnywhere Account Setup

### 1.1 Create/Login to PythonAnywhere Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free account or login if you have one
3. Note your username (e.g., `adamcordova`)

### 1.2 Upgrade Account (Recommended)
- Free tier has limitations: 3 months, limited CPU seconds, small disk space
- Consider upgrading to "Hacker" plan ($5/month) for better performance
- This is especially important for your large database

## Step 2: Clone Repository on PythonAnywhere

### 2.1 Open Bash Console
1. Login to PythonAnywhere dashboard
2. Click on "Consoles" tab
3. Click "Bash" to open a new console

### 2.2 Clone Your Repository
```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/leruseadam/AGTDesigner.git

# Navigate to project directory
cd AGTDesigner

# Verify files are present
ls -la
```

## Step 3: Set Up Python Environment

### 3.1 Create Virtual Environment
```bash
# Create virtual environment with Python 3.11
mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env

# Activate the environment
workon labelmaker-env

# Verify Python version
python --version
# Should show: Python 3.11.x
```

### 3.2 Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install core dependencies in order
pip install Flask==2.3.3
pip install Werkzeug==2.3.7
pip install Flask-CORS==4.0.0
pip install Flask-Caching==2.1.0

# Install data processing
pip install pandas==2.1.4
pip install openpyxl==3.1.2
pip install xlrd==2.0.1

# Install document processing
pip install python-docx==0.8.11
pip install docxtpl==0.16.7
pip install docxcompose==1.4.0
pip install lxml==4.9.3

# Install image processing
pip install Pillow==10.1.0

# Install utilities
pip install python-dateutil==2.8.2
pip install pytz==2023.3
pip install jellyfish==1.2.0
pip install requests>=2.32.0
pip install fuzzywuzzy>=0.18.0
pip install python-Levenshtein>=0.27.0
```

## Step 4: Database Migration Strategy

### 4.1 Check Database Size
Your database files:
- `product_database.db`: 68KB (SQLite)
- `products_dump.sql`: 4.1MB (SQL dump)

### 4.2 Upload Database Files
Since your database is relatively small, you can upload it directly:

#### Option A: Upload via Files Tab (Recommended)
1. Go to "Files" tab in PythonAnywhere dashboard
2. Navigate to `/home/yourusername/AGTDesigner/`
3. Upload `product_database.db` and `products_dump.sql`

#### Option B: Upload via Console
```bash
# If you have the files locally, you can use scp or rsync
# Or download from your GitHub repository if committed
```

### 4.3 Initialize Database
```bash
# Navigate to project directory
cd ~/AGTDesigner

# Initialize database (if needed)
python init_database.py

# Or restore from SQL dump
python -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
with open('products_dump.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Database restored successfully')
"
```

## Step 5: Create Required Directories

```bash
# Create necessary directories
mkdir -p ~/AGTDesigner/uploads
mkdir -p ~/AGTDesigner/output
mkdir -p ~/AGTDesigner/cache
mkdir -p ~/AGTDesigner/sessions
mkdir -p ~/AGTDesigner/logs
mkdir -p ~/AGTDesigner/temp

# Set proper permissions
chmod 755 ~/AGTDesigner/uploads
chmod 755 ~/AGTDesigner/output
chmod 755 ~/AGTDesigner/cache
chmod 755 ~/AGTDesigner/sessions
chmod 755 ~/AGTDesigner/logs
chmod 755 ~/AGTDesigner/temp
```

## Step 6: Configure Web App

### 6.1 Create Web App
1. Go to "Web" tab in PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select **Python 3.11**
5. Don't use a framework template

### 6.2 Configure WSGI File
1. Click on the WSGI configuration file link
2. Replace the contents with this configuration:

```python
#!/usr/bin/env python3
"""
PythonAnywhere WSGI configuration - Production ready
"""

import os
import sys
import logging

# Project directory configuration
project_dir = '/home/adamcordova/AGTDesigner'  # Replace 'adamcordova' with your username

# Add project to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s - %(message)s'
)

# Suppress verbose logging
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

try:
    # Import the Flask application
    from app import app as application
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    
    print("WSGI application loaded successfully")
    
except ImportError as e:
    print(f"Failed to import Flask app: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    raise
except Exception as e:
    print(f"Error configuring Flask app: {e}")
    raise
```

### 6.3 Configure Static Files
1. In the Web tab, scroll down to "Static files"
2. Add static file mapping:
   - URL: `/static/`
   - Directory: `/home/adamcordova/AGTDesigner/static/` (replace with your username)

## Step 7: Test Configuration

### 7.1 Test Database Connection
```bash
# Navigate to project directory
cd ~/AGTDesigner

# Test database connection
python -c "
import sqlite3
try:
    conn = sqlite3.connect('product_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    print(f'Database connection successful. Products count: {count}')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### 7.2 Test Application Import
```bash
# Test if the app can be imported
python -c "
try:
    from app import app
    print('Application import successful')
    print(f'App name: {app.name}')
except Exception as e:
    print(f'Application import failed: {e}')
    import traceback
    traceback.print_exc()
"
```

## Step 8: Deploy and Test

### 8.1 Reload Web App
1. Go to "Web" tab
2. Click "Reload" button
3. Wait for reload to complete

### 8.2 Test Your Site
1. Visit your site: `https://adamcordova.pythonanywhere.com` (replace with your username)
2. Test key functionality:
   - Home page loads
   - File upload works
   - Database queries work
   - Label generation works

### 8.3 Check Error Logs
If there are issues, check the error logs:
1. Go to "Web" tab
2. Click "Error log" link
3. Look for any error messages

## Step 9: Performance Optimization

### 9.1 Enable HTTPS
1. Go to "Web" tab
2. Enable "Force HTTPS"
3. Update any hardcoded HTTP URLs

### 9.2 Set Up Scheduled Tasks (Optional)
If you need periodic maintenance:
1. Go to "Tasks" tab
2. Create scheduled tasks for:
   - Database cleanup
   - Cache clearing
   - Log rotation

## Step 10: Monitoring and Maintenance

### 10.1 Regular Updates
```bash
# Update code from GitHub
cd ~/AGTDesigner
git pull origin main

# Update dependencies if needed
pip install -r requirements.txt

# Reload web app after changes
```

### 10.2 Monitor Performance
- Check error logs regularly
- Monitor CPU usage in dashboard
- Watch disk space usage

## Troubleshooting Common Issues

### Issue 1: Module Not Found
```bash
# Verify virtual environment is active
workon labelmaker-env

# Reinstall missing packages
pip install [missing-package]
```

### Issue 2: Database Connection Failed
```bash
# Check database file exists and has correct permissions
ls -la product_database.db
chmod 644 product_database.db
```

### Issue 3: Static Files Not Loading
- Verify static file mapping in Web tab
- Check file permissions: `chmod 755 static/`

### Issue 4: Memory Issues (Free Account)
- Optimize imports in your code
- Use smaller database if possible
- Consider upgrading to paid plan

### Issue 5: Large File Upload Issues
- Check `MAX_CONTENT_LENGTH` setting
- Consider using chunked uploads
- Optimize file processing

## Security Considerations

1. **Never commit sensitive data** (passwords, API keys)
2. **Use environment variables** for configuration
3. **Keep dependencies updated**
4. **Monitor error logs regularly**
5. **Enable HTTPS**

## Support Resources

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask Documentation: https://flask.palletsprojects.com/
- Your project's GitHub repository for issues

## Quick Commands Reference

```bash
# Navigate to project
cd ~/AGTDesigner

# Activate virtual environment
workon labelmaker-env

# Update code
git pull origin main

# Install new dependencies
pip install [package-name]

# Test database
python -c "import sqlite3; conn = sqlite3.connect('product_database.db'); print('OK')"

# Test app import
python -c "from app import app; print('OK')"

# Check logs
tail -f /var/log/adamcordova.pythonanywhere.com.error.log
```

---

**Important Notes:**
- Replace `adamcordova` with your actual PythonAnywhere username throughout
- Free accounts have limitations; consider upgrading for production use
- Always test thoroughly before going live
- Keep backups of your database and code
