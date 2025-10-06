# PythonAnywhere Deployment - No Virtual Environment

## Quick Setup (No Virtual Environment)

Since PythonAnywhere free accounts don't support `mkvirtualenv`, use this approach:

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
```

### 2. Run No-VEnv Deployment Script
```bash
chmod +x deploy_pythonanywhere_no_venv.sh
./deploy_pythonanywhere_no_venv.sh
```

This script will:
- Install all packages using `pip3.11 install --user` (no virtual environment)
- Create the WSGI file with proper Python path configuration
- Set up all required directories
- Test the application import

### 3. Web App Configuration

**Create Web App:**
- Go to PythonAnywhere Web tab
- Add new web app → Manual configuration → Python 3.11

**WSGI File:**
Set to: `/home/adamcordova/AGTDesigner/wsgi_configured_no_venv.py`

**Static Files:**
- URL: `/static/`
- Directory: `/home/adamcordova/AGTDesigner/static/`

### 4. Reload and Test
Click "Reload" and visit your app URL.

## Manual Installation (Alternative)

If the script fails, install manually:

```bash
# Install core dependencies
python3.11 -m pip install --user Flask==2.3.3 pandas==2.1.4 openpyxl==3.1.2
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7 
python3.11 -m pip install --user Pillow==10.1.0 fuzzywuzzy jellyfish

# Create directories
mkdir -p uploads output cache sessions logs temp

# Test import
python3.11 -c "from app import app; print('Success!')"
```

## Troubleshooting

**Import errors:** Check that packages are installed with `python3.11 -m pip list --user`

**Path issues:** The WSGI file adds user site-packages to Python path automatically

**Memory issues:** The app includes PythonAnywhere optimizations for free accounts