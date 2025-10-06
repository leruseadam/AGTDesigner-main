#!/usr/bin/env python3.11
"""
Fix empty database issue on PythonAnywhere
This script will check the database and populate it if needed
"""

import os
import sys
import logging

# Add project directory to path - detect environment
import os
if os.path.exists('/home/adamcordova'):
    # PythonAnywhere environment
    project_dir = '/home/adamcordova/AGTDesigner'
else:
    # Local environment
    project_dir = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 5'

if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

def check_database_status():
    """Check the current database status"""
    print("🔍 Checking database status...")
    
    try:
        # Import the database
        from src.core.data.product_database import ProductDatabase
        
        # Check if Bothell database file exists
        db_path = os.path.join(project_dir, 'uploads', 'product_database_AGT_Bothell.db')
        if not os.path.exists(db_path):
            print(f"❌ Bothell database file not found: {db_path}")
            # Try default database as fallback
            db_path = os.path.join(project_dir, 'product_database.db')
            if not os.path.exists(db_path):
                print(f"❌ Default database file also not found: {db_path}")
                return False
            else:
                print(f"⚠️  Using default database: {db_path}")
        else:
            print(f"✅ Using Bothell database: {db_path}")
        
        # Get database size
        db_size = os.path.getsize(db_path)
        print(f"📊 Database file size: {db_size} bytes")
        
        if db_size == 0:
            print("❌ Database file is empty")
            return False
        
        # Try to connect and count products
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        
        # Count products
        try:
            products = product_db.get_all_products()
            count = len(products)
            print(f"📈 Total products in database: {count}")
            
            if count == 0:
                print("❌ Database is empty (0 products)")
                return False
            else:
                print("✅ Database has products")
                return True
                
        except Exception as e:
            print(f"❌ Error counting products: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def find_excel_files():
    """Find Excel files that can be used to populate the database"""
    print("\n🔍 Looking for Excel files...")
    
    excel_files = []
    
    # Check uploads directory
    uploads_dir = os.path.join(project_dir, 'uploads')
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(uploads_dir, file)
                file_size = os.path.getsize(file_path)
                excel_files.append((file, file_path, file_size))
                print(f"📄 Found Excel file: {file} ({file_size} bytes)")
    
    # Check Downloads directory (PythonAnywhere specific)
    downloads_dir = '/home/adamcordova/Downloads'
    if os.path.exists(downloads_dir):
        for file in os.listdir(downloads_dir):
            if 'greener today' in file.lower() and file.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(downloads_dir, file)
                file_size = os.path.getsize(file_path)
                excel_files.append((file, file_path, file_size))
                print(f"📄 Found Excel file in Downloads: {file} ({file_size} bytes)")
    
    # Check current directory for any Excel files
    current_dir_files = os.listdir(project_dir)
    for file in current_dir_files:
        if file.endswith(('.xlsx', '.xls')):
            file_path = os.path.join(project_dir, file)
            file_size = os.path.getsize(file_path)
            excel_files.append((file, file_path, file_size))
            print(f"📄 Found Excel file in project directory: {file} ({file_size} bytes)")
    
    if not excel_files:
        print("❌ No Excel files found")
        print(f"💡 Searched in:")
        print(f"   - {uploads_dir}")
        print(f"   - {downloads_dir}")
        print(f"   - {project_dir}")
        return None
    
    # Return the largest file (most likely to be the inventory)
    largest_file = max(excel_files, key=lambda x: x[2])
    print(f"🎯 Using largest file: {largest_file[0]} ({largest_file[2]} bytes)")
    return largest_file[1]

def populate_database_from_excel(excel_file_path):
    """Populate the database from an Excel file"""
    print(f"\n🚀 Populating database from: {excel_file_path}")
    
    try:
        # Import required modules
        import pandas as pd
        from src.core.data.excel_processor import ExcelProcessor
        from src.core.data.product_database import ProductDatabase
        
        # Create Excel processor
        processor = ExcelProcessor()
        
        # Load the Excel file
        print("📖 Loading Excel file...")
        success = processor.load_file(excel_file_path)
        
        if not success or processor.df is None or processor.df.empty:
            print("❌ Failed to load Excel file")
            return False
        
        print(f"✅ Loaded {len(processor.df)} rows from Excel file")
        
        # Store in Bothell database
        print("💾 Storing data in Bothell database...")
        db_path = os.path.join(project_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        # Ensure uploads directory exists
        os.makedirs(os.path.join(project_dir, 'uploads'), exist_ok=True)
        
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        
        # Store the data
        storage_result = product_db.store_excel_data(processor.df, excel_file_path)
        print(f"✅ Database storage result: {storage_result}")
        
        # Verify the data was stored
        count = product_db.get_product_count()
        print(f"📈 Total products now in database: {count}")
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to fix empty database"""
    print("🚀 FIXING EMPTY DATABASE ON PYTHONANYWHERE")
    print("=" * 50)
    
    # Show environment info
    print(f"📍 Project directory: {project_dir}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"🏠 Home directory: {os.path.expanduser('~')}")
    
    # Check current database status
    db_ok = check_database_status()
    
    if db_ok:
        print("\n✅ Database is already populated!")
        return True
    
    # Find Excel files
    excel_file = find_excel_files()
    
    if not excel_file:
        print("\n❌ No Excel files found to populate database")
        print("💡 Please upload an Excel file first, then run this script again")
        return False
    
    # Populate database
    success = populate_database_from_excel(excel_file)
    
    if success:
        print("\n🎉 Database successfully populated!")
        print("💡 Refresh your web page to see the products")
        return True
    else:
        print("\n❌ Failed to populate database")
        return False

if __name__ == "__main__":
    main()
