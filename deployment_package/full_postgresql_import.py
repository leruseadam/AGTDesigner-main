#!/usr/bin/env python3
"""
Full PostgreSQL import script for all products
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgresql_config():
    """Get PostgreSQL connection config."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'agt_designer'),
        'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }

def normalize_name(name):
    """Normalize product name for database storage."""
    if not name or pd.isna(name):
        return ''
    return str(name).strip().upper()

def full_import():
    """Import all products from Excel to PostgreSQL."""
    try:
        # Connect to PostgreSQL
        config = get_postgresql_config()
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        logger.info("Connected to PostgreSQL database")
        
        # Read Excel file
        excel_file = "uploads/A Greener Today - Bothell_inventory_09-26-2025  4_51 PM.xlsx"
        if not os.path.exists(excel_file):
            logger.error(f"Excel file not found: {excel_file}")
            return False
            
        logger.info(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file)
        logger.info(f"Loaded {len(df)} rows from Excel file")
        
        # Clear existing data
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM strains")
        conn.commit()
        logger.info("Cleared existing data from database")
        
        # Process and insert ALL data
        products_added = 0
        strains_added = 0
        
        for index, row in df.iterrows():
            try:
                # Get product name - use Product Name* column
                product_name = row.get('Product Name*', '')
                
                # Skip only if completely empty or header row
                if not product_name or str(product_name).strip() == '' or str(product_name).strip() == 'Product Name*':
                    continue
                
                # Clean up the product name
                product_name = str(product_name).strip()
                normalized_name = normalize_name(product_name)
                
                # Get other fields
                product_type = row.get('Product Type*', 'Unknown')
                vendor = row.get('Vendor/Supplier*', 'Unknown')
                brand = row.get('Product Brand', 'Unknown')
                description = row.get('Description', '')
                weight = row.get('Weight*', '')
                weight_unit = row.get('Weight Unit* (grams/gm or ounces/oz)', '')
                price = row.get('Price* (Tier Name for Bulk)', '')
                cost = row.get('Cost*', '')
                lineage = row.get('Lineage', '')
                strain = row.get('Product Strain', '')
                thc = row.get('THC test result', '')
                cbd = row.get('CBD test result', '')
                quantity = row.get('Quantity*', '')
                lot_number = row.get('Lot Number', '')
                barcode = row.get('Barcode*', '')
                room = row.get('Room*', '')
                
                # Insert product
                cursor.execute("""
                    INSERT INTO products (
                        "Product Name*", "ProductName", normalized_name, "Product Type*",
                        "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units",
                        "Price", "Cost", "Lineage", "Product Strain", "THC test result", "CBD test result",
                        "Quantity*", "Lot Number", "Barcode*", "Room*", first_seen_date, last_seen_date,
                        total_occurrences, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    product_name, product_name, normalized_name, product_type,
                    vendor, brand, description, weight, weight_unit, price, cost, lineage, strain,
                    thc, cbd, quantity, lot_number, barcode, room,
                    datetime.now().isoformat(), datetime.now().isoformat(), 1,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                
                product_id = cursor.fetchone()[0]
                products_added += 1
                
                # Insert strain if it's a classic type and has strain info
                classic_types = ['Flower', 'Pre-Roll', 'Concentrate', 'Vape', 'Edible']
                if product_type in classic_types and strain and str(strain).strip() and str(strain).strip() != 'Product Strain':
                    strain_name = str(strain).strip()
                    canonical_lineage = lineage if lineage and str(lineage).strip() != 'Lineage' else 'Unknown'
                    
                    # Normalize strain name
                    normalized_strain = normalize_name(strain_name)
                    
                    cursor.execute("""
                        INSERT INTO strains (
                            strain_name, normalized_name, canonical_lineage, first_seen_date, last_seen_date,
                            total_occurrences, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (strain_name) 
                        DO UPDATE SET 
                            last_seen_date = EXCLUDED.last_seen_date,
                            total_occurrences = strains.total_occurrences + 1,
                            updated_at = EXCLUDED.updated_at
                        RETURNING id
                    """, (
                        strain_name, normalized_strain, canonical_lineage, datetime.now().isoformat(),
                        datetime.now().isoformat(), 1, datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    strain_id = cursor.fetchone()[0]
                    strains_added += 1
                    
                    # Update product with strain_id
                    cursor.execute("UPDATE products SET strain_id = %s WHERE id = %s", (strain_id, product_id))
                
                # Commit every 100 products
                if products_added % 100 == 0:
                    conn.commit()
                    logger.info(f"Processed {products_added} products...")
                    
            except Exception as e:
                logger.error(f"Error processing row {index}: {e}")
                conn.rollback()
                continue
        
        # Final commit
        conn.commit()
        conn.close()
        
        logger.info(f"Import completed successfully!")
        logger.info(f"Products added: {products_added}")
        logger.info(f"Strains added: {strains_added}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        return False

if __name__ == "__main__":
    success = full_import()
    if success:
        print("✅ All data imported successfully to PostgreSQL!")
    else:
        print("❌ Failed to import data to PostgreSQL")
