#!/usr/bin/env python3
"""
Large Database Migration Script for PythonAnywhere
Handles 500MB+ database with 17,841 products
"""

import os
import sqlite3
import shutil
import gzip
import json
from pathlib import Path
import time

def get_database_info(db_path):
    """Get comprehensive information about the database"""
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table information
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get counts for each table
    table_counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
        except:
            table_counts[table] = "Error"
    
    # Get database size
    db_size = os.path.getsize(db_path)
    
    # Get database page count and page size
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'tables': tables,
        'table_counts': table_counts,
        'size_bytes': db_size,
        'size_mb': round(db_size / (1024 * 1024), 2),
        'page_count': page_count,
        'page_size': page_size,
        'total_pages_mb': round((page_count * page_size) / (1024 * 1024), 2)
    }

def optimize_database(db_path, output_path=None):
    """Optimize database for PythonAnywhere deployment"""
    if output_path is None:
        output_path = db_path.replace('.db', '_optimized.db')
    
    print(f"🔧 Optimizing database: {db_path}")
    print(f"   Output: {output_path}")
    
    start_time = time.time()
    
    conn = sqlite3.connect(db_path)
    
    # Create optimized database
    print("  Creating optimized database...")
    conn.execute(f"VACUUM INTO '{output_path}'")
    
    # Close original connection
    conn.close()
    
    # Open new database for analysis
    new_conn = sqlite3.connect(output_path)
    cursor = new_conn.cursor()
    
    # Analyze tables for better query performance
    print("  Analyzing tables for better performance...")
    cursor.execute("ANALYZE")
    
    # Get optimization results
    original_size = os.path.getsize(db_path)
    optimized_size = os.path.getsize(output_path)
    reduction = round((1 - optimized_size / original_size) * 100, 1)
    
    new_conn.close()
    
    elapsed_time = round(time.time() - start_time, 2)
    print(f"  ✅ Database optimization complete")
    print(f"     Original: {round(original_size / (1024 * 1024), 2)} MB")
    print(f"     Optimized: {round(optimized_size / (1024 * 1024), 2)} MB")
    print(f"     Reduction: {reduction}%")
    print(f"     Time: {elapsed_time} seconds")
    
    return output_path

def create_production_database(db_path, output_path=None):
    """Create production-ready database by removing unnecessary data"""
    if output_path is None:
        output_path = db_path.replace('.db', '_production.db')
    
    print(f"🏭 Creating production database: {output_path}")
    
    conn = sqlite3.connect(db_path)
    new_conn = sqlite3.connect(output_path)
    
    # Get all tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Tables to exclude from production
    exclude_tables = ['products_backup', '_migration_log', 'lost_and_found', 'sqlite_stat1']
    production_tables = [t for t in tables if t not in exclude_tables]
    
    print(f"  Production tables: {production_tables}")
    print(f"  Excluded tables: {exclude_tables}")
    
    # Copy essential tables
    for table in production_tables:
        print(f"  Copying table: {table}")
        
        # Get table schema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        schema = cursor.fetchone()[0]
        
        # Create table in new database
        new_cursor = new_conn.cursor()
        new_cursor.execute(schema)
        
        # Copy data
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            placeholders = ','.join(['?' for _ in columns])
            
            # Insert data
            insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            new_cursor.executemany(insert_sql, rows)
    
    # Copy indexes
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    indexes = cursor.fetchall()
    
    for index_sql in indexes:
        try:
            new_cursor.execute(index_sql[0])
        except:
            pass  # Skip if index already exists
    
    # Optimize production database
    print("  Optimizing production database...")
    new_cursor.execute("VACUUM")
    new_cursor.execute("ANALYZE")
    
    new_conn.commit()
    new_conn.close()
    conn.close()
    
    # Get size comparison
    original_size = os.path.getsize(db_path)
    production_size = os.path.getsize(output_path)
    reduction = round((1 - production_size / original_size) * 100, 1)
    
    print(f"  ✅ Production database created")
    print(f"     Original: {round(original_size / (1024 * 1024), 2)} MB")
    print(f"     Production: {round(production_size / (1024 * 1024), 2)} MB")
    print(f"     Reduction: {reduction}%")
    
    return output_path

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
            shutil.copyfileobj(f_in, f_out)
    
    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = round((1 - compressed_size / original_size) * 100, 1)
    elapsed_time = round(time.time() - start_time, 2)
    
    print(f"  ✅ Compressed: {round(original_size / (1024 * 1024), 2)} MB → {round(compressed_size / (1024 * 1024), 2)} MB")
    print(f"     Compression: {compression_ratio}%")
    print(f"     Time: {elapsed_time} seconds")
    
    return compressed_path

def create_deployment_summary(db_paths):
    """Create comprehensive deployment summary"""
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'databases': {},
        'deployment_recommendations': {
            'pythonanywhere_plan': 'Hacker ($5/month) - Minimum required',
            'recommended_plan': 'Web Developer ($20/month) - Better performance',
            'upload_method': 'Console upload (files too large for Files tab)',
            'compression_required': True,
            'optimization_required': True
        },
        'file_sizes': {},
        'upload_instructions': []
    }
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            info = get_database_info(db_path)
            if info:
                summary['databases'][db_path] = info
                
                # Add file sizes
                summary['file_sizes'][db_path] = {
                    'size_mb': info['size_mb'],
                    'compressed_size_mb': 0
                }
                
                # Check for compressed version
                compressed_path = f"{db_path}.gz"
                if os.path.exists(compressed_path):
                    compressed_size = os.path.getsize(compressed_path)
                    summary['file_sizes'][db_path]['compressed_size_mb'] = round(compressed_size / (1024 * 1024), 2)
    
    # Generate upload instructions
    summary['upload_instructions'] = [
        "1. Upgrade PythonAnywhere to Hacker plan ($5/month) - REQUIRED",
        "2. Use console upload for large files:",
        "   - wget or curl for remote files",
        "   - scp for local files",
        "3. Restore database on PythonAnywhere:",
        "   - gunzip product_database_dump.sql.gz",
        "   - python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); conn.executescript(open('product_database_dump.sql').read()); conn.close()\"",
        "4. Test database:",
        "   - python3 -c \"import sqlite3; conn = sqlite3.connect('product_database.db'); print('OK')\""
    ]
    
    summary_path = 'large_database_deployment_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📋 Deployment summary created: {summary_path}")
    return summary

def main():
    """Main migration function for large database"""
    print("🚀 Large Database Migration for PythonAnywhere")
    print("==============================================")
    
    # Check for database files
    db_candidates = [
        'uploads/product_database_AGT_Bothell_clean.db',
        'uploads/product_database_AGT_Bothell_web.db',
        'uploads/product_database.db'
    ]
    
    working_dbs = []
    for db_path in db_candidates:
        if os.path.exists(db_path):
            try:
                info = get_database_info(db_path)
                if info:
                    working_dbs.append(db_path)
                    print(f"✅ Found working database: {db_path}")
                    print(f"   Size: {info['size_mb']} MB")
                    print(f"   Products: {info['table_counts'].get('products', 'N/A')}")
                    print(f"   Tables: {len(info['tables'])}")
                else:
                    print(f"❌ Database corrupted: {db_path}")
            except Exception as e:
                print(f"❌ Database error: {db_path} - {e}")
    
    if not working_dbs:
        print("❌ No working databases found!")
        return
    
    # Use the first working database
    source_db = working_dbs[0]
    print(f"\n📊 Using source database: {source_db}")
    
    # Get source database info
    source_info = get_database_info(source_db)
    print(f"   Size: {source_info['size_mb']} MB")
    print(f"   Products: {source_info['table_counts'].get('products', 'N/A')}")
    print(f"   Tables: {source_info['tables']}")
    
    # Create optimized database
    print(f"\n🔧 Step 1: Creating optimized database...")
    optimized_db = optimize_database(source_db)
    
    # Create production database
    print(f"\n🏭 Step 2: Creating production database...")
    production_db = create_production_database(source_db)
    
    # Create SQL dumps
    print(f"\n📄 Step 3: Creating SQL dumps...")
    optimized_dump = create_sql_dump(optimized_db, 'product_database_optimized_dump.sql')
    production_dump = create_sql_dump(production_db, 'product_database_production_dump.sql')
    
    # Compress files
    print(f"\n🗜️  Step 4: Compressing files...")
    compressed_files = []
    for file_path in [optimized_db, production_db, optimized_dump, production_dump]:
        if os.path.exists(file_path):
            compressed_path = compress_file(file_path)
            compressed_files.append(compressed_path)
    
    # Create deployment summary
    print(f"\n📋 Step 5: Creating deployment summary...")
    all_files = [source_db, optimized_db, production_db, optimized_dump, production_dump] + compressed_files
    summary = create_deployment_summary(all_files)
    
    # Show final results
    print(f"\n🎉 Large Database Migration Complete!")
    print("=====================================")
    print(f"\n📊 Database Analysis:")
    print(f"   Source: {source_info['size_mb']} MB, {source_info['table_counts'].get('products', 'N/A')} products")
    print(f"   Optimized: {round(os.path.getsize(optimized_db) / (1024 * 1024), 2)} MB")
    print(f"   Production: {round(os.path.getsize(production_db) / (1024 * 1024), 2)} MB")
    
    print(f"\n📁 Files Created:")
    for file_path in all_files:
        if os.path.exists(file_path):
            size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            print(f"   {file_path}: {size_mb} MB")
    
    print(f"\n⚠️  IMPORTANT: PythonAnywhere Requirements:")
    print(f"   - Upgrade to Hacker plan ($5/month) - REQUIRED")
    print(f"   - Recommended: Web Developer plan ($20/month)")
    print(f"   - Free tier insufficient (512MB limit, database is 500MB+)")
    
    print(f"\n📋 Deployment Instructions:")
    print(f"1. Upgrade PythonAnywhere account to Hacker plan")
    print(f"2. Upload compressed files via console:")
    for compressed_file in compressed_files:
        print(f"   - {compressed_file}")
    print(f"3. Restore database on PythonAnywhere")
    print(f"4. Test deployment")
    
    print(f"\n✅ Ready for PythonAnywhere deployment!")

if __name__ == "__main__":
    main()
