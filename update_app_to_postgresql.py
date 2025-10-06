#!/usr/bin/env python3
"""
Update app to use PostgreSQL instead of SQLite
"""

import os
import shutil

def update_app_to_postgresql():
    """Update the app to use PostgreSQL"""
    
    print("🚀 Updating app to use PostgreSQL...")
    print("=" * 50)
    
    # 1. Backup original product_database.py
    original_file = "src/core/data/product_database.py"
    backup_file = "src/core/data/product_database_sqlite_backup.py"
    
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✅ Backed up original to: {backup_file}")
    
    # 2. Copy PostgreSQL version to replace SQLite version
    postgresql_file = "product_database_postgresql.py"
    if os.path.exists(postgresql_file):
        shutil.copy2(postgresql_file, original_file)
        print(f"✅ Updated {original_file} with PostgreSQL version")
    else:
        print(f"❌ PostgreSQL file not found: {postgresql_file}")
        return False
    
    # 3. Update app.py to use PostgreSQL
    update_app_py()
    
    # 4. Create PostgreSQL test script
    create_test_script()
    
    print("\n🎉 App updated to use PostgreSQL!")
    print("\n📋 Next steps:")
    print("1. Upload the updated files to PythonAnywhere")
    print("2. Test the PostgreSQL connection")
    print("3. Restart your app")
    print("4. Enjoy faster performance!")
    
    return True

def update_app_py():
    """Update app.py to use PostgreSQL"""
    
    app_py_path = "app.py"
    if not os.path.exists(app_py_path):
        print(f"❌ {app_py_path} not found")
        return
    
    # Read current app.py
    with open(app_py_path, 'r') as f:
        content = f.read()
    
    # Add PostgreSQL import at the top
    if "from product_database_postgresql import get_postgresql_database" not in content:
        # Find the imports section
        import_section = content.find("import os")
        if import_section != -1:
            # Add PostgreSQL import after other imports
            content = content[:import_section] + "from product_database_postgresql import get_postgresql_database\n" + content[import_section:]
    
    # Update get_product_database function to use PostgreSQL
    old_function = """def get_product_database(store_name=None):
    \"\"\"Lazy load ProductDatabase to avoid startup delay.\"\"\"
    global _product_database
    if _product_database is None or (store_name and getattr(_product_database, '_store_name', None) != store_name):
        from src.core.data.product_database import ProductDatabase
        # Use store-specific database path
        if store_name:
            db_filename = f'product_database_{store_name}.db'
            db_path = os.path.join(current_dir, 'uploads', db_filename)
            _product_database = ProductDatabase(db_path)
            _product_database._store_name = store_name
            logging.info(f"ProductDatabase created for store '{store_name}' at: {db_path}")
        else:
            # Default to Bothell database for AGT
            store_name = 'AGT_Bothell'
            db_filename = f'product_database_{store_name}.db'
            db_path = os.path.join(current_dir, 'uploads', db_filename)
            _product_database = ProductDatabase(db_path)
            _product_database._store_name = store_name
            logging.info(f"ProductDatabase created (default Bothell) at: {db_path}")
    return _product_database"""
    
    new_function = """def get_product_database(store_name=None):
    \"\"\"Lazy load PostgreSQL ProductDatabase to avoid startup delay.\"\"\"
    global _product_database
    if _product_database is None or (store_name and getattr(_product_database, 'store_name', None) != store_name):
        # Use PostgreSQL instead of SQLite
        _product_database = get_postgresql_database(store_name)
        logging.info(f"PostgreSQL ProductDatabase created for store '{store_name or 'AGT_Bothell'}'")
    return _product_database"""
    
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✅ Updated get_product_database function in app.py")
    
    # Update session product database function
    old_session_function = """def get_session_product_database():
    \"\"\"Get ProductDatabase instance for the current session.\"\"\"
    try:
        if not hasattr(app, '_product_database'):
            from src.core.data.product_database import ProductDatabase
            # CRITICAL FIX: Use the correct database path - prioritize AGT_Bothell
            db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
            
            # Fallback to main database if AGT_Bothell doesn't exist
            if not os.path.exists(db_path):
                db_path = os.path.join(current_dir, 'uploads', 'product_database.db')
            
            app._product_database = ProductDatabase(db_path)
            logging.info(f"Created new ProductDatabase instance for session at {db_path}")
        return app._product_database
    except Exception as e:
        logging.error(f"Error getting session product database: {e}")
        return None"""
    
    new_session_function = """def get_session_product_database():
    \"\"\"Get PostgreSQL ProductDatabase instance for the current session.\"\"\"
    try:
        if not hasattr(app, '_product_database'):
            # Use PostgreSQL instead of SQLite
            app._product_database = get_postgresql_database('AGT_Bothell')
            logging.info(f"Created new PostgreSQL ProductDatabase instance for session")
        return app._product_database
    except Exception as e:
        logging.error(f"Error getting session product database: {e}")
        return None"""
    
    if old_session_function in content:
        content = content.replace(old_session_function, new_session_function)
        print("✅ Updated get_session_product_database function in app.py")
    
    # Write updated app.py
    with open(app_py_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated app.py to use PostgreSQL")

def create_test_script():
    """Create a test script for PostgreSQL"""
    
    test_script = """#!/usr/bin/env python3
\"\"\"
Test PostgreSQL connection and performance
\"\"\"

import time
from product_database_postgresql import get_postgresql_database

def test_postgresql():
    print("🧪 Testing PostgreSQL Connection...")
    print("=" * 40)
    
    # Test connection
    db = get_postgresql_database('AGT_Bothell')
    
    if not db.test_connection():
        print("❌ PostgreSQL connection failed")
        return False
    
    print("✅ PostgreSQL connection successful")
    
    # Test search performance
    print("\\n🔍 Testing search performance...")
    
    test_queries = [
        "Blue Dream",
        "OG",
        "Indica",
        "Sativa",
        "Hybrid"
    ]
    
    for query in test_queries:
        start_time = time.time()
        results = db.search_products(query, limit=10)
        end_time = time.time()
        
        print(f"   '{query}': {len(results)} results in {end_time - start_time:.3f}s")
    
    # Test database stats
    print("\\n📊 Database Statistics:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        if key != 'performance_stats':
            print(f"   {key}: {value}")
    
    # Performance stats
    perf_stats = stats.get('performance_stats', {})
    if perf_stats:
        print("\\n⚡ Performance Stats:")
        print(f"   Queries: {perf_stats.get('queries', 0)}")
        print(f"   Cache hits: {perf_stats.get('cache_hits', 0)}")
        print(f"   Cache misses: {perf_stats.get('cache_misses', 0)}")
        if perf_stats.get('queries', 0) > 0:
            avg_time = perf_stats.get('total_time', 0) / perf_stats.get('queries', 1)
            print(f"   Average query time: {avg_time:.3f}s")
    
    print("\\n🎉 PostgreSQL test completed successfully!")
    return True

if __name__ == "__main__":
    test_postgresql()
"""
    
    with open("test_postgresql_performance.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_postgresql_performance.py")

if __name__ == "__main__":
    update_app_to_postgresql()
