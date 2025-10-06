#!/usr/bin/env python3
"""
Final price formatting to ensure ALL prices have proper dollar formatting
"""

import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_price_complete(price_value):
    """Format price with dollar sign, handling all edge cases"""
    if not price_value or str(price_value).strip() == '':
        return '$0'
    
    # If already formatted correctly, leave it
    if str(price_value).startswith('$'):
        return str(price_value)
    
    try:
        # Convert to float first
        price = float(str(price_value))
        
        if price == 0:
            return '$0'
        elif price == int(price):  # No decimal places needed (25.0 -> $25)
            return f'${int(price)}'
        else:  # Has meaningful decimal places (25.50 -> $25.50)
            return f'${price:.2f}'
    except (ValueError, TypeError):
        return '$0'

def main():
    db_path = 'uploads/product_database_AGT_Bothell.db'
    
    logger.info("🚀 Final price formatting update...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get ALL products that don't have proper dollar formatting
    cursor.execute('''
        SELECT id, "Product Name*", Price 
        FROM products 
        WHERE Price IS NOT NULL AND (Price NOT LIKE '$%' OR Price = '')
    ''')
    products = cursor.fetchall()
    
    logger.info(f"📊 Found {len(products)} products needing formatting")
    
    updated_count = 0
    
    for product_id, product_name, current_price in products:
        # Format the price
        formatted_price = format_price_complete(current_price)
        
        # Only update if it's actually different
        if formatted_price != current_price:
            cursor.execute('''
                UPDATE products 
                SET Price = ?, updated_at = ?
                WHERE id = ?
            ''', (formatted_price, datetime.now().isoformat(), product_id))
            
            updated_count += 1
            
            # Show first 20 updates as examples
            if updated_count <= 20:
                logger.info(f"Updated: '{current_price}' -> '{formatted_price}' for '{product_name[:50]}...'")
            elif updated_count == 21:
                logger.info("... (showing first 20 updates)")
    
    conn.commit()
    
    # Final verification
    cursor.execute('''
        SELECT 
            COUNT(CASE WHEN Price = '$0' THEN 1 END) as zero_prices,
            COUNT(CASE WHEN Price LIKE '$%' AND Price != '$0' THEN 1 END) as formatted_prices,
            COUNT(CASE WHEN Price NOT LIKE '$%' THEN 1 END) as still_unformatted,
            COUNT(*) as total,
            MIN(CASE WHEN Price LIKE '$%' AND Price != '$0' THEN Price END) as min_price,
            MAX(CASE WHEN Price LIKE '$%' AND Price != '$0' THEN Price END) as max_price
        FROM products
    ''')
    
    stats = cursor.fetchone()
    
    # Sample of well-formatted prices
    cursor.execute('SELECT "Product Name*", Price FROM products WHERE Price LIKE "$%" AND Price != "$0" ORDER BY RANDOM() LIMIT 10')
    sample_prices = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"🎉 Final formatting complete! Updated {updated_count} products")
    logger.info("📊 Final price format distribution:")
    logger.info(f"   - $0 prices: {stats[0]:,}")
    logger.info(f"   - $ formatted prices: {stats[1]:,}")
    logger.info(f"   - Still unformatted: {stats[2]:,}")
    logger.info(f"   - Total products: {stats[3]:,}")
    
    if stats[4] and stats[5]:
        logger.info(f"   - Price range: {stats[4]} to {stats[5]}")
    
    logger.info("💰 Sample formatted prices:")
    for name, price in sample_prices:
        logger.info(f"   {name[:60]}... -> {price}")

if __name__ == '__main__':
    main()