#!/usr/bin/env python3
"""
Script to update database with extracted JointRatio values for pre-roll products.
"""

import sqlite3
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_joint_ratio(product_name, product_type):
    """Extract JointRatio from product name for pre-roll products."""
    if not product_type or 'pre-roll' not in product_type.lower():
        return None
    
    # Patterns to extract JointRatio information from product names
    joint_ratio_patterns = [
        r'(\d*\.?\d+g\s*x\s*\d+(?:\s+Pack)?)',  # "1g x 2 Pack", "0.5g x 2", ".75g x 5 Pack"
        r'(\d*\.?\d+g)',  # "1g", "0.5g", ".75g"
        r'(\d*\.?\d+(?:mg|ML))',  # "100mg", "5ML"
        r'(\d*\.?\d+\s*(?:g|mg|ml|oz|each|pc|count)(?:\s*x\s*\d+)?(?:\s+Pack)?)'  # More flexible pattern
    ]
    
    for pattern in joint_ratio_patterns:
        matches = re.findall(pattern, product_name, re.IGNORECASE)
        if matches:
            # Take the last match (usually the most specific one)
            joint_ratio = matches[-1]
            logger.debug(f"Extracted JointRatio '{joint_ratio}' from '{product_name}'")
            return joint_ratio
    
    return None

def update_database_jointratio():
    """Update the database with extracted JointRatio values for pre-roll products."""
    
    # Connect to database
    db_path = 'AGT_Bothell'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all pre-roll products without JointRatio
        cursor.execute('''
        SELECT "Product Name*", "Product Type*", JointRatio, rowid
        FROM products 
        WHERE "Product Type*" LIKE '%pre-roll%' 
        AND (JointRatio IS NULL OR JointRatio = '' OR JointRatio = 'nan')
        ''')
        
        products = cursor.fetchall()
        logger.info(f"Found {len(products)} pre-roll products without JointRatio")
        
        updated_count = 0
        
        for product_name, product_type, current_ratio, rowid in products:
            # Extract JointRatio from product name
            new_ratio = extract_joint_ratio(product_name, product_type)
            
            if new_ratio:
                # Update the database
                cursor.execute('''
                UPDATE products 
                SET JointRatio = ? 
                WHERE rowid = ?
                ''', (new_ratio, rowid))
                
                logger.info(f"Updated '{product_name}' -> JointRatio: '{new_ratio}'")
                updated_count += 1
            else:
                logger.warning(f"Could not extract JointRatio from '{product_name}'")
        
        # Commit changes
        conn.commit()
        logger.info(f"Updated {updated_count} products with JointRatio values")
        
        # Verify updates
        cursor.execute('''
        SELECT "Product Name*", "Product Type*", JointRatio
        FROM products 
        WHERE "Product Type*" LIKE '%pre-roll%' 
        AND JointRatio IS NOT NULL 
        AND JointRatio != '' 
        AND JointRatio != 'nan'
        LIMIT 10
        ''')
        
        updated_products = cursor.fetchall()
        logger.info(f"Verification: Found {len(updated_products)} products with JointRatio values")
        
        for product_name, product_type, joint_ratio in updated_products:
            logger.info(f"  {product_name} -> {joint_ratio}")
            
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_jointratio()