#!/usr/bin/env python3
import sys
import os

# Add the project root to the path so we can import the modules
sys.path.insert(0, os.path.abspath('.'))

from src.core.data.product_database import ProductDatabase, get_database_path

def test_app_database():
    print(f"Database path: {get_database_path()}")
    
    # Test if the database file exists
    db_path = get_database_path()
    if os.path.exists(db_path):
        print(f"✅ Database file exists")
    else:
        print(f"❌ Database file does not exist")
        return
    
    # Create a ProductDatabase instance like the app does
    try:
        db = ProductDatabase()
        print("✅ ProductDatabase created successfully")
        
        # Test a simple add operation with minimal data
        test_product = {
            'Product Name*': 'Test Product',
            'normalized_name': 'test_product',
            'Product Type*': 'Flower',
            'ProductName': 'Test Product Alt',  # This should work!
            'Vendor/Supplier*': 'Test Vendor',
            'Product Brand': 'Test Brand',
            'Weight*': '1g',
            'Units': 'gram',
            'Price': '$10'
        }
        
        print("Attempting to add product...")
        result = db.add_or_update_product(test_product)
        print(f"✅ Product added successfully with ID: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_app_database()