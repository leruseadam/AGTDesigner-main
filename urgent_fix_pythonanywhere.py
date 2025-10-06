#!/usr/bin/env python3
"""
URGENT: Fix PythonAnywhere Database Connection
This script MUST be run on PythonAnywhere Bash console
"""

import os
import shutil

def urgent_fix():
    """Urgent fix for database connection"""
    print("🚨 URGENT: Fixing PythonAnywhere Database Connection")
    print("=" * 55)
    
    # Step 1: Check current WSGI file
    wsgi_file = '/var/www/www_agtpricetags_com_wsgi.py'
    print(f"Checking WSGI file: {wsgi_file}")
    
    if os.path.exists(wsgi_file):
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        if 'adamcordova-4822.postgres.pythonanywhere-services.com' in content:
            print("✅ WSGI file already has correct database settings")
        else:
            print("❌ WSGI file has WRONG database settings")
            print("🔧 Fixing WSGI file...")
            
            # Create backup
            backup_file = f"{wsgi_file}.backup"
            shutil.copy2(wsgi_file, backup_file)
            print(f"✅ Created backup: {backup_file}")
            
            # Copy correct WSGI file
            source_file = '/home/adamcordova/AGTDesigner/wsgi_pythonanywhere_python311.py'
            if os.path.exists(source_file):
                shutil.copy2(source_file, wsgi_file)
                print("✅ WSGI file updated!")
            else:
                print(f"❌ Source file not found: {source_file}")
                return False
    else:
        print(f"❌ WSGI file not found: {wsgi_file}")
        return False
    
    # Step 2: Test environment variables
    print("\n🔧 Testing environment variables...")
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'
    
    print("Environment variables set:")
    print(f"  DB_HOST: {os.environ['DB_HOST']}")
    print(f"  DB_PORT: {os.environ['DB_PORT']}")
    
    # Step 3: Test database connection
    print("\n🔗 Testing database connection...")
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
        print(f"✅ Database connection SUCCESSFUL! Products: {count}")
        cursor.close()
        conn.close()
        
        print("\n🎉 FIX COMPLETED!")
        print("💡 Now go to PythonAnywhere Web tab and click 'Reload'")
        print("💡 Wait 60 seconds, then test your web app")
        return True
        
    except Exception as e:
        print(f"❌ Database connection FAILED: {e}")
        print("\n💡 Possible issues:")
        print("   1. PostgreSQL server is down")
        print("   2. Wrong credentials")
        print("   3. Network issues")
        return False

if __name__ == "__main__":
    urgent_fix()
