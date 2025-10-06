#!/usr/bin/env python3.11
"""
Quick PythonAnywhere Diagnostic Tool
Run this script to quickly identify deployment issues
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")

def print_status(message, status="info"):
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    print(f"{icons.get(status, 'ℹ️')} {message}")

def check_basic_environment():
    """Check basic environment"""
    print_header("BASIC ENVIRONMENT")
    
    print(f"👤 Username: {os.getenv('USER', 'unknown')}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📂 Current Directory: {os.getcwd()}")
    print(f"📁 Directory Contents: {os.listdir('.')}")
    
    # Check for critical files
    critical_files = ['app.py', 'requirements.txt']
    for file in critical_files:
        if os.path.exists(file):
            print_status(f"{file} exists", "success")
        else:
            print_status(f"{file} missing", "error")

def check_dependencies():
    """Check installed packages"""
    print_header("DEPENDENCIES")
    
    required_packages = [
        'flask', 'pandas', 'openpyxl', 'python-docx', 'docxtpl', 
        'Pillow', 'jellyfish', 'fuzzywuzzy'
    ]
    
    for package in required_packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print_status(f"{package} installed", "success")
            else:
                print_status(f"{package} missing", "error")
        except Exception as e:
            print_status(f"{package} check failed: {e}", "error")

def check_database():
    """Check database status"""
    print_header("DATABASE")
    
    db_paths = [
        "product_database.db",
        "uploads/product_database.db"
    ]
    
    db_found = False
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                conn.close()
                
                print_status(f"Database found: {db_path}", "success")
                print_status(f"Tables: {len(tables)}", "info")
                print_status(f"Products: {product_count}", "info")
                db_found = True
                break
            except Exception as e:
                print_status(f"Database error at {db_path}: {e}", "error")
    
    if not db_found:
        print_status("No valid database found", "warning")

def check_directories():
    """Check required directories"""
    print_header("DIRECTORIES")
    
    required_dirs = [
        'uploads', 'output', 'cache', 'sessions', 'logs', 'temp',
        'src', 'src/core', 'src/core/data', 'src/utils', 'src/gui'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print_status(f"{dir_path} exists", "success")
        else:
            print_status(f"{dir_path} missing", "warning")

def check_init_files():
    """Check __init__.py files"""
    print_header("INIT FILES")
    
    init_files = [
        'src/__init__.py',
        'src/core/__init__.py',
        'src/core/data/__init__.py',
        'src/utils/__init__.py',
        'src/gui/__init__.py'
    ]
    
    for init_file in init_files:
        if os.path.exists(init_file):
            print_status(f"{init_file} exists", "success")
        else:
            print_status(f"{init_file} missing", "warning")

def test_imports():
    """Test critical imports"""
    print_header("IMPORT TESTS")
    
    imports_to_test = [
        'flask', 'pandas', 'openpyxl', 'docxtpl'
    ]
    
    for module in imports_to_test:
        try:
            __import__(module)
            print_status(f"{module} import successful", "success")
        except ImportError as e:
            print_status(f"{module} import failed: {e}", "error")
    
    # Test app import
    try:
        from app import app
        print_status("app.py import successful", "success")
        print_status(f"App name: {app.name}", "info")
    except Exception as e:
        print_status(f"app.py import failed: {e}", "error")

def generate_recommendations():
    """Generate fix recommendations"""
    print_header("RECOMMENDATIONS")
    
    print("🎯 QUICK FIXES:")
    print("1. Run: chmod +x deploy_pythonanywhere_simple.sh && ./deploy_pythonanywhere_simple.sh")
    print("2. Or run: python3.11 fix_pythonanywhere_deployment.py")
    print("")
    print("📝 WSGI CONFIGURATION:")
    print("- Use: /home/adamcordova/AGTDesigner/wsgi_simple.py")
    print("- Static files: /home/adamcordova/AGTDesigner/static/")
    print("")
    print("🔧 MANUAL FIXES:")
    print("- Install missing packages: python3.11 -m pip install --user [package]")
    print("- Create missing directories: mkdir -p uploads output cache sessions logs temp")
    print("- Create __init__.py files: touch src/__init__.py src/core/__init__.py")
    print("- Fix database: python3.11 init_pythonanywhere_database.py")

def main():
    """Run all diagnostic checks"""
    print("🚨 PythonAnywhere Quick Diagnostic")
    print("=" * 50)
    
    check_basic_environment()
    check_dependencies()
    check_database()
    check_directories()
    check_init_files()
    test_imports()
    generate_recommendations()
    
    print("\n🎉 Diagnostic complete!")
    print("Follow the recommendations above to fix any issues.")

if __name__ == "__main__":
    main()
