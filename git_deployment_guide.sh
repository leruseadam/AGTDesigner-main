#!/bin/bash

# Git-Based Deployment Guide for AGT Label Maker
# ===============================================

echo "🚀 Git Deployment Setup for AGT Label Maker"
echo "============================================="

cat << 'EOF'

## Option 1: Direct Git Clone Deployment (Recommended for most hosting)

### Step 1: On your hosting server/service, clone the repository

```bash
# Clone your repository
git clone https://github.com/leruseadam/AGTDesigner.git labelmaker
cd labelmaker

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export SECRET_KEY="your-secure-secret-key"
export FLASK_ENV="production"

# Test the deployment
python3 test_deployment.py

# Start the application
python3 -m flask run --host=0.0.0.0 --port=5000
```

### Step 2: For production deployment with WSGI

```bash
# Configure your web server to point to wsgi.py
# Example for gunicorn:
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

---

## Option 2: Git Pull Deployment (For updates)

### Initial Setup:
```bash
# On your server, clone once
git clone https://github.com/leruseadam/AGTDesigner.git /path/to/your/app
cd /path/to/your/app
pip install -r requirements.txt
```

### For updates:
```bash
# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Restart your web server
# (restart command depends on your hosting service)
```

---

## Option 3: GitHub Actions Auto-Deploy (Advanced)

Create `.github/workflows/deploy.yml` for automatic deployment:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.0
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /path/to/your/app
          git pull origin main
          pip install -r requirements.txt
          # Restart your web server here
```

---

## Option 4: PythonAnywhere Git Integration

### Setup:
1. Open a Bash console on PythonAnywhere
2. Clone your repository:
```bash
git clone https://github.com/leruseadam/AGTDesigner.git
cd AGTDesigner
pip3.x install --user -r requirements.txt
```

3. In your web app configuration:
   - Set Source code: `/home/yourusername/AGTDesigner`
   - Set WSGI file: `/home/yourusername/AGTDesigner/wsgi.py`

### For updates:
```bash
# In PythonAnywhere Bash console
cd AGTDesigner
git pull origin main
pip3.x install --user -r requirements.txt
# Then reload your web app in the Web tab
```

---

## Current Repository Status

Your repository includes:
✅ Complete working application (app.py)
✅ All source code (src/ directory)
✅ Web interface (templates/, static/)
✅ Database (uploads/product_database_AGT_Bothell.db)
✅ Requirements file with all dependencies
✅ WSGI configuration (wsgi.py)
✅ Production configuration
✅ All fixes applied (including concentrate weight fix)

EOF

echo ""
echo "📋 Next Steps:"
echo "1. Choose your deployment method above"
echo "2. Make sure your repository is up to date"
echo "3. Deploy using Git clone or pull"
echo "4. Your hosting service will have the exact same version as your local copy"
echo ""
echo "🎯 Benefits of Git Deployment:"
echo "- Always in sync with your development"
echo "- Easy updates with 'git pull'"
echo "- Version control and rollback capability" 
echo "- No need to manually upload files"
echo ""