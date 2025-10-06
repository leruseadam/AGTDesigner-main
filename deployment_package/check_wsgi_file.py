#!/usr/bin/env python3
"""
Quick WSGI file verification script
Run this on PythonAnywhere Bash console
"""

import os

def check_wsgi_file():
    """Check if WSGI file has correct settings"""
    wsgi_file = '/var/www/www_agtpricetags_com_wsgi.py'
    
    print("🔍 Checking WSGI file...")
    print(f"File: {wsgi_file}")
    
    if not os.path.exists(wsgi_file):
        print("❌ WSGI file not found!")
        return False
    
    with open(wsgi_file, 'r') as f:
        content = f.read()
    
    # Check for correct database settings
    checks = [
        ('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com'),
        ('DB_PORT', '14822'),
        ('DB_NAME', 'postgres'),
        ('DB_USER', 'super'),
        ('application = app', 'application = app')
    ]
    
    all_good = True
    for check_name, check_value in checks:
        if check_value in content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_good = False
    
    if all_good:
        print("\n🎉 WSGI file looks correct!")
        print("💡 If web app still shows 'Coming Soon', try:")
        print("   1. Go to Web tab")
        print("   2. Click Reload")
        print("   3. Wait 60 seconds")
    else:
        print("\n❌ WSGI file needs to be updated!")
        print("💡 Run: python urgent_fix_pythonanywhere.py")
    
    return all_good

if __name__ == "__main__":
    check_wsgi_file()
