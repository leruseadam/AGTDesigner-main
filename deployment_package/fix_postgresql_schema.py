#!/usr/bin/env python3
"""
Fix PostgreSQL database schema by adding missing columns
"""

import psycopg2
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Add missing columns to PostgreSQL database."""
    
    # PostgreSQL connection config
    config = {
        'host': os.getenv('DB_HOST', 'adamcordova-4822.postgres.pythonanywhere-services.com'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'super'),
        'password': os.getenv('DB_PASSWORD', '193154life'),
        'port': os.getenv('DB_PORT', '14822'),
        'connect_timeout': 60,
        'application_name': 'SchemaFix'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        cursor = conn.cursor()
        
        logger.info("Connected to PostgreSQL database")
        
        # Check if strain_id column exists in products table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' AND column_name = 'strain_id'
        """)
        
        if not cursor.fetchone():
            logger.info("Adding strain_id column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN strain_id INTEGER REFERENCES strains(id)
            """)
            logger.info("✓ Added strain_id column to products table")
        else:
            logger.info("✓ strain_id column already exists in products table")
        
        # Check if lineage column exists in strains table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'strains' AND column_name = 'lineage'
        """)
        
        if not cursor.fetchone():
            logger.info("Adding lineage column to strains table...")
            cursor.execute("""
                ALTER TABLE strains 
                ADD COLUMN lineage TEXT
            """)
            logger.info("✓ Added lineage column to strains table")
        else:
            logger.info("✓ lineage column already exists in strains table")
        
        # Check if sovereign_lineage column exists in strains table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'strains' AND column_name = 'sovereign_lineage'
        """)
        
        if not cursor.fetchone():
            logger.info("Adding sovereign_lineage column to strains table...")
            cursor.execute("""
                ALTER TABLE strains 
                ADD COLUMN sovereign_lineage TEXT
            """)
            logger.info("✓ Added sovereign_lineage column to strains table")
        else:
            logger.info("✓ sovereign_lineage column already exists in strains table")
        
        # Commit changes
        conn.commit()
        logger.info("✓ Database schema updated successfully!")
        
        # Verify the schema
        logger.info("\nVerifying database schema...")
        
        # Check products table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position
        """)
        
        logger.info("Products table columns:")
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
        
        # Check strains table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'strains'
            ORDER BY ordinal_position
        """)
        
        logger.info("\nStrains table columns:")
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_database_schema()
