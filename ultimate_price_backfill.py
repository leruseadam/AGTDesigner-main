#!/usr/bin/env python3
"""
FINAL comprehensive price backfill using ALL Excel files
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

def infer_price_by_type_and_weight(product_name, product_type, weight_str=""):
    """Infer price based on product type and weight."""
    name = str(product_name).lower()
    ptype = str(product_type).lower() if product_type else ""
    
    # Extract weight
    import re
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*g', name + " " + weight_str)
    weight = float(weight_match.group(1)) if weight_match else 1.0
    
    # Base prices per gram by type
    if 'flower' in ptype:
        base_price = 8.0
        if weight >= 28:  # Ounce
            return base_price * weight * 0.8  # 20% bulk discount
        elif weight >= 14:  # Half oz
            return base_price * weight * 0.9  # 10% bulk discount
        else:
            return base_price * weight
    
    elif 'concentrate' in ptype or 'live resin' in name or 'sugar' in name:
        base_price = 35.0
        return base_price * weight
    
    elif 'pre-roll' in ptype or 'preroll' in name:
        if '2 pack' in name or '2pack' in name or 'x 2' in name:
            return 16.0  # $8 per pre-roll
        else:
            return 8.0
    
    elif 'vape' in ptype or 'cartridge' in ptype or 'disposable' in name:
        return 35.0  # Standard vape price
    
    elif 'edible' in ptype or 'gummies' in name or 'chocolate' in name:
        return 20.0
    
    else:
        # Default based on weight
        return max(8.0 * weight, 10.0)

def main():
    current_dir = Path(__file__).parent
    uploads_dir = current_dir / 'uploads'
    target_db = uploads_dir / 'product_database_AGT_Bothell.db'
    
    logger.info("🚀 Starting FINAL comprehensive price backfill...")
    
    # Collect prices from ALL Excel files
    all_price_mappings = {}
    excel_files = list(uploads_dir.glob('*.xlsx'))
    
    for excel_file in excel_files:
        if excel_file.name.startswith('~'):
            continue
            
        try:
            logger.info(f"Processing: {excel_file.name}")
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            for _, row in df.iterrows():
                product_name = row.get('Product Name*')
                price = row.get('Price* (Tier Name for Bulk)')
                
                if product_name and str(product_name).strip():
                    normalized_name = normalize_product_name(product_name)
                    normalized_price = normalize_price(price)
                    
                    if normalized_name and normalized_price > 0:
                        # Prefer newer files (keep existing if better)
                        if normalized_name not in all_price_mappings or '2025' in excel_file.name:
                            all_price_mappings[normalized_name] = normalized_price
                            
        except Exception as e:
            logger.warning(f"Error reading {excel_file.name}: {e}")
    
    logger.info(f"📈 Collected {len(all_price_mappings)} total price mappings")
    
    # Update database
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, "Product Name*", normalized_name, "Product Type*"
        FROM products 
        WHERE CAST(Price AS REAL) = 0
    ''')
    
    products_to_update = cursor.fetchall()
    logger.info(f"🎯 Found {len(products_to_update)} products still needing prices")
    
    updated_count = 0
    inferred_count = 0
    
    for product_id, product_name, normalized_name, product_type in products_to_update:
        new_price = None
        method = None
        
        # Try exact mapping
        if normalized_name and normalized_name in all_price_mappings:
            new_price = all_price_mappings[normalized_name]
            method = "mapping"
        else:
            # Try alternative normalization
            alt_normalized = normalize_product_name(product_name)
            if alt_normalized in all_price_mappings:
                new_price = all_price_mappings[alt_normalized]
                method = "alt_mapping"
        
        # If no mapping, infer price
        if not new_price:
            new_price = infer_price_by_type_and_weight(product_name, product_type)
            method = "inference"
            inferred_count += 1
        
        if new_price and new_price > 0:
            cursor.execute('''
                UPDATE products 
                SET Price = ?, updated_at = ?
                WHERE id = ?
            ''', (new_price, datetime.now().isoformat(), product_id))
            
            updated_count += 1
            if updated_count <= 20:
                logger.info(f"Updated ({method}): '{product_name}' -> \${new_price:.2f}")
            elif updated_count == 21:
                logger.info("... (showing first 20 updates)")
    
    conn.commit()
    
    # Final statistics
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
    
    logger.info("🎉 FINAL price backfill complete!")
    logger.info(f"📈 Updated {updated_count} products ({inferred_count} inferred)")
    logger.info(f"📊 Final statistics:")
    logger.info(f"   - Total products: {stats[0]:,}")
    logger.info(f"   - Products with prices: {stats[2]:,}")
    logger.info(f"   - Products still at \$0.00: {stats[1]:,}")
    logger.info(f"   - Average price: \${stats[3]:.2f}" if stats[3] else "   - Average price: N/A")
    logger.info(f"   - Total inventory value: \${stats[4]:,.2f}")
    
    # Calculate completion percentage
    completion_pct = (stats[2] / stats[0]) * 100 if stats[0] > 0 else 0
    logger.info(f"🎯 Price completion: {completion_pct:.1f}%")

if __name__ == '__main__':
    main()