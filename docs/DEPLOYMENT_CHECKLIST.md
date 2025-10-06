# PythonAnywhere Deployment Checklist

## Pre-Deployment Preparation
- [ ] Test your app locally with `python app.py`
- [ ] Ensure all dependencies are in `requirements_pythonanywhere.txt`
- [ ] Remove or comment out GUI-related packages (PyQt6) from requirements
- [ ] Test with production config (`DEVELOPMENT_MODE=false`)

## PythonAnywhere Setup
- [ ] Create PythonAnywhere account
- [ ] Upload project files to `/home/yourusername/labelmaker/`
- [ ] Create virtual environment: `python3.10 -m venv ~/labelmaker-venv`
- [ ] Activate virtual environment: `source ~/labelmaker-venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements_pythonanywhere.txt`

## Web App Configuration
- [ ] Go to Web tab in PythonAnywhere dashboard
- [ ] Create new web app (Manual configuration, Python 3.10)
- [ ] Set source code path: `/home/yourusername/labelmaker`
- [ ] Set working directory: `/home/yourusername/labelmaker`
- [ ] Set virtual environment: `/home/yourusername/labelmaker-venv`
- [ ] Edit WSGI file (copy content from your wsgi.py)

## Environment Variables
- [ ] Set `DEVELOPMENT_MODE=false` in Web tab → Environment variables
- [ ] Set `FLASK_ENV=production` in Web tab → Environment variables
- [ ] Set `SECRET_KEY=your-secret-key-here` in Web tab → Environment variables

## Static Files Configuration
- [ ] Set static files URL: `/static/`
- [ ] Set static files directory: `/home/yourusername/labelmaker/static`

## Final Steps
- [ ] Reload web app
- [ ] Test basic functionality
- [ ] Check error logs if issues occur
- [ ] Test file upload functionality
- [ ] Verify document generation works

## Troubleshooting Commands
```bash
# Check if virtual environment is active
echo $VIRTUAL_ENV

# Test imports in Python console
python3 -c "from app import app; print('App imported successfully')"

# Check file permissions
ls -la ~/labelmaker/

# View recent error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

## Common Issues and Solutions

### 1. ModuleNotFoundError
- Solution: Ensure all dependencies are installed in virtual environment
- Check: `pip list` in activated virtual environment

### 2. Permission Errors
- Solution: Set proper permissions: `chmod -R 755 ~/labelmaker/`

### 3. Static Files Not Loading
- Solution: Configure static files mapping in Web tab

### 4. Database/File Upload Issues
- Solution: Create necessary directories and set permissions:
  ```bash
  mkdir -p ~/labelmaker/{uploads,output,cache,logs}
  chmod -R 755 ~/labelmaker/
  ```

### 5. Import Errors
- Solution: Check Python path in WSGI file
- Ensure all local imports use absolute paths

## Performance Optimization
- [ ] Enable gzip compression in Web tab
- [ ] Set appropriate cache headers for static files
- [ ] Monitor CPU seconds usage (free tier has limits)
- [ ] Consider upgrading to paid tier for better performance

## Post-Deployment
- [ ] Set up monitoring/logging
- [ ] Create backup strategy
- [ ] Document any custom configurations
- [ ] Test all features thoroughly
- [ ] Update DNS if using custom domain
