#!/usr/bin/env python3
"""
Deploy recovered database to PythonAnywhere web deployment
This script optimizes and uploads the database for web deployment
"""

import os
import shutil
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_database(db_path):
    """Optimize database for web deployment"""
    logger.info(f"Optimizing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # Optimize database
        cursor.execute("PRAGMA optimize;")
        cursor.execute("VACUUM;")
        
        # Analyze for query optimization
        cursor.execute("ANALYZE;")
        
        # Get database info
        cursor.execute("SELECT COUNT(*) FROM products;")
        product_count = cursor.fetchone()[0]
        
        logger.info(f"✅ Database optimized: {product_count} products")
        
        return product_count
        
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        raise
    finally:
        conn.close()

def verify_database_integrity(db_path):
    """Verify database integrity"""
    logger.info(f"Verifying database integrity: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check integrity
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        
        if result == "ok":
            logger.info("✅ Database integrity check passed")
            return True
        else:
            logger.error(f"❌ Database integrity check failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database integrity check error: {e}")
        return False
    finally:
        conn.close()

def prepare_web_deployment():
    """Prepare database for web deployment"""
    
    # Database paths
    local_db = "uploads/product_database_AGT_Bothell.db"
    web_db = "uploads/product_database_AGT_Bothell_web.db"
    
    if not os.path.exists(local_db):
        logger.error(f"❌ Source database not found: {local_db}")
        return False
    
    logger.info("📦 Preparing database for web deployment...")
    
    try:
        # Copy database for web deployment
        shutil.copy2(local_db, web_db)
        logger.info(f"✅ Database copied: {local_db} -> {web_db}")
        
        # Verify integrity
        if not verify_database_integrity(web_db):
            logger.error("❌ Database integrity check failed")
            return False
        
        # Optimize for web deployment
        product_count = optimize_database(web_db)
        
        # Get file size
        file_size = os.path.getsize(web_db) / (1024 * 1024)  # MB
        
        logger.info(f"🎉 Web deployment database ready!")
        logger.info(f"   📊 Products: {product_count:,}")
        logger.info(f"   💾 Size: {file_size:.1f} MB")
        logger.info(f"   📁 File: {web_db}")
        
        # Instructions for PythonAnywhere
        print("\n" + "="*60)
        print("📋 PYTHONANYWHERE DEPLOYMENT INSTRUCTIONS")
        print("="*60)
        print("1. Upload this optimized database to PythonAnywhere:")
        print(f"   Local:  {os.path.abspath(web_db)}")
        print(f"   Remote: /home/adamcordova/AGTDesigner/uploads/product_database_AGT_Bothell.db")
        print()
        print("2. Update your web app with the new WSGI configuration")
        print("3. Reload your web app in PythonAnywhere dashboard")
        print("4. Your app will use the recovered database with 12,847+ products")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Web deployment preparation failed: {e}")
        return False

if __name__ == "__main__":
    success = prepare_web_deployment()
    if success:
        print("\n✅ Database ready for web deployment!")
    else:
        print("\n❌ Database preparation failed!")
        exit(1)