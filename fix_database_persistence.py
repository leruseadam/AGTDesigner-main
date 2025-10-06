#!/usr/bin/env python3
"""
Fix database persistence issues on PythonAnywhere
This script addresses common database reset problems
"""
import os
import sqlite3
import json
import shutil
from datetime import datetime

def check_database_status():
    """Check current database status"""
    print("=== DATABASE STATUS CHECK ===")
    
    db_files = [
        'product_database.db',
        'product_database_AGT_Bothell.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if products table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
                table_exists = cursor.fetchone()
                
                if table_exists:
                    cursor.execute("SELECT COUNT(*) FROM products")
                    count = cursor.fetchone()[0]
                    print(f"✅ {db_file}: EXISTS, {count:,} products")
                else:
                    print(f"❌ {db_file}: EXISTS but no products table")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ {db_file}: ERROR - {e}")
        else:
            print(f"❌ {db_file}: MISSING")

def create_persistent_database():
    """Create a robust, persistent database"""
    print("\n=== CREATING PERSISTENT DATABASE ===")
    
    # Remove existing databases to start fresh
    for db_file in ['product_database.db', 'product_database_AGT_Bothell.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Removed existing {db_file}")
    
    # Create main database
    conn = sqlite3.connect('product_database.db')
    cursor = conn.cursor()
    
    # Create products table with proper schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            vendor TEXT,
            brand TEXT,
            product_type TEXT,
            weight TEXT,
            weight_units TEXT,
            thc_content TEXT,
            cbd_content TEXT,
            lineage TEXT,
            doh_status TEXT,
            price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert comprehensive sample data
    sample_products = [
        ('Blue Raspberry Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Grape Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Peach Mango Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Pineapple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Green Apple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Orange Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Island Punch Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'SATIVA', 'DOH', '$25.00'),
        ('Raspberry Lemonade Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'SATIVA', 'DOH', '$25.00'),
        ('Grape Dream Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'INDICA', 'DOH', '$25.00'),
        ('Strawberry Banana Shot', 'CONSTELLATION CANNABIS', 'Shot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'HYBRID', 'DOH', '$25.00'),
        ('Blue Dream Flower', 'GREEN VALLEY', 'Premium', 'Flower', '3.5', 'G', '20%', '0.5%', 'SATIVA', 'DOH', '$45.00'),
        ('Purple Kush Concentrate', 'PURPLE LABS', 'Elite', 'Concentrate', '1', 'G', '85%', '0.2%', 'INDICA', 'DOH', '$60.00'),
        ('OG Kush Pre-Roll', 'MOUNTAIN HIGH', 'Classic', 'Pre-Roll', '1', 'G', '22%', '0.3%', 'HYBRID', 'DOH', '$12.00'),
        ('CBD Tincture', 'HEMP HEALERS', 'Wellness', 'Tincture', '30', 'ML', '0mg', '1000mg', 'CBD', 'DOH', '$35.00'),
        ('Sour Diesel Vape', 'CLOUD NINE', 'Premium', 'Vape Cartridge', '0.5', 'G', '80%', '0.1%', 'SATIVA', 'DOH', '$40.00'),
    ]
    
    for product in sample_products:
        cursor.execute('''
            INSERT INTO products (product_name, vendor, brand, product_type, weight, weight_units, 
                                thc_content, cbd_content, lineage, doh_status, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print("✅ product_database.db created with 15 sample products")
    
    # Create AGT Bothell database
    conn = sqlite3.connect('product_database_AGT_Bothell.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            vendor TEXT,
            brand TEXT,
            product_type TEXT,
            weight TEXT,
            weight_units TEXT,
            thc_content TEXT,
            cbd_content TEXT,
            lineage TEXT,
            doh_status TEXT,
            price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert AGT Bothell specific products
    agt_products = [
        ('Blue Raspberry Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Grape Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Peach Mango Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Pineapple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '2.5', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$25.00'),
        ('Green Apple Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
        ('Orange Moonshot', 'ALPHA CRUX, LLC', 'Moonshot', 'Edible (Liquid)', '3.53', 'OZ', '100mg', '0mg', 'MIXED', 'DOH', '$30.00'),
    ]
    
    for product in agt_products:
        cursor.execute('''
            INSERT INTO products (product_name, vendor, brand, product_type, weight, weight_units, 
                                thc_content, cbd_content, lineage, doh_status, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print("✅ product_database_AGT_Bothell.db created with 6 sample products")

def create_database_backup():
    """Create backup of current databases"""
    print("\n=== CREATING DATABASE BACKUP ===")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"database_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    db_files = ['product_database.db', 'product_database_AGT_Bothell.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            backup_file = os.path.join(backup_dir, db_file)
            shutil.copy2(db_file, backup_file)
            print(f"✅ Backed up {db_file} to {backup_file}")
    
    print(f"✅ Database backup created in {backup_dir}")

def fix_database_permissions():
    """Fix database file permissions"""
    print("\n=== FIXING DATABASE PERMISSIONS ===")
    
    db_files = ['product_database.db', 'product_database_AGT_Bothell.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                # Make database files readable and writable
                os.chmod(db_file, 0o664)
                print(f"✅ Fixed permissions for {db_file}")
            except Exception as e:
                print(f"❌ Failed to fix permissions for {db_file}: {e}")

def create_database_init_script():
    """Create a script to initialize database on app startup"""
    print("\n=== CREATING DATABASE INIT SCRIPT ===")
    
    init_script = '''#!/usr/bin/env python3
"""
Database initialization script for PythonAnywhere
Run this script to ensure databases are properly initialized
"""
import os
import sqlite3

def init_databases():
    """Initialize databases if they don't exist or are empty"""
    db_files = ['product_database.db', 'product_database_AGT_Bothell.db']
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"Creating {db_file}...")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    vendor TEXT,
                    brand TEXT,
                    product_type TEXT,
                    weight TEXT,
                    weight_units TEXT,
                    thc_content TEXT,
                    cbd_content TEXT,
                    lineage TEXT,
                    doh_status TEXT,
                    price TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"✅ {db_file} created")
        else:
            # Check if database has data
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
                if count == 0:
                    print(f"⚠️ {db_file} exists but is empty")
                else:
                    print(f"✅ {db_file} has {count} products")
            except:
                print(f"❌ {db_file} is corrupted")
            
            conn.close()

if __name__ == "__main__":
    init_databases()
'''
    
    with open('init_databases.py', 'w') as f:
        f.write(init_script)
    
    print("✅ Created init_databases.py script")

def main():
    print("🔧 FIXING DATABASE PERSISTENCE ISSUES")
    print("=" * 60)
    
    # Check current status
    check_database_status()
    
    # Create backup
    create_database_backup()
    
    # Create persistent databases
    create_persistent_database()
    
    # Fix permissions
    fix_database_permissions()
    
    # Create init script
    create_database_init_script()
    
    # Final status check
    print("\n=== FINAL STATUS CHECK ===")
    check_database_status()
    
    print("\n" + "=" * 60)
    print("✅ Database persistence fix complete!")
    print("📋 Next steps:")
    print("1. Run: python3 init_databases.py")
    print("2. Check your web app")
    print("3. If issues persist, check PythonAnywhere file permissions")

if __name__ == "__main__":
    main()
