#!/usr/bin/env python3
"""
Database transfer script - Exports local database and creates import script for PythonAnywhere
"""

import sqlite3
import os
import json
from datetime import datetime

def export_database_data():
    """Export data from local database to JSON format"""
    
    # Find local database
    possible_db_paths = [
        "product_database.db",
        "uploads/product_database.db",
        os.path.expanduser("~/Desktop/labelMaker_ QR copy SAFEST copy 5/product_database.db"),
        os.path.expanduser("~/Desktop/labelMaker_ QR copy SAFEST copy 5/uploads/product_database.db")
    ]
    
    local_db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            local_db_path = path
            break
    
    if not local_db_path:
        print("❌ Local database not found!")
        print("Searched paths:", possible_db_paths)
        return False
    
    print(f"📂 Found local database: {local_db_path}")
    
    try:
        conn = sqlite3.connect(local_db_path)
        conn.row_factory = sqlite3.Row  # Enable column name access
        cursor = conn.cursor()
        
        # Get all products
        cursor.execute("SELECT * FROM products")
        products = [dict(row) for row in cursor.fetchall()]
        
        print(f"📊 Found {len(products)} products in local database")
        
        # Get all strains if table exists
        strains = []
        try:
            cursor.execute("SELECT * FROM strains")
            strains = [dict(row) for row in cursor.fetchall()]
            print(f"📊 Found {len(strains)} strains in local database")
        except sqlite3.OperationalError:
            print("⚠️  No strains table found - will skip strains")
        
        conn.close()
        
        # Export to JSON
        export_data = {
            'export_date': datetime.now().isoformat(),
            'products': products,
            'strains': strains
        }
        
        export_file = "database_export.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Data exported to: {export_file}")
        
        # Create import script for PythonAnywhere
        create_import_script()
        
        return True
        
    except Exception as e:
        print(f"❌ Error exporting database: {e}")
        return False

def create_import_script():
    """Create Python script to import data on PythonAnywhere"""
    
    import_script = '''#!/usr/bin/env python3
"""
Import database data from JSON export
Run this script on PythonAnywhere after uploading database_export.json
"""

import sqlite3
import json
import os
from datetime import datetime

def import_database_data():
    """Import data from JSON export"""
    
    export_file = "database_export.json"
    if not os.path.exists(export_file):
        print(f"❌ Export file not found: {export_file}")
        print("Please upload database_export.json to your PythonAnywhere directory first!")
        return False
    
    print(f"📂 Loading data from: {export_file}")
    
    try:
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        strains = data.get('strains', [])
        
        print(f"📊 Found {len(products)} products to import")
        print(f"📊 Found {len(strains)} strains to import")
        
        # Connect to database
        db_path = "uploads/product_database.db"
        if not os.path.exists("uploads"):
            os.makedirs("uploads", exist_ok=True)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Import strains first
        if strains:
            print("➕ Importing strains...")
            for strain in strains:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO strains 
                        (id, name, lineage, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        strain.get('id'),
                        strain.get('name'),
                        strain.get('lineage'),
                        strain.get('created_at'),
                        strain.get('updated_at')
                    ))
                except Exception as e:
                    print(f"⚠️  Error importing strain {strain.get('name', 'unknown')}: {e}")
        
        # Import products
        if products:
            print("➕ Importing products...")
            imported_count = 0
            
            for product in products:
                try:
                    # Build INSERT statement dynamically based on available columns
                    columns = list(product.keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    column_names = ', '.join([f'"{col}"' for col in columns])
                    
                    sql = f"""
                        INSERT OR REPLACE INTO products 
                        ({column_names})
                        VALUES ({placeholders})
                    """
                    
                    values = [product[col] for col in columns]
                    cursor.execute(sql, values)
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        print(f"   Imported {imported_count} products...")
                        
                except Exception as e:
                    print(f"⚠️  Error importing product {product.get('Product Name*', 'unknown')}: {e}")
            
            print(f"✅ Imported {imported_count} products")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database import completed successfully!")
        
        # Verify import
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"📊 Total products in database: {product_count}")
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing database: {e}")
        return False

if __name__ == "__main__":
    print("🗃️  Database Import Tool")
    print("=" * 40)
    
    success = import_database_data()
    
    if success:
        print("\\n🎉 Import completed successfully!")
    else:
        print("\\n❌ Import failed!")
'''
    
    with open("import_pythonanywhere_database.py", "w") as f:
        f.write(import_script)
    
    print("✅ Created import script: import_pythonanywhere_database.py")

if __name__ == "__main__":
    print("🗃️  Database Export Tool")
    print("=" * 40)
    
    success = export_database_data()
    
    if success:
        print("\n🎉 Export completed successfully!")
        print("\nNext steps:")
        print("1. Upload database_export.json to your PythonAnywhere directory")
        print("2. Upload import_pythonanywhere_database.py to your PythonAnywhere directory")
        print("3. Run: python3.11 import_pythonanywhere_database.py")
    else:
        print("\n❌ Export failed!")