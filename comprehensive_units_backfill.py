#!/usr/bin/env python3
"""
Comprehensive Units backfill script that uses ALL available data sources:
1. All Excel inventory files
2. All other product databases
3. Product name pattern analysis
4. Product type-based inference
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

def normalize_units(unit_value):
    """Normalize and standardize unit values."""
    if not unit_value or str(unit_value).strip().lower() in ['nan', 'none', 'null', '']:
        return 'each'
    
    unit = str(unit_value).strip().lower()
    
    # Comprehensive unit mappings
    unit_mappings = {
        'grams': 'g', 'gram': 'g', 'gm': 'g', 'gr': 'g',
        'ounces': 'oz', 'ounce': 'oz', 'fl oz': 'oz', 'floz': 'oz',
        'milligrams': 'mg', 'milligram': 'mg', 'mgs': 'mg',
        'milliliters': 'ml', 'milliliter': 'ml', 'mls': 'ml',
        'liters': 'l', 'liter': 'l',
        'each': 'each', 'ea': 'each', 'piece': 'each', 'unit': 'each', 'pcs': 'each',
        'pack': 'pack', 'pk': 'pack', 'package': 'pack',
        'bottle': 'bottle', 'btl': 'bottle',
        'tube': 'tube', 'container': 'each'
    }
    
    return unit_mappings.get(unit, unit)

def infer_units_from_product_name(product_name, product_type=""):
    """Infer units from product name and type patterns."""
    if not product_name:
        return 'each'
    
    name = str(product_name).lower()
    ptype = str(product_type).lower()
    
    # Weight pattern matching
    weight_patterns = [
        r'(\d+(?:\.\d+)?)\s*g\b',      # 1g, 3.5g, etc.
        r'(\d+(?:\.\d+)?)\s*gram',     # 1gram, etc.
        r'(\d+(?:\.\d+)?)\s*oz\b',     # 1oz, 2oz, etc.
        r'(\d+(?:\.\d+)?)\s*ounce',    # 1ounce, etc.
        r'(\d+(?:\.\d+)?)\s*mg\b',     # 100mg, etc.
        r'(\d+(?:\.\d+)?)\s*ml\b',     # 30ml, etc.
    ]
    
    for pattern in weight_patterns:
        match = re.search(pattern, name)
        if match:
            weight_val = float(match.group(1))
            if 'g' in pattern and weight_val > 0:
                return 'g'
            elif 'oz' in pattern and weight_val > 0:
                return 'oz'  
            elif 'mg' in pattern and weight_val > 0:
                return 'mg'
            elif 'ml' in pattern and weight_val > 0:
                return 'ml'
    
    # Product type-based inference
    liquid_indicators = ['tincture', 'liquid', 'oil', 'syrup', 'drink', 'beverage', 'elixir']
    topical_indicators = ['cream', 'lotion', 'balm', 'salve', 'rub', 'topical', 'gel']
    flower_indicators = ['flower', 'bud', 'eighth', 'quarter', 'half', 'ounce', 'gram']
    
    # Check for liquid products (usually oz)
    if any(indicator in name or indicator in ptype for indicator in liquid_indicators):
        return 'oz'
    
    # Check for topical products (usually oz)  
    if any(indicator in name or indicator in ptype for indicator in topical_indicators):
        return 'oz'
    
    # Check for flower products (usually g)
    if any(indicator in name or indicator in ptype for indicator in flower_indicators):
        return 'g'
    
    # Check for concentrates/extracts (usually g)
    concentrate_indicators = ['wax', 'shatter', 'rosin', 'resin', 'hash', 'concentrate', 'extract', 'dab', 'sauce']
    if any(indicator in name or indicator in ptype for indicator in concentrate_indicators):
        return 'g'
    
    # Check for edibles (usually each or mg for potency)
    edible_indicators = ['gummy', 'gummies', 'chocolate', 'cookie', 'brownie', 'candy', 'mint', 'chew', 'edible']
    if any(indicator in name or indicator in ptype for indicator in edible_indicators):
        # If it has mg in the name, it's probably measured by mg potency but sold as each
        if 'mg' in name:
            return 'each'  # Edibles are typically sold as individual pieces
    
    # Check for pre-rolls (usually each or g)
    if 'pre-roll' in name or 'preroll' in name or 'joint' in name:
        # If it mentions weight like "1g" it's sold by weight
        if re.search(r'\d+(?:\.\d+)?\s*g', name):
            return 'g'
        else:
            return 'each'  # Individual pre-rolls
    
    # Check for vape products (usually each)
    vape_indicators = ['cartridge', 'cart', 'vape', 'pen', 'battery']
    if any(indicator in name or indicator in ptype for indicator in vape_indicators):
        return 'each'
    
    # Check for accessories/hardware (always each)
    accessory_indicators = ['pipe', 'bong', 'grinder', 'lighter', 'battery', 'charger', 'case', 'tool', 'cap', 'nail', 'banger', 'bowl', 'stem']
    if any(indicator in name or indicator in ptype for indicator in accessory_indicators):
        return 'each'
    
    # Default to each for unknown items
    return 'each'

def extract_units_from_excel(excel_file_path):
    """Extract product name to units mapping from Excel file."""
    try:
        logger.info(f"Reading Excel file: {excel_file_path.name}")
        
        df = pd.read_excel(excel_file_path, engine='openpyxl')
        
        # Find columns
        product_name_col = None
        units_col = None
        weight_col = None
        product_type_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'product name' in col_lower and not product_name_col:
                product_name_col = col
            elif any(x in col_lower for x in ['weight unit', 'units']) and not units_col:
                units_col = col
            elif 'weight' in col_lower and 'unit' not in col_lower and not weight_col:
                weight_col = col
            elif 'product type' in col_lower and not product_type_col:
                product_type_col = col
        
        if not product_name_col:
            logger.warning(f"No product name column found in {excel_file_path.name}")
            return {}
        
        logger.info(f"Using columns: {product_name_col} -> {units_col or 'None'}")
        
        # Create mapping
        units_mapping = {}
        for _, row in df.iterrows():
            product_name = row.get(product_name_col)
            units = row.get(units_col) if units_col else None
            weight = row.get(weight_col) if weight_col else None
            product_type = row.get(product_type_col) if product_type_col else ""
            
            if product_name and str(product_name).strip():
                normalized_name = normalize_product_name(product_name)
                
                if units:
                    # Use explicit units from Excel
                    normalized_units = normalize_units(units)
                    
                    # For zero weight products with weight units, use 'each'
                    if weight_col and (not weight or str(weight).strip() in ['0', '0.0', 'nan', 'None']):
                        if normalized_units in ['g', 'oz', 'mg', 'ml']:
                            normalized_units = 'each'
                else:
                    # Infer units from product name/type
                    normalized_units = infer_units_from_product_name(product_name, product_type)
                
                if normalized_name and normalized_units:
                    units_mapping[normalized_name] = normalized_units
        
        logger.info(f"Extracted {len(units_mapping)} mappings from {excel_file_path.name}")
        return units_mapping
        
    except Exception as e:
        logger.error(f"Error reading {excel_file_path.name}: {e}")
        return {}

def extract_units_from_database(db_path):
    """Extract units mapping from another database."""
    try:
        logger.info(f"Reading database: {db_path.name}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if this database has units data
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'Units' not in columns:
            logger.warning(f"No Units column in {db_path.name}")
            return {}
        
        # Get products with valid units
        cursor.execute('''
            SELECT "Product Name*", normalized_name, Units 
            FROM products 
            WHERE Units IS NOT NULL AND Units != '' AND Units != 'each'
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        units_mapping = {}
        for product_name, normalized_name, units in results:
            if product_name and normalized_name and units:
                units_mapping[normalized_name] = normalize_units(units)
        
        logger.info(f"Extracted {len(units_mapping)} mappings from {db_path.name}")
        return units_mapping
        
    except Exception as e:
        logger.error(f"Error reading database {db_path.name}: {e}")
        return {}

def main():
    """Main comprehensive backfill process."""
    current_dir = Path(__file__).parent
    uploads_dir = current_dir / 'uploads'
    
    # Target database
    target_db = uploads_dir / 'product_database_AGT_Bothell.db'
    if not target_db.exists():
        logger.error(f"Target database not found: {target_db}")
        return
    
    logger.info("🚀 Starting comprehensive units backfill from ALL sources...")
    
    # Collect units mappings from all sources
    all_units_mappings = {}
    sources_used = []
    
    # 1. Excel files
    excel_files = list(uploads_dir.glob('*.xlsx'))
    logger.info(f"Found {len(excel_files)} Excel files")
    
    for excel_file in excel_files:
        if excel_file.name.startswith('~') or 'test' in excel_file.name.lower():
            continue  # Skip temp files and test files
            
        units_mapping = extract_units_from_excel(excel_file)
        if units_mapping:
            all_units_mappings.update(units_mapping)
            sources_used.append(f"Excel: {excel_file.name}")
    
    # 2. Other databases
    db_files = list(uploads_dir.glob('product_database*.db'))
    logger.info(f"Found {len(db_files)} database files")
    
    for db_file in db_files:
        if db_file.name == target_db.name:
            continue  # Skip the target database
        if 'shm' in db_file.name or 'wal' in db_file.name:
            continue  # Skip SQLite temp files
            
        units_mapping = extract_units_from_database(db_file)
        if units_mapping:
            all_units_mappings.update(units_mapping)
            sources_used.append(f"Database: {db_file.name}")
    
    logger.info(f"📊 Collected {len(all_units_mappings)} total mappings from {len(sources_used)} sources")
    logger.info("Sources used:")
    for source in sources_used:
        logger.info(f"  - {source}")
    
    # 3. Get products that still need units
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, "Product Name*", normalized_name, Units, "Product Type*"
        FROM products 
        WHERE Units = 'each' OR Units = '' OR Units IS NULL
    ''')
    
    products_to_update = cursor.fetchall()
    logger.info(f"🎯 Found {len(products_to_update)} products that need units")
    
    # 4. Update products with mappings or inferred units
    updated_count = 0
    inferred_count = 0
    no_change_count = 0
    
    for product_id, product_name, normalized_name, current_units, product_type in products_to_update:
        new_units = None
        method = None
        
        # Try exact mapping first
        if normalized_name and normalized_name in all_units_mappings:
            new_units = all_units_mappings[normalized_name]
            method = "mapping"
        else:
            # Try alternative normalization
            alt_normalized = normalize_product_name(product_name)
            if alt_normalized in all_units_mappings:
                new_units = all_units_mappings[alt_normalized]
                method = "alt_mapping"
        
        # If no mapping found, try inference
        if not new_units or new_units == 'each':
            inferred_units = infer_units_from_product_name(product_name, product_type or "")
            if inferred_units and inferred_units != 'each':
                new_units = inferred_units
                method = "inference"
                inferred_count += 1
        
        # Update if we found better units
        if new_units and new_units != current_units:
            cursor.execute('''
                UPDATE products 
                SET Units = ?, updated_at = ?
                WHERE id = ?
            ''', (new_units, datetime.now().isoformat(), product_id))
            
            updated_count += 1
            if updated_count <= 20:  # Show first 20 updates
                logger.info(f"Updated ({method}): '{product_name}' -> {new_units}")
            elif updated_count == 21:
                logger.info("... (showing first 20 updates)")
        else:
            no_change_count += 1
    
    conn.commit()
    
    # 5. Show final statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN Units = 'each' THEN 1 END) as each_units,
            COUNT(CASE WHEN Units = 'g' THEN 1 END) as gram_units,
            COUNT(CASE WHEN Units = 'oz' THEN 1 END) as ounce_units,
            COUNT(CASE WHEN Units = 'mg' THEN 1 END) as mg_units,
            COUNT(CASE WHEN Units = 'ml' THEN 1 END) as ml_units,
            COUNT(CASE WHEN Units NOT IN ('each', 'g', 'oz', 'mg', 'ml') THEN 1 END) as other_units
        FROM products
    ''')
    
    stats = cursor.fetchone()
    conn.close()
    
    logger.info("🎉 Comprehensive backfill complete!")
    logger.info(f"📈 Updated {updated_count} products ({inferred_count} from inference)")
    logger.info(f"📊 Final units distribution:")
    logger.info(f"   - each: {stats[1]}")
    logger.info(f"   - g: {stats[2]}")
    logger.info(f"   - oz: {stats[3]}")
    logger.info(f"   - mg: {stats[4]}")
    logger.info(f"   - ml: {stats[5]}")
    logger.info(f"   - other: {stats[6]}")
    logger.info(f"   - total: {stats[0]}")

if __name__ == '__main__':
    main()