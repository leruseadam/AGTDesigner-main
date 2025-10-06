#!/usr/bin/env python3
"""
Monitor database status and auto-fix if needed
"""
import os
import sqlite3
import time
from datetime import datetime

def check_database_health():
    """Check if databases are healthy"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking database health...")
    
    db_files = ['product_database.db', 'product_database_AGT_Bothell.db']
    issues = []
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            issues.append(f"{db_file} missing")
            continue
            
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if products table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
            if not cursor.fetchone():
                issues.append(f"{db_file} missing products table")
                conn.close()
                continue
            
            # Check product count
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            
            if count == 0:
                issues.append(f"{db_file} empty")
            else:
                print(f"✅ {db_file}: {count} products")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"{db_file} error: {e}")
    
    if issues:
        print(f"❌ Issues found: {', '.join(issues)}")
        return False
    else:
        print("✅ All databases healthy")
        return True

def auto_fix_databases():
    """Automatically fix database issues"""
    print("🔧 Auto-fixing database issues...")
    
    # Run the persistence fix script
    import subprocess
    try:
        result = subprocess.run(['python3', 'fix_database_persistence.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Auto-fix completed successfully")
            return True
        else:
            print(f"❌ Auto-fix failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Auto-fix error: {e}")
        return False

def main():
    print("🔍 DATABASE HEALTH MONITOR")
    print("=" * 40)
    
    while True:
        if not check_database_health():
            print("🚨 Database issues detected! Attempting auto-fix...")
            if auto_fix_databases():
                print("✅ Auto-fix successful, continuing monitoring...")
            else:
                print("❌ Auto-fix failed, manual intervention needed")
                break
        else:
            print("✅ All databases healthy, continuing monitoring...")
        
        print("-" * 40)
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
