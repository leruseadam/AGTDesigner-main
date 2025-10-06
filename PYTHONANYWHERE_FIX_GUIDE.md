# 🚨 PythonAnywhere Deployment Fix Guide

## The Problem
Your last PythonAnywhere deployment failed and led to database problems. This guide provides a comprehensive fix for common deployment issues.

## 🎯 Quick Fix (Recommended)

### Step 1: Upload the Fix Script
1. Upload `deploy_pythonanywhere_simple.sh` to your PythonAnywhere home directory
2. Upload `fix_pythonanywhere_deployment.py` to your AGTDesigner directory

### Step 2: Run the Simple Fix
```bash
cd ~/AGTDesigner
chmod +x ../deploy_pythonanywhere_simple.sh
../deploy_pythonanywhere_simple.sh
```

### Step 3: Configure Web App
1. Go to PythonAnywhere **Web tab**
2. Set your web app configuration:
   - **Source code**: `/home/adamcordova/AGTDesigner`
   - **WSGI file**: `/home/adamcordova/AGTDesigner/wsgi_simple.py`
   - **Static files URL**: `/static/`
   - **Static files path**: `/home/adamcordova/AGTDesigner/static/`

### Step 4: Reload and Test
1. **Reload your web app**
2. **Check error logs** if there are issues
3. **Test your application**

## 🔧 Comprehensive Fix (If Simple Fix Fails)

### Option A: Run the Python Fixer
```bash
cd ~/AGTDesigner
python3.11 fix_pythonanywhere_deployment.py
```

### Option B: Manual Fix Process

#### 1. Fix Directory Structure
```bash
cd ~/AGTDesigner
mkdir -p uploads output cache sessions logs temp src src/core src/core/data src/utils src/gui
touch src/__init__.py src/core/__init__.py src/core/data/__init__.py src/utils/__init__.py src/gui/__init__.py
```

#### 2. Install Dependencies
```bash
python3.11 -m pip install --user --upgrade pip setuptools wheel
python3.11 -m pip install --user Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0
python3.11 -m pip install --user pandas==2.1.4 python-dateutil==2.8.2 pytz==2023.3
python3.11 -m pip install --user openpyxl==3.1.2 xlrd==2.0.1
python3.11 -m pip install --user python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3
python3.11 -m pip install --user Pillow==10.1.0
python3.11 -m pip install --user jellyfish==1.2.0 fuzzywuzzy>=0.18.0 requests>=2.32.0
python3.11 -m pip install --user python-Levenshtein>=0.27.0 || echo "python-Levenshtein failed - will use fallback"
```

#### 3. Fix Database Issues
```bash
# Remove corrupted databases
ls *.db 2>/dev/null | while read db; do
    if ! sqlite3 "$db" "SELECT 1;" >/dev/null 2>&1; then
        echo "Removing corrupted database: $db"
        mv "$db" "${db}.corrupted_backup"
    fi
done

# Initialize fresh database
python3.11 init_pythonanywhere_database.py
```

#### 4. Test Application
```bash
python3.11 -c "from app import app; print('✅ Application imported successfully')"
```

## 🗃️ Database-Specific Fixes

### Fix 1: Empty Database
If your database is empty or corrupted:

```bash
cd ~/AGTDesigner
python3.11 init_pythonanywhere_database.py
```

### Fix 2: Import Your Data
If you have exported data:

```bash
# Upload database_export.json to your AGTDesigner directory
python3.11 import_pythonanywhere_database.py
```

### Fix 3: Verify Database
```bash
python3.11 -c "
import sqlite3
conn = sqlite3.connect('uploads/product_database.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f'Products in database: {count}')
conn.close()
"
```

## ⚙️ WSGI Configuration Fixes

### Debug WSGI (For Troubleshooting)
Set WSGI file to: `/home/adamcordova/AGTDesigner/wsgi_debug.py`

### Simple WSGI (Recommended)
Set WSGI file to: `/home/adamcordova/AGTDesigner/wsgi_simple.py`

### Optimized WSGI (After Everything Works)
Set WSGI file to: `/home/adamcordova/AGTDesigner/wsgi_ultra_optimized.py`

## 🔍 Troubleshooting Common Issues

### Issue 1: Module Not Found
**Symptoms**: ImportError when loading the app
**Fix**:
```bash
python3.11 -m pip install --user [missing-module]
```

### Issue 2: Database Connection Error
**Symptoms**: Database-related errors in logs
**Fix**:
```bash
cd ~/AGTDesigner
python3.11 fix_pythonanywhere_database.py
```

### Issue 3: Permission Errors
**Symptoms**: File permission errors
**Fix**:
```bash
chmod 755 ~/AGTDesigner
chmod 755 ~/AGTDesigner/uploads
chmod 755 ~/AGTDesigner/static
```

### Issue 4: Memory Issues (Free Accounts)
**Symptoms**: App crashes or times out
**Fix**: Use optimized WSGI and enable performance optimizations

## 📋 Verification Checklist

- [ ] All directories created (`uploads`, `output`, `cache`, etc.)
- [ ] All `__init__.py` files exist
- [ ] Dependencies installed successfully
- [ ] Database initialized with sample data
- [ ] Application imports without errors
- [ ] WSGI file configured correctly
- [ ] Web app reloaded
- [ ] Error logs checked (no critical errors)
- [ ] Application functionality tested

## 🚀 Performance Optimization (After Fix)

Once your app is working:

1. **Switch to optimized WSGI**: `wsgi_ultra_optimized.py`
2. **Enable caching**: Already configured in optimized WSGI
3. **Monitor memory usage**: Check PythonAnywhere dashboard
4. **Optimize database queries**: Review slow queries in logs

## 📞 Getting Help

### Check Error Logs
```bash
# View recent error logs
tail -f /var/log/adamcordova.pythonanywhere.com.error.log

# View server logs  
tail -f /var/log/adamcordova.pythonanywhere.com.server.log
```

### Run Diagnostics
```bash
cd ~/AGTDesigner
python3.11 diagnose_pythonanywhere.py
```

### Manual Testing
```bash
cd ~/AGTDesigner
python3.11 -c "
import sys
sys.path.insert(0, '.')
from app import app
print('✅ App loaded successfully')
print(f'Debug mode: {app.debug}')
print(f'App name: {app.name}')
"
```

## 🎯 Success Indicators

Your deployment is successful when:
- ✅ Web app loads without errors
- ✅ Database contains products (check with sample data)
- ✅ File uploads work
- ✅ Label generation works
- ✅ No critical errors in logs

## 🔄 Maintenance

### Regular Updates
```bash
cd ~/AGTDesigner
git pull origin main
python3.11 -m pip install --user -r requirements.txt
# Reload web app
```

### Database Backups
```bash
cd ~/AGTDesigner
cp uploads/product_database.db "backup_$(date +%Y%m%d_%H%M%S).db"
```

---

**Remember**: Start with the simple fix script. It handles 90% of common deployment issues automatically. Only use the manual process if the simple fix doesn't work.
