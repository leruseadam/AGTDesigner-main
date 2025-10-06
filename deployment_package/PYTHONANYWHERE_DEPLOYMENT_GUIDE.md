# PythonAnywhere Deployment Guide - Python 3.11

## Overview
This guide will help you deploy your Label Maker application to PythonAnywhere using Python 3.11 (same version as your local environment).

## Prerequisites
- PythonAnywhere account (Free or Paid)
- Git repository access (GitHub recommended)
- Your local project working correctly

## Step 1: Push to GitHub (if not already done)

First, let's initialize and push your project to GitHub:

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit - Label Maker with JSON match improvements"

# Add your GitHub remote (replace with your actual repository)
git remote add origin https://github.com/leruseadam/AGTDesigner.git
git branch -M main
git push -u origin main
```

## Step 2: Clone on PythonAnywhere

1. **Log into PythonAnywhere** and open a Bash console

2. **Clone your repository:**
```bash
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
```

## Step 3: Create Virtual Environment with Python 3.11

PythonAnywhere supports Python 3.11, so we can use the same version:

```bash
# Create virtual environment with Python 3.11
mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env

# Activate the environment (should happen automatically)
workon labelmaker-env

# Verify Python version
python --version
# Should show: Python 3.11.x
```

## Step 4: Install Dependencies

Install packages in the correct order to avoid dependency conflicts:

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install core Flask dependencies
pip install Flask==2.3.3
pip install Werkzeug==2.3.7
pip install Flask-CORS==4.0.0
pip install Flask-Caching==2.1.0

# Install data processing libraries
pip install pandas==2.1.4
pip install python-dateutil==2.8.2
pip install pytz==2023.3

# Install Excel processing
pip install openpyxl==3.1.2
pip install xlrd==2.0.1

# Install document processing
pip install python-docx==0.8.11
pip install docxtpl==0.16.7
pip install docxcompose==1.4.0
pip install lxml==4.9.3

# Install image processing
pip install Pillow==10.1.0

# Install utility libraries
pip install jellyfish==1.2.0
pip install fuzzywuzzy>=0.18.0
pip install python-Levenshtein>=0.27.0
pip install requests>=2.32.0
```

## Step 5: Configure Web App

1. **Go to Web tab** in PythonAnywhere dashboard
2. **Create a new web app:**
   - Choose "Manual configuration"
   - Select **Python 3.11**
   - Don't use a framework template

3. **Configure WSGI file:**
   - Click on the WSGI configuration file link
   - Replace the contents with the prepared WSGI configuration (see `wsgi_pythonanywhere_fixed.py`)

4. **Set up static files:**
   - URL: `/static/`
   - Directory: `/home/yourusername/AGTDesigner/static/`

## Step 6: Update WSGI Configuration

Edit your WSGI file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):

```python
#!/usr/bin/env python3

import os
import sys
import logging

# Set the project directory
project_dir = '/home/yourusername/AGTDesigner'

# Add project to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure minimal logging
logging.basicConfig(level=logging.ERROR)

# Import the Flask app
from app import app as application

# Configure for production
application.config['DEBUG'] = False
application.config['TESTING'] = False

if __name__ == "__main__":
    application.run()
```

## Step 7: Create Required Directories

```bash
# Create necessary directories
mkdir -p ~/AGTDesigner/uploads
mkdir -p ~/AGTDesigner/output
mkdir -p ~/AGTDesigner/cache
mkdir -p ~/AGTDesigner/sessions
mkdir -p ~/AGTDesigner/logs
mkdir -p ~/AGTDesigner/temp

# Set permissions
chmod 755 ~/AGTDesigner/uploads
chmod 755 ~/AGTDesigner/output
chmod 755 ~/AGTDesigner/cache
chmod 755 ~/AGTDesigner/sessions
```

## Step 8: Environment Configuration

Create a production config file:

```bash
# Copy the PythonAnywhere config
cp pythonanywhere_config.py config_production.py
```

## Step 9: Database Setup

If you have a database file, upload it:

```bash
# If you have a local database, you can upload it via Files tab
# Or recreate it:
python init_database.py
```

## Step 10: Test and Deploy

1. **Reload web app** in the Web tab
2. **Check error logs** if there are issues
3. **Visit your site** at `yourusername.pythonanywhere.com`

## Troubleshooting

### Common Issues:

1. **Module not found errors:**
   ```bash
   # Verify virtual environment is active
   workon labelmaker-env
   # Reinstall missing packages
   pip install [missing-package]
   ```

2. **Path issues:**
   - Ensure WSGI file has correct project path
   - Check static files configuration

3. **Database issues:**
   - Ensure database file exists and has correct permissions
   - Check database initialization

4. **Memory issues (free accounts):**
   - Optimize imports in pythonanywhere_config.py
   - Use fallback functions for missing dependencies

### Checking Logs:

```bash
# View error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# View server logs
tail -f /var/log/yourusername.pythonanywhere.com.server.log
```

## Step 11: Enable HTTPS (Recommended)

1. Go to **Web tab**
2. Enable **Force HTTPS**
3. Update any hardcoded HTTP URLs to HTTPS

## Step 12: Set up Scheduled Tasks (if needed)

If your app needs scheduled maintenance:

1. Go to **Tasks tab**
2. Create scheduled tasks for database cleanup, etc.

## Maintenance Commands

```bash
# Update code from GitHub
cd ~/AGTDesigner
git pull origin main

# Restart web app (in Web tab or via API)
# Update dependencies if needed
pip install -r requirements.txt

# Reload web app after changes
```

## Production Optimizations

1. **Disable debug mode** (already done in WSGI)
2. **Enable compression** (configured in pythonanywhere_config.py)
3. **Set up caching** (Flask-Caching already configured)
4. **Optimize database queries**
5. **Use CDN for static files** (optional)

## Security Considerations

1. **Never commit sensitive data** (already in .gitignore)
2. **Use environment variables** for secrets
3. **Keep dependencies updated**
4. **Monitor error logs regularly**

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask Documentation: https://flask.palletsprojects.com/
- Your application-specific issues: Check error logs and GitHub issues

---

**Note**: Replace `yourusername` with your actual PythonAnywhere username throughout this guide.