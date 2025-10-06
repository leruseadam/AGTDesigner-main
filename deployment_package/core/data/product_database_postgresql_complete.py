#!/usr/bin/env python3
"""
Complete PostgreSQL ProductDatabase implementation
Includes all methods from SQLite version adapted for PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import json
from .field_mapping import get_canonical_field

logger = logging.getLogger(__name__)

def get_database_config(store_name=None):
    """Get PostgreSQL connection config."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'agt_designer'),
        'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }

def timed_operation(operation_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                return func(self, *args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                if elapsed > 0.1:
                    logger.warning(f"⏱️  {operation_name}: {elapsed:.3f}s")
        return wrapper
    return decorator

def retry_on_lock(max_retries=3, delay=0.5):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except psycopg2.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    raise
            return None
        return wrapper
    return decorator

class ProductDatabase:
    """PostgreSQL database for storing and managing product and strain information."""
    
    def __init__(self, store_name: str = None):
        self.store_name = store_name or 'AGT_Bothell'
        self.config = get_database_config(store_name)
        self._connection_pool = {}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._initialized = False
        self._init_lock = threading.Lock()
        self._write_lock = threading.RLock()
        
        # Performance timing
        self._timing_stats = {
            'queries': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _get_connection(self):
        """Get a PostgreSQL connection, reusing if possible."""
        thread_id = threading.get_ident()
        if thread_id not in self._connection_pool:
            try:
                conn = psycopg2.connect(**self.config)
                conn.autocommit = False
                self._connection_pool[thread_id] = conn
            except psycopg2.OperationalError as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                return None
        return self._connection_pool[thread_id]
    
    def init_database(self):
        """Initialize the database with required tables."""
        if self._initialized:
            return True
            
        with self._init_lock:
            if self._initialized:
                return True
                
            try:
                conn = self._get_connection()
                if not conn:
                    return False
                    
                cursor = conn.cursor()
                
                # Create products table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        "Product Name*" TEXT NOT NULL,
                        "ProductName" TEXT,
                        normalized_name TEXT NOT NULL,
                        strain_id INTEGER,
                        "Product Type*" TEXT NOT NULL,
                        "Vendor/Supplier*" TEXT,
                        "Product Brand" TEXT,
                        "Description" TEXT,
                        "Weight*" TEXT,
                        "Units" TEXT,
                        "Price" TEXT,
                        "Lineage" TEXT,
                        first_seen_date TEXT NOT NULL,
                        last_seen_date TEXT NOT NULL,
                        total_occurrences INTEGER DEFAULT 1,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        "Product Strain" TEXT,
                        "Quantity*" TEXT,
                        "DOH" TEXT,
                        "Concentrate Type" TEXT,
                        "Ratio" TEXT,
                        "JointRatio" TEXT,
                        "THC test result" TEXT,
                        "CBD test result" TEXT,
                        "Test result unit (% or mg)" TEXT,
                        "State" TEXT,
                        "Is Sample? (yes/no)" TEXT,
                        "Is MJ product?(yes/no)" TEXT,
                        "Discountable? (yes/no)" TEXT,
                        "Room*" TEXT,
                        "Batch Number" TEXT,
                        "Lot Number" TEXT,
                        "Barcode*" TEXT,
                        "Medical Only (Yes/No)" TEXT,
                        "Med Price" TEXT,
                        "Expiration Date(YYYY-MM-DD)" TEXT,
                        "Is Archived? (yes/no)" TEXT,
                        "THC Per Serving" TEXT,
                        "Allergens" TEXT,
                        "Solvent" TEXT,
                        "Accepted Date" TEXT,
                        "Internal Product Identifier" TEXT,
                        "Product Tags (comma separated)" TEXT,
                        "Image URL" TEXT,
                        "Ingredients" TEXT,
                        "Total THC" TEXT,
                        "THCA" TEXT,
                        "CBDA" TEXT,
                        "CBN" TEXT,
                        "THC" TEXT,
                        "CBD" TEXT,
                        "Total CBD" TEXT,
                        "CBGA" TEXT,
                        "CBG" TEXT,
                        "Total CBG" TEXT,
                        "CBC" TEXT,
                        "CBDV" TEXT,
                        "THCV" TEXT,
                        "CBGV" TEXT,
                        "CBNV" TEXT,
                        "CBGVA" TEXT
                    )
                """)
                
                # Create strains table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strains (
                        id SERIAL PRIMARY KEY,
                        strain_name TEXT NOT NULL,
                        normalized_name TEXT NOT NULL,
                        canonical_lineage TEXT,
                        first_seen_date TEXT,
                        last_seen_date TEXT,
                        total_occurrences INTEGER DEFAULT 1,
                        sovereign_lineage TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                self._initialized = True
                logger.info(f"PostgreSQL database initialized for store '{self.store_name}'")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL database: {e}")
                return False
    
    @timed_operation("add_or_update_product")
    @retry_on_lock(max_retries=3, delay=0.5)
    def add_or_update_product(self, product_data: Dict[str, Any]) -> int:
        """Add or update a product in the database."""
        conn = self._get_connection()
        if not conn:
            raise Exception("No database connection available")
            
        cursor = conn.cursor()
        
        try:
            # Extract required fields
            product_name = product_data.get('Product Name*', '')
            normalized_name = product_data.get('normalized_name', '')
            product_type = product_data.get('Product Type*', '')
            
            if not product_name or not normalized_name or not product_type:
                raise ValueError("Missing required fields: Product Name*, normalized_name, or Product Type*")
            
            current_time = datetime.now().isoformat()
            
            # Check if product exists
            cursor.execute('''
                SELECT id FROM products WHERE normalized_name = %s
            ''', (normalized_name,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing product
                product_id = existing[0]
                cursor.execute('''
                    UPDATE products SET
                        "Product Name*" = %s,
                        "ProductName" = %s,
                        "Product Type*" = %s,
                        "Vendor/Supplier*" = %s,
                        "Product Brand" = %s,
                        "Description" = %s,
                        "Weight*" = %s,
                        "Units" = %s,
                        "Price" = %s,
                        "Lineage" = %s,
                        last_seen_date = %s,
                        total_occurrences = total_occurrences + 1,
                        updated_at = %s,
                        "Product Strain" = %s,
                        "Quantity*" = %s,
                        "DOH" = %s,
                        "Concentrate Type" = %s,
                        "Ratio" = %s,
                        "JointRatio" = %s,
                        "THC test result" = %s,
                        "CBD test result" = %s,
                        "Test result unit (% or mg)" = %s,
                        "State" = %s,
                        "Is Sample? (yes/no)" = %s,
                        "Is MJ product?(yes/no)" = %s,
                        "Discountable? (yes/no)" = %s,
                        "Room*" = %s,
                        "Batch Number" = %s,
                        "Lot Number" = %s,
                        "Barcode*" = %s,
                        "Medical Only (Yes/No)" = %s,
                        "Med Price" = %s,
                        "Expiration Date(YYYY-MM-DD)" = %s,
                        "Is Archived? (yes/no)" = %s,
                        "THC Per Serving" = %s,
                        "Allergens" = %s,
                        "Solvent" = %s,
                        "Accepted Date" = %s,
                        "Internal Product Identifier" = %s,
                        "Product Tags (comma separated)" = %s,
                        "Image URL" = %s,
                        "Ingredients" = %s,
                        "Total THC" = %s,
                        "THCA" = %s,
                        "CBDA" = %s,
                        "CBN" = %s,
                        "THC" = %s,
                        "CBD" = %s,
                        "Total CBD" = %s,
                        "CBGA" = %s,
                        "CBG" = %s,
                        "Total CBG" = %s,
                        "CBC" = %s,
                        "CBDV" = %s,
                        "THCV" = %s,
                        "CBGV" = %s,
                        "CBNV" = %s,
                        "CBGVA" = %s
                    WHERE id = %s
                ''', (
                    product_name,
                    product_data.get('ProductName', product_name),
                    product_type,
                    product_data.get('Vendor/Supplier*'),
                    product_data.get('Product Brand'),
                    product_data.get('Description'),
                    product_data.get('Weight*'),
                    product_data.get('Units'),
                    product_data.get('Price'),
                    product_data.get('Lineage'),
                    current_time,
                    current_time,
                    product_data.get('Product Strain'),
                    product_data.get('Quantity*'),
                    product_data.get('DOH'),
                    product_data.get('Concentrate Type'),
                    product_data.get('Ratio'),
                    product_data.get('JointRatio'),
                    product_data.get('THC test result'),
                    product_data.get('CBD test result'),
                    product_data.get('Test result unit (% or mg)'),
                    product_data.get('State'),
                    product_data.get('Is Sample? (yes/no)'),
                    product_data.get('Is MJ product?(yes/no)'),
                    product_data.get('Discountable? (yes/no)'),
                    product_data.get('Room*'),
                    product_data.get('Batch Number'),
                    product_data.get('Lot Number'),
                    product_data.get('Barcode*'),
                    product_data.get('Medical Only (Yes/No)'),
                    product_data.get('Med Price'),
                    product_data.get('Expiration Date(YYYY-MM-DD)'),
                    product_data.get('Is Archived? (yes/no)'),
                    product_data.get('THC Per Serving'),
                    product_data.get('Allergens'),
                    product_data.get('Solvent'),
                    product_data.get('Accepted Date'),
                    product_data.get('Internal Product Identifier'),
                    product_data.get('Product Tags (comma separated)'),
                    product_data.get('Image URL'),
                    product_data.get('Ingredients'),
                    product_data.get('Total THC'),
                    product_data.get('THCA'),
                    product_data.get('CBDA'),
                    product_data.get('CBN'),
                    product_data.get('THC'),
                    product_data.get('CBD'),
                    product_data.get('Total CBD'),
                    product_data.get('CBGA'),
                    product_data.get('CBG'),
                    product_data.get('Total CBG'),
                    product_data.get('CBC'),
                    product_data.get('CBDV'),
                    product_data.get('THCV'),
                    product_data.get('CBGV'),
                    product_data.get('CBNV'),
                    product_data.get('CBGVA'),
                    product_id
                ))
            else:
                # Insert new product
                cursor.execute('''
                    INSERT INTO products (
                        "Product Name*", "ProductName", normalized_name, "Product Type*",
                        "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units", "Price", "Lineage",
                        first_seen_date, last_seen_date, total_occurrences, created_at, updated_at,
                        "Product Strain", "Quantity*", "DOH", "Concentrate Type", "Ratio", "JointRatio",
                        "THC test result", "CBD test result", "Test result unit (% or mg)", "State",
                        "Is Sample? (yes/no)", "Is MJ product?(yes/no)", "Discountable? (yes/no)", "Room*",
                        "Batch Number", "Lot Number", "Barcode*", "Medical Only (Yes/No)", "Med Price",
                        "Expiration Date(YYYY-MM-DD)", "Is Archived? (yes/no)", "THC Per Serving", "Allergens", "Solvent",
                        "Accepted Date", "Internal Product Identifier", "Product Tags (comma separated)", "Image URL", "Ingredients",
                        "Total THC", "THCA", "CBDA", "CBN", "THC", "CBD", "Total CBD", "CBGA", "CBG", "Total CBG",
                        "CBC", "CBDV", "THCV", "CBGV", "CBNV", "CBGVA"
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                ''', (
                    product_name,
                    product_data.get('ProductName', product_name),
                    normalized_name,
                    product_type,
                    product_data.get('Vendor/Supplier*'),
                    product_data.get('Product Brand'),
                    product_data.get('Description'),
                    product_data.get('Weight*'),
                    product_data.get('Units'),
                    product_data.get('Price'),
                    product_data.get('Lineage'),
                    current_time,
                    current_time,
                    1,
                    current_time,
                    current_time,
                    product_data.get('Product Strain'),
                    product_data.get('Quantity*'),
                    product_data.get('DOH'),
                    product_data.get('Concentrate Type'),
                    product_data.get('Ratio'),
                    product_data.get('JointRatio'),
                    product_data.get('THC test result'),
                    product_data.get('CBD test result'),
                    product_data.get('Test result unit (% or mg)'),
                    product_data.get('State'),
                    product_data.get('Is Sample? (yes/no)'),
                    product_data.get('Is MJ product?(yes/no)'),
                    product_data.get('Discountable? (yes/no)'),
                    product_data.get('Room*'),
                    product_data.get('Batch Number'),
                    product_data.get('Lot Number'),
                    product_data.get('Barcode*'),
                    product_data.get('Medical Only (Yes/No)'),
                    product_data.get('Med Price'),
                    product_data.get('Expiration Date(YYYY-MM-DD)'),
                    product_data.get('Is Archived? (yes/no)'),
                    product_data.get('THC Per Serving'),
                    product_data.get('Allergens'),
                    product_data.get('Solvent'),
                    product_data.get('Accepted Date'),
                    product_data.get('Internal Product Identifier'),
                    product_data.get('Product Tags (comma separated)'),
                    product_data.get('Image URL'),
                    product_data.get('Ingredients'),
                    product_data.get('Total THC'),
                    product_data.get('THCA'),
                    product_data.get('CBDA'),
                    product_data.get('CBN'),
                    product_data.get('THC'),
                    product_data.get('CBD'),
                    product_data.get('Total CBD'),
                    product_data.get('CBGA'),
                    product_data.get('CBG'),
                    product_data.get('Total CBG'),
                    product_data.get('CBC'),
                    product_data.get('CBDV'),
                    product_data.get('THCV'),
                    product_data.get('CBGV'),
                    product_data.get('CBNV'),
                    product_data.get('CBGVA')
                ))
                product_id = cursor.fetchone()[0]
            
            conn.commit()
            return product_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding/updating product '{product_name}': {e}")
            raise
    
    @timed_operation("add_or_update_strain")
    @retry_on_lock(max_retries=3, delay=0.5)
    def add_or_update_strain(self, strain_name: str, lineage: str = None, sovereign: bool = False) -> int:
        """Add or update a strain in the database."""
        conn = self._get_connection()
        if not conn:
            raise Exception("No database connection available")
            
        cursor = conn.cursor()
        
        try:
            normalized_name = strain_name.lower().strip()
            current_date = datetime.now().isoformat()
            
            # Check if strain exists
            cursor.execute('''
                SELECT id FROM strains WHERE normalized_name = %s
            ''', (normalized_name,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing strain
                strain_id = existing[0]
                cursor.execute('''
                    UPDATE strains SET
                        canonical_lineage = %s,
                        last_seen_date = %s,
                        total_occurrences = total_occurrences + 1,
                        updated_at = %s,
                        sovereign_lineage = %s
                    WHERE id = %s
                ''', (lineage, current_date, current_date, lineage if sovereign else None, strain_id))
            else:
                # Insert new strain
                cursor.execute('''
                    INSERT INTO strains (
                        strain_name, normalized_name, canonical_lineage, first_seen_date, last_seen_date,
                        total_occurrences, created_at, updated_at, sovereign_lineage
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    strain_name, normalized_name, lineage, current_date, current_date, 1,
                    current_date, current_date, lineage if sovereign else None
                ))
                strain_id = cursor.fetchone()[0]
            
            conn.commit()
            return strain_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding/updating strain '{strain_name}': {e}")
            raise
    
    def get_products_by_names(self, product_names: List[str]) -> List[Dict[str, Any]]:
        """Get products by their normalized names."""
        if not product_names:
            return []
            
        conn = self._get_connection()
        if not conn:
            return []
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            placeholders = ','.join(['%s'] * len(product_names))
            cursor.execute(f'''
                SELECT * FROM products WHERE normalized_name IN ({placeholders})
            ''', product_names)
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting products by names: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self._get_connection()
        if not conn:
            return {'error': 'No database connection'}
            
        cursor = conn.cursor()
        
        try:
            # Get product count
            cursor.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]
            
            # Get strain count
            cursor.execute('SELECT COUNT(*) FROM strains')
            strain_count = cursor.fetchone()[0]
            
            return {
                'products': product_count,
                'strains': strain_count,
                'database_type': 'PostgreSQL',
                'store_name': self.store_name
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
    
    def close_connections(self):
        """Close all database connections."""
        for conn in self._connection_pool.values():
            try:
                conn.close()
            except:
                pass
        self._connection_pool.clear()

# Global instance for lazy loading
_product_database_instance = None
_product_database_lock = threading.Lock()

def get_product_database(store_name=None):
    """Get or create a ProductDatabase instance."""
    global _product_database_instance
    with _product_database_lock:
        if _product_database_instance is None:
            _product_database_instance = ProductDatabase(store_name)
        return _product_database_instance

# Global PostgreSQL database instance
_postgresql_db = None

def get_postgresql_database(store_name: str = None) -> ProductDatabase:
    """Get PostgreSQL database instance."""
    global _postgresql_db
    if _postgresql_db is None or (store_name and _postgresql_db.store_name != store_name):
        _postgresql_db = ProductDatabase(store_name)
        _postgresql_db.init_database()
    return _postgresql_db
