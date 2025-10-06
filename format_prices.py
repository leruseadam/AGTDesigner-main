#!/usr/bin/env python3
"""
Format all prices in the database with proper dollar sign formatting.
12.00 -> $12, 12.50 -> $12.50, etc.
"""

import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_price(price_value):
    """Format price with dollar sign, removing unnecessary .00"""
    try:
        price = float(price_value)
        if price == 0:
            return "$0"
        elif price == int(price):  # No decimal places needed
            return f"${int(price)}"
        else:  # Has decimal places
            return f"${price:.2f}"
    except (ValueError, TypeError):
        return "$0"

def main():
    db_path = 'uploads/product_database_AGT_Bothell.db'
    
    logger.info("🚀 Starting price formatting update...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all products with prices
    cursor.execute('SELECT id, "Product Name*", Price FROM products WHERE Price IS NOT NULL')
    products = cursor.fetchall()
    
    logger.info(f"📊 Found {len(products)} products to format")
    
    updated_count = 0
    
    for product_id, product_name, current_price in products:
        # Format the price
        formatted_price = format_price(current_price)
        
        # Update the database
        cursor.execute('''
            UPDATE products 
            SET Price = ?, updated_at = ?
            WHERE id = ?
        ''', (formatted_price, datetime.now().isoformat(), product_id))
        
        updated_count += 1
        
        # Show first 20 updates as examples
        if updated_count <= 20:
            logger.info(f"Updated: '{product_name}' -> {current_price} -> {formatted_price}")
        elif updated_count == 21:
            logger.info("... (showing first 20 updates)")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎉 Price formatting complete! Updated {updated_count} products")
    
    # Verify results
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT "Product Name*", Price FROM products WHERE Price != "$0" ORDER BY RANDOM() LIMIT 10')
    sample_results = cursor.fetchall()
    
    logger.info("📋 Sample formatted prices:")
    for name, price in sample_results:
        logger.info(f"  {name} -> {price}")
    
    # Count different price formats
    cursor.execute('''
        SELECT 
            COUNT(CASE WHEN Price = "$0" THEN 1 END) as zero_prices,
            COUNT(CASE WHEN Price LIKE "$%" AND Price != "$0" THEN 1 END) as dollar_prices,
            COUNT(CASE WHEN Price NOT LIKE "$%" THEN 1 END) as unformatted_prices,
            COUNT(*) as total
        FROM products
    ''')
    
    stats = cursor.fetchone()
    conn.close()
    
    logger.info("📊 Final price format distribution:")
    logger.info(f"   - $0 prices: {stats[0]:,}")
    logger.info(f"   - $ formatted prices: {stats[1]:,}")  
    logger.info(f"   - Unformatted prices: {stats[2]:,}")
    logger.info(f"   - Total products: {stats[3]:,}")

if __name__ == '__main__':
    main()