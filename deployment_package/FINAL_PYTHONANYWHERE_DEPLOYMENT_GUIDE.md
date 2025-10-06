# Final PythonAnywhere Deployment Guide - Large Database (500MB)

## 🚨 CRITICAL: Large Database Deployment

Your database is **499.79 MB** with **17,841 products** - this requires a **paid PythonAnywhere plan**.

## 📊 Database Analysis Results

**Database Statistics:**
- **Size**: 499.79 MB (original) → 26.18 MB (compressed)
- **Products**: 17,841 products
- **Tables**: 8 tables (strains, products, lineage_history, etc.)
- **Compression**: 98.6% reduction (1.9GB → 26MB)

**Files Prepared:**
- `product_database.db.gz`: 29.25 MB (compressed database)
- `product_database_dump.sql.gz`: 26.18 MB (compressed SQL dump) ⭐ **Use this one**

## ⚠️ PythonAnywhere Account Requirements

### ❌ Free Tier Limitations
- **Disk Space**: 512MB total (your database alone is 500MB)
- **File Upload**: 100MB limit per file
- **CPU Seconds**: Limited (database operations will consume quickly)

### ✅ REQUIRED: Upgrade to Paid Plan
- **Minimum**: Hacker plan ($5/month) - 3GB disk space
- **Recommended**: Web Developer ($20/month) - 20GB disk space, better performance
- **Best**: Startup ($100/month) - 100GB disk space, dedicated resources

## 🚀 Step-by-Step Deployment

### Step 1: Upgrade PythonAnywhere Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Login to your account
3. Go to "Account" tab
4. Upgrade to **Hacker plan ($5/month)** - **REQUIRED**
5. Wait for account upgrade to complete

### Step 2: Clone Repository on PythonAnywhere
1. Open Bash console in PythonAnywhere
2. Clone your repository:
```bash
cd ~
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
```

### Step 3: Upload Compressed Database
Since the compressed file is only 26.18 MB, you can upload it via Files tab:

1. Go to "Files" tab in PythonAnywhere dashboard
2. Navigate to `/home/yourusername/AGTDesigner/`
3. Upload `product_database_dump.sql.gz` (26.18 MB)

**Alternative - Console Upload:**
```bash
# If you have the file on a web server or GitHub releases
wget https://your-server.com/product_database_dump.sql.gz
# Or use scp if you have SSH access
```

### Step 4: Restore Database
```bash
# Navigate to project directory
cd ~/AGTDesigner

# Decompress the database dump
gunzip product_database_dump.sql.gz

# Restore database from SQL dump
python3 -c "
import sqlite3
print('Creating database...')
conn = sqlite3.connect('product_database.db')
print('Restoring from SQL dump...')
with open('product_database_dump.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Database restored successfully!')
"

# Test database
python3 -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f'Database test successful! Products: {count}')
conn.close()
"
```

### Step 5: Set Up Python Environment
```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.11 labelmaker-env
workon labelmaker-env

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install Flask==2.3.3 Werkzeug==2.3.7 Flask-CORS==4.0.0 Flask-Caching==2.1.0
pip install pandas==2.1.4 openpyxl==3.1.2 xlrd==2.0.1
pip install python-docx==0.8.11 docxtpl==0.16.7 docxcompose==1.4.0 lxml==4.9.3
pip install Pillow==10.1.0 python-dateutil==2.8.2 pytz==2023.3
pip install jellyfish==1.2.0 requests>=2.32.0 fuzzywuzzy>=0.18.0 python-Levenshtein>=0.27.0
```

### Step 6: Create Required Directories
```bash
mkdir -p uploads output cache sessions logs temp
chmod 755 uploads output cache sessions logs temp
```

### Step 7: Configure Web App
1. Go to "Web" tab in PythonAnywhere dashboard
2. Create new web app:
   - Choose "Manual configuration"
   - Select **Python 3.11**
   - Don't use framework template

3. Configure WSGI file (replace `yourusername` with your actual username):
```python
#!/usr/bin/env python3
import os
import sys
import logging

# Project directory
project_dir = '/home/yourusername/AGTDesigner'

# Add to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure logging
logging.basicConfig(level=logging.ERROR)
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

try:
    from app import app as application
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    print("WSGI application loaded successfully")
except Exception as e:
    print(f"Error: {e}")
    raise
```

4. Configure static files:
   - URL: `/static/`
   - Directory: `/home/yourusername/AGTDesigner/static/`

### Step 8: Test Application
```bash
# Test application import
python3 -c "
try:
    from app import app
    print('✅ Application import successful')
    print(f'App name: {app.name}')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    import traceback
    traceback.print_exc()
"
```

### Step 9: Deploy and Test
1. **Reload web app** in PythonAnywhere Web tab
2. **Visit your site**: `https://yourusername.pythonanywhere.com`
3. **Test key functionality**:
   - Home page loads
   - File upload works
   - Database queries work
   - Label generation works

## 🔧 Performance Optimization for Large Database

### Database Optimization
```bash
# Optimize database after restoration
python3 -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
print('Database optimized')
"
```

### Application Optimization
- **Pagination**: Implement pagination for product listings
- **Caching**: Use Flask-Caching for frequently accessed data
- **Query Optimization**: Add indexes for frequently queried columns
- **Static Files**: Use CDN for static assets

## 🚨 Troubleshooting Large Database Issues

### Common Problems

1. **Out of Memory Errors**
   ```bash
   # Monitor memory usage
   free -h
   # Optimize queries, use LIMIT clauses
   ```

2. **Slow Database Queries**
   ```bash
   # Add indexes
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('product_database.db')
   conn.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
   conn.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')
   conn.commit()
   conn.close()
   print('Indexes created')
   "
   ```

3. **Disk Space Issues**
   ```bash
   # Check disk usage
   df -h
   # Clean up old files
   rm -f product_database_dump.sql  # Remove uncompressed dump
   ```

4. **Upload Timeout**
   - Use compressed files (26MB vs 500MB)
   - Upload via Files tab (under 100MB limit)
   - Use console upload for larger files

### Monitoring Commands
```bash
# Check database size
du -h product_database.db

# Check disk usage
df -h

# Monitor CPU usage
top

# Check error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

## 💰 Cost Analysis

### PythonAnywhere Plans
- **Free**: ❌ Insufficient (512MB disk, 500MB database)
- **Hacker ($5/month)**: ✅ Minimum viable (3GB disk)
- **Web Developer ($20/month)**: ✅ Recommended (20GB disk, better performance)
- **Startup ($100/month)**: ✅ Best performance (100GB disk, dedicated resources)

### Alternative Hosting Options
- **Railway**: $5/month + PostgreSQL $5/month = $10/month
- **DigitalOcean**: $12/month droplet + $15/month PostgreSQL = $27/month
- **Heroku**: $7/month + PostgreSQL $9/month = $16/month

## 📋 Quick Reference Commands

```bash
# Navigate to project
cd ~/AGTDesigner

# Activate virtual environment
workon labelmaker-env

# Test database
python3 -c "import sqlite3; conn = sqlite3.connect('product_database.db'); print('OK')"

# Test application
python3 -c "from app import app; print('OK')"

# Check database size
du -h product_database.db

# Optimize database
python3 -c "import sqlite3; conn = sqlite3.connect('product_database.db'); conn.execute('VACUUM'); conn.close()"

# Update code
git pull origin main

# Reload web app (in Web tab)
```

## ✅ Deployment Checklist

- [ ] Upgrade PythonAnywhere to Hacker plan ($5/month)
- [ ] Clone repository from GitHub
- [ ] Upload `product_database_dump.sql.gz` (26.18 MB)
- [ ] Restore database from SQL dump
- [ ] Test database (17,841 products)
- [ ] Set up Python 3.11 virtual environment
- [ ] Install all dependencies
- [ ] Create required directories
- [ ] Configure web app (Manual, Python 3.11)
- [ ] Set up WSGI configuration
- [ ] Configure static files
- [ ] Test application import
- [ ] Reload web app
- [ ] Test deployment at your site URL
- [ ] Monitor performance and error logs

## 🎉 Success Indicators

- ✅ Database restored with 17,841 products
- ✅ Application imports successfully
- ✅ Web app loads without errors
- ✅ File upload functionality works
- ✅ Label generation works
- ✅ No memory or disk space errors

---

**⚠️ Remember**: Your 500MB database requires a paid PythonAnywhere plan. The free tier will not work with this database size.

**📞 Support**: If you encounter issues, check the error logs in the Web tab and refer to the troubleshooting section above.
