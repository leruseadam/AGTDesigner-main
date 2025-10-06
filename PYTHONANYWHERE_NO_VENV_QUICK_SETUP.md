# PythonAnywhere Deployment - No Virtual Environment

## Quick Setup Commands

Since you're already in the AGTDesigner directory on PythonAnywhere, run these commands:

### 1. Install Dependencies (No Virtual Environment)

```bash
# Install Flask and core dependencies
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0

# Install data processing libraries
python3.11 -m pip install --user pandas==2.1.4 python-dateutil==2.8.2 pytz==2023.3

# Install Excel processing libraries
python3.11 -m pip install --user openpyxl==3.1.2 xlrd==2.0.1

# Install document processing libraries
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7 lxml==4.9.3

# Install image processing
python3.11 -m pip install --user Pillow==10.1.0

# Install utility libraries
python3.11 -m pip install --user jellyfish==1.2.0 fuzzywuzzy requests
```

### 2. Create Required Directories

```bash
mkdir -p uploads output cache sessions logs temp
chmod 755 uploads output cache sessions
```

### 3. Create Simple WSGI File

```bash
cat > wsgi_simple.py << 'EOF'
#!/usr/bin/python3.11

import sys
import os

# Add your project directory to the Python path
sys.path.append('/home/adamcordova/AGTDesigner')

# Set environment variables for PythonAnywhere optimization
os.environ['PYTHONANYWHERE_DOMAIN'] = 'True'
os.environ['DISABLE_STARTUP_FILE_LOADING'] = 'True'

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF
```

### 4. Test the Application

```bash
python3.11 -c "
import sys
sys.path.append('/home/adamcordova/AGTDesigner')
from app import app
print('✅ Application imported successfully')
print('✅ Flask app type:', type(app))
"
```

### 5. Web App Configuration

In PythonAnywhere Web tab:

1. **Create new web app**: Manual configuration, Python 3.11
2. **Source code**: `/home/adamcordova/AGTDesigner`
3. **WSGI file**: `/home/adamcordova/AGTDesigner/wsgi_simple.py`
4. **Static files**:
   - URL: `/static/`
   - Directory: `/home/adamcordova/AGTDesigner/static/`
5. **Virtual environment**: LEAVE EMPTY
6. **Reload** your web app

## Alternative: Use Existing No-Venv Script

```bash
chmod +x deploy_pythonanywhere_no_venv.sh
./deploy_pythonanywhere_no_venv.sh
```

This will automatically install everything and create the WSGI file for you.

## Troubleshooting

If you get import errors:
```bash
# Check what's installed
python3.11 -m pip list --user

# Test specific imports
python3.11 -c "import flask; print('Flask OK')"
python3.11 -c "import pandas; print('Pandas OK')"
```

Your app should then be available at: `https://adamcordova.pythonanywhere.com`