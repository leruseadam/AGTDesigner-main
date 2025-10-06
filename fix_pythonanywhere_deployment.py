#!/usr/bin/env python3.11
"""
Comprehensive PythonAnywhere Deployment Fix
Handles database issues, missing dependencies, and deployment problems
"""

import os
import sys
import sqlite3
import subprocess
import json
from datetime import datetime
from pathlib import Path

class PythonAnywhereDeploymentFixer:
    def __init__(self):
        self.username = os.getenv('USER', 'adamcordova')
        self.project_dir = f"/home/{self.username}/AGTDesigner"
        self.issues_found = []
        self.fixes_applied = []
        self.critical_errors = []

    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print(f"{'='*60}")

    def print_status(self, message, status="info"):
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        print(f"{icons.get(status, 'ℹ️')} {message}")

    def check_environment(self):
        """Check PythonAnywhere environment"""
        self.print_header("ENVIRONMENT CHECK")
        
        print(f"👤 Username: {self.username}")
        print(f"📁 Project Directory: {self.project_dir}")
        print(f"🐍 Python Version: {sys.version}")
        print(f"📂 Current Directory: {os.getcwd()}")
        
        # Check if we're in the right directory
        if not os.path.exists("app.py"):
            self.print_status("app.py not found in current directory", "error")
            self.critical_errors.append("Not in project directory")
            return False
        
        self.print_status("Environment check passed", "success")
        return True

    def fix_directory_structure(self):
        """Fix missing directories and __init__.py files"""
        self.print_header("DIRECTORY STRUCTURE FIX")
        
        required_dirs = [
            "uploads",
            "output", 
            "cache",
            "sessions",
            "logs",
            "temp",
            "src",
            "src/core",
            "src/core/data",
            "src/utils",
            "src/gui"
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                self.print_status(f"Created directory: {dir_path}", "success")
                self.fixes_applied.append(f"Created directory: {dir_path}")
        
        # Create missing __init__.py files
        init_files = [
            "src/__init__.py",
            "src/core/__init__.py", 
            "src/core/data/__init__.py",
            "src/utils/__init__.py",
            "src/gui/__init__.py"
        ]
        
        for init_file in init_files:
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Auto-generated __init__.py\n')
                self.print_status(f"Created: {init_file}", "success")
                self.fixes_applied.append(f"Created: {init_file}")

    def fix_database_issues(self):
        """Fix database corruption and initialization"""
        self.print_header("DATABASE FIX")
        
        # Find existing database files
        db_patterns = ['*.db', '*database*', '*.sqlite*']
        existing_dbs = []
        
        for pattern in db_patterns:
            for db_file in Path('.').rglob(pattern):
                if db_file.is_file():
                    existing_dbs.append(str(db_file))
        
        if existing_dbs:
            self.print_status(f"Found {len(existing_dbs)} database files", "info")
            
            # Test each database
            for db_path in existing_dbs:
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    self.print_status(f"✅ {db_path}: {len(tables)} tables", "success")
                except sqlite3.DatabaseError as e:
                    self.print_status(f"❌ {db_path}: Corrupted - {e}", "error")
                    # Backup and remove corrupted database
                    backup_path = f"{db_path}.corrupted_backup"
                    os.rename(db_path, backup_path)
                    self.print_status(f"Backed up corrupted database to: {backup_path}", "warning")
                    self.fixes_applied.append(f"Backed up corrupted database: {db_path}")
        
        # Initialize fresh database
        db_path = "uploads/product_database.db"
        self.print_status("Initializing fresh database...", "info")
        
        try:
            # Ensure uploads directory exists
            os.makedirs("uploads", exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create products table with full schema
            create_products_sql = '''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    "Product Name*" TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    strain_id INTEGER,
                    "Product Type*" TEXT NOT NULL,
                    "Vendor/Supplier*" TEXT,
                    "Product Brand" TEXT,
                    "Description" TEXT,
                    "Weight*" TEXT,
                    "Units" TEXT,
                    "Price" TEXT,
                    "Lineage" TEXT,
                    first_seen_date TEXT NOT NULL,
                    last_seen_date TEXT NOT NULL,
                    total_occurrences INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    "Product Strain" TEXT,
                    "Quantity*" TEXT,
                    "DOH" TEXT,
                    "Concentrate Type" TEXT,
                    "Ratio" TEXT,
                    "JointRatio" TEXT,
                    "THC test result" TEXT,
                    "CBD test result" TEXT,
                    "Test result unit (% or mg)" TEXT,
                    "State" TEXT,
                    "Is Sample? (yes/no)" TEXT,
                    "Is MJ product?(yes/no)" TEXT,
                    "Discountable? (yes/no)" TEXT,
                    "Room*" TEXT,
                    "Batch Number" TEXT,
                    "Lot Number" TEXT,
                    "Barcode*" TEXT,
                    "Medical Only (Yes/No)" TEXT,
                    "Med Price" TEXT,
                    "Expiration Date(YYYY-MM-DD)" TEXT,
                    "Is Archived? (yes/no)" TEXT,
                    "THC Per Serving" TEXT,
                    "Allergens" TEXT,
                    "Solvent" TEXT,
                    "Accepted Date" TEXT,
                    "Internal Product Identifier" TEXT,
                    "Product Tags (comma separated)" TEXT,
                    "Image URL" TEXT,
                    "Ingredients" TEXT,
                    "Total THC" TEXT,
                    "THCA" TEXT,
                    "CBDA" TEXT,
                    "CBN" TEXT,
                    "THC" TEXT,
                    "CBD" TEXT,
                    "Total CBD" TEXT,
                    "CBGA" TEXT,
                    "CBG" TEXT,
                    "Total CBG" TEXT,
                    "CBC" TEXT,
                    "CBDV" TEXT,
                    "THCV" TEXT,
                    "CBGV" TEXT,
                    "CBNV" TEXT,
                    "CBGVA" TEXT,
                    FOREIGN KEY (strain_id) REFERENCES strains (id),
                    UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
                )
            '''
            
            cursor.execute(create_products_sql)
            
            # Create strains table
            create_strains_sql = '''
                CREATE TABLE IF NOT EXISTS strains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    lineage TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            '''
            
            cursor.execute(create_strains_sql)
            
            # Add sample data
            now = datetime.now().isoformat()
            sample_products = [
                ("Blue Dream - 3.5g", "blue_dream_35g", "Flower", "A Greener Today", "High End Farms", 
                 "3.5", "g", "$45.00", "HYBRID", "Blue Dream", now, now, now, now, "%"),
                ("Wedding Cake - 1g", "wedding_cake_1g", "Flower", "A Greener Today", "Thunder Chief", 
                 "1", "g", "$15.00", "INDICA", "Wedding Cake", now, now, now, now, "%"),
                ("Sour Diesel - 1g Pre-Roll", "sour_diesel_1g_preroll", "Pre-Roll", "A Greener Today", "Various", 
                 "1", "g", "$12.00", "SATIVA", "Sour Diesel", now, now, now, now, "%"),
                ("Mixed Strain Gummies - 10mg", "mixed_strain_gummies_10mg", "Edible (Solid)", "A Greener Today", "Kellys", 
                 "10", "mg", "$8.00", "MIXED", "Mixed", now, now, now, now, "%")
            ]
            
            for product in sample_products:
                cursor.execute('''
                    INSERT OR IGNORE INTO products 
                    ("Product Name*", normalized_name, "Product Type*", "Vendor/Supplier*", "Product Brand", 
                     "Weight*", "Units", "Price", "Lineage", "Product Strain", 
                     first_seen_date, last_seen_date, created_at, updated_at, "Test result unit (% or mg)") 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', product)
            
            conn.commit()
            conn.close()
            
            self.print_status(f"Database initialized successfully: {db_path}", "success")
            self.fixes_applied.append(f"Initialized database: {db_path}")
            
        except Exception as e:
            self.print_status(f"Database initialization failed: {e}", "error")
            self.critical_errors.append(f"Database initialization failed: {e}")

    def check_dependencies(self):
        """Check and install missing dependencies"""
        self.print_header("DEPENDENCY CHECK")
        
        required_packages = [
            "flask",
            "pandas", 
            "openpyxl",
            "python-docx",
            "docxtpl",
            "Pillow",
            "jellyfish",
            "fuzzywuzzy"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.print_status(f"✅ {package} installed", "success")
                else:
                    missing_packages.append(package)
                    self.print_status(f"❌ {package} missing", "error")
            except Exception as e:
                missing_packages.append(package)
                self.print_status(f"❌ {package} check failed: {e}", "error")
        
        if missing_packages:
            self.print_status(f"Installing missing packages: {', '.join(missing_packages)}", "info")
            try:
                for package in missing_packages:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--user", package],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.print_status(f"✅ Installed {package}", "success")
                        self.fixes_applied.append(f"Installed package: {package}")
                    else:
                        self.print_status(f"❌ Failed to install {package}: {result.stderr}", "error")
                        self.critical_errors.append(f"Failed to install {package}")
            except Exception as e:
                self.print_status(f"Package installation failed: {e}", "error")
                self.critical_errors.append(f"Package installation failed: {e}")

    def test_application_import(self):
        """Test if the Flask application can be imported"""
        self.print_header("APPLICATION IMPORT TEST")
        
        try:
            # Test basic imports
            self.print_status("Testing Flask import...", "info")
            import flask
            
            self.print_status("Testing pandas import...", "info")
            import pandas
            
            self.print_status("Testing openpyxl import...", "info")
            import openpyxl
            
            self.print_status("Testing docxtpl import...", "info")
            import docxtpl
            
            # Test application import
            self.print_status("Testing application import...", "info")
            from app import app
            
            self.print_status("✅ Application imported successfully!", "success")
            self.print_status(f"App name: {app.name}", "info")
            self.print_status(f"Debug mode: {app.debug}", "info")
            
            return True
            
        except ImportError as e:
            self.print_status(f"❌ Import failed: {e}", "error")
            self.critical_errors.append(f"Import failed: {e}")
            return False
        except Exception as e:
            self.print_status(f"❌ Application test failed: {e}", "error")
            self.critical_errors.append(f"Application test failed: {e}")
            return False

    def create_wsgi_config(self):
        """Create optimized WSGI configuration"""
        self.print_header("WSGI CONFIGURATION")
        
        wsgi_content = f'''#!/usr/bin/env python3.11
"""
PythonAnywhere WSGI configuration for Label Maker application
Auto-generated by deployment fixer
"""

import os
import sys
import logging

# Configure the project directory
project_dir = '{self.project_dir}'

# Add project to Python path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Add user site-packages for --user installed packages
import site
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Set environment variables for PythonAnywhere
os.environ['PYTHONANYWHERE_SITE'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Configure minimal logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s - %(message)s'
)

# Suppress verbose logging from libraries
for logger_name in ['werkzeug', 'urllib3', 'requests', 'pandas', 'openpyxl']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

try:
    # Import the Flask application
    from app import app as application
    
    # Production configuration
    application.config.update(
        DEBUG=False,
        TESTING=False,
        TEMPLATES_AUTO_RELOAD=False,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year cache for static files
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max file size
    )
    
    print("✅ WSGI application loaded successfully")
    
except ImportError as e:
    print(f"❌ Failed to import Flask app: {{e}}")
    print(f"Python path: {{sys.path}}")
    print(f"Current working directory: {{os.getcwd()}}")
    raise
except Exception as e:
    print(f"❌ Error configuring Flask app: {{e}}")
    raise

# For direct execution
if __name__ == "__main__":
    application.run(debug=False)
'''
        
        wsgi_file = "wsgi_fixed.py"
        with open(wsgi_file, 'w') as f:
            f.write(wsgi_content)
        
        self.print_status(f"Created WSGI configuration: {wsgi_file}", "success")
        self.fixes_applied.append(f"Created WSGI config: {wsgi_file}")
        
        return wsgi_file

    def generate_final_report(self):
        """Generate comprehensive fix report"""
        self.print_header("DEPLOYMENT FIX REPORT")
        
        print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
        for i, fix in enumerate(self.fixes_applied, 1):
            print(f"   {i}. {fix}")
        
        print(f"\n⚠️  Issues Found: {len(self.issues_found)}")
        for i, issue in enumerate(self.issues_found, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n❌ Critical Errors: {len(self.critical_errors)}")
        for i, error in enumerate(self.critical_errors, 1):
            print(f"   {i}. {error}")
        
        if self.critical_errors:
            self.print_status("❌ Critical errors found - deployment may not work", "error")
        else:
            self.print_status("✅ No critical errors - deployment should work", "success")
        
        print(f"\n🎯 NEXT STEPS:")
        print("="*30)
        print("1. 📝 In PythonAnywhere Web tab:")
        print(f"   - Source code: {self.project_dir}")
        print(f"   - WSGI file: {self.project_dir}/wsgi_fixed.py")
        print(f"   - Static files URL: /static/")
        print(f"   - Static files path: {self.project_dir}/static/")
        print("")
        print("2. 🔄 Reload your web app")
        print("")
        print("3. 📋 Check error logs if there are issues")
        print("")
        print("4. 🧪 Test your application functionality")
        print("")
        print("5. ✅ Switch to optimized WSGI once confirmed working:")
        print(f"   {self.project_dir}/wsgi_ultra_optimized.py")

    def run_complete_fix(self):
        """Run the complete deployment fix process"""
        print("🚨 PythonAnywhere Deployment Fix")
        print("="*50)
        print(f"Timestamp: {datetime.now()}")
        print(f"Username: {self.username}")
        print(f"Project: {self.project_dir}")
        
        # Step 1: Environment check
        if not self.check_environment():
            self.print_status("Environment check failed - aborting", "error")
            return False
        
        # Step 2: Fix directory structure
        self.fix_directory_structure()
        
        # Step 3: Fix database issues
        self.fix_database_issues()
        
        # Step 4: Check dependencies
        self.check_dependencies()
        
        # Step 5: Test application import
        if not self.test_application_import():
            self.print_status("Application import test failed", "error")
        
        # Step 6: Create WSGI configuration
        self.create_wsgi_config()
        
        # Step 7: Generate report
        self.generate_final_report()
        
        return len(self.critical_errors) == 0

if __name__ == "__main__":
    fixer = PythonAnywhereDeploymentFixer()
    success = fixer.run_complete_fix()
    
    if success:
        print("\n🎉 Deployment fix completed successfully!")
    else:
        print("\n❌ Deployment fix completed with errors - check the report above")
