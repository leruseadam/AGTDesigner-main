#!/usr/bin/env python3
"""
Corrected PostgreSQL import script using only existing columns
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

def corrected_import():
    """Import all products using only existing columns."""
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
                
                # Get other fields that exist in the database
                product_type = row.get('Product Type*', 'Unknown')
                vendor = row.get('Vendor/Supplier*', 'Unknown')
                brand = row.get('Product Brand', 'Unknown')
                description = row.get('Description', '')
                weight = row.get('Weight*', '')
                weight_unit = row.get('Weight Unit* (grams/gm or ounces/oz)', '')
                price = row.get('Price* (Tier Name for Bulk)', '')
                lineage = row.get('Lineage', '')
                strain = row.get('Product Strain', '')
                thc = row.get('THC test result', '')
                cbd = row.get('CBD test result', '')
                quantity = row.get('Quantity*', '')
                lot_number = row.get('Lot Number', '')
                barcode = row.get('Barcode*', '')
                room = row.get('Room*', '')
                concentrate_type = row.get('Concentrate Type', '')
                test_unit = row.get('Test result unit (% or mg)', '')
                state = row.get('State', '')
                is_sample = row.get('Is Sample? (yes/no)', '')
                is_mj = row.get('Is MJ product?(yes/no)', '')
                discountable = row.get('Discountable? (yes/no)', '')
                batch_number = row.get('Batch Number', '')
                medical_only = row.get('Medical Only (Yes/No)', '')
                med_price = row.get('Med Price', '')
                expiration = row.get('Expiration Date(YYYY-MM-DD)', '')
                is_archived = row.get('Is Archived? (yes/no)', '')
                thc_per_serving = row.get('THC Per Serving', '')
                allergens = row.get('Allergens', '')
                solvent = row.get('Solvent', '')
                accepted_date = row.get('Accepted Date', '')
                internal_id = row.get('Internal Product Identifier', '')
                product_tags = row.get('Product Tags (comma separated)', '')
                image_url = row.get('Image URL', '')
                ingredients = row.get('Ingredients', '')
                total_thc = row.get('Total THC', '')
                thca = row.get('THCA', '')
                cbda = row.get('CBDA', '')
                cbn = row.get('CBN', '')
                
                # Insert product using only existing columns
                cursor.execute("""
                    INSERT INTO products (
                        "Product Name*", "ProductName", normalized_name, "Product Type*",
                        "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units",
                        "Price", "Lineage", "Product Strain", "THC test result", "CBD test result",
                        "Quantity*", "Lot Number", "Barcode*", "Room*", "Concentrate Type",
                        "Test result unit (% or mg)", "State", "Is Sample? (yes/no)", 
                        "Is MJ product?(yes/no)", "Discountable? (yes/no)", "Batch Number",
                        "Medical Only (Yes/No)", "Med Price", "Expiration Date(YYYY-MM-DD)",
                        "Is Archived? (yes/no)", "THC Per Serving", "Allergens", "Solvent",
                        "Accepted Date", "Internal Product Identifier", "Product Tags (comma separated)",
                        "Image URL", "Ingredients", "Total THC", "THCA", "CBDA", "CBN",
                        first_seen_date, last_seen_date, total_occurrences, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    product_name, product_name, normalized_name, product_type,
                    vendor, brand, description, weight, weight_unit, price, lineage, strain,
                    thc, cbd, quantity, lot_number, barcode, room, concentrate_type,
                    test_unit, state, is_sample, is_mj, discountable, batch_number,
                    medical_only, med_price, expiration, is_archived, thc_per_serving,
                    allergens, solvent, accepted_date, internal_id, product_tags,
                    image_url, ingredients, total_thc, thca, cbda, cbn,
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
    success = corrected_import()
    if success:
        print("✅ All data imported successfully to PostgreSQL!")
    else:
        print("❌ Failed to import data to PostgreSQL")
