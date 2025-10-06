#!/usr/bin/env python3
"""
Comprehensive Price backfill script that uses ALL available data sources:
1. All Excel inventory files (Price* columns)
2. All other product databases
3. Price pattern analysis from product names
4. Market-based price inference for common products
"""

import os
import sqlite3
import pandas as pd
import logging
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

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

def infer_price_from_product_name(product_name, product_type="", units="each"):
    """Infer reasonable price from product name patterns and market knowledge."""
    if not product_name:
        return 0.0
    
    name = str(product_name).lower()
    ptype = str(product_type).lower()
    
    # Extract weight/quantity from name
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|gram|oz|ounce|mg)(?:\s|$)', name)
    quantity_match = re.search(r'(\d+)\s*(?:pack|pk|x|count)', name)
    
    weight = float(weight_match.group(1)) if weight_match else 1.0
    weight_unit = weight_match.group(2) if weight_match else units
    quantity = float(quantity_match.group(1)) if quantity_match else 1.0
    
    # Base price estimates per gram for different product types
    base_prices = {
        # Flower prices (per gram)
        'flower': {'g': 8.0, 'oz': 8.0},
        'bud': {'g': 8.0, 'oz': 8.0},
        'sungrown': {'g': 6.0, 'oz': 6.0},
        'greenhouse': {'g': 7.0, 'oz': 7.0},
        'indoor': {'g': 10.0, 'oz': 10.0},
        'premium': {'g': 12.0, 'oz': 12.0},
        'top shelf': {'g': 15.0, 'oz': 15.0},
        
        # Concentrates (per gram)
        'wax': {'g': 25.0, 'oz': 25.0},
        'shatter': {'g': 20.0, 'oz': 20.0},
        'rosin': {'g': 45.0, 'oz': 45.0},
        'live rosin': {'g': 55.0, 'oz': 55.0},
        'resin': {'g': 30.0, 'oz': 30.0},
        'live resin': {'g': 35.0, 'oz': 35.0},
        'hash': {'g': 30.0, 'oz': 30.0},
        'diamonds': {'g': 40.0, 'oz': 40.0},
        'sauce': {'g': 35.0, 'oz': 35.0},
        'budder': {'g': 30.0, 'oz': 30.0},
        'batter': {'g': 30.0, 'oz': 30.0},
        'crumble': {'g': 25.0, 'oz': 25.0},
        
        # Pre-rolls (per piece)
        'pre-roll': {'each': 8.0, 'g': 8.0},
        'preroll': {'each': 8.0, 'g': 8.0},
        'joint': {'each': 8.0, 'g': 8.0},
        'infused': {'each': 15.0, 'g': 15.0},  # Infused pre-rolls
        
        # Edibles (per piece/package)
        'gummy': {'each': 15.0},
        'gummies': {'each': 15.0},
        'chocolate': {'each': 20.0},
        'brownie': {'each': 12.0},
        'cookie': {'each': 10.0},
        'mint': {'each': 8.0},
        'chew': {'each': 15.0},
        'firecracker': {'each': 18.0},
        
        # Vapes (per cartridge)
        'cartridge': {'each': 35.0},
        'cart': {'each': 35.0},
        'disposable': {'each': 25.0},
        'vape': {'each': 30.0},
        'pen': {'each': 30.0},
        
        # Tinctures/liquids (per oz)
        'tincture': {'oz': 40.0, 'each': 40.0},
        'liquid': {'oz': 35.0, 'each': 35.0},
        'oil': {'oz': 45.0, 'each': 45.0},
        'syrup': {'oz': 50.0, 'each': 50.0},
        
        # Topicals (per oz)
        'cream': {'oz': 30.0, 'each': 30.0},
        'lotion': {'oz': 25.0, 'each': 25.0},
        'balm': {'oz': 35.0, 'each': 35.0},
        'salve': {'oz': 30.0, 'each': 30.0},
        'rub': {'oz': 28.0, 'each': 28.0},
        
        # Accessories (per piece)
        'pipe': {'each': 25.0},
        'bong': {'each': 80.0},
        'grinder': {'each': 15.0},
        'lighter': {'each': 3.0},
        'battery': {'each': 20.0},
        'charger': {'each': 15.0},
        'dabber': {'each': 8.0},
        'tool': {'each': 10.0},
        'mat': {'each': 15.0},
        'banger': {'each': 20.0},
        'nail': {'each': 15.0},
        'cap': {'each': 12.0},
        'insert': {'each': 5.0},
        'tweezers': {'each': 8.0},
        'coil': {'each': 10.0},
    }
    
    # Find matching product type and calculate price
    estimated_price = 0.0
    
    for product_type_key, price_data in base_prices.items():
        if product_type_key in name or product_type_key in ptype:
            unit_key = weight_unit if weight_unit in price_data else 'each'
            base_price = price_data.get(unit_key, price_data.get('each', 0.0))
            
            if weight_unit in ['g', 'gram']:
                estimated_price = base_price * weight * quantity
            elif weight_unit in ['oz', 'ounce']:
                # Convert oz to grams for flower/concentrates
                if product_type_key in ['flower', 'bud', 'wax', 'shatter', 'rosin', 'resin', 'hash']:
                    estimated_price = base_price * weight * 28.35 * quantity  # 28.35g per oz
                else:
                    estimated_price = base_price * weight * quantity
            else:
                estimated_price = base_price * quantity
            
            break
    
    # Apply bulk discounts for larger quantities
    if weight_unit in ['g', 'gram']:
        if weight >= 28:  # Ounce or more
            estimated_price *= 0.85  # 15% bulk discount
        elif weight >= 14:  # Half ounce
            estimated_price *= 0.90  # 10% bulk discount
        elif weight >= 7:  # Quarter ounce
            estimated_price *= 0.95  # 5% bulk discount
    
    # Multi-pack discounts
    if quantity > 1:
        if quantity >= 10:
            estimated_price *= 0.90  # 10% multi-pack discount
        elif quantity >= 5:
            estimated_price *= 0.95  # 5% multi-pack discount
    
    # Round to reasonable price points
    if estimated_price > 0:
        if estimated_price < 10:
            return round(estimated_price * 2) / 2  # Round to nearest $0.50
        elif estimated_price < 100:
            return round(estimated_price)  # Round to nearest dollar
        else:
            return round(estimated_price / 5) * 5  # Round to nearest $5
    
    return 0.0

def extract_prices_from_excel(excel_file_path):
    """Extract product name to price mapping from Excel file."""
    try:
        logger.info(f"Reading Excel file: {excel_file_path.name}")
        
        df = pd.read_excel(excel_file_path, engine='openpyxl')
        
        # Find columns
        product_name_col = None
        price_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            if 'product name' in col_lower and not product_name_col:
                product_name_col = col
            elif 'price' in col_lower:
                price_cols.append(col)
        
        # Prefer 'Price* (Tier Name for Bulk)' column, then any Price* column
        main_price_col = None
        for col in price_cols:
            if 'Price* (Tier Name for Bulk)' == col:
                main_price_col = col
                break
            elif col.startswith('Price*') and 'med' not in col.lower():
                main_price_col = col
                break
        
        if not main_price_col and price_cols:
            # Filter out med price
            non_med_price_cols = [col for col in price_cols if 'med' not in col.lower()]
            main_price_col = non_med_price_cols[0] if non_med_price_cols else None
        
        if not product_name_col or not main_price_col:
            logger.warning(f"Missing columns in {excel_file_path.name}: product={product_name_col}, price={main_price_col}")
            return {}
        
        logger.info(f"Using columns: {product_name_col} -> {main_price_col}")
        
        # Create mapping
        price_mapping = {}
        for _, row in df.iterrows():
            product_name = row.get(product_name_col)
            price = row.get(main_price_col)
            
            if product_name and str(product_name).strip():
                normalized_name = normalize_product_name(product_name)
                normalized_price = normalize_price(price)
                
                if normalized_name and normalized_price > 0:
                    price_mapping[normalized_name] = normalized_price
        
        logger.info(f"Extracted {len(price_mapping)} price mappings from {excel_file_path.name}")
        return price_mapping
        
    except Exception as e:
        logger.error(f"Error reading {excel_file_path.name}: {e}")
        return {}

def extract_prices_from_database(db_path):
    """Extract price mapping from another database."""
    try:
        logger.info(f"Reading database: {db_path.name}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if this database has price data
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'Price' not in columns:
            logger.warning(f"No Price column in {db_path.name}")
            return {}
        
        # Get products with valid prices
        cursor.execute('''
            SELECT "Product Name*", normalized_name, Price 
            FROM products 
            WHERE Price IS NOT NULL AND Price != '' AND Price > 0
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        price_mapping = {}
        for product_name, normalized_name, price in results:
            if product_name and normalized_name and price:
                normalized_price = normalize_price(price)
                if normalized_price > 0:
                    price_mapping[normalized_name] = normalized_price
        
        logger.info(f"Extracted {len(price_mapping)} price mappings from {db_path.name}")
        return price_mapping
        
    except Exception as e:
        logger.error(f"Error reading database {db_path.name}: {e}")
        return {}

def main():
    """Main comprehensive price backfill process."""
    current_dir = Path(__file__).parent
    uploads_dir = current_dir / 'uploads'
    
    # Target database
    target_db = uploads_dir / 'product_database_AGT_Bothell.db'
    if not target_db.exists():
        logger.error(f"Target database not found: {target_db}")
        return
    
    logger.info("🚀 Starting comprehensive price backfill from ALL sources...")
    
    # Collect price mappings from all sources
    all_price_mappings = {}
    sources_used = []
    
    # 1. Excel files
    excel_files = list(uploads_dir.glob('*.xlsx'))
    logger.info(f"Found {len(excel_files)} Excel files")
    
    for excel_file in excel_files:
        if excel_file.name.startswith('~') or 'test' in excel_file.name.lower():
            continue  # Skip temp files and test files
            
        price_mapping = extract_prices_from_excel(excel_file)
        if price_mapping:
            # Prefer newer files for conflicts
            for name, price in price_mapping.items():
                if name not in all_price_mappings or '2025' in excel_file.name:
                    all_price_mappings[name] = price
            sources_used.append(f"Excel: {excel_file.name}")
    
    # 2. Other databases
    db_files = list(uploads_dir.glob('product_database*.db'))
    logger.info(f"Found {len(db_files)} database files")
    
    for db_file in db_files:
        if db_file.name == target_db.name:
            continue  # Skip the target database
        if 'shm' in db_file.name or 'wal' in db_file.name:
            continue  # Skip SQLite temp files
            
        price_mapping = extract_prices_from_database(db_file)
        if price_mapping:
            for name, price in price_mapping.items():
                if name not in all_price_mappings:  # Don't overwrite Excel data
                    all_price_mappings[name] = price
            sources_used.append(f"Database: {db_file.name}")
    
    logger.info(f"📊 Collected {len(all_price_mappings)} total price mappings from {len(sources_used)} sources")
    logger.info("Sources used:")
    for source in sources_used:
        logger.info(f"  - {source}")
    
    # 3. Get products that need prices
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, "Product Name*", normalized_name, Price, "Product Type*", Units
        FROM products 
        WHERE Price = 0.00 OR Price = '' OR Price IS NULL OR Price = 0
    ''')
    
    products_to_update = cursor.fetchall()
    logger.info(f"🎯 Found {len(products_to_update)} products that need prices")
    
    # 4. Update products with mappings or inferred prices
    updated_count = 0
    inferred_count = 0
    no_change_count = 0
    total_updated_value = 0.0
    
    for product_id, product_name, normalized_name, current_price, product_type, units in products_to_update:
        new_price = None
        method = None
        
        # Try exact mapping first
        if normalized_name and normalized_name in all_price_mappings:
            new_price = all_price_mappings[normalized_name]
            method = "mapping"
        else:
            # Try alternative normalization
            alt_normalized = normalize_product_name(product_name)
            if alt_normalized in all_price_mappings:
                new_price = all_price_mappings[alt_normalized]
                method = "alt_mapping"
        
        # If no mapping found, try inference
        if not new_price or new_price <= 0:
            inferred_price = infer_price_from_product_name(product_name, product_type or "", units or "each")
            if inferred_price > 0:
                new_price = inferred_price
                method = "inference"
                inferred_count += 1
        
        # Update if we found a price
        if new_price and new_price > 0:
            cursor.execute('''
                UPDATE products 
                SET Price = ?, updated_at = ?
                WHERE id = ?
            ''', (new_price, datetime.now().isoformat(), product_id))
            
            updated_count += 1
            total_updated_value += new_price
            
            if updated_count <= 20:  # Show first 20 updates
                logger.info(f"Updated ({method}): '{product_name}' -> ${new_price:.2f}")
            elif updated_count == 21:
                logger.info("... (showing first 20 updates)")
        else:
            no_change_count += 1
    
    conn.commit()
    
    # 5. Show final statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN Price = 0 OR Price IS NULL THEN 1 END) as no_price,
            COUNT(CASE WHEN Price > 0 THEN 1 END) as has_price,
            AVG(CASE WHEN Price > 0 THEN Price END) as avg_price,
            MIN(CASE WHEN Price > 0 THEN Price END) as min_price,
            MAX(Price) as max_price,
            SUM(Price) as total_value
        FROM products
    ''')
    
    stats = cursor.fetchone()
    conn.close()
    
    logger.info("🎉 Comprehensive price backfill complete!")
    logger.info(f"📈 Updated {updated_count} products ({inferred_count} from inference)")
    logger.info(f"💰 Total value added: ${total_updated_value:,.2f}")
    logger.info(f"📊 Final price statistics:")
    logger.info(f"   - Products with prices: {stats[2]:,}")
    logger.info(f"   - Products without prices: {stats[1]:,}")
    logger.info(f"   - Average price: ${stats[3]:.2f}" if stats[3] else "   - Average price: N/A")
    logger.info(f"   - Price range: ${stats[4]:.2f} - ${stats[5]:.2f}" if stats[4] and stats[5] else "   - Price range: N/A")
    logger.info(f"   - Total inventory value: ${stats[6]:,.2f}" if stats[6] else "   - Total inventory value: $0.00")

if __name__ == '__main__':
    main()