#!/usr/bin/env python3
"""
Upload large database to PythonAnywhere
This script prepares the database for upload and provides instructions
"""

import os
import sqlite3
import gzip
import shutil
from datetime import datetime

def prepare_database_for_upload():
    """Prepare the database for PythonAnywhere upload"""
    
    print("🔍 Preparing database for PythonAnywhere upload...")
    
    # Source database
    source_db = 'uploads/product_database.db'
    target_db = 'uploads/product_database_pythonanywhere.db'
    
    if not os.path.exists(source_db):
        print(f"❌ Source database not found: {source_db}")
        return False
    
    # Get original size
    original_size = os.path.getsize(source_db)
    original_size_mb = original_size / (1024 * 1024)
    print(f"📊 Original database size: {original_size_mb:.1f} MB")
    
    # Copy database
    shutil.copy2(source_db, target_db)
    print(f"✅ Database copied to: {target_db}")
    
    # Test the copied database
    try:
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        
        # Get table counts
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables: {len(tables)}")
        
        # Get product count
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0]
        print(f"📦 Products: {product_count:,}")
        
        # Get strain count
        cursor.execute('SELECT COUNT(*) FROM strains')
        strain_count = cursor.fetchone()[0]
        print(f"🌿 Strains: {strain_count:,}")
        
        conn.close()
        print("✅ Database test successful")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Create compressed version for easier upload
    compressed_db = f"{target_db}.gz"
    print(f"🗜️  Creating compressed version...")
    
    with open(target_db, 'rb') as f_in:
        with gzip.open(compressed_db, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    compressed_size = os.path.getsize(compressed_db)
    compressed_size_mb = compressed_size / (1024 * 1024)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"📊 Compressed size: {compressed_size_mb:.1f} MB")
    print(f"📊 Compression ratio: {compression_ratio:.1f}%")
    
    return True

def print_upload_instructions():
    """Print instructions for uploading to PythonAnywhere"""
    
    print("\n" + "="*60)
    print("📋 PYTHONANYWHERE DATABASE UPLOAD INSTRUCTIONS")
    print("="*60)
    print()
    print("🔧 Method 1: Direct Upload (Recommended)")
    print("   1. Go to PythonAnywhere Files tab")
    print("   2. Navigate to /home/adamcordova/AGTDesigner/uploads/")
    print("   3. Upload: product_database_pythonanywhere.db.gz")
    print("   4. Extract: gunzip product_database_pythonanywhere.db.gz")
    print("   5. Rename: mv product_database_pythonanywhere.db product_database.db")
    print()
    print("🔧 Method 2: Using PythonAnywhere Console")
    print("   1. Open PythonAnywhere Console")
    print("   2. Run: cd ~/AGTDesigner/uploads")
    print("   3. Upload the .gz file via Files tab")
    print("   4. Run: gunzip product_database_pythonanywhere.db.gz")
    print("   5. Run: mv product_database_pythonanywhere.db product_database.db")
    print()
    print("⚠️  Important Notes:")
    print("   - Database size: ~500MB (requires Hacker plan)")
    print("   - Upload may take 10-15 minutes")
    print("   - Ensure you have sufficient disk space")
    print("   - Test database after upload")
    print()
    print("🧪 Test Database After Upload:")
    print("   python3.11 -c \"")
    print("   import sqlite3")
    print("   conn = sqlite3.connect('uploads/product_database.db')")
    print("   cursor = conn.cursor()")
    print("   cursor.execute('SELECT COUNT(*) FROM products')")
    print("   print(f'Products: {cursor.fetchone()[0]:,}')")
    print("   conn.close()")
    print("   \"")
    print()

if __name__ == "__main__":
    print("🚀 PythonAnywhere Database Upload Preparation")
    print("=" * 50)
    
    if prepare_database_for_upload():
        print_upload_instructions()
        print("✅ Database preparation complete!")
    else:
        print("❌ Database preparation failed!")
