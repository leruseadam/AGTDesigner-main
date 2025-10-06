# 🚀 Fresh Label Maker Deployment

## Overview
This script will create a completely fresh deployment of your Label Maker application by cloning from GitHub and setting up everything from scratch.

## What it does:
1. **Cleans up** any existing deployment
2. **Clones fresh** repository from GitHub
3. **Sets up** virtual environment 
4. **Installs** all dependencies
5. **Creates** database with proper schema
6. **Configures** WSGI for production
7. **Tests** the deployment

## Usage

### For PythonAnywhere Deployment:

1. **Push your latest code to GitHub** (if you haven't already):
   ```bash
   git add .
   git commit -m "Fresh deployment ready"
   git push origin main
   ```

2. **On PythonAnywhere Console**, run:
   ```bash
   wget https://raw.githubusercontent.com/leruseadam/AGTDesigner/main/deploy_fresh_complete.sh
   chmod +x deploy_fresh_complete.sh
   ./deploy_fresh_complete.sh
   ```

3. **Configure your PythonAnywhere Web App**:
   - Go to **Web** tab in dashboard
   - Delete existing web app (if any) and create new one
   - Choose **Manual configuration** with **Python 3.11**
   - Set these values:
     - **Source code**: `/home/yourusername/labelMaker`
     - **WSGI file**: `/home/yourusername/labelMaker/wsgi.py`
     - **Virtual environment**: `/home/yourusername/.virtualenvs/labelmaker-env`
     - **Static files**: URL: `/static/`, Directory: `/home/yourusername/labelMaker/static/`

4. **Reload** your web app and test!

### For Local Testing:

```bash
# Make sure you're in the project directory
cd "/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15"

# Run the deployment script
./deploy_fresh_complete.sh
```

## What You Get:

✅ **Complete Flask application** with all features  
✅ **Database** with proper schema and indexes  
✅ **Excel processing** and product matching  
✅ **Label generation** with QR codes  
✅ **Production-optimized** configuration  
✅ **Error handling** and logging  
✅ **Test scripts** for verification  

## After Deployment:

- **Test the deployment**: `cd ~/labelMaker && python test_deployment.py`
- **Update from GitHub**: `cd ~/labelMaker && git pull origin main`
- **Activate environment**: `workon labelmaker-env`

## Troubleshooting:

If you encounter issues:
1. Check the deployment logs during script execution
2. Run the test script: `python test_deployment.py`
3. Check PythonAnywhere error logs in the Web tab
4. Verify all paths are correct in the Web app configuration

## Features Included:

- **Label Generation**: Multiple templates, QR codes, bulk processing
- **Product Management**: Database integration, Excel upload, filtering  
- **Data Processing**: JSON matching, strain categorization, validation
- **User Interface**: Responsive design, real-time feedback
- **Performance**: Optimized for PythonAnywhere deployment

Your Label Maker will work exactly like your local version! 🎉