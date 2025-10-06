# Development Guide

## Hot Reloading Setup

The Label Maker application now supports hot reloading for development, so you don't have to restart the app to see changes.

## Quick Start

### Development Mode (with Hot Reloading)
```bash
python run_dev.py
```

### Production Mode (without Hot Reloading)
```bash
python run_prod.py
```

### Traditional Method
```bash
python app.py
```

## What's Changed

### 🔄 Hot Reloading Features
- **Template Auto-Reload**: HTML templates automatically refresh when changed
- **Static File Reloading**: CSS, JS, and image files update without restart
- **Python Code Reloading**: Most Python changes trigger automatic restart
- **Debug Mode**: Enhanced error messages and debugging information

### ⚙️ Configuration
The app now uses a `DEVELOPMENT_MODE` setting in `config.py`:

```python
# config.py
class Config:
    # Set to True for development, False for production
    DEVELOPMENT_MODE = True
```

### 🚀 Development Runner (`run_dev.py`)
- Automatically sets development environment variables
- Enables debug mode and hot reloading
- Provides clear startup messages
- Optimized logging for development

### ⚡ Production Runner (`run_prod.py`)
- Runs without hot reloading for better performance
- Enables static file caching
- Disables debug mode
- Optimized for production use

## What Gets Hot Reloaded

### ✅ Automatic Reload
- HTML templates in `templates/` directory
- Static files (CSS, JS, images) in `static/` directory
- Most Python route changes
- Configuration changes in `config.py`

### ⚠️ Requires Manual Restart
- Changes to the main `app.py` file structure
- New imports or major code restructuring
- Changes to the `LabelMakerApp` class initialization

## Development Workflow

1. **Start Development Server**:
   ```bash
   python run_dev.py
   ```

2. **Make Changes**:
   - Edit HTML templates → Auto-refresh
   - Edit CSS/JS files → Auto-refresh
   - Edit Python routes → Auto-restart
   - Edit configuration → Auto-restart

3. **View Changes**:
   - Browser automatically refreshes for template changes
   - Static file changes are immediately visible
   - Python changes restart the server automatically

## Troubleshooting

### Hot Reloading Not Working?
1. Ensure you're using `python run_dev.py`
2. Check that `DEVELOPMENT_MODE = True` in `config.py`
3. Verify the file you're editing is in a watched directory

### Server Won't Start?
1. Check if port 5000 is already in use
2. Ensure all dependencies are installed
3. Check the console for error messages

### Changes Not Appearing?
1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)
2. Check the browser's developer console for errors
3. Verify the file was saved properly

## Performance Notes

- **Development Mode**: Slower startup, no caching, detailed logging
- **Production Mode**: Faster startup, full caching, minimal logging
- **Hot Reloading**: Adds minimal overhead during development

## Environment Variables

The development runner sets these automatically:
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`

You can override these by setting them manually before running the app. 