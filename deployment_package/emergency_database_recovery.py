#!/usr/bin/env python3
"""
Emergency database recovery for PythonAnywhere deployment
Handles corruption and creates clean web-ready database
"""

import os
import shutil
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def recover_corrupted_database(corrupted_db, recovered_db):
    """Recover corrupted database using SQLite recovery mode"""
    logger.info(f"🔧 Recovering corrupted database: {corrupted_db}")
    
    try:
        # Use SQLite recovery mode to extract data
        recovery_cmd = f'sqlite3 "{corrupted_db}" ".recover"'
        import subprocess
        
        # Run recovery and pipe to new database
        with open(recovered_db + '.sql', 'w') as recovery_file:
            result = subprocess.run(
                ['sqlite3', corrupted_db, '.recover'],
                stdout=recovery_file,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Create new database from recovery SQL
        conn = sqlite3.connect(recovered_db)
        with open(recovered_db + '.sql', 'r') as sql_file:
            conn.executescript(sql_file.read())
        conn.close()
        
        # Clean up SQL file
        os.remove(recovered_db + '.sql')
        
        logger.info(f"✅ Database recovery completed: {recovered_db}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database recovery failed: {e}")
        return False

def verify_database_integrity(db_path):
    """Verify database integrity"""
    logger.info(f"🔍 Verifying database integrity: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        
        if result == "ok":
            logger.info("✅ Database integrity check passed")
            
            # Get product count
            cursor.execute("SELECT COUNT(*) FROM products;")
            count = cursor.fetchone()[0]
            logger.info(f"✅ Products in database: {count:,}")
            
            conn.close()
            return True, count
        else:
            logger.error(f"❌ Database integrity check failed: {result}")
            conn.close()
            return False, 0
            
    except Exception as e:
        logger.error(f"❌ Database integrity check error: {e}")
        return False, 0

def optimize_database(db_path):
    """Optimize database for web deployment"""
    logger.info(f"⚡ Optimizing database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # Set performance settings
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA cache_size=10000;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        
        # Optimize database
        cursor.execute("PRAGMA optimize;")
        cursor.execute("VACUUM;")
        cursor.execute("ANALYZE;")
        
        conn.close()
        logger.info("✅ Database optimization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        return False

def emergency_web_deployment_recovery():
    """Emergency recovery for PythonAnywhere deployment"""
    
    # Database paths
    corrupted_db = "uploads/product_database_AGT_Bothell.db"
    recovered_db = "uploads/product_database_AGT_Bothell_recovered.db"
    web_db = "uploads/product_database_AGT_Bothell_web.db"
    
    logger.info("🚨 Starting emergency database recovery for web deployment...")
    
    # Step 1: Check if source database exists
    if not os.path.exists(corrupted_db):
        logger.error(f"❌ Source database not found: {corrupted_db}")
        return False
    
    # Step 2: Backup corrupted database
    backup_db = corrupted_db + ".corrupted_backup"
    shutil.copy2(corrupted_db, backup_db)
    logger.info(f"✅ Corrupted database backed up: {backup_db}")
    
    # Step 3: Attempt recovery
    if not recover_corrupted_database(corrupted_db, recovered_db):
        logger.error("❌ Database recovery failed")
        return False
    
    # Step 4: Verify recovered database
    is_valid, product_count = verify_database_integrity(recovered_db)
    if not is_valid:
        logger.error("❌ Recovered database is still corrupted")
        return False
    
    # Step 5: Optimize for web deployment
    if not optimize_database(recovered_db):
        logger.error("❌ Database optimization failed")
        return False
    
    # Step 6: Create web deployment copy
    shutil.copy2(recovered_db, web_db)
    logger.info(f"✅ Web deployment database created: {web_db}")
    
    # Step 7: Replace original with recovered version
    shutil.move(recovered_db, corrupted_db)
    logger.info(f"✅ Original database replaced with recovered version")
    
    # Get final file size
    file_size = os.path.getsize(web_db) / (1024 * 1024)  # MB
    
    # Final verification
    is_valid_final, final_count = verify_database_integrity(web_db)
    
    if is_valid_final:
        logger.info("🎉 Emergency recovery completed successfully!")
        logger.info(f"   📊 Products recovered: {final_count:,}")
        logger.info(f"   💾 File size: {file_size:.1f} MB")
        logger.info(f"   📁 Web deployment file: {web_db}")
        
        # PythonAnywhere instructions
        print("\n" + "="*70)
        print("🚀 PYTHONANYWHERE EMERGENCY DEPLOYMENT INSTRUCTIONS")
        print("="*70)
        print("1. Upload this RECOVERED database to PythonAnywhere:")
        print(f"   Local:  {os.path.abspath(web_db)}")
        print(f"   Remote: /home/adamcordova/AGTDesigner/uploads/product_database_AGT_Bothell.db")
        print()
        print("2. In PythonAnywhere console, verify integrity:")
        print("   sqlite3 uploads/product_database_AGT_Bothell.db 'PRAGMA integrity_check;'")
        print()
        print("3. Reload your web app")
        print(f"4. Database now has {final_count:,} products and is corruption-free!")
        print("="*70)
        
        return True
    else:
        logger.error("❌ Final verification failed")
        return False

if __name__ == "__main__":
    success = emergency_web_deployment_recovery()
    if success:
        print("\n✅ Emergency recovery successful! Ready for deployment!")
    else:
        print("\n❌ Emergency recovery failed!")
        exit(1)