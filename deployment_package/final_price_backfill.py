#!/usr/bin/env python3
"""
Final comprehensive price backfill that replaces ALL 0.00 prices with Excel data
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_product_name(name):
    """Normalize product name for matching."""
    if not name:
        return ""
    return str(name).strip().lower().replace(" ", "").replace("-", "").replace("_", "")

def normalize_price(price_value):
    """Normalize and standardize price values."""
    if not price_value or str(price_value).strip().lower() in ['nan', 'none', 'null', '']:
        return 0.0
    
    # Handle string prices with $ symbols
    if isinstance(price_value, str):
        price_str = price_value.strip().replace('$', '').replace(',', '')
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    try:
        price = float(price_value)
        return price if price > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0

def main():
    current_dir = Path(__file__).parent
    uploads_dir = current_dir / 'uploads'
    target_db = uploads_dir / 'product_database_AGT_Bothell.db'
    
    logger.info("🚀 Starting final price backfill using Excel data...")
    
    # Get the most recent Excel file (latest inventory)
    excel_file = uploads_dir / 'A Greener Today - Bothell_inventory_09-19-2025  4_52 PM.xlsx'
    
    logger.info(f"📊 Reading latest inventory: {excel_file.name}")
    df = pd.read_excel(excel_file, engine='openpyxl')
    
    # Create price mapping from Excel
    price_mapping = {}
    for _, row in df.iterrows():
        product_name = row.get('Product Name*')
        price = row.get('Price* (Tier Name for Bulk)')
        
        if product_name and str(product_name).strip():
            normalized_name = normalize_product_name(product_name)
            normalized_price = normalize_price(price)
            
            if normalized_name and normalized_price > 0:
                price_mapping[normalized_name] = normalized_price
    
    logger.info(f"📈 Created {len(price_mapping)} price mappings from Excel")
    
    # Update database
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    # Get all products with 0 prices
    cursor.execute('''
        SELECT id, "Product Name*", normalized_name
        FROM products 
        WHERE CAST(Price AS REAL) = 0
    ''')
    
    products_to_update = cursor.fetchall()
    logger.info(f"🎯 Found {len(products_to_update)} products with 0.00 prices")
    
    # Update with Excel prices
    updated_count = 0
    total_value_added = 0.0
    
    for product_id, product_name, normalized_name in products_to_update:
        new_price = None
        
        # Try exact match
        if normalized_name and normalized_name in price_mapping:
            new_price = price_mapping[normalized_name]
        else:
            # Try alternative normalization
            alt_normalized = normalize_product_name(product_name)
            if alt_normalized in price_mapping:
                new_price = price_mapping[alt_normalized]
        
        if new_price and new_price > 0:
            cursor.execute('''
                UPDATE products 
                SET Price = ?, updated_at = ?
                WHERE id = ?
            ''', (new_price, datetime.now().isoformat(), product_id))
            
            updated_count += 1
            total_value_added += new_price
            
            if updated_count <= 20:
                logger.info(f"Updated: '{product_name}' -> ${new_price:.2f}")
            elif updated_count == 21:
                logger.info("... (showing first 20 updates)")
    
    conn.commit()
    
    # Get final statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN CAST(Price AS REAL) = 0 THEN 1 END) as zero_price,
            COUNT(CASE WHEN CAST(Price AS REAL) > 0 THEN 1 END) as has_price,
            ROUND(AVG(CASE WHEN CAST(Price AS REAL) > 0 THEN CAST(Price AS REAL) END), 2) as avg_price,
            ROUND(SUM(CAST(Price AS REAL)), 2) as total_value
        FROM products
    ''')
    
    stats = cursor.fetchone()
    conn.close()
    
    logger.info("🎉 Final price backfill complete!")
    logger.info(f"📈 Updated {updated_count} products")
    logger.info(f"💰 Value added: ${total_value_added:,.2f}")
    logger.info(f"📊 Final statistics:")
    logger.info(f"   - Total products: {stats[0]:,}")
    logger.info(f"   - Products with prices: {stats[2]:,}")
    logger.info(f"   - Products still at $0.00: {stats[1]:,}")
    logger.info(f"   - Average price: ${stats[3]:.2f}" if stats[3] else "   - Average price: N/A")
    logger.info(f"   - Total inventory value: ${stats[4]:,.2f}")

if __name__ == '__main__':
    main()