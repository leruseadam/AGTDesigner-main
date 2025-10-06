# AGT Label Maker - Web Version

## Consolidated Web Application

This repository now contains a **single, consolidated web version** of the AGT Label Maker application.

### Main Application File
- **`app.py`** - The sole web application source file containing all functionality

### Key Features
- ✅ Complete Flask web interface
- ✅ 100% database-derived product matching
- ✅ JointRatio support for pre-roll products  
- ✅ Advanced DOCX label generation with unified font sizing
- ✅ Real-time Excel processing
- ✅ Session management and caching
- ✅ Enhanced JSON matching with database priority

### How to Run
```bash
python app.py
```
The application will start on `http://localhost:8000`

### Consolidation History
- **Date**: October 1, 2025
- **Action**: Consolidated all web versions into single `app.py` file
- **Removed**: `web_deployment/` folder (backed up)
- **Removed**: Alternative app files (`app_backup.py`, `app_integration.py`, `app_simple.py`, `app_webview.py`)
- **Backups Created**: 
  - `web_deployment_backup_YYYYMMDD_HHMMSS.tar.gz`
  - `app_alternatives_backup_YYYYMMDD_HHMMSS.tar.gz`

### Architecture
- **Templates**: `/templates/` - HTML templates for web interface
- **Static Assets**: `/static/` - CSS, JS, and image files
- **Source Code**: `/src/` - Core application modules
- **Database**: `product_database.db` - SQLite database with 13,000+ products

### Recent Updates
- JointRatio functionality for pre-roll products
- Enhanced JSON matching with database priority
- Unified font sizing system
- Template processor optimizations