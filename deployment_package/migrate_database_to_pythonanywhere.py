#!/usr/bin/env python3
"""
Database Migration Script for PythonAnywhere
Handles large database migration with optimization
"""

import os
import sqlite3
import shutil
import gzip
import json
from pathlib import Path

def get_database_info(db_path):
    """Get information about the database"""
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table information
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get product count
    product_count = 0
    if 'products' in tables:
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
    
    # Get database size
    db_size = os.path.getsize(db_path)
    
    conn.close()
    
    return {
        'tables': tables,
        'product_count': product_count,
        'size_bytes': db_size,
        'size_mb': round(db_size / (1024 * 1024), 2)
    }

def optimize_database(db_path):
    """Optimize database for PythonAnywhere deployment"""
    print(f"🔧 Optimizing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Run VACUUM to optimize database
    print("  Running VACUUM to optimize database...")
    cursor.execute("VACUUM")
    
    # Analyze tables for better query performance
    print("  Analyzing tables for better performance...")
    cursor.execute("ANALYZE")
    
    conn.close()
    print("  ✅ Database optimization complete")

def create_sql_dump(db_path, output_path):
    """Create SQL dump of the database"""
    print(f"📄 Creating SQL dump: {output_path}")
    
    conn = sqlite3.connect(db_path)
    
    with open(output_path, 'w') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    
    conn.close()
    
    # Get dump size
    dump_size = os.path.getsize(output_path)
    print(f"  ✅ SQL dump created: {round(dump_size / (1024 * 1024), 2)} MB")

def compress_file(file_path):
    """Compress file for easier upload"""
    compressed_path = f"{file_path}.gz"
    print(f"🗜️  Compressing file: {file_path}")
    
    with open(file_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = round((1 - compressed_size / original_size) * 100, 1)
    
    print(f"  ✅ Compressed: {round(original_size / (1024 * 1024), 2)} MB → {round(compressed_size / (1024 * 1024), 2)} MB ({compression_ratio}% reduction)")
    
    return compressed_path

def create_database_summary(db_path):
    """Create a summary of the database for deployment"""
    info = get_database_info(db_path)
    if not info:
        return None
    
    summary = {
        'database_info': info,
        'deployment_notes': {
            'recommended_plan': 'Hacker ($5/month)' if info['size_mb'] > 10 else 'Free',
            'upload_method': 'Files tab' if info['size_mb'] < 50 else 'Console upload',
            'optimization_needed': info['size_mb'] > 20
        },
        'tables': info['tables'],
        'product_count': info['product_count']
    }
    
    summary_path = 'database_deployment_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📋 Database summary created: {summary_path}")
    return summary

def main():
    """Main migration function"""
    print("🚀 PythonAnywhere Database Migration")
    print("=====================================")
    
    # Check for database files
    db_files = ['product_database.db', 'products_dump.sql']
    found_files = [f for f in db_files if os.path.exists(f)]
    
    if not found_files:
        print("❌ No database files found!")
        print("Expected files: product_database.db or products_dump.sql")
        return
    
    print(f"📁 Found database files: {', '.join(found_files)}")
    
    # Process each database file
    for db_file in found_files:
        print(f"\n📊 Processing: {db_file}")
        
        if db_file.endswith('.db'):
            # SQLite database
            info = get_database_info(db_file)
            if info:
                print(f"  Tables: {', '.join(info['tables'])}")
                print(f"  Products: {info['product_count']}")
                print(f"  Size: {info['size_mb']} MB")
                
                # Optimize if large
                if info['size_mb'] > 5:
                    optimize_database(db_file)
                
                # Create SQL dump
                dump_path = f"{db_file.replace('.db', '')}_dump.sql"
                create_sql_dump(db_file, dump_path)
                
                # Compress if large
                if info['size_mb'] > 10:
                    compress_file(db_file)
                    compress_file(dump_path)
                
                # Create summary
                create_database_summary(db_file)
        
        elif db_file.endswith('.sql'):
            # SQL dump
            dump_size = os.path.getsize(db_file)
            dump_size_mb = round(dump_size / (1024 * 1024), 2)
            print(f"  Size: {dump_size_mb} MB")
            
            # Compress if large
            if dump_size_mb > 10:
                compress_file(db_file)
    
    print("\n🎉 Database Migration Complete!")
    print("===============================")
    print("\n📋 Deployment Instructions:")
    print("1. Upload database files to PythonAnywhere:")
    print("   - Go to Files tab")
    print("   - Navigate to /home/yourusername/AGTDesigner/")
    print("   - Upload product_database.db (or .db.gz if compressed)")
    print("   - Upload products_dump.sql (or .sql.gz if compressed)")
    print("\n2. On PythonAnywhere console:")
    print("   cd ~/AGTDesigner")
    print("   python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); print('Database OK')\"")
    print("\n3. If database is missing, restore from SQL dump:")
    print("   python3 -c \"")
    print("   import sqlite3")
    print("   conn = sqlite3.connect('product_database.db')")
    print("   with open('products_dump.sql', 'r') as f:")
    print("       conn.executescript(f.read())")
    print("   conn.close()")
    print("   print('Database restored')")
    print("   \"")
    
    # Show file sizes for upload planning
    print("\n📊 File Sizes for Upload:")
    for file in os.listdir('.'):
        if any(ext in file for ext in ['.db', '.sql']) and not file.endswith('.gz'):
            size = os.path.getsize(file)
            size_mb = round(size / (1024 * 1024), 2)
            compressed_file = f"{file}.gz"
            if os.path.exists(compressed_file):
                comp_size = os.path.getsize(compressed_file)
                comp_size_mb = round(comp_size / (1024 * 1024), 2)
                print(f"  {file}: {size_mb} MB (compressed: {comp_size_mb} MB)")
            else:
                print(f"  {file}: {size_mb} MB")

if __name__ == "__main__":
    main()
