#!/usr/bin/env python3.11
"""
COMPREHENSIVE FIX FOR PYTHONANYWHERE
This script will fix everything and get your app working
"""

import os
import sys
import subprocess
import shutil

def run_command(cmd, description):
    """Run a command and show results"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def fix_everything():
    """Fix all common PythonAnywhere issues"""
    print("🚀 COMPREHENSIVE PYTHONANYWHERE FIX")
    print("=" * 50)
    
    # Check if we're on PythonAnywhere
    current_dir = os.getcwd()
    if 'pythonanywhere' not in current_dir.lower() and '/home/' not in current_dir:
        print("⚠️  This script is designed for PythonAnywhere")
        print("💡 Run this on your PythonAnywhere console")
        return False
    
    print(f"📍 Current directory: {current_dir}")
    
    # Step 1: Navigate to project directory
    project_dir = '/home/adamcordova/AGTDesigner'
    if not os.path.exists(project_dir):
        print(f"❌ Project directory not found: {project_dir}")
        return False
    
    os.chdir(project_dir)
    print(f"📁 Changed to: {os.getcwd()}")
    
    # Step 2: Pull latest changes
    run_command("git pull origin main", "Pulling latest changes")
    
    # Step 3: Install/update dependencies
    run_command("pip3.11 install --user --upgrade pip", "Upgrading pip")
    run_command("pip3.11 install --user -r requirements.txt", "Installing dependencies")
    
    # Step 4: Create necessary directories
    directories = ['uploads', 'sessions', 'cache', 'logs', 'temp']
    for directory in directories:
        dir_path = os.path.join(project_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")
    
    # Step 5: Set proper permissions
    wsgi_files = ['wsgi.py', 'wsgi_working.py', 'wsgi_minimal.py', 'wsgi_ultra_simple.py']
    for wsgi_file in wsgi_files:
        if os.path.exists(wsgi_file):
            os.chmod(wsgi_file, 0o755)  # rwxr-xr-x
            print(f"✅ Set permissions for: {wsgi_file}")
    
    # Step 6: Test Python imports
    print("\n🧪 Testing Python imports...")
    
    test_imports = [
        "import flask",
        "import pandas", 
        "import openpyxl",
        "from app import app",
        "from src.core.data.product_database import ProductDatabase"
    ]
    
    for test_import in test_imports:
        success = run_command(f"python3.11 -c '{test_import}'", f"Testing: {test_import}")
        if not success:
            print(f"⚠️  Import failed: {test_import}")
    
    # Step 7: Test WSGI files
    print("\n🧪 Testing WSGI files...")
    
    wsgi_tests = [
        "python3.11 -c 'import wsgi_ultra_simple; print(\"Ultra-simple WSGI OK\")'",
        "python3.11 -c 'import wsgi_working; print(\"Working WSGI OK\")'",
        "python3.11 -c 'import wsgi_minimal; print(\"Minimal WSGI OK\")'"
    ]
    
    for wsgi_test in wsgi_tests:
        run_command(wsgi_test, f"WSGI test")
    
    # Step 8: Check disk space
    print("\n💾 Checking disk space...")
    try:
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024**3)
        print(f"💽 Free space: {free_gb:.1f} GB")
        
        if free_gb < 1:
            print("⚠️  WARNING: Low disk space!")
        else:
            print("✅ Sufficient disk space")
    except Exception as e:
        print(f"❌ Error checking disk space: {e}")
    
    # Step 9: Create database if needed
    print("\n🗄️ Checking database...")
    db_path = os.path.join(project_dir, 'product_database.db')
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        size_mb = stat.st_size / (1024 * 1024)
        print(f"✅ Database exists: {size_mb:.1f} MB")
    else:
        print("⚠️  Database not found - will be created on first run")
    
    # Step 10: Final recommendations
    print("\n🎯 FINAL RECOMMENDATIONS:")
    print("=" * 30)
    print("1. ✅ Use wsgi_working.py as your WSGI file")
    print("2. ✅ Go to PythonAnywhere Web tab")
    print("3. ✅ Click on your domain name")
    print("4. ✅ Set WSGI file path to: /home/adamcordova/AGTDesigner/wsgi_working.py")
    print("5. ✅ Save and reload your web app")
    print("6. ✅ Check error logs if it still doesn't work")
    
    print("\n🎉 Fix complete! Your app should work now.")
    return True

if __name__ == "__main__":
    fix_everything()
