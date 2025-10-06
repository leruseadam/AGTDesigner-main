#!/usr/bin/env python3
"""
Migration script to transfer all products from SQLite to PostgreSQL
"""
import sqlite3
import psycopg2
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_postgresql_config():
    """Get PostgreSQL connection configuration"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'agt_designer'),
        'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }

def migrate_products():
    """Migrate all products from SQLite to PostgreSQL"""
    
    # SQLite database path
    sqlite_path = '/Users/adamcordova/Desktop/labelMaker_ QR copy/uploads/product_database_AGT_Bothell.db'
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        return False
    
    # Connect to SQLite
    logger.info("Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    logger.info("Connecting to PostgreSQL database...")
    pg_config = get_postgresql_config()
    pg_conn = psycopg2.connect(**pg_config)
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get total count
        sqlite_cursor.execute("SELECT COUNT(*) FROM products")
        total_products = sqlite_cursor.fetchone()[0]
        logger.info(f"Found {total_products} products in SQLite database")
        
        # Get all products from SQLite
        sqlite_cursor.execute("SELECT * FROM products")
        products = sqlite_cursor.fetchall()
        
        # Get column names
        sqlite_cursor.execute("PRAGMA table_info(products)")
        columns_info = sqlite_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        logger.info(f"Column names: {column_names}")
        
        # Prepare PostgreSQL INSERT statement
        # Remove 'id' column as it's auto-generated in PostgreSQL
        pg_columns = [col for col in column_names if col != 'id']
        placeholders = ', '.join(['%s'] * len(pg_columns))
        
        insert_sql = f"""
        INSERT INTO products ({', '.join([f'"{col}"' for col in pg_columns])})
        VALUES ({placeholders})
        ON CONFLICT ("Product Name*", "Vendor/Supplier*") 
        DO UPDATE SET
            "Product Type*" = EXCLUDED."Product Type*",
            "Product Brand" = EXCLUDED."Product Brand",
            "Product Strain" = EXCLUDED."Product Strain",
            "Lineage" = EXCLUDED."Lineage",
            "Description" = EXCLUDED."Description",
            "Weight*" = EXCLUDED."Weight*",
            "Units" = EXCLUDED."Units",
            "Price" = EXCLUDED."Price",
            "Quantity*" = EXCLUDED."Quantity*",
            "DOH" = EXCLUDED."DOH",
            "Concentrate Type" = EXCLUDED."Concentrate Type",
            "Ratio" = EXCLUDED."Ratio",
            "JointRatio" = EXCLUDED."JointRatio",
            "State" = EXCLUDED."State",
            "Is Sample? (yes/no)" = EXCLUDED."Is Sample? (yes/no)",
            "Is MJ product?(yes/no)" = EXCLUDED."Is MJ product?(yes/no)",
            "Discountable? (yes/no)" = EXCLUDED."Discountable? (yes/no)",
            "Room*" = EXCLUDED."Room*",
            "Batch Number" = EXCLUDED."Batch Number",
            "Lot Number" = EXCLUDED."Lot Number",
            "Barcode*" = EXCLUDED."Barcode*",
            "Medical Only (Yes/No)" = EXCLUDED."Medical Only (Yes/No)",
            "Med Price" = EXCLUDED."Med Price",
            "Expiration Date(YYYY-MM-DD)" = EXCLUDED."Expiration Date(YYYY-MM-DD)",
            "Is Archived? (yes/no)" = EXCLUDED."Is Archived? (yes/no)",
            "THC Per Serving" = EXCLUDED."THC Per Serving",
            "Allergens" = EXCLUDED."Allergens",
            "Solvent" = EXCLUDED."Solvent",
            "Accepted Date" = EXCLUDED."Accepted Date",
            "Internal Product Identifier" = EXCLUDED."Internal Product Identifier",
            "Product Tags (comma separated)" = EXCLUDED."Product Tags (comma separated)",
            "Image URL" = EXCLUDED."Image URL",
            "Ingredients" = EXCLUDED."Ingredients",
            "CombinedWeight" = EXCLUDED."CombinedWeight",
            "Ratio_or_THC_CBD" = EXCLUDED."Ratio_or_THC_CBD",
            "Description_Complexity" = EXCLUDED."Description_Complexity",
            "Total THC" = EXCLUDED."Total THC",
            "THCA" = EXCLUDED."THCA",
            "CBDA" = EXCLUDED."CBDA",
            "CBN" = EXCLUDED."CBN",
            "normalized_name" = EXCLUDED."normalized_name",
            "total_occurrences" = EXCLUDED."total_occurrences",
            "Weight Unit* (grams/gm or ounces/oz)" = EXCLUDED."Weight Unit* (grams/gm or ounces/oz)",
            "first_seen_date" = EXCLUDED."first_seen_date",
            "last_seen_date" = EXCLUDED."last_seen_date",
            "created_at" = EXCLUDED."created_at",
            "updated_at" = EXCLUDED."updated_at",
            "Test result unit (% or mg)" = EXCLUDED."Test result unit (% or mg)",
            "THC" = EXCLUDED."THC",
            "CBD" = EXCLUDED."CBD",
            "Total CBD" = EXCLUDED."Total CBD",
            "CBGA" = EXCLUDED."CBGA",
            "CBG" = EXCLUDED."CBG",
            "Total CBG" = EXCLUDED."Total CBG",
            "CBC" = EXCLUDED."CBC",
            "CBDV" = EXCLUDED."CBDV",
            "THCV" = EXCLUDED."THCV",
            "CBGV" = EXCLUDED."CBGV",
            "CBNV" = EXCLUDED."CBNV",
            "CBGVA" = EXCLUDED."CBGVA",
            "strain_id" = EXCLUDED."strain_id"
        """
        
        # Process products in batches
        batch_size = 100
        successful_inserts = 0
        failed_inserts = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            
            for product in batch:
                try:
                    # Convert product tuple to dict
                    product_dict = dict(zip(column_names, product))
                    
                    # Remove 'id' field as it's auto-generated
                    if 'id' in product_dict:
                        del product_dict['id']
                    
                    # Prepare values in the correct order
                    values = [product_dict.get(col, None) for col in pg_columns]
                    
                    # Execute insert
                    pg_cursor.execute(insert_sql, values)
                    successful_inserts += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert product '{product_dict.get('Product Name*', 'Unknown')}': {e}")
                    failed_inserts += 1
                    continue
            
            # Commit batch
            pg_conn.commit()
            logger.info(f"Batch committed. Success: {successful_inserts}, Failed: {failed_inserts}")
        
        logger.info(f"Migration completed!")
        logger.info(f"Successfully migrated: {successful_inserts} products")
        logger.info(f"Failed migrations: {failed_inserts} products")
        
        # Verify final count
        pg_cursor.execute("SELECT COUNT(*) FROM products")
        final_count = pg_cursor.fetchone()[0]
        logger.info(f"Final PostgreSQL product count: {final_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        pg_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    logger.info("Starting SQLite to PostgreSQL migration...")
    success = migrate_products()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        exit(1)
