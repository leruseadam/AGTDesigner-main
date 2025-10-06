#!/usr/bin/env python3
"""
Complete PythonAnywhere Fix Script
Run this on PythonAnywhere Bash console
"""

import os
import shutil

def fix_pythonanywhere_complete():
    """Complete fix for PythonAnywhere web app"""
    print("🚀 Complete PythonAnywhere Fix")
    print("=" * 40)
    
    # Step 1: Update code
    print("Step 1: Updating code...")
    os.system("cd ~/AGTDesigner && git pull origin main")
    print("✅ Code updated")
    
    # Step 2: Copy WSGI file
    print("\nStep 2: Copying WSGI file...")
    source_file = '/home/adamcordova/AGTDesigner/wsgi_pythonanywhere_python311.py'
    target_file = '/var/www/www_agtpricetags_com_wsgi.py'
    
    if os.path.exists(source_file):
        # Create backup
        if os.path.exists(target_file):
            backup_file = f"{target_file}.backup"
            shutil.copy2(target_file, backup_file)
            print(f"✅ Created backup: {backup_file}")
        
        # Copy the file
        shutil.copy2(source_file, target_file)
        print(f"✅ WSGI file copied successfully!")
        
        # Verify the copy
        with open(target_file, 'r') as f:
            content = f.read()
        
        if "DB_HOST" in content and "adamcordova-4822.postgres.pythonanywhere-services.com" in content:
            print("✅ WSGI file verification passed!")
        else:
            print("❌ WSGI file verification failed!")
            return False
    else:
        print(f"❌ Source file not found: {source_file}")
        return False
    
    # Step 3: Test database connection
    print("\nStep 3: Testing database connection...")
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ['DB_PORT']
        )
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products;')
        count = cursor.fetchone()[0]
        print(f"✅ Database connection successful! Products: {count}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    print("\n🎉 All fixes completed successfully!")
    print("💡 Now go to PythonAnywhere Web tab and click 'Reload'")
    print("💡 Wait 60 seconds, then test your web app")
    
    return True

if __name__ == "__main__":
    fix_pythonanywhere_complete()
