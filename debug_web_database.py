#!/usr/bin/env python3
"""
Debug script to check web database status
"""
import os
import sqlite3
import sys

def check_database_files():
    """Check if database files exist"""
    print("=== DATABASE FILE CHECK ===")
    
    db_files = [
        'product_database.db',
        'product_database_AGT_Bothell.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print(f"✅ {db_file}: EXISTS ({size:,} bytes)")
        else:
            print(f"❌ {db_file}: MISSING")

def check_database_content():
    """Check database content"""
    print("\n=== DATABASE CONTENT CHECK ===")
    
    db_files = [
        'product_database.db',
        'product_database_AGT_Bothell.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"\n📊 {db_file} Tables:")
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count:,} rows")
                
                conn.close()
                print(f"✅ {db_file}: Database accessible")
                
            except Exception as e:
                print(f"❌ {db_file}: Error - {e}")
        else:
            print(f"❌ {db_file}: File missing")

def check_app_database_config():
    """Check app.py database configuration"""
    print("\n=== APP DATABASE CONFIG CHECK ===")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Check for database initialization
        if 'init_database()' in content:
            print("✅ Database initialization function found")
        else:
            print("❌ Database initialization function not found")
            
        # Check for database path
        if 'product_database.db' in content:
            print("✅ Database file reference found")
        else:
            print("❌ Database file reference not found")
            
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")

def main():
    print("🔍 WEB DATABASE DIAGNOSTIC")
    print("=" * 50)
    
    check_database_files()
    check_database_content()
    check_app_database_config()
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete")

if __name__ == "__main__":
    main()
