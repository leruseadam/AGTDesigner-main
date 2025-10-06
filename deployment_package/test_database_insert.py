#!/usr/bin/env python3
"""
Test script to verify database connectivity and test minimal product insert.
"""

import os
import sys
import logging
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_insert():
    """Test database connectivity and minimal product insert."""
    try:
        logger.info("=== DATABASE INSERT TEST ===")
        
        # Import the database class
        from src.core.data.product_database import ProductDatabase
        
        # Get the database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        logger.info(f"Using database path: {db_path}")
        
        # Initialize database
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        logger.info("✅ Database initialized successfully")
        
        # Test minimal product data
        test_product = {
            'Product Name*': 'TEST PRODUCT - Database Insert Test',
            'Product Type*': 'Flower',
            'Vendor/Supplier*': 'Test Vendor',
            'Product Brand': 'Test Brand',
            'Description': 'Test product for database insert verification',
            'Weight*': '3.5g',
            'Price': '25.00'
        }
        
        logger.info(f"Testing insert with product: {test_product['Product Name*']}")
        
        # Attempt to insert the test product
        product_id = product_db.add_or_update_product(test_product)
        
        if product_id:
            logger.info(f"✅ SUCCESS: Product inserted with ID {product_id}")
            
            # Verify the product exists
            conn = product_db._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM products WHERE "Product Name*" = %s', (test_product['Product Name*'],))
            count = cursor.fetchone()[0]
            logger.info(f"✅ VERIFICATION: Found {count} products with test name")
            
            # Clean up test product
            cursor.execute('DELETE FROM products WHERE "Product Name*" = %s', (test_product['Product Name*'],))
            conn.commit()
            logger.info("✅ Cleaned up test product")
            
            return True
        else:
            logger.error("❌ FAILED: Product insert returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_excel_data_storage():
    """Test storing minimal Excel data."""
    try:
        logger.info("=== EXCEL DATA STORAGE TEST ===")
        
        from src.core.data.product_database import ProductDatabase
        
        # Get the database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        # Initialize database
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        
        # Create minimal test DataFrame
        test_data = {
            'Product Name*': ['TEST EXCEL PRODUCT 1', 'TEST EXCEL PRODUCT 2'],
            'Product Type*': ['Flower', 'Edible (Solid)'],
            'Vendor/Supplier*': ['Test Vendor', 'Test Vendor'],
            'Product Brand': ['Test Brand', 'Test Brand'],
            'Description': ['Test Excel product 1', 'Test Excel product 2'],
            'Weight*': ['3.5g', '10mg'],
            'Price': ['25.00', '5.00']
        }
        
        df = pd.DataFrame(test_data)
        logger.info(f"Created test DataFrame with {len(df)} rows")
        
        # Test store_excel_data method
        result = product_db.store_excel_data(df, 'test_file.xlsx')
        
        logger.info(f"Storage result: {result}")
        
        stored = result.get('stored', 0)
        updated = result.get('updated', 0)
        errors = result.get('errors', 0)
        
        if stored > 0 or updated > 0:
            logger.info(f"✅ SUCCESS: Stored {stored} new, updated {updated} existing products")
            
            # Clean up test products
            conn = product_db._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE "Product Name*" LIKE %s', ('TEST EXCEL PRODUCT%',))
            conn.commit()
            logger.info("✅ Cleaned up test Excel products")
            
            return True
        else:
            logger.error(f"❌ FAILED: No products stored. Errors: {errors}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting database tests...")
    
    # Test 1: Basic insert
    test1_success = test_database_insert()
    
    # Test 2: Excel data storage
    test2_success = test_excel_data_storage()
    
    if test1_success and test2_success:
        logger.info("🎉 ALL TESTS PASSED - Database is working correctly")
        sys.exit(0)
    else:
        logger.error("❌ SOME TESTS FAILED - Database has issues")
        sys.exit(1)
