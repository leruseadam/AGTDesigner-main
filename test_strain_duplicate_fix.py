#!/usr/bin/env python3
"""
Test script to verify the strain duplicate handling fix.
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

def test_strain_duplicate_handling():
    """Test that duplicate strains don't cause transaction rollbacks."""
    try:
        logger.info("=== STRAIN DUPLICATE HANDLING TEST ===")
        
        from src.core.data.product_database import ProductDatabase
        
        # Get the database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        # Initialize database
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        logger.info("✅ Database initialized successfully")
        
        # Test 1: Add a new strain
        logger.info("Test 1: Adding new strain 'TEST STRAIN DUPLICATE'")
        strain_id1 = product_db.add_or_update_strain('TEST STRAIN DUPLICATE', 'Test Lineage')
        if strain_id1:
            logger.info(f"✅ SUCCESS: New strain added with ID {strain_id1}")
        else:
            logger.error("❌ FAILED: New strain returned None")
            return False
        
        # Test 2: Try to add the same strain again (should handle duplicate gracefully)
        logger.info("Test 2: Adding duplicate strain 'TEST STRAIN DUPLICATE'")
        strain_id2 = product_db.add_or_update_strain('TEST STRAIN DUPLICATE', 'Test Lineage')
        if strain_id2:
            logger.info(f"✅ SUCCESS: Duplicate strain handled with ID {strain_id2}")
            if strain_id1 == strain_id2:
                logger.info("✅ CORRECT: Same ID returned for duplicate strain")
            else:
                logger.warning(f"⚠️ WARNING: Different IDs returned ({strain_id1} vs {strain_id2})")
        else:
            logger.warning("⚠️ WARNING: Duplicate strain returned None (acceptable)")
        
        # Test 3: Add a product with the strain (should work even after duplicate strain)
        logger.info("Test 3: Adding product with the strain")
        test_product = {
            'Product Name*': 'TEST PRODUCT WITH DUPLICATE STRAIN',
            'Product Type*': 'Flower',
            'Vendor/Supplier*': 'Test Vendor',
            'Product Brand': 'Test Brand',
            'Product Strain': 'TEST STRAIN DUPLICATE',
            'Lineage': 'Test Lineage',
            'Description': 'Test product with duplicate strain',
            'Weight*': '3.5g',
            'Price': '25.00'
        }
        
        product_id = product_db.add_or_update_product(test_product)
        if product_id:
            logger.info(f"✅ SUCCESS: Product added with ID {product_id} despite duplicate strain")
        else:
            logger.error("❌ FAILED: Product insert failed after duplicate strain")
            return False
        
        # Clean up test data
        conn = product_db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE "Product Name*" = %s', ('TEST PRODUCT WITH DUPLICATE STRAIN',))
        cursor.execute('DELETE FROM strains WHERE strain_name = %s', ('TEST STRAIN DUPLICATE',))
        conn.commit()
        logger.info("✅ Cleaned up test data")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_excel_upload_with_duplicate_strains():
    """Test Excel upload with products that have duplicate strains."""
    try:
        logger.info("=== EXCEL UPLOAD WITH DUPLICATE STRAINS TEST ===")
        
        from src.core.data.product_database import ProductDatabase
        
        # Get the database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        # Initialize database
        product_db = ProductDatabase(db_path)
        product_db.init_database()
        
        # Create test DataFrame with products that have duplicate strains
        test_data = {
            'Product Name*': [
                'TEST EXCEL PRODUCT WITH BLUE DREAM',
                'TEST EXCEL PRODUCT WITH BLUE DREAM 2',
                'TEST EXCEL PRODUCT WITH GRAPE RUNTZ'
            ],
            'Product Type*': ['Flower', 'Flower', 'Flower'],
            'Vendor/Supplier*': ['Test Vendor', 'Test Vendor', 'Test Vendor'],
            'Product Brand': ['Test Brand', 'Test Brand', 'Test Brand'],
            'Product Strain': ['Blue Dream', 'Blue Dream', 'Grape Runtz'],  # These strains likely exist
            'Lineage': ['Sativa', 'Sativa', 'Hybrid'],
            'Description': ['Test 1', 'Test 2', 'Test 3'],
            'Weight*': ['3.5g', '3.5g', '3.5g'],
            'Price': ['25.00', '25.00', '25.00']
        }
        
        df = pd.DataFrame(test_data)
        logger.info(f"Created test DataFrame with {len(df)} rows (including duplicate strains)")
        
        # Test store_excel_data method
        result = product_db.store_excel_data(df, 'test_duplicate_strains.xlsx')
        
        logger.info(f"Storage result: {result}")
        
        stored = result.get('stored', 0)
        updated = result.get('updated', 0)
        errors = result.get('errors', 0)
        
        if stored > 0 or updated > 0:
            logger.info(f"✅ SUCCESS: Stored {stored} new, updated {updated} existing products despite duplicate strains")
            
            # Clean up test products
            conn = product_db._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE "Product Name*" LIKE %s', ('TEST EXCEL PRODUCT%',))
            conn.commit()
            logger.info("✅ Cleaned up test Excel products")
            
            return True
        else:
            logger.error(f"❌ FAILED: No products stored. Errors: {errors}")
            if 'error_details' in result:
                logger.error(f"Error details: {result['error_details']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Starting strain duplicate handling tests...")
    
    # Test 1: Basic strain duplicate handling
    test1_success = test_strain_duplicate_handling()
    
    # Test 2: Excel upload with duplicate strains
    test2_success = test_excel_upload_with_duplicate_strains()
    
    if test1_success and test2_success:
        logger.info("🎉 ALL TESTS PASSED - Strain duplicate handling is working correctly")
        sys.exit(0)
    else:
        logger.error("❌ SOME TESTS FAILED - Strain duplicate handling needs more work")
        sys.exit(1)
