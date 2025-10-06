#!/usr/bin/env python3
"""
PythonAnywhere Performance Optimization Script
Optimizes database queries and reduces loading time
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import time

def optimize_database_performance():
    """Optimize database performance for faster loading"""
    
    print("⚡ Optimizing PythonAnywhere Performance...")
    print("=" * 50)
    
    # Database connection parameters
    db_config = {
        'host': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'database': 'postgres',
        'user': 'super',
        'password': '193154life',
        'port': '14822'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Create indexes for faster queries
        print("🔧 Creating database indexes for faster queries...")
        
        indexes_to_create = [
            # Products table indexes
            ('products', 'product_name', 'idx_products_name'),
            ('products', 'brand', 'idx_products_brand'),
            ('products', '"Vendor/Supplier*"', 'idx_products_vendor'),
            ('products', '"Product Type*"', 'idx_products_type'),
            
            # Strains table indexes
            ('strains', 'strain_name', 'idx_strains_name'),
            ('strains', 'strain_type', 'idx_strains_type'),
        ]
        
        for table, column, index_name in indexes_to_create:
            try:
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table} ({column});
                """)
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️ Could not create index {index_name}: {e}")
        
        # Analyze tables for better query planning
        print("📊 Analyzing tables for better query performance...")
        
        tables_to_analyze = ['products', 'strains']
        for table in tables_to_analyze:
            try:
                cur.execute(f"ANALYZE {table};")
                print(f"✅ Analyzed table: {table}")
            except Exception as e:
                print(f"⚠️ Could not analyze table {table}: {e}")
        
        # Test query performance
        print("🚀 Testing query performance...")
        
        test_queries = [
            "SELECT COUNT(*) FROM products;",
            "SELECT COUNT(DISTINCT brand) FROM products;",
            "SELECT COUNT(DISTINCT \"Vendor/Supplier*\") FROM products;",
            "SELECT COUNT(*) FROM strains;"
        ]
        
        for query in test_queries:
            start_time = time.time()
            cur.execute(query)
            result = cur.fetchone()[0]
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print(f"⚡ Query completed in {query_time:.2f}ms: {result} results")
        
        # Check database statistics
        print("\n📈 Database Statistics:")
        cur.execute("SELECT COUNT(*) FROM products;")
        product_count = cur.fetchone()[0]
        print(f"📊 Total products: {product_count}")
        
        cur.execute("SELECT COUNT(*) FROM strains;")
        strain_count = cur.fetchone()[0]
        print(f"🌿 Total strains: {strain_count}")
        
        cur.execute("SELECT COUNT(DISTINCT brand) FROM products WHERE brand IS NOT NULL;")
        brand_count = cur.fetchone()[0]
        print(f"🏷️ Unique brands: {brand_count}")
        
        cur.execute("SELECT COUNT(DISTINCT \"Vendor/Supplier*\") FROM products WHERE \"Vendor/Supplier*\" IS NOT NULL;")
        vendor_count = cur.fetchone()[0]
        print(f"🏢 Unique vendors: {vendor_count}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Performance optimization completed!")
        print("💡 Your web app should now load much faster!")
        return True
        
    except Exception as e:
        print(f"❌ Performance optimization failed: {e}")
        return False

def create_loading_optimization_config():
    """Create configuration to optimize app loading"""
    
    print("\n🔧 Creating loading optimization configuration...")
    
    config_content = '''# PythonAnywhere Loading Optimization Configuration
# This file optimizes the app loading performance

import os
import logging

# Disable verbose logging during startup
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('pandas').setLevel(logging.ERROR)
logging.getLogger('openpyxl').setLevel(logging.ERROR)
logging.getLogger('psycopg2').setLevel(logging.ERROR)

# Set environment variables for faster loading
os.environ['PYTHONANYWHERE_OPTIMIZED'] = 'True'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Disable Flask auto-reload for production
os.environ['FLASK_RUN_RELOAD'] = 'False'

print("⚡ Loading optimization configuration applied")
'''
    
    try:
        with open('loading_optimization.py', 'w') as f:
            f.write(config_content)
        print("✅ Created loading_optimization.py")
        return True
    except Exception as e:
        print(f"❌ Could not create optimization config: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PythonAnywhere Performance Optimization")
    print("=" * 50)
    
    # Optimize database
    db_success = optimize_database_performance()
    
    # Create loading optimization config
    config_success = create_loading_optimization_config()
    
    if db_success and config_success:
        print("\n🎉 All optimizations completed successfully!")
        print("💡 Your web app should now load much faster!")
        print("\n📋 Next steps:")
        print("1. Reload your PythonAnywhere web app")
        print("2. Test the loading speed")
        print("3. Check that all features work correctly")
    else:
        print("\n⚠️ Some optimizations failed, but the app should still work")
