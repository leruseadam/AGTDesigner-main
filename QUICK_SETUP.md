# Quick PythonAnywhere Setup - Python 3.11

## 🚀 Fast Track Deployment

### Step 1: Push to GitHub (if needed)
```bash
# On your local machine
git add .
git commit -m "Ready for PythonAnywhere deployment with Python 3.11"
git push origin main
```

### Step 2: Clone on PythonAnywhere
```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
```

### Step 3: Run Automated Setup
```bash
# Make sure you're in the AGTDesigner directory
./deploy_pythonanywhere.sh
```

### Step 4: Web App Configuration
1. **Go to PythonAnywhere Web tab**
2. **Click "Add a new web app"**
3. **Choose "Manual configuration"**
4. **Select "Python 3.11"**
5. **Set WSGI file**: `/home/yourusername/AGTDesigner/wsgi_configured.py`
6. **Set static files**:
   - URL: `/static/`
   - Directory: `/home/yourusername/AGTDesigner/static/`

### Step 5: Test
1. **Reload web app**
2. **Visit**: `yourusername.pythonanywhere.com`

---

## 🔧 Manual Installation (if script fails)

### Create Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env
workon labelmaker-env
python --version  # Should show Python 3.11.x
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements_python311.txt
```

### Create Directories
```bash
mkdir -p uploads output cache sessions logs temp
```

### Test Import
```bash
python -c "from app import app; print('Success!')"
```

---

## 🚨 Troubleshooting

### Common Issues:

**1. "Module not found" errors:**
```bash
workon labelmaker-env
pip install [missing-package]
```

**2. Permission errors:**
```bash
chmod 755 uploads output cache sessions
```

**3. WSGI configuration issues:**
- Make sure the path in your WSGI file matches your actual directory
- Check that Python 3.11 is selected in the Web tab

**4. Import errors:**
```bash
# Test individual components
python -c "import flask; print('Flask OK')"
python -c "import pandas; print('Pandas OK')"
python -c "import docx; print('DocX OK')"
```

### Check Logs:
- Go to Web tab → Error log
- Look for specific error messages
- Most common: path issues or missing dependencies

---

## ✅ Verification Checklist

- [ ] Python 3.11 selected in Web tab
- [ ] Virtual environment created and activated
- [ ] All dependencies installed without errors
- [ ] WSGI file path correct
- [ ] Static files configured
- [ ] Application imports successfully
- [ ] Web app reloaded
- [ ] Site loads without 500 errors

---

**Need Help?** Check the full deployment guide in `PYTHONANYWHERE_DEPLOYMENT_GUIDE.md`