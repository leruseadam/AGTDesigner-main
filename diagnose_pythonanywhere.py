#!/usr/bin/env python3.11
"""
Comprehensive PythonAnywhere App Loading Diagnostics
Deep Python-based troubleshooting for Flask app issues
"""

import os
import sys
import importlib.util
import sqlite3
from pathlib import Path
from datetime import datetime

class PythonAnywhereAppDiagnostics:
    def __init__(self):
        self.username = os.getenv('USER', 'adamcordova')
        self.project_dir = f"/home/{self.username}/AGTDesigner"
        self.issues_found = []
        self.fixes_applied = []

    def print_header(self, title):
        print(f"\n{'='*50}")
        print(f"🔍 {title}")
        print(f"{'='*50}")

    def check_environment(self):
        """Check Python environment and paths"""
        self.print_header("PYTHON ENVIRONMENT DIAGNOSTICS")
        
        print(f"� Current working directory: {os.getcwd()}")
        print(f"🐍 Python executable: {sys.executable}")
        print(f"🎯 Python version: {sys.version}")
        print(f"� Python path entries: {len(sys.path)}")
        
        for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
            print(f"   {i}: {path}")
        
        if len(sys.path) > 5:
            print(f"   ... and {len(sys.path) - 5} more paths")

    def check_project_structure(self):
        """Verify project directory and critical files"""
        self.print_header("PROJECT STRUCTURE CHECK")
        
        if not os.path.exists(self.project_dir):
            print(f"❌ Project directory not found: {self.project_dir}")
            self.issues_found.append("Missing project directory")
            return False
        
        print(f"✅ Project directory exists: {self.project_dir}")
        
        # Check critical files
        critical_files = [
            'app.py',
            'requirements.txt',
            'src/__init__.py',
            'src/core/__init__.py', 
            'src/core/data/__init__.py'
        ]
        
        missing_files = []
        for file in critical_files:
            file_path = os.path.join(self.project_dir, file)
            if os.path.exists(file_path):
                print(f"✅ {file}")
            else:
                print(f"❌ {file} - MISSING")
                missing_files.append(file)
                
        if missing_files:
            self.issues_found.append(f"Missing files: {', '.join(missing_files)}")
            self.create_missing_init_files(missing_files)
        
        return len(missing_files) == 0

    def create_missing_init_files(self, missing_files):
        """Create missing __init__.py files"""
        for file in missing_files:
            if file.endswith('__init__.py'):
                file_path = os.path.join(self.project_dir, file)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Add appropriate content based on location
                if 'core' in file:
                    content = '# Core module initialization\n'
                elif 'data' in file:
                    content = '# Data module initialization\n'
                else:
                    content = '# Module initialization\n'
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                print(f"🔧 Created: {file}")
                self.fixes_applied.append(f"Created {file}")

    def test_imports(self):
        """Test critical imports"""
        self.print_header("IMPORT TESTING")
        
        # Change to project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(self.project_dir)
            sys.path.insert(0, self.project_dir)
            
            # Test standard library imports
            standard_imports = ['flask', 'pandas', 'openpyxl', 'docxtpl', 'sqlite3']
            
            for module in standard_imports:
                try:
                    spec = importlib.util.find_spec(module)
                    if spec is not None:
                        imported_module = importlib.import_module(module)
                        print(f"✅ {module} - {getattr(imported_module, '__version__', 'version unknown')}")
                    else:
                        print(f"❌ {module} - not found")
                        self.issues_found.append(f"Missing package: {module}")
                except Exception as e:
                    print(f"❌ {module} - {str(e)}")
                    self.issues_found.append(f"Import error {module}: {str(e)}")
            
            # Test project-specific imports
            project_imports = ['src', 'src.core', 'src.core.data']
            
            for module in project_imports:
                try:
                    imported_module = importlib.import_module(module)
                    print(f"✅ {module}")
                except Exception as e:
                    print(f"❌ {module} - {str(e)}")
                    self.issues_found.append(f"Project import error {module}: {str(e)}")
            
            # Test Flask app import
            print("\n🧪 Flask App Import Test:")
            try:
                from app import app
                print(f"✅ Flask app imported successfully")
                print(f"   App name: {getattr(app, 'name', 'unknown')}")
                print(f"   Debug mode: {getattr(app, 'debug', 'unknown')}")
                
                # Test if app can be configured
                with app.app_context():
                    print(f"✅ App context works")
                    
            except Exception as e:
                print(f"❌ Flask app import failed: {str(e)}")
                self.issues_found.append(f"Flask app import error: {str(e)}")
                
                # Print full traceback for Flask app errors
                import traceback
                print("\nFull Flask app import traceback:")
                traceback.print_exc()
                
        finally:
            os.chdir(original_cwd)

    def check_database(self):
        """Check database status"""
        self.print_header("DATABASE CHECK")
        
        db_paths = [
            os.path.join(self.project_dir, 'product_database.db'),
            os.path.join(self.project_dir, 'uploads', 'product_database.db')
        ]
        
        db_found = False
        for db_path in db_paths:
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                print(f"✅ Database found: {db_path}")
                print(f"   Size: {db_size:,} bytes")
                
                # Test database connection
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    print(f"   Tables: {[table[0] for table in tables]}")
                    
                    # Check row counts
                    for table in tables:
                        table_name = table[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        count = cursor.fetchone()[0]
                        print(f"   {table_name}: {count} rows")
                    
                    conn.close()
                    db_found = True
                    break
                    
                except Exception as e:
                    print(f"   ⚠️ Database connection error: {str(e)}")
                    self.issues_found.append(f"Database error: {str(e)}")
        
        if not db_found:
            print("❌ No database found")
            self.issues_found.append("Missing database")
            print("💡 Run: python3.11 init_pythonanywhere_database.py")

    def check_wsgi_files(self):
        """Check available WSGI configurations"""
        self.print_header("WSGI CONFIGURATION CHECK")
        
        wsgi_files = [
            'wsgi_debug.py',
            'wsgi_pythonanywhere_python311.py',
            'wsgi_ultra_optimized.py',
            'wsgi.py'
        ]
        
        for wsgi_file in wsgi_files:
            wsgi_path = os.path.join(self.project_dir, wsgi_file)
            if os.path.exists(wsgi_path):
                size = os.path.getsize(wsgi_path)
                print(f"✅ {wsgi_file} ({size} bytes)")
                
                # Quick syntax check
                try:
                    with open(wsgi_path, 'r') as f:
                        content = f.read()
                    compile(content, wsgi_file, 'exec')
                    print(f"   ✅ Syntax valid")
                except SyntaxError as e:
                    print(f"   ❌ Syntax error: {str(e)}")
                    self.issues_found.append(f"WSGI syntax error in {wsgi_file}")
            else:
                print(f"❌ {wsgi_file} - missing")

    def generate_report(self):
        """Generate final diagnostic report"""
        self.print_header("DIAGNOSTIC REPORT")
        
        print(f"🔍 Total issues found: {len(self.issues_found)}")
        for i, issue in enumerate(self.issues_found, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n🔧 Fixes applied: {len(self.fixes_applied)}")
        for i, fix in enumerate(self.fixes_applied, 1):
            print(f"   {i}. {fix}")
        
        print(f"\n🎯 RECOMMENDED NEXT STEPS:")
        print("="*30)
        
        if not self.issues_found:
            print("✅ No issues detected! Your app should be working.")
            print("   💡 Try reloading your web app in PythonAnywhere")
        else:
            print("1. � Install missing packages:")
            print("   python3.11 -m pip install --user flask pandas openpyxl python-docx docxtpl")
            
            print("\n2. 🗃️  Initialize database if missing:")
            print("   python3.11 init_pythonanywhere_database.py")
            
            print("\n3. ⚙️  Set WSGI file to debug version:")
            print(f"   {self.project_dir}/wsgi_debug.py")
            
            print("\n4. 🔄 Reload web app and check error logs")
            
            print("\n5. ✅ Once working, switch to optimized WSGI:")
            print(f"   {self.project_dir}/wsgi_ultra_optimized.py")

    def run_full_diagnostics(self):
        """Run complete diagnostic suite"""
        print("🚨 PythonAnywhere App Loading Diagnostics")
        print("==========================================")
        
        self.check_environment()
        self.check_project_structure()
        self.test_imports()
        self.check_database()
        self.check_wsgi_files()
        self.generate_report()

def run_diagnostics():
    """Legacy function for backwards compatibility"""
    diagnostics = PythonAnywhereAppDiagnostics()
    diagnostics.run_full_diagnostics()

if __name__ == "__main__":
    diagnostics = PythonAnywhereAppDiagnostics()
    diagnostics.run_full_diagnostics()