#!/usr/bin/env python3
"""
Simplified Large Database Preparation for PythonAnywhere
Handles 500MB database with 17,841 products
"""

import os
import sqlite3
import gzip
import json
import time

def get_database_info(db_path):
    """Get database information"""
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

def create_sql_dump(db_path, output_path):
    """Create SQL dump of the database"""
    print(f"📄 Creating SQL dump: {output_path}")
    
    start_time = time.time()
    
    conn = sqlite3.connect(db_path)
    
    with open(output_path, 'w') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    
    conn.close()
    
    # Get dump size
    dump_size = os.path.getsize(output_path)
    elapsed_time = round(time.time() - start_time, 2)
    
    print(f"  ✅ SQL dump created: {round(dump_size / (1024 * 1024), 2)} MB")
    print(f"     Time: {elapsed_time} seconds")
    
    return output_path

def compress_file(file_path):
    """Compress file for easier upload"""
    compressed_path = f"{file_path}.gz"
    print(f"🗜️  Compressing file: {file_path}")
    
    start_time = time.time()
    
    with open(file_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            f_in.seek(0)
            while True:
                chunk = f_in.read(1024 * 1024)  # Read 1MB chunks
                if not chunk:
                    break
                f_out.write(chunk)
    
    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = round((1 - compressed_size / original_size) * 100, 1)
    elapsed_time = round(time.time() - start_time, 2)
    
    print(f"  ✅ Compressed: {round(original_size / (1024 * 1024), 2)} MB → {round(compressed_size / (1024 * 1024), 2)} MB")
    print(f"     Compression: {compression_ratio}%")
    print(f"     Time: {elapsed_time} seconds")
    
    return compressed_path

def copy_working_database():
    """Copy the working database to the main location"""
    source_db = 'uploads/product_database_AGT_Bothell_clean.db'
    target_db = 'product_database.db'
    
    if os.path.exists(source_db):
        print(f"📋 Copying working database...")
        print(f"   Source: {source_db}")
        print(f"   Target: {target_db}")
        
        # Remove existing target if it exists
        if os.path.exists(target_db):
            os.remove(target_db)
        
        # Copy the file
        import shutil
        shutil.copy2(source_db, target_db)
        
        # Verify copy
        if os.path.exists(target_db):
            size_mb = round(os.path.getsize(target_db) / (1024 * 1024), 2)
            print(f"  ✅ Database copied successfully: {size_mb} MB")
            return target_db
        else:
            print(f"  ❌ Copy failed")
            return None
    else:
        print(f"❌ Source database not found: {source_db}")
        return None

def main():
    """Main function to prepare large database for PythonAnywhere"""
    print("🚀 Large Database Preparation for PythonAnywhere")
    print("================================================")
    
    # Step 1: Copy working database
    print(f"\n📋 Step 1: Setting up working database...")
    db_path = copy_working_database()
    
    if not db_path:
        print("❌ No working database found!")
        return
    
    # Step 2: Get database info
    print(f"\n📊 Step 2: Analyzing database...")
    info = get_database_info(db_path)
    if info:
        print(f"   Size: {info['size_mb']} MB")
        print(f"   Products: {info['product_count']}")
        print(f"   Tables: {info['tables']}")
    else:
        print("❌ Database analysis failed!")
        return
    
    # Step 3: Create SQL dump
    print(f"\n📄 Step 3: Creating SQL dump...")
    dump_path = create_sql_dump(db_path, 'product_database_dump.sql')
    
    # Step 4: Compress files
    print(f"\n🗜️  Step 4: Compressing files...")
    compressed_db = compress_file(db_path)
    compressed_dump = compress_file(dump_path)
    
    # Step 5: Create deployment instructions
    print(f"\n📋 Step 5: Creating deployment instructions...")
    
    instructions = {
        'database_info': info,
        'files_created': {
            'database': db_path,
            'sql_dump': dump_path,
            'compressed_database': compressed_db,
            'compressed_dump': compressed_dump
        },
        'file_sizes': {
            'database_mb': info['size_mb'],
            'sql_dump_mb': round(os.path.getsize(dump_path) / (1024 * 1024), 2),
            'compressed_database_mb': round(os.path.getsize(compressed_db) / (1024 * 1024), 2),
            'compressed_dump_mb': round(os.path.getsize(compressed_dump) / (1024 * 1024), 2)
        },
        'pythonanywhere_requirements': {
            'minimum_plan': 'Hacker ($5/month)',
            'recommended_plan': 'Web Developer ($20/month)',
            'reason': f'Database is {info["size_mb"]} MB, free tier only allows 512 MB total'
        },
        'upload_method': 'Console upload (files too large for Files tab)',
        'deployment_steps': [
            "1. Upgrade PythonAnywhere to Hacker plan ($5/month) - REQUIRED",
            "2. Clone repository: git clone https://github.com/leruseadam/AGTDesigner.git",
            "3. Upload compressed files via console:",
            f"   - {compressed_dump} ({round(os.path.getsize(compressed_dump) / (1024 * 1024), 2)} MB)",
            "4. Restore database:",
            "   gunzip product_database_dump.sql.gz",
            "   python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); conn.executescript(open('product_database_dump.sql').read()); conn.close()\"",
            "5. Test database:",
            "   python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); print('OK')\"",
            "6. Run deployment script: bash pythonanywhere_quick_setup.sh"
        ]
    }
    
    # Save instructions
    with open('large_database_deployment_instructions.json', 'w') as f:
        json.dump(instructions, f, indent=2)
    
    # Show final results
    print(f"\n🎉 Large Database Preparation Complete!")
    print("=====================================")
    print(f"\n📊 Database Summary:")
    print(f"   Size: {info['size_mb']} MB")
    print(f"   Products: {info['product_count']}")
    print(f"   Tables: {len(info['tables'])}")
    
    print(f"\n📁 Files Created:")
    print(f"   {db_path}: {info['size_mb']} MB")
    print(f"   {dump_path}: {round(os.path.getsize(dump_path) / (1024 * 1024), 2)} MB")
    print(f"   {compressed_db}: {round(os.path.getsize(compressed_db) / (1024 * 1024), 2)} MB")
    print(f"   {compressed_dump}: {round(os.path.getsize(compressed_dump) / (1024 * 1024), 2)} MB")
    
    print(f"\n⚠️  CRITICAL: PythonAnywhere Requirements:")
    print(f"   ❌ Free tier insufficient (512MB limit)")
    print(f"   ✅ Minimum: Hacker plan ($5/month)")
    print(f"   ✅ Recommended: Web Developer ($20/month)")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Upgrade PythonAnywhere account to Hacker plan")
    print(f"2. Upload {compressed_dump} to PythonAnywhere")
    print(f"3. Follow deployment instructions in large_database_deployment_instructions.json")
    
    print(f"\n✅ Ready for PythonAnywhere deployment!")

if __name__ == "__main__":
    main()
