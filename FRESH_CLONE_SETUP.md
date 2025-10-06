# Fresh Git Clone Setup for PythonAnywhere

## Step 1: Clean Start (if needed)

If you have an existing AGTDesigner directory that's causing issues:

```bash
# Remove the existing directory
rm -rf AGTDesigner

# OR rename it as backup
mv AGTDesigner AGTDesigner_backup
```

## Step 2: Fresh Git Clone

```bash
# Clone the repository fresh
git clone https://github.com/leruseadam/AGTDesigner.git

# Enter the directory
cd AGTDesigner

# Verify you have the latest code
git pull origin main
```

## Step 3: Quick Setup (No Virtual Environment)

```bash
# Install dependencies to user directory
python3.11 -m pip install --user Flask==2.3.3 pandas==2.1.4 openpyxl==3.1.2 python-docx==0.8.11 Pillow==10.1.0 jellyfish==1.2.0 fuzzywuzzy requests Werkzeug==2.3.7 Flask-CORS==4.0.0

# Create required directories
mkdir -p uploads output cache sessions logs temp

# Create simple WSGI file
cat > wsgi_fresh.py << 'EOF'
#!/usr/bin/python3.11
import sys
import os

# Add project to Python path
sys.path.insert(0, '/home/adamcordova/AGTDesigner')

# Set optimization flags
os.environ['PYTHONANYWHERE_DOMAIN'] = 'True'
os.environ['DISABLE_STARTUP_FILE_LOADING'] = 'True'

# Import Flask app
from app import app as application

if __name__ == "__main__":
    application.run()
EOF

# Test the import
python3.11 -c "
import sys
sys.path.insert(0, '/home/adamcordova/AGTDesigner')
try:
    from app import app
    print('✅ App imported successfully!')
    print('✅ App type:', type(app))
except Exception as e:
    print('❌ Import failed:', e)
    import traceback
    traceback.print_exc()
"
```

## Step 4: PythonAnywhere Web App Setup

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.11**
5. Configure:
   - **Source code**: `/home/adamcordova/AGTDesigner`
   - **WSGI file**: `/home/adamcordova/AGTDesigner/wsgi_fresh.py`
   - **Static files**: 
     - URL: `/static/`
     - Directory: `/home/adamcordova/AGTDesigner/static/`
   - **Virtual environment**: Leave **EMPTY**
6. Click **Reload** 

## Step 5: Check for Success

Your app should be available at: `https://adamcordova.pythonanywhere.com`

## Troubleshooting

If you get errors:

```bash
# Check Python path
python3.11 -c "import sys; print(sys.path)"

# Check installed packages
python3.11 -m pip list --user

# Test specific imports
python3.11 -c "import flask; print('Flask version:', flask.__version__)"

# Check app.py directly
python3.11 -c "exec(open('app.py').read())"
```

## If Still Having Issues

Check the error logs in PythonAnywhere Web tab → Error log, and let me know what specific error you're seeing.