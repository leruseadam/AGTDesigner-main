#!/usr/bin/env python3
"""
Simple PostgreSQL import script with better error handling
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

def simple_import():
    """Simple import with better error handling."""
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
        
        # Process and insert data in smaller batches
        products_added = 0
        strains_added = 0
        batch_size = 10
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            try:
                for index, row in batch_df.iterrows():
                    try:
                        # Get product name
                        product_name = (row.get('Product Name*', '') or 
                                      row.get('ProductName', '') or 
                                      row.get('Product Name', ''))
                        
                        # Skip empty products
                        if not product_name or str(product_name).strip() == '' or str(product_name).strip().lower() == 'nan':
                            continue
                        
                        normalized_name = normalize_name(product_name)
                        product_type = row.get('Product Type*', 'Unknown')
                        vendor = row.get('Vendor/Supplier*', 'Unknown')
                        brand = row.get('Product Brand', 'Unknown')
                        description = row.get('Description', '')
                        weight = row.get('Weight*', '')
                        units = row.get('Units', '')
                        price = row.get('Price', '')
                        lineage = row.get('Lineage', '')
                        strain = row.get('Product Strain', '')
                        
                        # Insert product
                        cursor.execute("""
                            INSERT INTO products (
                                "Product Name*", "ProductName", normalized_name, "Product Type*",
                                "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units",
                                "Price", "Lineage", "Product Strain", first_seen_date, last_seen_date,
                                total_occurrences, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            product_name, product_name, normalized_name, product_type,
                            vendor, brand, description, weight, units, price, lineage, strain,
                            datetime.now().isoformat(), datetime.now().isoformat(), 1,
                            datetime.now().isoformat(), datetime.now().isoformat()
                        ))
                        
                        product_id = cursor.fetchone()[0]
                        products_added += 1
                        
                        # Insert strain if it's a classic type
                        classic_types = ['Flower', 'Pre-Roll', 'Concentrate', 'Vape', 'Edible']
                        if product_type in classic_types and strain and str(strain).strip():
                            strain_name = str(strain).strip()
                            canonical_lineage = lineage if lineage else 'Unknown'
                            
                            cursor.execute("""
                                INSERT INTO strains (
                                    strain_name, canonical_lineage, first_seen_date, last_seen_date,
                                    total_occurrences, created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (strain_name) 
                                DO UPDATE SET 
                                    last_seen_date = EXCLUDED.last_seen_date,
                                    total_occurrences = strains.total_occurrences + 1,
                                    updated_at = EXCLUDED.updated_at
                                RETURNING id
                            """, (
                                strain_name, canonical_lineage, datetime.now().isoformat(),
                                datetime.now().isoformat(), 1, datetime.now().isoformat(),
                                datetime.now().isoformat()
                            ))
                            
                            strain_id = cursor.fetchone()[0]
                            strains_added += 1
                            
                            # Update product with strain_id
                            cursor.execute("UPDATE products SET strain_id = %s WHERE id = %s", (strain_id, product_id))
                        
                    except Exception as e:
                        logger.error(f"Error processing row {index}: {e}")
                        continue
                
                # Commit batch
                conn.commit()
                logger.info(f"Processed batch {i//batch_size + 1}, total products: {products_added}")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                conn.rollback()
                continue
        
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
        print("✅ Data imported successfully to PostgreSQL!")
    else:
        print("❌ Failed to import data to PostgreSQL")
