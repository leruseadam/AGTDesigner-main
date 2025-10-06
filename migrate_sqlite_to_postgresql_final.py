#!/usr/bin/env python3
"""
Final migration script to transfer all products from SQLite to PostgreSQL
Handles exact column differences between SQLite and PostgreSQL schemas
"""
import sqlite3
import psycopg2
import os
import sys
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

def resolve_sqlite_path() -> str:
    """Resolve the SQLite path from CLI arg, env, or sensible defaults on PythonAnywhere."""
    # CLI argument: --sqlite PATH
    sqlite_path = None
    argv = sys.argv
    for i, a in enumerate(argv):
        if a == '--sqlite' and i + 1 < len(argv):
            sqlite_path = argv[i + 1]
            break
    # Environment override
    if not sqlite_path:
        sqlite_path = os.environ.get('SQLITE_PATH')
    # Defaults: look in uploads/ within current project
    if not sqlite_path:
        candidate1 = os.path.join(os.getcwd(), 'uploads', 'product_database_AGT_Bothell.db')
        candidate2 = os.path.join(os.getcwd(), 'uploads', 'product_database.db')
        if os.path.exists(candidate1):
            sqlite_path = candidate1
        elif os.path.exists(candidate2):
            sqlite_path = candidate2
    return sqlite_path or ''


def migrate_products():
    """Migrate all products from SQLite to PostgreSQL"""
    
    # SQLite database path
    sqlite_path = resolve_sqlite_path()
    
    if not sqlite_path or not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path or '(empty)'}")
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
        # Get SQLite column names
        sqlite_cursor.execute("PRAGMA table_info(products)")
        sqlite_columns_info = sqlite_cursor.fetchall()
        sqlite_column_names = [col[1] for col in sqlite_columns_info]
        
        # Get PostgreSQL column names
        pg_cursor.execute('''
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            ORDER BY ordinal_position
        ''')
        pg_column_names = [row[0] for row in pg_cursor.fetchall()]
        
        logger.info(f"SQLite columns: {len(sqlite_column_names)}")
        logger.info(f"PostgreSQL columns: {len(pg_column_names)}")
        
        # Define column mapping (SQLite -> PostgreSQL)
        # Exclude columns that don't exist in PostgreSQL
        excluded_columns = ['CombinedWeight', 'Ratio_or_THC_CBD', 'Description_Complexity', 'Weight Unit* (grams/gm or ounces/oz)']
        
        # Get common columns (excluding 'id' which is auto-generated in PostgreSQL)
        common_columns = [col for col in sqlite_column_names if col in pg_column_names and col != 'id' and col not in excluded_columns]
        
        logger.info(f"Common columns to migrate: {len(common_columns)}")
        logger.info(f"Excluded columns: {excluded_columns}")
        
        # Get total count
        sqlite_cursor.execute("SELECT COUNT(*) FROM products")
        total_products = sqlite_cursor.fetchone()[0]
        logger.info(f"Found {total_products} products in SQLite database")
        
        # Get all products from SQLite
        sqlite_cursor.execute("SELECT * FROM products")
        products = sqlite_cursor.fetchall()
        
        # Prepare PostgreSQL INSERT statement
        placeholders = ', '.join(['%s'] * len(common_columns))
        
        insert_sql = f"""
        INSERT INTO products ({', '.join([f'"{col}"' for col in common_columns])})
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
            "Total THC" = EXCLUDED."Total THC",
            "THCA" = EXCLUDED."THCA",
            "CBDA" = EXCLUDED."CBDA",
            "CBN" = EXCLUDED."CBN",
            "normalized_name" = EXCLUDED."normalized_name",
            "total_occurrences" = EXCLUDED."total_occurrences",
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
                    product_dict = dict(zip(sqlite_column_names, product))
                    
                    # Prepare values for common columns only
                    values = []
                    for col in common_columns:
                        value = product_dict.get(col, None)
                        
                        # Handle special cases for NOT NULL columns
                        if col == 'normalized_name' and not value:
                            value = product_dict.get('Product Name*', '').lower().strip()
                        elif col in ['first_seen_date', 'last_seen_date', 'created_at', 'updated_at'] and not value:
                            value = datetime.now().isoformat()
                        
                        values.append(value)
                    
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
    logger.info("Starting final SQLite to PostgreSQL migration...")
    success = migrate_products()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        exit(1)
