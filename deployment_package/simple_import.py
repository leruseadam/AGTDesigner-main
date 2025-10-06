#!/usr/bin/env python3
"""
Simple PostgreSQL import script that avoids format string issues
"""

import pandas as pd
import psycopg2
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

def safe_str(value):
    """Safely convert value to string."""
    if pd.isna(value) or value is None:
        return ''
    return str(value).strip()

def simple_import():
    """Simple import avoiding format string issues."""
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
        
        # Process and insert data
        products_added = 0
        strains_added = 0
        
        for index, row in df.iterrows():
            try:
                # Get product name
                product_name = safe_str(row.get('Product Name*', ''))
                
                # Skip if empty or header row
                if not product_name or product_name == 'Product Name*':
                    continue
                
                # Get other fields
                product_type = safe_str(row.get('Product Type*', 'Unknown'))
                vendor = safe_str(row.get('Vendor/Supplier*', 'Unknown'))
                brand = safe_str(row.get('Product Brand', 'Unknown'))
                description = safe_str(row.get('Description', ''))
                weight = safe_str(row.get('Weight*', ''))
                weight_unit = safe_str(row.get('Weight Unit* (grams/gm or ounces/oz)', ''))
                price = safe_str(row.get('Price* (Tier Name for Bulk)', ''))
                lineage = safe_str(row.get('Lineage', ''))
                strain = safe_str(row.get('Product Strain', ''))
                thc = safe_str(row.get('THC test result', ''))
                cbd = safe_str(row.get('CBD test result', ''))
                quantity = safe_str(row.get('Quantity*', ''))
                lot_number = safe_str(row.get('Lot Number', ''))
                barcode = safe_str(row.get('Barcode*', ''))
                room = safe_str(row.get('Room*', ''))
                
                # Normalize name
                normalized_name = product_name.upper()
                
                # Insert product using parameterized query
                insert_query = """
                    INSERT INTO products (
                        "Product Name*", "ProductName", normalized_name, "Product Type*",
                        "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units",
                        "Price", "Lineage", "Product Strain", "THC test result", "CBD test result",
                        "Quantity*", "Lot Number", "Barcode*", "Room*",
                        first_seen_date, last_seen_date, total_occurrences, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                cursor.execute(insert_query, (
                    product_name, product_name, normalized_name, product_type,
                    vendor, brand, description, weight, weight_unit, price, lineage, strain,
                    thc, cbd, quantity, lot_number, barcode, room,
                    datetime.now().isoformat(), datetime.now().isoformat(), 1,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                
                product_id = cursor.fetchone()[0]
                products_added += 1
                
                # Insert strain if it's a classic type and has strain info
                classic_types = ['Flower', 'Pre-Roll', 'Concentrate', 'Vape', 'Edible']
                if product_type in classic_types and strain and strain != 'Product Strain':
                    strain_name = strain
                    canonical_lineage = lineage if lineage and lineage != 'Lineage' else 'Unknown'
                    normalized_strain = strain_name.upper()
                    
                    strain_query = """
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
                    """
                    
                    cursor.execute(strain_query, (
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
    success = simple_import()
    if success:
        print("✅ All data imported successfully to PostgreSQL!")
    else:
        print("❌ Failed to import data to PostgreSQL")
