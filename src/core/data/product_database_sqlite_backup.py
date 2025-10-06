from .field_mapping import get_canonical_field
import sqlite3
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import pandas as pd
from pathlib import Path
from functools import lru_cache
import threading
import os

def get_database_path(store_name=None):
    """Get the correct database path for ProductDatabase instances."""
    # Get the current directory of this file
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    uploads_dir = os.path.join(current_dir, 'uploads')
    
    # Create uploads directory if it doesn't exist
    os.makedirs(uploads_dir, exist_ok=True)
    
    if store_name:
        # Create store-specific database file
        db_filename = f'product_database_{store_name}.db'
        return os.path.join(uploads_dir, db_filename)
    else:
        # Default database for backward compatibility
        return os.path.join(uploads_dir, 'product_database.db')

logger = logging.getLogger(__name__)

# Performance optimization: disable debug logging in production
DEBUG_ENABLED = False

def timed_operation(operation_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                return func(self, *args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                # You can log or store timing here if you want
                if elapsed > 0.1:
                    logger.warning(f"⏱️  {operation_name}: {elapsed:.3f}s")
        return wrapper
    return decorator

def retry_on_lock(max_retries=3, delay=0.5):
    """Decorator to retry database operations on locking errors."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            current_delay = delay  # Use a local variable to avoid scope issues
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"Database locked for {func.__name__}, retrying in {current_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
                    else:
                        raise e
            return None
        return wrapper
    return decorator

class ProductDatabase:
    """Database for storing and managing product and strain information."""
    
    def __init__(self, db_path: str = None, store_name: str = None):
        if db_path is None:
            self.db_path = get_database_path(store_name)
        else:
            self.db_path = db_path
        self._connection_pool = {}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._initialized = False
        self._init_lock = threading.Lock()
        # Serialize writers to avoid 'database is locked' under concurrent writes
        self._write_lock = threading.RLock()
        
        # Performance timing
        self._timing_stats = {
            'queries': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _get_connection(self):
        """Get a database connection, reusing if possible."""
        thread_id = threading.get_ident()
        if thread_id not in self._connection_pool:
            # Configure connection for better concurrency
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout for database operations
                check_same_thread=False  # Allow connection sharing across threads
            )
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout (60s) to ride out background batches
            conn.execute("PRAGMA busy_timeout=60000")
            # Optimize for concurrent access
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self._connection_pool[thread_id] = conn
        return self._connection_pool[thread_id]
    
    def init_database(self):
        """Initialize the database with required tables (lazy initialization)."""
        if self._initialized:
            return
            
        with self._init_lock:
            if self._initialized:  # Double-check pattern
                return
                
            start_time = time.time()
            logger.info(f"Initializing product database at {self.db_path}...")
            
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Check if products table exists and has data
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
                products_exists = cursor.fetchone() is not None
                
                if products_exists:
                    # Check if table has data
                    cursor.execute("SELECT COUNT(*) FROM products")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        logger.info(f"Database already initialized with {count} products")
                        self._initialized = True
                        return
                
                # Create strains table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strains (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strain_name TEXT UNIQUE NOT NULL,
                        normalized_name TEXT NOT NULL,
                        canonical_lineage TEXT,
                        first_seen_date TEXT NOT NULL,
                        last_seen_date TEXT NOT NULL,
                        total_occurrences INTEGER DEFAULT 1,
                        lineage_confidence REAL DEFAULT 0.0,
                        sovereign_lineage TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Create products table with essential columns for Excel data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        "Product Name*" TEXT NOT NULL,
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
                        -- Additional cannabinoid columns for comprehensive testing
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
                        "CBGVA" TEXT,
                        FOREIGN KEY (strain_id) REFERENCES strains (id),
                        UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
                    )
                ''')
                
                # Create lineage_history table for tracking lineage changes
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lineage_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strain_id INTEGER,
                        old_lineage TEXT,
                        new_lineage TEXT,
                        change_date TEXT NOT NULL,
                        change_reason TEXT,
                        FOREIGN KEY (strain_id) REFERENCES strains (id)
                    )
                ''')
                
                # Create strain-brand lineage overrides
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strain_brand_lineage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strain_name TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        lineage TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(strain_name, brand)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_strains_normalized ON strains(normalized_name)')
                
                # Only create normalized_name index if the column exists
                cursor.execute("PRAGMA table_info(products)")
                product_columns = [col[1] for col in cursor.fetchall()]
                if 'normalized_name' in product_columns:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_normalized ON products(normalized_name)')
                
                # Only create strain_id index if the column exists
                if 'strain_id' in product_columns:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_strain ON products(strain_id)')
                    
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_vendor_brand ON products("Vendor/Supplier*", "Product Brand")')
                
                conn.commit()
                
                # Check if we need to add missing columns (migration)
                # Only migrate if tables are empty or missing critical columns
                self._migrate_database_schema_safe(cursor, conn)
                
                # CRITICAL FIX: Force check for essential columns and add if missing
                self._ensure_essential_columns_exist(cursor, conn)
                
                self._initialized = True
                
                elapsed = time.time() - start_time
                logger.info(f"Product database initialized successfully in {elapsed:.3f}s")
                
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
                raise
    
    def _migrate_database_schema_safe(self, cursor, conn):
        """Safely migrate database schema only if necessary."""
        try:
            # Check if tables exist and have data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strains'")
            strains_table_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            products_table_exists = cursor.fetchone() is not None
            
            if strains_table_exists and products_table_exists:
                # Check if tables have data
                cursor.execute("SELECT COUNT(*) FROM strains")
                strain_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                
                if strain_count > 0 or product_count > 0:
                    logger.info(f"Database has existing data ({strain_count} strains, {product_count} products). Skipping destructive migration.")
                    # Add missing columns to existing tables
                    self._add_missing_columns_safe(cursor, conn)
                    return
            
            logger.info("Database is empty or missing tables. Performing safe schema migration...")
            # Only proceed with migration if tables are empty or don't exist
            self._migrate_database_schema(cursor, conn)
            
        except Exception as e:
            logger.error(f"Error during safe schema migration: {e}")
            # Don't raise - continue with existing schema
    
    def _ensure_essential_columns_exist(self, cursor, conn):
        """Ensure essential columns exist that are needed for Excel processor compatibility."""
        try:
            # Get current columns
            cursor.execute("PRAGMA table_info(products)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Essential columns that must exist for Excel processor compatibility
            essential_columns = [
                'ProductName',
                'Units', 
                'Price',
                '"Price*"',
                '"Price* (Tier Name for Bulk)"',
                '"Product Name*"',
                '"Vendor/Supplier*"',
                '"Weight*"',
                '"Weight Unit*"',
                '"Quantity*"',
                '"Quantity Received*"',
                '"DOH Compliant*"',
                '"DOH Compliant (Yes/No)"',
                '"Joint Ratio"',
                'qty',
                '"Weight Unit* (grams/gm or ounces/oz)"',
                'Vendor'
            ]
            
            added_columns = []
            for col_name in essential_columns:
                # Strip quotes for comparison with existing columns
                col_name_clean = col_name.strip('"')
                if col_name_clean not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} TEXT")
                        added_columns.append(col_name)
                        logger.info(f"Added essential column: {col_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            logger.warning(f"Could not add essential column {col_name}: {e}")
                    except Exception as e:
                        logger.warning(f"Could not add essential column {col_name}: {e}")
            
            if added_columns:
                conn.commit()
                logger.info(f"Added {len(added_columns)} essential columns to products table")
            else:
                logger.debug("All essential columns already exist")
                
        except Exception as e:
            logger.error(f"Error ensuring essential columns exist: {e}")

    def _migrate_database_schema(self, cursor, conn):
        """Force recreate database with correct schema - USE WITH CAUTION."""
        try:
            logger.info("Forcing database recreation with correct schema...")
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("DROP TABLE IF EXISTS strains")
            cursor.execute("DROP TABLE IF EXISTS lineage_history")
            cursor.execute("DROP TABLE IF EXISTS strain_brand_lineage")
            
            # Recreate tables with correct schema
            cursor.execute('''
                CREATE TABLE strains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strain_name TEXT UNIQUE NOT NULL,
                    normalized_name TEXT NOT NULL,
                    canonical_lineage TEXT,
                    first_seen_date TEXT NOT NULL,
                    last_seen_date TEXT NOT NULL,
                    total_occurrences INTEGER DEFAULT 1,
                    lineage_confidence REAL DEFAULT 0.0,
                    sovereign_lineage TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    "Product Name*" TEXT NOT NULL,
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
                    -- Additional Excel columns for comprehensive JSON matching
                    "CombinedWeight" TEXT,
                    "Ratio_or_THC_CBD" TEXT,
                    "Description_Complexity" TEXT,
                    "Total THC" TEXT,
                    "THCA" TEXT,
                    "CBDA" TEXT,
                    "CBN" TEXT,
                    -- Additional cannabinoid columns for comprehensive testing
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
                    "CBGVA" TEXT,
                    -- Calculated THC/CBD values
                    "AI" TEXT,
                    "AJ" TEXT,
                    "AK" TEXT,
                    -- Terpene columns for comprehensive product data
                    "A-Bisabolol (mg/g)" TEXT,
                    "A-Humulene (mg/g)" TEXT,
                    "A-Maaliene (mg/g)" TEXT,
                    "A-Myrcene (mg/g)" TEXT,
                    "A-Pinene (mg/g)" TEXT,
                    "B-Caryophyllene (mg/g)" TEXT,
                    "B-Myrcene (mg/g)" TEXT,
                    "B-Pinene (mg/g)" TEXT,
                    bisabolol_mg_g TEXT,
                    borneol_mg_g TEXT,
                    camphene_mg_g TEXT,
                    camphor_mg_g TEXT,
                    carene_mg_g TEXT,
                    carvacrol_mg_g TEXT,
                    carvone_mg_g TEXT,
                    caryophyllene_mg_g TEXT,
                    cedrol_mg_g TEXT,
                    citral_mg_g TEXT,
                    citronellol_mg_g TEXT,
                    cymene_mg_g TEXT,
                    delta_3_carene_mg_g TEXT,
                    eucalyptol_mg_g TEXT,
                    fenchol_mg_g TEXT,
                    fenchone_mg_g TEXT,
                    geraniol_mg_g TEXT,
                    geranyl_acetate_mg_g TEXT,
                    guaiol_mg_g TEXT,
                    humulene_mg_g TEXT,
                    isoborneol_mg_g TEXT,
                    isobornyl_acetate_mg_g TEXT,
                    isopulegol_mg_g TEXT,
                    limonene_mg_g TEXT,
                    linalool_mg_g TEXT,
                    linalyl_acetate_mg_g TEXT,
                    m_cymene_mg_g TEXT,
                    menthal_mg_g TEXT,
                    menthone_mg_g TEXT,
                    myrcene_mg_g TEXT,
                    nerolidol_mg_g TEXT,
                    o_cymene_mg_g TEXT,
                    ocimene_mg_g TEXT,
                    p_cymene_mg_g TEXT,
                    phellandrene_mg_g TEXT,
                    phytol_mg_g TEXT,
                    pinene_mg_g TEXT,
                    piperitone_mg_g TEXT,
                    pulegone_mg_g TEXT,
                    sabinene_mg_g TEXT,
                    safranal_mg_g TEXT,
                    selinadiene_mg_g TEXT,
                    terpineol_mg_g TEXT,
                    terpinolene_mg_g TEXT,
                    thujene_mg_g TEXT,
                    thymol_mg_g TEXT,
                    trans_nerolidol_mg_g TEXT,
                    trans_alpha_bergamotene_mg_g TEXT,
                    valencene_mg_g TEXT,
                    alpha_bisabolene_mg_g TEXT,
                    alpha_bulnesene_mg_g TEXT,
                    alpha_farnesene_mg_g TEXT,
                    alpha_maaliene_mg_g TEXT,
                    alpha_ocimene_mg_g TEXT,
                    alpha_phellandrene_mg_g TEXT,
                    alpha_pinene_mg_g TEXT,
                    alpha_terpinene_mg_g TEXT,
                    alpha_thujone_mg_g TEXT,
                    beta_farnesene_mg_g TEXT,
                    beta_maaliene_mg_g TEXT,
                    beta_ocimene_mg_g TEXT,
                    beta_pinene_mg_g TEXT,
                    gamma_terpinene_mg_g TEXT,
                    -- Additional source Excel columns for comprehensive matching
                    product_name_alt TEXT,
                    vendor_supplier TEXT,
                    vendor_supplier_alt TEXT,
                    weight_with_units TEXT,
                    weight_units TEXT,
                    quantity_received TEXT,
                    product_type_alt TEXT,
                    product_brand_alt TEXT,
                    product_brand_center TEXT,
                    ratio_or_thc_cbd_alt TEXT,
                    thc_cbd TEXT,
                    thc_cbd_alt TEXT,
                    ai_column TEXT,
                    aj_column TEXT,
                    ak_column TEXT,
                    al_column TEXT,
                    am_column TEXT,
                    an_column TEXT,
                    ao_column TEXT,
                    ap_column TEXT,
                    aq_column TEXT,
                    ar_column TEXT,
                    as_column TEXT,
                    at_column TEXT,
                    au_column TEXT,
                    av_column TEXT,
                    aw_column TEXT,
                    ax_column TEXT,
                    ay_column TEXT,
                    az_column TEXT,
                    ba_column TEXT,
                    bb_column TEXT,
                    bc_column TEXT,
                    bd_column TEXT,
                    be_column TEXT,
                    bf_column TEXT,
                    bg_column TEXT,
                    bh_column TEXT,
                    bi_column TEXT,
                    bj_column TEXT,
                    bk_column TEXT,
                    bl_column TEXT,
                    bm_column TEXT,
                    bn_column TEXT,
                    bo_column TEXT,
                    bp_column TEXT,
                    bq_column TEXT,
                    br_column TEXT,
                    bs_column TEXT,
                    bt_column TEXT,
                    bu_column TEXT,
                    bv_column TEXT,
                    bw_column TEXT,
                    bx_column TEXT,
                    by_column TEXT,
                    bz_column TEXT,
                    ca_column TEXT,
                    cb_column TEXT,
                    cc_column TEXT,
                    cd_column TEXT,
                    ce_column TEXT,
                    cf_column TEXT,
                    cg_column TEXT,
                    ch_column TEXT,
                    ci_column TEXT,
                    cj_column TEXT,
                    ck_column TEXT,
                    cl_column TEXT,
                    cm_column TEXT,
                    cn_column TEXT,
                    co_column TEXT,
                    cp_column TEXT,
                    cq_column TEXT,
                    cr_column TEXT,
                    cs_column TEXT,
                    ct_column TEXT,
                    cu_column TEXT,
                    cv_column TEXT,
                    cw_column TEXT,
                    cx_column TEXT,
                    cy_column TEXT,
                    cz_column TEXT,
                    -- Excel processor compatibility columns
                    "ProductName" TEXT,  -- Alternative to "Product Name*"
                    "Units" TEXT,  -- Alternative to "Weight Unit* (grams/gm or ounces/oz)"
                    "Price" TEXT,  -- Alternative to "Price* (Tier Name for Bulk)"
                    "DOH Compliant (Yes/No)" TEXT,  -- Alternative to "DOH"
                    "Joint Ratio" TEXT,  -- Alternative to "JointRatio"
                    "Quantity Received*" TEXT,  -- Alternative to "Quantity*"
                    "qty" TEXT,  -- Alternative to "Quantity*"
                    FOREIGN KEY (strain_id) REFERENCES strains (id),
                    UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE lineage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strain_id INTEGER,
                    old_lineage TEXT,
                    new_lineage TEXT,
                    change_date TEXT NOT NULL,
                    change_reason TEXT,
                    FOREIGN KEY (strain_id) REFERENCES strains (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE strain_brand_lineage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strain_name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    lineage TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(strain_name, brand)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX idx_strains_normalized ON strains(normalized_name)')
            cursor.execute('CREATE INDEX idx_products_normalized ON products(normalized_name)')
            cursor.execute('CREATE INDEX idx_products_strain ON products(strain_id)')
            cursor.execute('CREATE INDEX idx_products_vendor_brand ON products("Vendor/Supplier*", "Product Brand")')
            
            conn.commit()
            logger.info("Database recreated with correct schema")
            
        except Exception as e:
            logger.error(f"Error recreating database: {e}")
            raise
    
    def _get_cache_key(self, operation: str, *args) -> str:
        """Generate a cache key for the given operation and arguments."""
        return f"{operation}:{hash(str(args))}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from cache with thread safety."""
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                # Check if cache entry has expired
                if cached_data['expires'] < time.time():
                    del self._cache[cache_key]
                    self._timing_stats['cache_misses'] += 1
                    return None
                self._timing_stats['cache_hits'] += 1
                return cached_data['value']
            self._timing_stats['cache_misses'] += 1
            return None
    
    def _set_cache(self, cache_key: str, value: Any, ttl: int = 300):
        """Set value in cache with thread safety and TTL."""
        with self._cache_lock:
            self._cache[cache_key] = {
                'value': value,
                'expires': time.time() + ttl
            }
    
    def _clean_expired_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        with self._cache_lock:
            expired_keys = [
                key for key, data in self._cache.items()
                if data['expires'] < current_time
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def get_mode_lineage(self, strain_id: int) -> str:
        """Return the most common (mode) lineage for a strain from the products table."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # First get the strain name from the strains table
            cursor.execute('SELECT strain_name FROM strains WHERE id = ?', (strain_id,))
            strain_result = cursor.fetchone()
            if not strain_result:
                return None
            
            strain_name = strain_result[0]
            
            # Then find the most common lineage for this strain in products
            cursor.execute('''
                SELECT "Lineage", COUNT(*) as count
                FROM products
                WHERE "Product Strain" = ? AND "Lineage" IS NOT NULL AND "Lineage" != ''
                GROUP BY "Lineage"
                ORDER BY count DESC
                LIMIT 1
            ''', (strain_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting mode lineage for strain_id {strain_id}: {e}")
            return None

    def update_all_canonical_lineages_to_mode(self):
        """Update all strains' canonical_lineage to the mode lineage from the products table."""
        self.init_database()
        conn = self._get_connection()
        cursor = conn.cursor()
        # Get all strains
        cursor.execute('SELECT id, strain_name, canonical_lineage FROM strains')
        strains = cursor.fetchall()
        updated = 0
        for strain_id, strain_name, canonical_lineage in strains:
            mode_lineage = self.get_mode_lineage(strain_id)
            if mode_lineage and mode_lineage != canonical_lineage:
                cursor.execute('''
                    UPDATE strains SET canonical_lineage = ?, updated_at = ? WHERE id = ?
                ''', (mode_lineage, datetime.now().isoformat(), strain_id))
                logger.info(f"Updated canonical_lineage for '{strain_name}' to '{mode_lineage}' (was '{canonical_lineage}')")
                updated += 1
        conn.commit()
        logger.info(f"Canonical lineage update complete. {updated} strains updated.")

    @timed_operation("add_or_update_strain")
    @retry_on_lock(max_retries=3, delay=0.5)
    def add_or_update_strain(self, strain_name: str, lineage: str = None, sovereign: bool = False) -> int:
        """Add a new strain or update existing strain information. If sovereign is True, set sovereign_lineage."""
        try:
            self.init_database()  # Ensure DB is initialized
            normalized_name = self._normalize_strain_name(strain_name)
            current_date = datetime.now().isoformat()
            # Serialize write operations
            with self._write_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                # Check if we're already in a transaction
                try:
                    cursor.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError as e:
                    if "cannot start a transaction within a transaction" in str(e):
                        # We're already in a transaction, continue without BEGIN
                        pass
                    else:
                        raise e
                
                # Check if strain exists
                cursor.execute('''
                    SELECT id, canonical_lineage, total_occurrences, lineage_confidence, sovereign_lineage
                    FROM strains 
                    WHERE normalized_name = ?
                ''', (normalized_name,))
                existing = cursor.fetchone()
                
                if existing:
                    strain_id, existing_lineage, occurrences, confidence, existing_sovereign = existing
                    new_occurrences = occurrences + 1
                    # Update lineage if provided and different
                    if lineage and lineage != existing_lineage:
                        cursor.execute('''
                            INSERT INTO lineage_history (strain_id, old_lineage, new_lineage, change_date, change_reason)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (strain_id, existing_lineage, lineage, current_date, 'New data upload'))
                        cursor.execute('''
                            UPDATE strains 
                            SET canonical_lineage = ?, total_occurrences = ?, last_seen_date = ?, updated_at = ?
                            WHERE id = ?
                        ''', (lineage, new_occurrences, current_date, current_date, strain_id))
                        
                        # Notify all sessions of the lineage update (non-blocking)
                        try:
                            from .database_notifier import notify_lineage_update
                            notify_lineage_update(strain_name, existing_lineage, lineage)
                        except Exception as notify_error:
                            logger.warning(f"Failed to notify lineage update: {notify_error}")
                    else:
                        cursor.execute('''
                            UPDATE strains 
                            SET total_occurrences = ?, last_seen_date = ?, updated_at = ?
                            WHERE id = ?
                        ''', (new_occurrences, current_date, current_date, strain_id))
                    # Sovereign lineage update
                    if sovereign and lineage:
                        cursor.execute('''
                            UPDATE strains SET sovereign_lineage = ? WHERE id = ?
                        ''', (lineage, strain_id))
                        
                        # Notify all sessions of the sovereign lineage update (non-blocking)
                        try:
                            from .database_notifier import notify_sovereign_lineage_set
                            notify_sovereign_lineage_set(strain_name, lineage)
                        except Exception as notify_error:
                            logger.warning(f"Failed to notify sovereign lineage update: {notify_error}")
                        
                    conn.commit()
                    cache_key = self._get_cache_key("strain_info", normalized_name)
                    with self._cache_lock:
                        if cache_key in self._cache:
                            del self._cache[cache_key]
                    return strain_id
                else:
                    cursor.execute('''
                        INSERT INTO strains (strain_name, normalized_name, canonical_lineage, first_seen_date, last_seen_date, created_at, updated_at, sovereign_lineage)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (strain_name, normalized_name, lineage, current_date, current_date, current_date, current_date, lineage if sovereign else None))
                    strain_id = cursor.lastrowid
                    conn.commit()
                    
                    # Notify all sessions of the new strain (non-blocking)
                    try:
                        from .database_notifier import notify_strain_add
                        notify_strain_add(strain_name, {
                            'lineage': lineage,
                            'sovereign': sovereign,
                            'strain_id': strain_id
                        })
                    except Exception as notify_error:
                        logger.warning(f"Failed to notify strain add: {notify_error}")
                    
                    if DEBUG_ENABLED:
                        logger.debug(f"Added new strain '{strain_name}' with lineage '{lineage}'")
                    return strain_id
                    
        except Exception as e:
            logger.error(f"Error adding/updating strain '{strain_name}': {e}")
            raise
    
    @timed_operation("add_or_update_product")
    @retry_on_lock(max_retries=3, delay=0.5)
    def add_or_update_product(self, product_data: Dict[str, Any]) -> int:
        """Add a new product or update existing product information."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            # Handle both 'ProductName' and 'Product Name*' column names
            product_name = product_data.get(get_canonical_field('Product Name*'), product_data.get(get_canonical_field('ProductName'), ''))
            normalized_name = self._normalize_product_name(product_name)
            current_date = datetime.now().isoformat()
            
            # Get or create strain
            strain_name = product_data.get('Product Strain', '')
            strain_id = None
            if strain_name:
                # Normalize lineage before storing
                normalized_lineage = self._normalize_lineage(product_data.get('Lineage'))
                strain_id = self.add_or_update_strain(strain_name, normalized_lineage)
            
            # Serialize write operations
            with self._write_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                # Check if we're already in a transaction
                try:
                    cursor.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError as e:
                    if "cannot start a transaction within a transaction" in str(e):
                        # We're already in a transaction, continue without BEGIN
                        pass
                    else:
                        raise e
                
                # Enhanced duplicate detection: Check multiple combinations
                # First check exact match (name + vendor + brand)
                cursor.execute('''
                    SELECT id, total_occurrences, "Product Name*"
                    FROM products 
                    WHERE normalized_name = ? AND "Vendor/Supplier*" = ? AND "Product Brand" = ?
                ''', (normalized_name, product_data.get(get_canonical_field('Vendor/Supplier*')), product_data.get(get_canonical_field('Product Brand'))))
                
                existing = cursor.fetchone()
                
                if existing:
                    product_id, occurrences, existing_name = existing
                    
                    # Log duplicate detection and update
                    logger.info(f"Found existing product: '{existing_name}' (ID: {product_id}, occurrences: {occurrences}) - REPLACING WITH NEW EXCEL DATA")
                    
                    # Update existing product with new data (new data always replaces old values)
                    self._update_existing_product(cursor, product_id, product_data)
                    conn.commit()
                    logger.info(f"Successfully replaced existing product '{existing_name}' with new Excel data")
                    return product_id
                
                # Check for similar products (same name + vendor, different brand)
                cursor.execute('''
                    SELECT id, total_occurrences, "Product Name*", "Product Brand"
                    FROM products 
                    WHERE normalized_name = ? AND "Vendor/Supplier*" = ? AND "Product Brand" != ?
                ''', (normalized_name, product_data.get('Vendor/Supplier*'), product_data.get('Product Brand')))
                
                similar_products = cursor.fetchall()
                if similar_products:
                    logger.info(f"Found {len(similar_products)} similar products with same name '{product_name}' and vendor '{product_data.get('Vendor')}' but different brands")
                    for similar_id, similar_occurrences, similar_name, similar_brand in similar_products:
                        logger.debug(f"Similar product: '{similar_name}' (Brand: {similar_brand}, ID: {similar_id})")
                else:
                    # Add new product with comprehensive column population
                    cursor.execute('''
                        INSERT INTO products (
                            "Product Name*", normalized_name, "Product Strain", "Product Type*", "Vendor/Supplier*", "Product Brand",
                            "Description", "Weight*", "Units", "Price", "Lineage", first_seen_date, last_seen_date, created_at, updated_at,
                            "Quantity*", "DOH", "Concentrate Type", "Ratio", "JointRatio", "Test result unit (% or mg)", "State", "Is Sample? (yes/no)", 
                            "Is MJ product?(yes/no)", "Discountable? (yes/no)", "Room*", "Batch Number", "Lot Number", "Barcode*",
                            "Medical Only (Yes/No)", "Med Price", "Expiration Date(YYYY-MM-DD)", "Is Archived? (yes/no)", 
                            "THC Per Serving", "Allergens", "Solvent", "Accepted Date", "Internal Product Identifier", 
                            "Product Tags (comma separated)", "Image URL", "Ingredients", "CombinedWeight", "Ratio_or_THC_CBD", 
                            "Description_Complexity", "Total THC", "THCA", "CBDA", "CBN",
                            "THC", "CBD", "Total CBD", "CBGA", "CBG", "Total CBG", "CBC", "CBDV", "THCV", "CBGV", "CBNV", "CBGVA",
                            "total_occurrences", "strain_id",
                            "ProductName", "DOH Compliant (Yes/No)", "Joint Ratio", "Quantity Received*", "qty",
                            "THC test result", "CBD test result", "Vendor/Supplier*", "Price",
                            "AI", "AJ", "AK"
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_name, normalized_name, self._calculate_product_strain_original(
                            product_data.get('Product Type*', ''),
                            product_data.get('Product Name*', ''),
                            product_data.get('Description', ''),
                            product_data.get('Ratio', '')
                        ), product_data.get('Product Type*'),
                        product_data.get('Vendor/Supplier*'), product_data.get('Product Brand'),
                        self._process_description(product_data.get('Product Name*', ''), product_data.get('Description', '')), product_data.get('Weight*'),
                        product_data.get('Units'), product_data.get('Price'),
                        self._normalize_lineage(product_data.get('Lineage')), current_date, current_date, current_date, current_date,
                        # Core product data
                        product_data.get('Quantity*', ''),
                        product_data.get('DOH', ''),
                        product_data.get('Concentrate Type', ''),
                        product_data.get('Ratio', ''),
                        product_data.get('JointRatio', ''),
                        product_data.get('Test result unit (% or mg)', ''),
                        product_data.get('State', ''),
                        product_data.get('Is Sample? (yes/no)', ''),
                        product_data.get('Is MJ product?(yes/no)', ''),
                        product_data.get('Discountable? (yes/no)', ''),
                        product_data.get('Room*', ''),
                        product_data.get('Batch Number', ''),
                        product_data.get('Lot Number', ''),
                        product_data.get('Barcode*', ''),
                        product_data.get('Medical Only (Yes/No)', ''),
                        product_data.get('Med Price', ''),
                        product_data.get('Expiration Date(YYYY-MM-DD)', ''),
                        product_data.get('Is Archived? (yes/no)', ''),
                        product_data.get('THC Per Serving', ''),
                        product_data.get('Allergens', ''),
                        product_data.get('Solvent', ''),
                        product_data.get('Accepted Date', ''),
                        product_data.get('Internal Product Identifier', ''),
                        product_data.get('Product Tags (comma separated)', ''),
                        product_data.get('Image URL', ''),
                        product_data.get('Ingredients', ''),
                        product_data.get('CombinedWeight', ''),
                        self._calculate_ratio_or_thc_cbd(
                            product_data.get('Product Type*', ''),
                            product_data.get('Ratio', ''),
                            product_data.get('JointRatio', ''),
                            product_name
                        ),
                        product_data.get('Description_Complexity', ''),
                        product_data.get('Total THC', ''),
                        product_data.get('THCA', ''),
                        product_data.get('CBDA', ''),
                        product_data.get('CBN', ''),
                        # Additional cannabinoid values
                        product_data.get('THC', ''),
                        product_data.get('CBD', ''),
                        product_data.get('Total CBD', ''),
                        product_data.get('CBGA', ''),
                        product_data.get('CBG', ''),
                        product_data.get('Total CBG', ''),
                        product_data.get('CBC', ''),
                        product_data.get('CBDV', ''),
                        product_data.get('THCV', ''),
                        product_data.get('CBGV', ''),
                        product_data.get('CBNV', ''),
                        product_data.get('CBGVA', ''),
                        # Additional required columns
                        product_data.get('total_occurrences', 1),  # Default to 1 for new products
                        strain_id,  # Foreign key to strains table
                        # Excel compatibility columns - populate from main columns if not present
                        product_data.get('ProductName', product_name),  # Alternative to "Product Name*"
                        product_data.get('DOH Compliant (Yes/No)', product_data.get('DOH', '')),  # Alternative to "DOH"
                        product_data.get('Joint Ratio', product_data.get('JointRatio', '')),  # Alternative to "JointRatio"
                        product_data.get('Quantity Received*', product_data.get('Quantity*', '')),  # Alternative to "Quantity*"
                        product_data.get('qty', product_data.get('Quantity*', '')),  # Alternative to "Quantity*"
                        # Additional missing values
                        product_data.get('THC test result', ''),
                        product_data.get('CBD test result', ''),
                        product_data.get('Vendor/Supplier*', ''),  # Map to Vendor/Supplier* column
                        product_data.get('Price', ''),  # Map to Price column,
                        # AI, AJ, AK values
                        product_data.get('AI', ''),
                        product_data.get('AJ', ''),
                        product_data.get('AK', '')
                    ))
                    
                    product_id = cursor.lastrowid
                    conn.commit()
                    if DEBUG_ENABLED:
                        logger.debug(f"Added new product '{product_name}'")
                    return product_id
                    
        except Exception as e:
            product_name = product_data.get('Product Name*', product_data.get('ProductName', ''))
            logger.error(f"Error adding/updating product '{product_name}': {e}")
            raise
    
    def store_excel_data(self, df: pd.DataFrame, source_file: str = None) -> Dict[str, Any]:
        """Store Excel data in the database. New data replaces existing data when duplicates are found."""
        try:
            self.init_database()  # Ensure DB is initialized
            logger.info(f"Starting to store Excel data with {len(df)} rows from {source_file}")
            
            if df is None or df.empty:
                logger.warning("No data to store - DataFrame is empty")
                return {'stored': 0, 'updated': 0, 'errors': 0, 'message': 'No data to store'}
            
            # TEMPORARILY DISABLE JSON match filtering to test database storage
            # filtered_df = self._filter_json_matched_tags(df)
            filtered_df = df.copy()  # Use all data without filtering

            # CRITICAL NORMALIZATION: map common column aliases used by different upload paths
            try:
                cols = set(filtered_df.columns)
                # Product name
                if 'Product Name*' not in cols and 'ProductName' in cols:
                    filtered_df['Product Name*'] = filtered_df['ProductName']
                    cols.add('Product Name*')
                if 'Product Name*' in cols:
                    filtered_df['Product Name*'] = filtered_df['Product Name*'].astype(str).str.strip()

                # Vendor
                if 'Vendor/Supplier*' not in cols and 'Vendor' in cols:
                    filtered_df['Vendor/Supplier*'] = filtered_df['Vendor']
                    cols.add('Vendor/Supplier*')
                if 'Vendor/Supplier*' in cols:
                    filtered_df['Vendor/Supplier*'] = filtered_df['Vendor/Supplier*'].astype(str).str.strip()

                # Product type
                if 'Product Type*' not in cols and 'Product Type' in cols:
                    filtered_df['Product Type*'] = filtered_df['Product Type']
                    cols.add('Product Type*')
                if 'Product Type*' in cols:
                    filtered_df['Product Type*'] = filtered_df['Product Type*'].astype(str).str.strip()

                # Price
                if 'Price' not in cols and 'Price* (Tier Name for Bulk)' in cols:
                    filtered_df['Price'] = filtered_df['Price* (Tier Name for Bulk)']
                    cols.add('Price')
                if 'Price' in cols:
                    filtered_df['Price'] = filtered_df['Price'].astype(str).str.strip()

                # Ensure minimal required fields exist to avoid skipping rows later
                for required_col in ['Product Name*', 'Product Type*', 'Vendor/Supplier*']:
                    if required_col not in filtered_df.columns:
                        filtered_df[required_col] = ''
            except Exception as norm_err:
                logger.warning(f"Column normalization failed: {norm_err}")
            
            print(f"🔍 DEBUG: Database storage - Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")
            print(f"🔍 DEBUG: Database storage - Columns: {list(filtered_df.columns)}")
            
            # if filtered_df.empty:
            #     logger.warning("All data was filtered out as JSON matched tags - nothing to store")
            #     return {
            #         'stored': 0, 
            #         'updated': 0, 
            #         'errors': 0, 
            #         'excluded_json_matches': len(df),
            #         'message': f'All {len(df)} rows were JSON matched tags - excluded from database storage'
            #     }
            
            # Initialize duplicate tracking for this upload
            self._current_upload_products = set()
            
            stored_count = 0
            updated_count = 0
            skipped_duplicates = 0
            error_count = 0
            errors = []
            
            # Process each row in the filtered DataFrame
            print(f"🔍 DEBUG: Starting to process {len(filtered_df)} rows for database storage")
            for index, row in filtered_df.iterrows():
                try:
                    if index % 100 == 0:  # Log every 100 rows
                        print(f"🔍 DEBUG: Processing row {index}/{len(filtered_df)}")
                    # Convert row to dictionary and handle NaN values
                    row_dict = {}
                    for col in filtered_df.columns:
                        value = row[col]
                        if pd.isna(value):
                            row_dict[col] = None
                        else:
                            row_dict[col] = str(value).strip() if isinstance(value, str) else value
                    
                    # Map to database columns correctly
                    product_data = {
                        'Product Name*': row_dict.get('Product Name*', ''),
                        'Product Type*': self._ensure_crucial_value(row_dict.get('Product Type*', ''), 'Unknown', 'Product Type'),
                        'Lineage': row_dict.get('Lineage', ''),
                        'Vendor/Supplier*': self._ensure_crucial_value(row_dict.get('Vendor/Supplier*', row_dict.get('Vendor', '')), 'Unknown Vendor', 'Vendor'),
                        'Vendor': self._ensure_crucial_value(row_dict.get('Vendor', row_dict.get('Vendor/Supplier*', '')), 'Unknown Vendor', 'Vendor'),
                        'Product Brand': self._ensure_crucial_value(row_dict.get('Product Brand', ''), 'Unknown Brand', 'Product Brand'),
                        'Description': self._process_description(
                            row_dict.get('Product Name*', ''), 
                            row_dict.get('Description', '')
                        ),
                        'Weight*': self._ensure_crucial_value(row_dict.get('Weight*', ''), '1g', 'Weight'),
                        'Units': self._ensure_crucial_value(row_dict.get('Units', ''), 'each', 'Units'),
                        'Price': self._ensure_crucial_value(row_dict.get('Price*', row_dict.get('Price', '')), '0.00', 'Price'),
                        'Product Strain': row_dict.get('Product Strain', ''),
                        'Quantity*': row_dict.get('Quantity*', ''),
                        'DOH': row_dict.get('DOH Compliant (Yes/No)', row_dict.get('DOH', '')),
                        'Concentrate Type': row_dict.get('Concentrate Type', ''),
                        'Ratio': self._extract_ratio_from_product_name(
                            row_dict.get('Product Name*', ''), 
                            row_dict.get('Product Type*', '')
                        ) if not (row_dict.get('Ratio', '') or '').strip() else row_dict.get('Ratio', ''),
                        'JointRatio': row_dict.get('JointRatio', ''),
                        'THC test result': self._ensure_crucial_value(row_dict.get('THC Content', ''), '0.0', 'THC Content'),
                        'CBD test result': self._ensure_crucial_value(row_dict.get('CBD test result', ''), '0.0', 'CBD test result'),
                        'Test result unit (% or mg)': row_dict.get('Test result unit (% or mg)', ''),
                        'State': row_dict.get('State', ''),
                        'Is Sample? (yes/no)': row_dict.get('Is Sample? (yes/no)', ''),
                        'Is MJ product?(yes/no)': row_dict.get('Is MJ product?(yes/no)', ''),
                        'Discountable? (yes/no)': row_dict.get('Discountable? (yes/no)', ''),
                        'Room*': row_dict.get('Room*', ''),
                        'Batch Number': row_dict.get('Batch Number', ''),
                        'Lot Number': row_dict.get('Lot Number', ''),
                        'Barcode*': row_dict.get('Barcode*', ''),
                        'Medical Only (Yes/No)': row_dict.get('Medical Only (Yes/No)', ''),
                        'Med Price': row_dict.get('Med Price', ''),
                        'Expiration Date(YYYY-MM-DD)': row_dict.get('Expiration Date(YYYY-MM-DD)', ''),
                        'Is Archived? (yes/no)': row_dict.get('Is Archived? (yes/no)', ''),
                        'THC Per Serving': row_dict.get('THC Per Serving', ''),
                        'Allergens': row_dict.get('Allergens', ''),
                        'Solvent': row_dict.get('Solvent', ''),
                        'Accepted Date': row_dict.get('Accepted Date', ''),
                        'Internal Product Identifier': row_dict.get('Internal Product Identifier', ''),
                        'Product Tags (comma separated)': row_dict.get('Product Tags (comma separated)', ''),
                        'Image URL': row_dict.get('Image URL', ''),
                        'Ingredients': row_dict.get('Ingredients', ''),
                        # Additional columns for comprehensive Excel data matching
                        'Total THC': row_dict.get('Total THC', ''),
                        'THCA': row_dict.get('THC Content', ''),
                        'CBDA': row_dict.get('Total CBD', ''),
                        'CBN': row_dict.get('CBN', ''),
                        'Ratio_or_THC_CBD': row_dict.get('Ratio_or_THC_CBD', ''),
                        'Vendor/Supplier*': row_dict.get('Vendor/Supplier*', ''),
                        'Vendor/Supplier': row_dict.get('Vendor/Supplier', ''),
                        'Product Name*': row_dict.get('Product Name*', ''),
                        'Product Name': row_dict.get('Product Name', ''),
                        'Quantity Received*': row_dict.get('Quantity Received*', ''),
                        'WeightWithUnits': row_dict.get('WeightWithUnits', ''),
                        'WeightUnits': row_dict.get('WeightUnits', ''),
                        'ProductBrand': row_dict.get('ProductBrand', ''),
                        'ProductBrandCenter': row_dict.get('ProductBrandCenter', ''),
                        'THC_CBD': row_dict.get('THC_CBD', ''),
                        'THC': row_dict.get('THC', ''),  # Direct THC value from Excel
                        'CBD': row_dict.get('CBD', ''),  # Direct CBD value from Excel
                        'AI': self._calculate_ai_value(row_dict),  # Calculate THC value
                        'AJ': row_dict.get('THC Content', ''),  # THC Content
                        'AK': self._calculate_ak_value(row_dict),  # Calculate CBD value
                        # Source field to track where the data came from
                        'Source': row_dict.get('Source', f'Excel Import - {source_file}' if source_file else 'Excel Import'),
                        # Date Added field to track when the data was added
                        'Date Added': row_dict.get('Date Added', datetime.now().isoformat()),
                        # Terpene columns
                        'A-Bisabolol (mg/g)': row_dict.get('A-Bisabolol (mg/g)', ''),
                        'A-Humulene (mg/g)': row_dict.get('A-Humulene (mg/g)', ''),
                        'A-Maaliene (mg/g)': row_dict.get('A-Maaliene (mg/g)', ''),
                        'A-Myrcene (mg/g)': row_dict.get('A-Myrcene (mg/g)', ''),
                        'A-Pinene (mg/g)': row_dict.get('A-Pinene (mg/g)', ''),
                        'B-Caryophyllene (mg/g)': row_dict.get('B-Caryophyllene (mg/g)', ''),
                        'B-Myrcene (mg/g)': row_dict.get('B-Myrcene (mg/g)', ''),
                        'B-Pinene (mg/g)': row_dict.get('B-Pinene (mg/g)', ''),
                        'Bisabolol (mg/g)': row_dict.get('Bisabolol (mg/g)', ''),
                        'Borneol (mg/g)': row_dict.get('Borneol (mg/g)', ''),
                        'Camphene (mg/g)': row_dict.get('Camphene (mg/g)', ''),
                        'Camphor (mg/g)': row_dict.get('Camphor (mg/g)', ''),
                        'Carene (mg/g)': row_dict.get('Carene (mg/g)', ''),
                        'Carvacrol (mg/g)': row_dict.get('Carvacrol (mg/g)', ''),
                        'Carvone (mg/g)': row_dict.get('Carvone (mg/g)', ''),
                        'Caryophyllene (mg/g)': row_dict.get('Caryophyllene (mg/g)', ''),
                        'Cedrol (mg/g)': row_dict.get('Cedrol (mg/g)', ''),
                        'Citral (mg/g)': row_dict.get('Citral (mg/g)', ''),
                        'Citronellol (mg/g)': row_dict.get('Citronellol (mg/g)', ''),
                        'Cymene (mg/g)': row_dict.get('Cymene (mg/g)', ''),
                        'Delta-3-Carene (mg/g)': row_dict.get('Delta-3-Carene (mg/g)', ''),
                        'Eucalyptol (mg/g)': row_dict.get('Eucalyptol (mg/g)', ''),
                        'Fenchol (mg/g)': row_dict.get('Fenchol (mg/g)', ''),
                        'Fenchone (mg/g)': row_dict.get('Fenchone (mg/g)', ''),
                        'Geraniol (mg/g)': row_dict.get('Geraniol (mg/g)', ''),
                        'Geranyl Acetate (mg/g)': row_dict.get('Geranyl Acetate (mg/g)', ''),
                        'Guaiol (mg/g)': row_dict.get('Guaiol (mg/g)', ''),
                        'Humulene (mg/g)': row_dict.get('Humulene (mg/g)', ''),
                        'Isoborneol (mg/g)': row_dict.get('Isoborneol (mg/g)', ''),
                        'Isobornyl Acetate (mg/g)': row_dict.get('Isobornyl Acetate (mg/g)', ''),
                        'Isopulegol (mg/g)': row_dict.get('Isopulegol (mg/g)', ''),
                        'Limonene (mg/g)': row_dict.get('Limonene (mg/g)', ''),
                        'Linalool (mg/g)': row_dict.get('Linalool (mg/g)', ''),
                        'Linalyl Acetate (mg/g)': row_dict.get('Linalyl Acetate (mg/g)', ''),
                        'M-Cymene (mg/g)': row_dict.get('M-Cymene (mg/g)', ''),
                        'Menthal (mg/g)': row_dict.get('Menthal (mg/g)', ''),
                        'Menthone (mg/g)': row_dict.get('Menthone (mg/g)', ''),
                        'Myrcene (mg/g)': row_dict.get('Myrcene (mg/g)', ''),
                        'Nerolidol (mg/g)': row_dict.get('Nerolidol (mg/g)', ''),
                        'O-Cymene (mg/g)': row_dict.get('O-Cymene (mg/g)', ''),
                        'Ocimene (mg/g)': row_dict.get('Ocimene (mg/g)', ''),
                        'P-Cymene (mg/g)': row_dict.get('P-Cymene (mg/g)', ''),
                        'Phellandrene (mg/g)': row_dict.get('Phellandrene (mg/g)', ''),
                        'Phytol (mg/g)': row_dict.get('Phytol (mg/g)', ''),
                        'Pinene (mg/g)': row_dict.get('Pinene (mg/g)', ''),
                        'Piperitone (mg/g)': row_dict.get('Piperitone (mg/g)', ''),
                        'Pulegone (mg/g)': row_dict.get('Pulegone (mg/g)', ''),
                        'Sabinene (mg/g)': row_dict.get('Sabinene (mg/g)', ''),
                        'Safranal (mg/g)': row_dict.get('Safranal (mg/g)', ''),
                        'Selinadiene (mg/g)': row_dict.get('Selinadiene (mg/g)', ''),
                        'Terpineol (mg/g)': row_dict.get('Terpineol (mg/g)', ''),
                        'Terpinolene (mg/g)': row_dict.get('Terpinolene (mg/g)', ''),
                        'Thujene (mg/g)': row_dict.get('Thujene (mg/g)', ''),
                        'Thymol (mg/g)': row_dict.get('Thymol (mg/g)', ''),
                        'Trans-Nerolidol (mg/g)': row_dict.get('Trans-Nerolidol (mg/g)', ''),
                        'Trans-Alpha-Bergamotene (mg/g)': row_dict.get('Trans-Alpha-Bergamotene (mg/g)', ''),
                        'Valencene (mg/g)': row_dict.get('Valencene (mg/g)', ''),
                        'Alpha-Bisabolene (mg/g)': row_dict.get('Alpha-Bisabolene (mg/g)', ''),
                        'Alpha-Bulnesene (mg/g)': row_dict.get('Alpha-Bulnesene (mg/g)', ''),
                        'Alpha-Farnesene (mg/g)': row_dict.get('Alpha-Farnesene (mg/g)', ''),
                        'Alpha-Maaliene (mg/g)': row_dict.get('Alpha-Maaliene (mg/g)', ''),
                        'Alpha-Ocimene (mg/g)': row_dict.get('Alpha-Ocimene (mg/g)', ''),
                        'Alpha-Phellandrene (mg/g)': row_dict.get('Alpha-Phellandrene (mg/g)', ''),
                        'Alpha-Pinene (mg/g)': row_dict.get('Alpha-Pinene (mg/g)', ''),
                        'Alpha-Terpinene (mg/g)': row_dict.get('Alpha-Terpinene (mg/g)', ''),
                        'Alpha-Thujone (mg/g)': row_dict.get('Alpha-Thujone (mg/g)', ''),
                        'Beta-Farnesene (mg/g)': row_dict.get('Beta-Farnesene (mg/g)', ''),
                        'Beta-Maaliene (mg/g)': row_dict.get('Beta-Maaliene (mg/g)', ''),
                        'Alpha-Maaliene (mg/g)': row_dict.get('Alpha-Maaliene (mg/g)', ''),
                        'Beta-Ocimene (mg/g)': row_dict.get('Beta-Ocimene (mg/g)', ''),
                        'Beta-Pinene (mg/g)': row_dict.get('Beta-Pinene (mg/g)', ''),
                        'Gamma-Terpinene (mg/g)': row_dict.get('Gamma-Terpinene (mg/g)', ''),
                        # Generic column placeholders for any additional Excel columns
                        'AL': row_dict.get('AL', ''),
                        'AM': row_dict.get('AM', ''),
                        'AN': row_dict.get('AN', ''),
                        'AO': row_dict.get('AO', ''),
                        'AP': row_dict.get('AP', ''),
                        'AQ': row_dict.get('AQ', ''),
                        'AR': row_dict.get('AR', ''),
                        'AS': row_dict.get('AS', ''),
                        'AT': row_dict.get('AT', ''),
                        'AU': row_dict.get('AU', ''),
                        'AV': row_dict.get('AV', ''),
                        'AW': row_dict.get('AW', ''),
                        'AX': row_dict.get('AX', ''),
                        'AY': row_dict.get('AY', ''),
                        'AZ': row_dict.get('AZ', ''),
                        'BA': row_dict.get('BA', ''),
                        'BB': row_dict.get('BB', ''),
                        'BC': row_dict.get('BC', ''),
                        'BD': row_dict.get('BD', ''),
                        'BE': row_dict.get('BE', ''),
                        'BF': row_dict.get('BF', ''),
                        'BG': row_dict.get('BG', ''),
                        'BH': row_dict.get('BH', ''),
                        'BI': row_dict.get('BI', ''),
                        'BJ': row_dict.get('BJ', ''),
                        'BK': row_dict.get('BK', ''),
                        'BL': row_dict.get('BL', ''),
                        'BM': row_dict.get('BM', ''),
                        'BN': row_dict.get('BN', ''),
                        'BO': row_dict.get('BO', ''),
                        'BP': row_dict.get('BP', ''),
                        'BQ': row_dict.get('BQ', ''),
                        'BR': row_dict.get('BR', ''),
                        'BS': row_dict.get('BS', ''),
                        'BT': row_dict.get('BT', ''),
                        'BU': row_dict.get('BU', ''),
                        'BV': row_dict.get('BV', ''),
                        'BW': row_dict.get('BW', ''),
                        'BX': row_dict.get('BX', ''),
                        'BY': row_dict.get('BY', ''),
                        'BZ': row_dict.get('BZ', ''),
                        'CA': row_dict.get('CA', ''),
                        'CB': row_dict.get('CB', ''),
                        'CC': row_dict.get('CC', ''),
                        'CD': row_dict.get('CD', ''),
                        'CE': row_dict.get('CE', ''),
                        'CF': row_dict.get('CF', ''),
                        'CG': row_dict.get('CG', ''),
                        'CH': row_dict.get('CH', ''),
                        'CI': row_dict.get('CI', ''),
                        'CJ': row_dict.get('CJ', ''),
                        'CK': row_dict.get('CK', ''),
                        'CL': row_dict.get('CL', ''),
                        'CM': row_dict.get('CM', ''),
                        'CN': row_dict.get('CN', ''),
                        'CO': row_dict.get('CO', ''),
                        'CP': row_dict.get('CP', ''),
                        'CQ': row_dict.get('CQ', ''),
                        'CR': row_dict.get('CR', ''),
                        'CS': row_dict.get('CS', ''),
                        'CT': row_dict.get('CT', ''),
                        'CU': row_dict.get('CU', ''),
                        'CV': row_dict.get('CV', ''),
                        'CW': row_dict.get('CW', ''),
                        'CX': row_dict.get('CX', ''),
                        'CY': row_dict.get('CY', ''),
                        'CZ': row_dict.get('CZ', '')
                    }
                    
                    # Skip rows without product name - check multiple possible column names
                    product_name = (product_data.get('ProductName') or 
                                  product_data.get('Product Name*') or 
                                  product_data.get('Product Name') or 
                                  product_data.get('product_name') or 
                                  '')
                    
                    # Enhanced validation: Skip blank or invalid entries
                    if not product_name or str(product_name).strip() == '' or str(product_name).lower() in ['nan', 'none', 'null', '']:
                        logger.warning(f"Row {index + 1}: Skipping blank/invalid product name: '{product_name}'")
                        continue
                    
                    # Skip rows with only whitespace or special characters
                    if str(product_name).strip() == '' or len(str(product_name).strip()) < 2:
                        logger.warning(f"Row {index + 1}: Skipping product name too short or only whitespace: '{product_name}'")
                        continue
                    
                    # Update the product data with the found name
                    product_data['Product Name*'] = str(product_name).strip()
                    
                    # Additional validation: Skip rows with missing essential data
                    vendor = product_data.get('Vendor', '').strip()
                    product_type = product_data.get('Product Type*', '').strip()
                    
                    if not vendor or str(vendor).lower() in ['nan', 'none', 'null', '']:
                        logger.warning(f"Row {index + 1}: Skipping product '{product_name}' - missing vendor information")
                        continue
                    
                    if not product_type or str(product_type).lower() in ['nan', 'none', 'null', '']:
                        logger.warning(f"Row {index + 1}: Skipping product '{product_name}' - missing product type")
                        continue
                    
                    # Skip duplicate entries within the same upload (same name + vendor + type combination)
                    duplicate_key = f"{product_name}|{vendor}|{product_type}"
                    if duplicate_key in self._current_upload_products:
                        skipped_duplicates += 1
                        logger.warning(f"Row {index + 1}: Skipping duplicate product '{product_name}' from same vendor '{vendor}' and type '{product_type}'")
                        continue
                    
                    # Track this product to prevent duplicates within the same upload
                    self._current_upload_products.add(duplicate_key)
                    
                    # Store the product in database
                    product_id = self.add_or_update_product(product_data)
                    if product_id:
                        stored_count += 1
                    elif product_id is None:
                        # Product was skipped as duplicate
                        skipped_duplicates += 1
                        logger.info(f"Row {index + 1}: Skipped duplicate product '{product_name}'")
                        continue
                    else:
                        error_count += 1
                        errors.append(f"Row {index + 1}: Failed to store product")
                        
                except Exception as row_error:
                    error_count += 1
                    errors.append(f"Row {index + 1}: {str(row_error)}")
                    logger.error(f"Error processing row {index + 1}: {row_error}")
                    continue
            
            # Calculate excluded counts
            excluded_count = len(df) - len(filtered_df)
            blank_entries_skipped = len(df) - len(filtered_df) - excluded_count
            
            result = {
                'stored': stored_count,
                'updated': updated_count,
                'skipped_duplicates': skipped_duplicates,
                'errors': error_count,
                'excluded_json_matches': excluded_count,
                'blank_entries_skipped': blank_entries_skipped,
                'total_rows': len(df),
                'filtered_rows': len(filtered_df),
                'source_file': source_file,
                'message': f'Successfully processed {stored_count} products (new data replaces existing), skipped {skipped_duplicates} duplicates, {error_count} errors, excluded {excluded_count} JSON matched tags, skipped {blank_entries_skipped} blank entries'
            }
            
            if errors:
                result['error_details'] = errors[:10]  # Limit error details to first 10
            
            print(f"🔍 DEBUG: Database storage completed - Stored: {stored_count}, Updated: {updated_count}, Errors: {error_count}")
            logger.info(f"Excel data storage completed: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"Error storing Excel data: {e}")
            return {'stored': 0, 'updated': 0, 'errors': 1, 'excluded_json_matches': 0, 'message': f'Storage failed: {str(e)}'}
    
    def cleanup_blank_entries(self) -> Dict[str, Any]:
        """
        Clean up existing blank entries in the database.
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Find and count blank entries
            cursor.execute('''
                SELECT COUNT(*) FROM products 
                WHERE "Product Name*" IS NULL 
                   OR "Product Name*" = '' 
                   OR "Product Name*" = 'nan' 
                   OR "Product Name*" = 'None' 
                   OR "Product Name*" = 'null'
                   OR LENGTH(TRIM("Product Name*")) < 2
            ''')
            
            blank_count = cursor.fetchone()[0]
            
            if blank_count == 0:
                return {
                    'cleaned': 0,
                    'message': 'No blank entries found in database'
                }
            
            # Delete blank entries
            cursor.execute('''
                DELETE FROM products 
                WHERE "Product Name*" IS NULL 
                   OR "Product Name*" = '' 
                   OR "Product Name*" = 'nan' 
                   OR "Product Name*" = 'None' 
                   OR "Product Name*" = 'null'
                   OR LENGTH(TRIM("Product Name*")) < 2
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} blank entries from database")
            
            return {
                'cleaned': deleted_count,
                'message': f'Successfully cleaned up {deleted_count} blank entries from database'
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up blank entries: {e}")
            return {
                'cleaned': 0,
                'error': str(e),
                'message': f'Failed to clean up blank entries: {str(e)}'
            }
    
    def _filter_json_matched_tags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out JSON matched tags from the DataFrame.
        
        Args:
            df: DataFrame to filter
            
        Returns:
            Filtered DataFrame with JSON matched tags removed
        """
        try:
            if df is None or df.empty:
                return df
            
            # Create a copy to avoid modifying the original
            filtered_df = df.copy()
            
            # Define JSON match indicators
            json_match_indicators = [
                'Source', 'ai_match_score', 'ai_confidence', 'ai_match_type',
                'json_match_score', 'json_confidence', 'json_match_type',
                'match_score', 'confidence', 'match_type'
            ]
            
            # Create a mask for JSON matched tags
            json_match_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            
            for col in json_match_indicators:
                if col in filtered_df.columns:
                    if col == 'Source':
                        # Look for JSON match indicators in Source column
                        json_match_mask |= filtered_df[col].astype(str).str.contains(
                            'JSON Match|AI Match|JSON|AI|Match|Generated', 
                            case=False, 
                            na=False
                        )
                    else:
                        # Look for non-null values in other JSON match columns
                        json_match_mask |= filtered_df[col].notna()
            
            # Apply the filter
            original_count = len(filtered_df)
            filtered_df = filtered_df[~json_match_mask]
            filtered_count = len(filtered_df)
            excluded_count = original_count - filtered_count
            
            if excluded_count > 0:
                logger.info(f"Filtered out {excluded_count} JSON matched tags, {filtered_count} rows remaining for database storage")
                
                # Log some examples of excluded tags for debugging
                excluded_examples = df[json_match_mask].head(3)
                for idx, row in excluded_examples.iterrows():
                    source_info = row.get('Source', 'Unknown') if 'Source' in row else 'No Source'
                    logger.debug(f"Excluded JSON matched tag: {row.get('Product Name*', row.get('ProductName', 'Unknown'))} (Source: {source_info})")
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error filtering JSON matched tags: {e}")
            # Return original DataFrame if filtering fails
            return df
    
    @timed_operation("get_strain_info")
    def get_strain_info(self, strain_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific strain (with caching)."""
        try:
            self.init_database()  # Ensure DB is initialized
            normalized_name = self._normalize_strain_name(strain_name)
            cache_key = self._get_cache_key("strain_info", normalized_name)
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, strain_name, canonical_lineage, total_occurrences, lineage_confidence, first_seen_date, last_seen_date, sovereign_lineage
                FROM strains 
                WHERE normalized_name = ?
            ''', (normalized_name,))
            result = cursor.fetchone()
            if result:
                strain_id = result[0]
                sovereign_lineage = result[7]
                canonical_lineage = result[2]
                # Use sovereign_lineage if set, else mode, else canonical
                display_lineage = None
                if sovereign_lineage and sovereign_lineage.strip():
                    display_lineage = sovereign_lineage
                else:
                    mode_lineage = self.get_mode_lineage(strain_id)
                    if mode_lineage:
                        display_lineage = mode_lineage
                    else:
                        display_lineage = canonical_lineage
                strain_info = {
                    'id': result[0],
                    'strain_name': result[1],
                    'canonical_lineage': canonical_lineage,
                    'total_occurrences': result[3],
                    'lineage_confidence': result[4],
                    'first_seen_date': result[5],
                    'last_seen_date': result[6],
                    'sovereign_lineage': sovereign_lineage,
                    'display_lineage': display_lineage
                }
                self._set_cache(cache_key, strain_info, ttl=300)
                return strain_info
            return None
        except Exception as e:
            logger.error(f"Error getting strain info for '{strain_name}': {e}")
            return None
    
    @timed_operation("get_product_info")
    def get_product_info(self, product_name: str, vendor: str = None, brand: str = None) -> Optional[Dict[str, Any]]:
        """Get information about a specific product (with caching)."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            normalized_name = self._normalize_product_name(product_name)
            cache_key = self._get_cache_key("product_info", normalized_name, vendor, brand)
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if vendor and brand:
                cursor.execute('''
                    SELECT p.id, p."Product Name*", p.normalized_name, p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                           s.strain_name, s.canonical_lineage, 0 as total_occurrences, '' as first_seen_date, '' as last_seen_date,
                           p."Description", p."Weight*", p."Units", p."Price"
                    FROM products p
                    LEFT JOIN strains s ON p.strain_id = s.id
                    WHERE p.normalized_name = ? AND p."Vendor/Supplier*" = ? AND p."Product Brand" = ?
                ''', (normalized_name, vendor, brand))
            else:
                cursor.execute('''
                    SELECT p.id, p."Product Name*", p.normalized_name, p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                           s.strain_name, s.canonical_lineage, 0 as total_occurrences, '' as first_seen_date, '' as last_seen_date,
                           p."Description", p."Weight*", p."Units", p."Price"
                    FROM products p
                    LEFT JOIN strains s ON p.strain_id = s.id
                    WHERE p.normalized_name = ?
                ''', (normalized_name,))
            
            result = cursor.fetchone()
            if result:
                product_info = {
                    'id': result[0],
                    'product_name': result[1],
                    'normalized_name': result[2],
                    'product_type': result[3],
                    'vendor': result[4],
                    'brand': result[5],
                    'lineage': result[6],
                    'strain_name': result[7],
                    'canonical_lineage': result[8],
                    'total_occurrences': result[9],
                    'first_seen_date': result[10],
                    'last_seen_date': result[11],
                    'description': result[12],
                    'weight': result[13],
                    'units': result[14],
                    'price': result[15]
                }
                
                # Cache the result for 5 minutes
                self._set_cache(cache_key, product_info, ttl=300)
                return product_info
            return None
            
        except Exception as e:
            logger.error(f"Error getting product info for '{product_name}': {e}")
            return None
    
    def validate_and_suggest_lineage(self, strain_name: str, proposed_lineage: str = None) -> Dict[str, Any]:
        """Validate strain lineage against database and suggest corrections."""
        try:
            strain_info = self.get_strain_info(strain_name)
            
            if not strain_info:
                return {
                    'valid': True,
                    'suggestion': proposed_lineage,
                    'confidence': 0.0,
                    'reason': 'New strain'
                }
            
            canonical_lineage = strain_info['canonical_lineage']
            occurrences = strain_info['total_occurrences']
            
            if not canonical_lineage:
                return {
                    'valid': True,
                    'suggestion': proposed_lineage,
                    'confidence': 0.0,
                    'reason': 'Strain exists but no lineage recorded'
                }
            
            # Calculate confidence based on occurrences
            confidence = min(occurrences / 10.0, 1.0)  # Max confidence at 10+ occurrences
            
            if proposed_lineage == canonical_lineage:
                return {
                    'valid': True,
                    'suggestion': canonical_lineage,
                    'confidence': confidence,
                    'reason': 'Matches database'
                }
            elif proposed_lineage:
                return {
                    'valid': False,
                    'suggestion': canonical_lineage,
                    'confidence': confidence,
                    'reason': f'Database suggests {canonical_lineage} (seen {occurrences} times)'
                }
            else:
                return {
                    'valid': True,
                    'suggestion': canonical_lineage,
                    'confidence': confidence,
                    'reason': f'Database suggests {canonical_lineage} (seen {occurrences} times)'
                }
                
        except Exception as e:
            logger.error(f"Error validating lineage for '{strain_name}': {e}")
            return {
                'valid': True,
                'suggestion': proposed_lineage,
                'confidence': 0.0,
                'reason': 'Error occurred during validation'
            }
    
    @timed_operation("get_strain_statistics")
    def get_strain_statistics(self) -> Dict[str, Any]:
        """Get statistics about strains in the database, excluding MIXED, CBD Blend, and Paraphernalia from stats."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total strains
            cursor.execute('SELECT COUNT(*) FROM strains')
            total_strains = cursor.fetchone()[0]
            
            # Strains by lineage (exclude unwanted)
            cursor.execute('''
                SELECT canonical_lineage, COUNT(*) 
                FROM strains 
                WHERE canonical_lineage IS NOT NULL 
                GROUP BY canonical_lineage
            ''')
            lineage_counts = dict(cursor.fetchall())
            # Exclude unwanted
            exclude_keys = {k.lower() for k in ['MIXED', 'CBD Blend', 'Paraphernalia']}
            lineage_counts = {k: v for k, v in lineage_counts.items() if k and k.strip().lower() not in exclude_keys}
            
            # Most common strains (exclude unwanted)
            cursor.execute('''
                SELECT strain_name, total_occurrences, canonical_lineage
                FROM strains 
                ORDER BY total_occurrences DESC 
                LIMIT 50
            ''')
            top_strains_raw = cursor.fetchall()
            top_strains = [
                {'name': name, 'occurrences': count}
                for name, count, lineage in top_strains_raw
                if lineage and lineage.strip().lower() not in exclude_keys and name and name.strip().lower() not in exclude_keys
            ][:10]
            
            # Total products
            cursor.execute('SELECT COUNT(*) FROM products')
            total_products = cursor.fetchone()[0]
            
            # Vendor statistics - use correct Excel column names
            cursor.execute('''
                SELECT "Vendor/Supplier*", COUNT(*) as count
                FROM products 
                WHERE "Vendor/Supplier*" IS NOT NULL AND "Vendor/Supplier*" != ''
                GROUP BY "Vendor/Supplier*"
                ORDER BY count DESC
                LIMIT 20
            ''')
            vendor_stats = [{'vendor': vendor, 'count': count} for vendor, count in cursor.fetchall()]
            
            # Brand statistics - use correct Excel column names
            cursor.execute('''
                SELECT "Product Brand", COUNT(*) as count
                FROM products 
                WHERE "Product Brand" IS NOT NULL AND "Product Brand" != ''
                GROUP BY "Product Brand"
                ORDER BY count DESC
                LIMIT 20
            ''')
            brand_stats = [{'brand': brand, 'count': count} for brand, count in cursor.fetchall()]
            
            # Product type statistics - use correct Excel column names
            cursor.execute('''
                SELECT "Product Type*", COUNT(*) as count
                FROM products 
                WHERE "Product Type*" IS NOT NULL AND "Product Type*" != ''
                GROUP BY "Product Type*"
                ORDER BY count DESC
                LIMIT 20
            ''')
            product_type_stats = [{'product_type': product_type, 'count': count} for product_type, count in cursor.fetchall()]
            
            # Vendor-Brand combinations - use correct Excel column names
            cursor.execute('''
                SELECT "Vendor/Supplier*", "Product Brand", COUNT(*) as count
                FROM products 
                WHERE "Vendor/Supplier*" IS NOT NULL AND "Vendor/Supplier*" != '' AND "Product Brand" IS NOT NULL AND "Product Brand" != ''
                GROUP BY "Vendor/Supplier*", "Product Brand"
                ORDER BY count DESC
                LIMIT 15
            ''')
            vendor_brand_stats = [{'vendor': vendor, 'brand': brand, 'count': count} for vendor, brand, count in cursor.fetchall()]
            
            return {
                'total_strains': total_strains,
                'total_products': total_products,
                'lineage_distribution': lineage_counts,
                'top_strains': top_strains,
                'vendor_statistics': vendor_stats,
                'brand_statistics': brand_stats,
                'product_type_statistics': product_type_stats,
                'vendor_brand_combinations': vendor_brand_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting strain statistics: {e}")
            return {}
    
    def export_database(self, output_path: str):
        """Export database to Excel file."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Database should already be initialized with all required columns
            # No need to add missing columns during export
            
            # Export strains
            strains_df = pd.read_sql_query('''
                SELECT strain_name, canonical_lineage, total_occurrences, first_seen_date, last_seen_date
                FROM strains
                ORDER BY total_occurrences DESC
            ''', conn)
            
            # Get available columns dynamically to avoid SQL errors
            cursor.execute("PRAGMA table_info(products)")
            product_columns = {row[1] for row in cursor.fetchall()}
            
            # Define column groups in order of preference (using actual column names without quotes)
            column_groups = [
                # Core columns that should always exist
                ['Product Name*', 'Product Type*', 'Vendor/Supplier*', 'Product Brand', 'Lineage'],
                # Basic product info
                ['Description', 'Weight*', 'Weight Unit* (grams/gm or ounces/oz)', 'Price* (Tier Name for Bulk)', 'Product Strain', 'Quantity*'],
                # Test results
                ['Test result unit (% or mg)'],
                # Additional product details
                ['DOH', 'Concentrate Type', 'Ratio', 'JointRatio', 'State'],
                # Product flags
                ['Is Sample? (yes/no)', 'Is MJ product?(yes/no)', 'Discountable? (yes/no)', 'Room*'],
                # Batch and inventory info
                ['Batch Number', 'Lot Number', 'Barcode*'],
                # Medical and pricing
                ['Medical Only (Yes/No)', 'Med Price', 'Expiration Date(YYYY-MM-DD)'],
                # Additional fields
                ['Is Archived? (yes/no)', 'THC Per Serving', 'Allergens', 'Solvent'],
                # Metadata
                ['Accepted Date', 'Internal Product Identifier', 'Product Tags (comma separated)', 'Image URL', 'Ingredients'],
                # THC/CBD data
                ['Total THC', 'THCA', 'CBDA', 'CBN'],
                # Excel compatibility columns
                ['ProductName', 'Units', 'Price', 'Joint Ratio', 'Quantity Received*', 'qty']
            ]
            
            # Use the same approach as get_all_products for consistency
            cursor.execute('''
                SELECT p.id, p."Product Name*", p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                       p."Description", p."Weight*", p."Weight Unit* (grams/gm or ounces/oz)", p."Price* (Tier Name for Bulk)", 
                       p."Quantity*", p."DOH", p."Concentrate Type", p."Ratio", p."JointRatio", p."State", p."Is Sample? (yes/no)",
                       p."Is MJ product?(yes/no)", p."Discountable? (yes/no)", p."Room*", p."Batch Number", p."Lot Number", p."Barcode*",
                       p."Medical Only (Yes/No)", p."Med Price", p."Expiration Date(YYYY-MM-DD)", p."Is Archived? (yes/no)", p."THC Per Serving", p."Allergens",
                       p."Solvent", p."Accepted Date", p."Internal Product Identifier", p."Product Tags (comma separated)", p."Image URL", p."Ingredients",
                       p."CombinedWeight", p."Total THC", p."THCA", p."CBDA", p."CBN",
                       p."DOH Compliant (Yes/No)"
                FROM products p
                ORDER BY p.id
            ''')
            
            results = cursor.fetchall()
            products_data = []
            
            # Debug logging
            logger.info(f"Number of results: {len(results)}")
            if results:
                logger.info(f"Number of columns in first result: {len(results[0])}")
            
            for result in results:
                product = {
                    'id': result[0],
                    'Product Name*': result[1],
                    'Product Type*': result[2],
                    'Vendor/Supplier*': result[3],
                    'Product Brand': result[4],
                    'Lineage': result[5],
                    'Description': result[6],
                    'Weight*': result[7],
                    'Weight Unit* (grams/gm or ounces/oz)': result[8],
                    'Price* (Tier Name for Bulk)': result[9],
                    'Quantity*': result[10],
                    'DOH': result[11],
                    'Concentrate Type': result[12],
                    'Ratio': result[13],
                    'JointRatio': result[14],
                    'State': result[15],
                    'Is Sample? (yes/no)': result[16],
                    'Is MJ product?(yes/no)': result[17],
                    'Discountable? (yes/no)': result[18],
                    'Room*': result[19],
                    'Batch Number': result[20],
                    'Lot Number': result[21],
                    'Barcode*': result[22],
                    'Medical Only (Yes/No)': result[23],
                    'Med Price': result[24],
                    'Expiration Date(YYYY-MM-DD)': result[25],
                    'Is Archived? (yes/no)': result[26],
                    'THC Per Serving': result[27],
                    'Allergens': result[28],
                    'Solvent': result[29],
                    'Accepted Date': result[30],
                    'Internal Product Identifier': result[31],
                    'Product Tags (comma separated)': result[32],
                    'Image URL': result[33],
                    'Ingredients': result[34],
                    'CombinedWeight': result[35],
                    'Total THC': result[36],
                    'THCA': result[37],
                    'CBDA': result[38],
                    'CBN': result[39],
                    'DOH Compliant (Yes/No)': result[40]
                }
                products_data.append(product)
            
            # Convert to DataFrame
            products_df = pd.DataFrame(products_data)
            
            # Export to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                strains_df.to_excel(writer, sheet_name='Strains', index=False)
                products_df.to_excel(writer, sheet_name='Products', index=False)
            
            logger.info(f"Database exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            raise
    
    def update_all_descriptions(self) -> Dict[str, Any]:
        """Update ALL Description column values with formula-created values from Product Name*."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products with their Product Name* values
            cursor.execute('''
                SELECT id, "Product Name*" FROM products 
                WHERE "Product Name*" IS NOT NULL AND "Product Name*" != ""
            ''')
            
            products_to_update = cursor.fetchall()
            updated_count = 0
            
            for product_id, product_name in products_to_update:
                # Generate description using the comprehensive processing formula
                new_description = self._process_description(product_name, '')
                
                # Update the Description column
                cursor.execute('''
                    UPDATE products 
                    SET "Description" = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_description, datetime.now().isoformat(), product_id))
                updated_count += 1
            
            conn.commit()
            logger.info(f"Updated {updated_count} product descriptions with formula-created values")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} product descriptions with formula-created values'
            }
            
        except Exception as e:
            logger.error(f"Error updating descriptions: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update descriptions: {str(e)}'
            }

    def populate_missing_columns(self) -> Dict[str, Any]:
        """Populate missing columns in existing products with default values."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products that need updating
            cursor.execute('''
                SELECT id, "Product Name*", "Product Type*", "Weight*", "Price* (Tier Name for Bulk)", 
                       "Quantity*", "DOH", "Concentrate Type", "Ratio", "JointRatio", "State"
                FROM products 
                WHERE "DOH Compliant (Yes/No)" IS NULL 
                   OR "Description" IS NULL 
                   OR "Description" = ''
            ''')
            
            products_to_update = cursor.fetchall()
            updated_count = 0
            
            for product in products_to_update:
                product_id, name, product_type, weight, price, quantity, doh, concentrate_type, ratio, joint_ratio, state = product
                
                # Set default values for missing columns
                updates = []
                values = []
                
                if not doh or doh == 'None':
                    updates.append('"DOH" = ?')
                    values.append('No')
                    doh = 'No'  # Update the variable for later use
                
                if not concentrate_type or concentrate_type == 'None':
                    updates.append('"Concentrate Type" = ?')
                    values.append('')
                
                if not ratio or ratio == 'None':
                    updates.append('"Ratio" = ?')
                    values.append('')
                
                if not joint_ratio or joint_ratio == 'None':
                    # Calculate joint ratio for pre-roll products
                    if product_type and 'pre-roll' in str(product_type).lower():
                        joint_ratio = self._calculate_joint_ratio_from_name(name, product_type, weight)
                    else:
                        joint_ratio = ''
                    updates.append('"JointRatio" = ?')
                    values.append(joint_ratio)
                
                if not state or state == 'None':
                    updates.append('"State" = ?')
                    values.append('active')
                
                # Set other missing columns with defaults (only for columns that exist)
                # Check which columns exist in the database
                cursor.execute("PRAGMA table_info(products)")
                existing_columns = {row[1] for row in cursor.fetchall()}
                
                # Define column mappings with existence checks
                column_mappings = [
                    ('"Description"', self._get_description(name)),
                    ('"Is Sample? (yes/no)"', 'no'),
                    ('"Is MJ product?(yes/no)"', 'yes' if product_type and 'mj' in str(product_type).lower() else 'no'),
                    ('"Discountable? (yes/no)"', 'yes'),
                    ('"Room*"', 'Default'),
                    ('"Batch Number"', ''),
                    ('"Lot Number"', ''),
                    ('"Barcode*"', ''),
                    ('"Medical Only (Yes/No)"', 'No'),
                    ('"Med Price"', ''),
                    ('"Expiration Date(YYYY-MM-DD)"', ''),
                    ('"Is Archived? (yes/no)"', 'no'),
                    ('"THC Per Serving"', ''),
                    ('"Allergens"', ''),
                    ('"Solvent"', ''),
                    ('"Accepted Date"', ''),
                    ('"Internal Product Identifier"', ''),
                    ('"Product Tags (comma separated)"', ''),
                    ('"Image URL"', ''),
                    ('"Ingredients"', ''),
                    ('"CombinedWeight"', ''),
                    ('"Ratio_or_THC_CBD"', ''),
                    ('"Description_Complexity"', ''),
                    ('"Total THC"', ''),
                    ('"THCA"', ''),
                    ('"CBDA"', ''),
                    ('"CBN"', ''),
                    ('"Units"', 'g'),
                    ('"Price"', price or ''),
                    ('"DOH Compliant (Yes/No)"', doh),
                    ('"Joint Ratio"', joint_ratio),
                    ('"Quantity Received*"', quantity or '')
                ]
                
                # Only add columns that exist in the database
                for col_name, default_value in column_mappings:
                    if col_name.strip('"') in existing_columns:
                        updates.append(f'{col_name} = ?')
                        values.append(default_value)
                
                if updates:
                    values.append(product_id)
                    update_query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(update_query, values)
                    updated_count += 1
            
            conn.commit()
            logger.info(f"Updated {updated_count} products with missing column data")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} products with missing column data'
            }
            
        except Exception as e:
            logger.error(f"Error populating missing columns: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to populate missing columns: {str(e)}'
            }
    
    def _get_description(self, product_name):
        """Generate description from product name by removing vendor information."""
        if not product_name:
            return ""
        
        name = str(product_name).strip()
        if not name:
            return ""
        
        # Remove everything after " by " or " By " to eliminate vendor information
        if ' by ' in name:
            return name.split(' by ')[0].strip()
        elif ' By ' in name:
            return name.split(' By ')[0].strip()
        
        # If no "by" pattern, return the name as-is
        return name.strip()
    
    def _calculate_joint_ratio_from_name(self, product_name, product_type, weight):
        """Calculate joint ratio for pre-roll products from product name."""
        if not product_name or not product_type or 'pre-roll' not in str(product_type).lower():
            return ''
        
        import re
        product_name_str = str(product_name)
        
        # Look for patterns like "0.5g x 2 Pack", "1g x 28 Pack", etc.
        patterns = [
            r'(\d+(?:\.\d+)?)g\s*x\s*(\d+)\s*pack',  # "0.5g x 2 Pack"
            r'(\d+(?:\.\d+)?)g\s*x\s*(\d+)',         # "0.5g x 2"
            r'(\d+(?:\.\d+)?)g\s*×\s*(\d+)',         # "0.5g × 2" (different x character)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name_str, re.IGNORECASE)
            if match:
                amount = match.group(1)
                count = match.group(2)
                try:
                    count_int = int(count)
                    if count_int == 1:
                        return f"{amount}g"
                    else:
                        return f"{amount}g x {count} Pack"
                except ValueError:
                    continue
        
        # If no pattern found, try to generate from weight
        if weight and str(weight).strip() != '' and str(weight).lower() != 'nan':
            try:
                weight_float = float(weight)
                if weight_float == 1.0:
                    return "1g"
                else:
                    # Format weight similar to price formatting - no decimals unless original has decimals
                    if weight_float.is_integer():
                        formatted_weight = f"{int(weight_float)}g"
                    else:
                        # Round to 2 decimal places and remove trailing zeros
                        formatted_weight = f"{weight_float:.2f}".rstrip("0").rstrip(".") + "g"
                    return formatted_weight
            except (ValueError, TypeError):
                pass
        
        return ''

    def _add_missing_columns_safe(self, cursor, conn):
        """Safely add missing columns to existing tables without losing data."""
        try:
            from datetime import datetime
            # Check if we've already run this migration to avoid repeated attempts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_migration_log'")
            if not cursor.fetchone():
                cursor.execute("CREATE TABLE _migration_log (migration_name TEXT PRIMARY KEY, applied_date TEXT)")
                conn.commit()
            
            # Check if column migration has already been applied
            cursor.execute("SELECT migration_name FROM _migration_log WHERE migration_name = 'column_migration_v2'")
            if cursor.fetchone():
                logger.debug("Column migration already applied, skipping")
                return
            
            # Also check if we've already run this migration in this session
            if hasattr(self, '_migration_applied'):
                logger.debug("Column migration already applied in this session, skipping")
                return
            
            # Check and add missing columns to products table
            cursor.execute("PRAGMA table_info(products)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            missing_columns = []
            
            # Define all expected columns using the actual database schema names
            expected_columns = [
                ('strain_id', 'INTEGER'),
                ('"Product Strain"', 'TEXT'),
                ('"Quantity*"', 'TEXT'),
                ('"DOH"', 'TEXT'),
                ('"Concentrate Type"', 'TEXT'),
                ('"Ratio"', 'TEXT'),
                ('"JointRatio"', 'TEXT'),
                ('"THC test result"', 'TEXT'),
                ('"CBD test result"', 'TEXT'),
                ('"Test result unit (% or mg)"', 'TEXT'),
                ('"State"', 'TEXT'),
                ('"Is Sample? (yes/no)"', 'TEXT'),
                ('"Is MJ product?(yes/no)"', 'TEXT'),
                ('"Discountable? (yes/no)"', 'TEXT'),
                ('"Room*"', 'TEXT'),
                ('"Batch Number"', 'TEXT'),
                ('"Lot Number"', 'TEXT'),
                ('"Barcode*"', 'TEXT'),
                ('"Medical Only (Yes/No)"', 'TEXT'),
                ('"Med Price"', 'TEXT'),
                ('"Expiration Date(YYYY-MM-DD)"', 'TEXT'),
                ('"Is Archived? (yes/no)"', 'TEXT'),
                # Excel processor compatibility columns
                ('"ProductName"', 'TEXT'),  # Alternative to "Product Name*"
                ('"Units"', 'TEXT'),  # Alternative to "Weight Unit* (grams/gm or ounces/oz)"
                ('"Price"', 'TEXT'),  # Alternative to "Price* (Tier Name for Bulk)"
                ('"DOH Compliant (Yes/No)"', 'TEXT'),  # Alternative to "DOH"
                ('"Joint Ratio"', 'TEXT'),  # Alternative to "JointRatio"
                ('"Quantity Received*"', 'TEXT'),  # Alternative to "Quantity*"
                ('"qty"', 'TEXT'),  # Alternative to "Quantity*"
                ('"THC Per Serving"', 'TEXT'),
                ('"Allergens"', 'TEXT'),
                ('"Solvent"', 'TEXT'),
                ('"Accepted Date"', 'TEXT'),
                ('"Internal Product Identifier"', 'TEXT'),
                ('"Product Tags (comma separated)"', 'TEXT'),
                ('"Image URL"', 'TEXT'),
                ('"Ingredients"', 'TEXT'),
                ('"CombinedWeight"', 'TEXT'),
                ('"Ratio_or_THC_CBD"', 'TEXT'),
                ('"Description_Complexity"', 'TEXT'),
                ('"Total THC"', 'TEXT'),
                ('"THCA"', 'TEXT'),
                ('"CBDA"', 'TEXT'),
                ('"CBN"', 'TEXT'),
                # Additional cannabinoid columns for comprehensive testing
                ('"THC"', 'TEXT'),
                ('"CBD"', 'TEXT'),
                ('"Total CBD"', 'TEXT'),
                ('"CBGA"', 'TEXT'),
                ('"CBG"', 'TEXT'),
                ('"Total CBG"', 'TEXT'),
                ('"CBC"', 'TEXT'),
                ('"CBDV"', 'TEXT'),
                ('"THCV"', 'TEXT'),
                ('"CBGV"', 'TEXT'),
                ('"CBNV"', 'TEXT'),
                ('"CBGVA"', 'TEXT'),
                # Calculated THC/CBD values
                ('"AI"', 'TEXT'),
                ('"AJ"', 'TEXT'),
                ('"AK"', 'TEXT'),
                # Terpene columns - using the actual schema names
                ('"A-Bisabolol (mg/g)"', 'TEXT'),
                ('"A-Humulene (mg/g)"', 'TEXT'),
                ('"A-Maaliene (mg/g)"', 'TEXT'),
                ('"A-Myrcene (mg/g)"', 'TEXT'),
                ('"A-Pinene (mg/g)"', 'TEXT'),
                ('"B-Caryophyllene (mg/g)"', 'TEXT'),
                ('b_myrcene_mg_g', 'TEXT'),
                ('b_pinene_mg_g', 'TEXT'),
                ('bisabolol_mg_g', 'TEXT'),
                ('borneol_mg_g', 'TEXT'),
                ('camphene_mg_g', 'TEXT'),
                ('camphor_mg_g', 'TEXT'),
                ('carene_mg_g', 'TEXT'),
                ('carvacrol_mg_g', 'TEXT'),
                ('carvone_mg_g', 'TEXT'),
                ('caryophyllene_mg_g', 'TEXT'),
                ('cedrol_mg_g', 'TEXT'),
                ('citral_mg_g', 'TEXT'),
                ('citronellol_mg_g', 'TEXT'),
                ('cymene_mg_g', 'TEXT'),
                ('delta_3_carene_mg_g', 'TEXT'),
                ('eucalyptol_mg_g', 'TEXT'),
                ('fenchol_mg_g', 'TEXT'),
                ('fenchone_mg_g', 'TEXT'),
                ('geraniol_mg_g', 'TEXT'),
                ('geranyl_acetate_mg_g', 'TEXT'),
                ('guaiol_mg_g', 'TEXT'),
                ('humulene_mg_g', 'TEXT'),
                ('isoborneol_mg_g', 'TEXT'),
                ('isobornyl_acetate_mg_g', 'TEXT'),
                ('isopulegol_mg_g', 'TEXT'),
                ('limonene_mg_g', 'TEXT'),
                ('linalool_mg_g', 'TEXT'),
                ('linalyl_acetate_mg_g', 'TEXT'),
                ('m_cymene_mg_g', 'TEXT'),
                ('menthal_mg_g', 'TEXT'),
                ('menthone_mg_g', 'TEXT'),
                ('myrcene_mg_g', 'TEXT'),
                ('nerolidol_mg_g', 'TEXT'),
                ('o_cymene_mg_g', 'TEXT'),
                ('ocimene_mg_g', 'TEXT'),
                ('p_cymene_mg_g', 'TEXT')
            ]
            
            for col_name, col_type in expected_columns:
                # Strip quotes for comparison with existing columns
                col_name_clean = col_name.strip('"')
                if col_name_clean not in existing_columns:
                    missing_columns.append((col_name, col_type))
            
            # Add missing columns
            for col_name, col_type in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added missing column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        logger.debug(f"Column {col_name} already exists, skipping")
                    else:
                        logger.warning(f"Could not add column {col_name}: {e}")
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
            
            if missing_columns:
                conn.commit()
                logger.info(f"Added {len(missing_columns)} missing columns to products table")
            
            # Log that this migration has been applied
            cursor.execute("INSERT OR REPLACE INTO _migration_log (migration_name, applied_date) VALUES (?, ?)", 
                          ('column_migration_v2', datetime.now().isoformat()))
            conn.commit()
            
            # Mark migration as applied in this session
            self._migration_applied = True
            
            # Check and add missing columns to strains table
            cursor.execute("PRAGMA table_info(strains)")
            existing_strain_columns = {row[1] for row in cursor.fetchall()}
            
            missing_strain_columns = []
            
            # Define expected strain columns
            expected_strain_columns = [
                ('lineage_confidence', 'REAL'),
                ('sovereign_lineage', 'TEXT')
            ]
            
            for col_name, col_type in expected_strain_columns:
                if col_name not in existing_strain_columns:
                    missing_strain_columns.append((col_name, col_type))
            
            # Add missing strain columns
            for col_name, col_type in missing_strain_columns:
                try:
                    cursor.execute(f"ALTER TABLE strains ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added missing strain column: {col_name}")
                except Exception as e:
                    logger.warning(f"Could not add strain column {col_name}: {e}")
            
            if missing_strain_columns:
                conn.commit()
                logger.info(f"Added {len(missing_strain_columns)} missing columns to strains table")
            
        except Exception as e:
            logger.error(f"Error adding missing columns: {e}")
            # Don't raise - continue with existing schema
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the database."""
        self._clean_expired_cache()
        return {
            'total_queries': self._timing_stats['queries'],
            'total_time': self._timing_stats['total_time'],
            'average_time': self._timing_stats['total_time'] / max(self._timing_stats['queries'], 1),
            'cache_hits': self._timing_stats['cache_hits'],
            'cache_misses': self._timing_stats['cache_misses'],
            'cache_hit_rate': self._timing_stats['cache_hits'] / max(self._timing_stats['cache_hits'] + self._timing_stats['cache_misses'], 1),
            'cache_size': len(self._cache),
            'initialized': self._initialized
        }
    
    def clear_cache(self):
        """Clear the cache."""
        with self._cache_lock:
            self._cache.clear()
        self._timing_stats['cache_hits'] = 0
        self._timing_stats['cache_misses'] = 0
    
    def close_connections(self):
        """Close all database connections."""
        for conn in self._connection_pool.values():
            conn.close()
        self._connection_pool.clear()
    
    def _normalize_strain_name(self, strain_name: str) -> str:
        """Normalize strain name for consistent matching."""
        if not isinstance(strain_name, str):
            return ""
        
        # Use the existing normalization function
        from .excel_processor import normalize_strain_name
        return normalize_strain_name(strain_name)
    
    def _normalize_product_name(self, product_name: str) -> str:
        """Normalize product name for consistent matching."""
        if not isinstance(product_name, str):
            return ""
        
        # Use the existing normalization function
        from .excel_processor import normalize_name
        return normalize_name(product_name)
    
    def _normalize_lineage(self, lineage: str) -> str:
        """Normalize lineage to proper ALL CAPS format."""
        if not lineage:
            return "HYBRID"  # Default to HYBRID
        
        lineage = str(lineage).strip().lower()
        
        # Map common variations to standard ALL CAPS format
        lineage_mapping = {
            'hybrid': 'HYBRID',
            'indica_hybrid': 'HYBRID/INDICA',
            'indica': 'INDICA',
            'sativa': 'SATIVA',
            'sativa_hybrid': 'HYBRID/SATIVA',
            'cbd': 'CBD',
            'mixed': 'HYBRID',  # Default mixed to hybrid
            'unknown': 'HYBRID',  # Default unknown to hybrid
            'none': 'HYBRID',  # Default none to hybrid
            '': 'HYBRID'  # Default empty to hybrid
        }
        
        return lineage_mapping.get(lineage, 'HYBRID')
    
    def _ensure_crucial_value(self, value, fallback, field_name):
        """Ensure crucial values are not empty, providing intelligent fallbacks."""
        if value is None or not value or str(value).strip() == '' or str(value).lower() in ['nan', 'none', 'null']:
            logger.debug(f"Missing crucial value for {field_name}, using fallback: {fallback}")
            return fallback
        return str(value).strip()
    
    def _calculate_ai_value(self, row_dict):
        """Calculate AI value (THC) using all available THC columns."""
        try:
            # Get THC values from all available columns
            total_thc_value = str(row_dict.get('Total THC', '') or '').strip()
            thc_content_value = str(row_dict.get('THC Content', row_dict.get('THCA', '')) or '').strip()
            thc_test_result = str(row_dict.get('THC test result', '') or '').strip()
            thc_cbd_value = str(row_dict.get('THC_CBD', '') or '').strip()
            
            # Clean up values
            if total_thc_value in ['nan', 'NaN', '']:
                total_thc_value = ''
            if thc_content_value in ['nan', 'NaN', '']:
                thc_content_value = ''
            if thc_test_result in ['nan', 'NaN', '']:
                thc_test_result = ''
            if thc_cbd_value in ['nan', 'NaN', '']:
                thc_cbd_value = ''
            
            # Helper function to safely convert to float
            def safe_float(value):
                if not value or value in ['nan', 'NaN', '']:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # Helper function to extract THC value from THC_CBD string
            def extract_thc_from_thc_cbd(thc_cbd_str):
                if not thc_cbd_str:
                    return 0.0
                try:
                    # Look for patterns like "18.5% THC / 0.5% CBD" or "0.3% THC / 900mg CBD"
                    import re
                    # Match THC value with %
                    thc_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*THC', thc_cbd_str, re.IGNORECASE)
                    if thc_match:
                        return float(thc_match.group(1))
                    return 0.0
                except (ValueError, AttributeError):
                    return 0.0
            
            # Calculate THC values from all sources
            total_thc_float = safe_float(total_thc_value)
            thc_content_float = safe_float(thc_content_value)
            thc_test_float = safe_float(thc_test_result)
            thc_cbd_thc_float = extract_thc_from_thc_cbd(thc_cbd_value)
            
            # Find the highest THC value from all sources
            thc_values = [
                (total_thc_float, total_thc_value),
                (thc_content_float, thc_content_value),
                (thc_test_float, thc_test_result),
                (thc_cbd_thc_float, str(thc_cbd_thc_float) if thc_cbd_thc_float > 0 else '')
            ]
            
            # Sort by float value (highest first) and return the first non-empty string value
            thc_values.sort(key=lambda x: x[0], reverse=True)
            
            for float_val, str_val in thc_values:
                if float_val > 0 and str_val:
                    return str_val
            
            # If no valid THC value found, return empty string
            return ''
        except Exception as e:
            logger.error(f"Error calculating AI value: {e}")
            return ''
    
    def _calculate_ak_value(self, row_dict):
        """Calculate AK value (CBD) using all available CBD columns."""
        try:
            # Get CBD values from all available columns
            total_cbd_value = str(row_dict.get('Total CBD', row_dict.get('CBDA', '')) or '').strip()
            cbd_test_result_value = str(row_dict.get('CBD test result', '') or '').strip()
            cbd_content_value = str(row_dict.get('CBD Content', '') or '').strip()
            thc_cbd_value = str(row_dict.get('THC_CBD', '') or '').strip()
            
            # Clean up values
            if total_cbd_value in ['nan', 'NaN', '']:
                total_cbd_value = ''
            if cbd_test_result_value in ['nan', 'NaN', '']:
                cbd_test_result_value = ''
            if cbd_content_value in ['nan', 'NaN', '']:
                cbd_content_value = ''
            if thc_cbd_value in ['nan', 'NaN', '']:
                thc_cbd_value = ''
            
            # Helper function to safely convert to float
            def safe_float(value):
                if not value or value in ['nan', 'NaN', '']:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # Helper function to extract CBD value from THC_CBD string
            def extract_cbd_from_thc_cbd(thc_cbd_str):
                if not thc_cbd_str:
                    return 0.0
                try:
                    # Look for patterns like "18.5% THC / 0.5% CBD" or "0.3% THC / 900mg CBD"
                    import re
                    # Match CBD value with % or mg
                    cbd_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|mg)?\s*CBD', thc_cbd_str, re.IGNORECASE)
                    if cbd_match:
                        return float(cbd_match.group(1))
                    return 0.0
                except (ValueError, AttributeError):
                    return 0.0
            
            # Calculate CBD values from all sources
            total_cbd_float = safe_float(total_cbd_value)
            cbd_test_result_float = safe_float(cbd_test_result_value)
            cbd_content_float = safe_float(cbd_content_value)
            thc_cbd_cbd_float = extract_cbd_from_thc_cbd(thc_cbd_value)
            
            # Find the highest CBD value from all sources
            cbd_values = [
                (total_cbd_float, total_cbd_value),
                (cbd_test_result_float, cbd_test_result_value),
                (cbd_content_float, cbd_content_value),
                (thc_cbd_cbd_float, str(thc_cbd_cbd_float) if thc_cbd_cbd_float > 0 else '')
            ]
            
            # Sort by float value (highest first) and return the first non-empty string value
            cbd_values.sort(key=lambda x: x[0], reverse=True)
            
            for float_val, str_val in cbd_values:
                if float_val > 0 and str_val:
                    return str_val
            
            # If no valid CBD value found, return empty string
            return ''
        except Exception as e:
            logger.error(f"Error calculating AK value: {e}")
            return ''
    
    def _update_existing_product(self, cursor, product_id, product_data):
        """Update an existing product with new data. New data always replaces old values."""
        try:
            current_date = datetime.now().isoformat()
            
            # Get current product data for comparison
            cursor.execute('SELECT "Price", "THC test result", "CBD test result", "Weight*", "Units" FROM products WHERE id = ?', (product_id,))
            current_data = cursor.fetchone()
            
            # Log changes for important fields
            if current_data:
                old_price, old_thc, old_cbd, old_weight, old_units = current_data
                new_price = product_data.get('Price', '')
                new_thc = product_data.get('THC test result', '')
                new_cbd = product_data.get('CBD test result', '')
                new_weight = product_data.get('Weight*', '')
                new_units = product_data.get('Units', '')
                
                changes = []
                if str(old_price) != str(new_price):
                    changes.append(f"Price: {old_price} → {new_price}")
                if str(old_thc) != str(new_thc):
                    changes.append(f"THC: {old_thc} → {new_thc}")
                if str(old_cbd) != str(new_cbd):
                    changes.append(f"CBD: {old_cbd} → {new_cbd}")
                if str(old_weight) != str(new_weight):
                    changes.append(f"Weight: {old_weight} → {new_weight}")
                if str(old_units) != str(new_units):
                    changes.append(f"Units: {old_units} → {new_units}")
                
                if changes:
                    logger.info(f"Product ID {product_id} data changes: {'; '.join(changes)}")
                else:
                    logger.info(f"Product ID {product_id} updated with same values (no changes detected)")
            
            # Calculate AI and AK values
            ai_value = self._calculate_ai_value(product_data)
            ak_value = self._calculate_ak_value(product_data)
            
            # Update the product with new data - NEW DATA ALWAYS REPLACES OLD VALUES
            cursor.execute('''
                UPDATE products SET
                    "Product Type*" = ?,
                    "Lineage" = ?,
                    "Vendor/Supplier*" = ?,
                    "Product Brand" = ?,
                    "Description" = ?,
                    "Weight*" = ?,
                    "Units" = ?,
                    "Price" = ?,
                    "Product Strain" = ?,
                    "Quantity*" = ?,
                    "DOH" = ?,
                    "Concentrate Type" = ?,
                    "Ratio" = ?,
                    "JointRatio" = ?,
                    "THC test result" = ?,
                    "CBD test result" = ?,
                    "Total THC" = ?,
                    "THCA" = ?,
                    "CBDA" = ?,
                    "THC" = ?,
                    "CBD" = ?,
                    "AI" = ?,
                    "AJ" = ?,
                    "AK" = ?,
                    "last_seen_date" = ?,
                    "updated_at" = ?
                WHERE id = ?
            ''', (
                product_data.get('Product Type*'),
                self._normalize_lineage(product_data.get('Lineage')),
                product_data.get('Vendor/Supplier*'),
                product_data.get('Product Brand'),
                product_data.get('Description'),
                product_data.get('Weight*'),
                product_data.get('Units'),
                product_data.get('Price'),
                self._calculate_product_strain_original(
                    product_data.get('Product Type*', ''),
                    product_data.get('Product Name*', ''),
                    product_data.get('Description', ''),
                    product_data.get('Ratio', '')
                ),
                product_data.get('Quantity*', ''),
                product_data.get('DOH', ''),
                product_data.get('Concentrate Type', ''),
                product_data.get('Ratio', ''),
                product_data.get('JointRatio', ''),
                product_data.get('THC test result', ''),
                product_data.get('CBD test result', ''),
                product_data.get('Total THC', ''),
                product_data.get('THCA', ''),
                product_data.get('CBDA', ''),
                product_data.get('THC', ''),
                product_data.get('CBD', ''),
                self._calculate_ai_value(product_data),
                product_data.get('THC Content', ''),
                self._calculate_ak_value(product_data),
                current_date,
                current_date,
                product_id
            ))
            
            logger.info(f"Successfully updated product ID {product_id} with new Excel data (old values replaced)")
            
        except Exception as e:
            logger.error(f"Error updating existing product {product_id}: {e}")
            raise
    
    def _process_description(self, product_name, original_description=''):
        """Process product name to create a clean description using the same rules as Excel processor."""
        if not product_name or str(product_name).strip() == '':
            return original_description if original_description else ''
        
        name = str(product_name).strip()
        if not name:
            return original_description if original_description else ''
        
        # Apply the same description processing rules as the Excel processor
        # Handle "Product Name by Vendor - Weight" format
        if ' by ' in name and ' - ' in name:
            # Extract just the product name part before " by "
            return name.split(' by ')[0].strip()
        elif ' by ' in name:
            return name.split(' by ')[0].strip()
        elif ' - ' in name:
            # Only split on dashes followed by weight information (numbers, decimals, units)
            import re
            if re.search(r' - [\d.]', name):
                # Remove weight part but preserve the dash in product names
                return re.sub(r' - [\d.].*$', '', name).strip()
            else:
                # No weight information, return the name as-is
                return name.strip()
        return name.strip()
    
    def fix_description_format(self):
        """Fix Description field format to extract just product name from 'Product Name by Vendor - Weight' format."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products with descriptions that contain " by " and " - "
            cursor.execute('''
                SELECT id, "Description", "Product Name*" 
                FROM products 
                WHERE "Description" LIKE '% by %' AND "Description" LIKE '% - %'
            ''')
            
            products_to_fix = cursor.fetchall()
            logger.info(f"Found {len(products_to_fix)} products with 'by Vendor - Weight' format in Description")
            
            fixed_count = 0
            for product_id, current_desc, product_name in products_to_fix:
                # Process the description to extract just the product name
                fixed_desc = self._process_description(current_desc, '')
                if fixed_desc != current_desc:
                    cursor.execute('''
                        UPDATE products 
                        SET "Description" = ?
                        WHERE id = ?
                    ''', (fixed_desc, product_id))
                    fixed_count += 1
                    logger.debug(f"Fixed Description for product {product_id}: '{current_desc}' -> '{fixed_desc}'")
            
            conn.commit()
            logger.info(f"Fixed {fixed_count} product descriptions")
            return {'fixed': fixed_count, 'total_checked': len(products_to_fix)}
            
        except Exception as e:
            logger.error(f"Error fixing description format: {e}")
            return {'fixed': 0, 'total_checked': 0, 'error': str(e)}

    def fix_all_description_values(self):
        """
        Comprehensive fix for all description values to ensure they meet Product Name transformation criteria.
        This function will:
        1. Replace Description with Product Name (everything before 'by')
        2. Remove vendor information after 'by'
        3. Remove weight information after ' - ' followed by numbers
        4. Clean parentheses and brackets but preserve content
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products that have both Product Name and Description AND valid IDs
            cursor.execute('''
                SELECT id, "Product Name*", "Description"
                FROM products 
                WHERE "Product Name*" IS NOT NULL AND "Product Name*" != '' AND id IS NOT NULL
            ''')
            
            all_products = cursor.fetchall()
            logger.info(f"Found {len(all_products)} products with Product Name and valid IDs to process")
            
            fixed_count = 0
            skipped_count = 0
            
            for product_id, product_name, current_desc in all_products:
                # Apply the same transformation logic as Excel processing
                # Use Product Name as base, everything before 'by'
                transformed_desc = self._process_description(product_name, current_desc)
                
                # Only update if the description would change
                if transformed_desc != current_desc:
                    cursor.execute('''
                        UPDATE products 
                        SET "Description" = ?
                        WHERE id = ?
                    ''', (transformed_desc, product_id))
                    fixed_count += 1
                    logger.debug(f"Fixed Description for product {product_id}: '{current_desc}' -> '{transformed_desc}'")
                else:
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Fixed {fixed_count} product descriptions, skipped {skipped_count} (already correct)")
            return {
                'fixed': fixed_count, 
                'skipped': skipped_count,
                'total_processed': len(all_products),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error fixing all description values: {e}")
            return {'fixed': 0, 'skipped': 0, 'total_processed': 0, 'error': str(e), 'success': False}

    def identify_bad_descriptions(self):
        """
        Identify all description values that don't meet the Product Name transformation criteria.
        Returns a list of products that need fixing.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products that have both Product Name and Description
            cursor.execute('''
                SELECT id, "Product Name*", "Description"
                FROM products 
                WHERE "Product Name*" IS NOT NULL AND "Product Name*" != ''
            ''')
            
            all_products = cursor.fetchall()
            bad_descriptions = []
            
            for product_id, product_name, current_desc in all_products:
                # Apply the transformation logic to see what the description should be
                expected_desc = self._process_description(product_name, current_desc)
                
                # Check if current description doesn't match expected
                if current_desc != expected_desc:
                    bad_descriptions.append({
                        'id': product_id,
                        'product_name': product_name,
                        'current_description': current_desc,
                        'expected_description': expected_desc
                    })
            
            logger.info(f"Found {len(bad_descriptions)} products with incorrect descriptions")
            return {
                'bad_descriptions': bad_descriptions,
                'total_products': len(all_products),
                'bad_count': len(bad_descriptions),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error identifying bad descriptions: {e}")
            return {'bad_descriptions': [], 'total_products': 0, 'bad_count': 0, 'error': str(e), 'success': False}

    def backfill_missing_crucial_values(self):
        """Backfill missing crucial values in existing products."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Update products with missing or old descriptions using processed descriptions
            # First, get all products that need description updates
            cursor.execute('''
                SELECT "id", "Product Name*", "Description"
                FROM products 
                WHERE "Description" IS NULL OR "Description" = "" OR "Description" = "nan"
                   OR "Description" LIKE "%Hustler's Ambition -%" 
                   OR "Description" LIKE "%Hustler's Ambition Flower%"
                   OR "Description" LIKE "%Hustler's Ambition - Wax%"
                   OR "Description" LIKE "%Hustler's Ambition - Preroll%"
            ''')
            products_to_update = cursor.fetchall()
            
            desc_updated = 0
            old_desc_updated = 0
            
            for product_id, product_name, current_desc in products_to_update:
                # Process the description using the same rules
                processed_desc = self._process_description(product_name, current_desc)
                
                # Update the product with the processed description
                cursor.execute('''
                    UPDATE products 
                    SET "Description" = ?
                    WHERE "id" = ?
                ''', (processed_desc, product_id))
                
                if not current_desc or current_desc.strip() == '' or current_desc == 'nan':
                    desc_updated += 1
                else:
                    old_desc_updated += 1
            
            # Update products with missing Weight
            cursor.execute('''
                UPDATE products 
                SET "Weight*" = "1g"
                WHERE "Weight*" IS NULL OR "Weight*" = "" OR "Weight*" = "nan"
            ''')
            weight_updated = cursor.rowcount
            
            # Update products with missing Price
            cursor.execute('''
                UPDATE products 
                SET "Price" = "0.00"
                WHERE "Price" IS NULL OR "Price" = "" OR "Price" = "nan"
            ''')
            price_updated = cursor.rowcount
            
            # Update products with missing THC test result
            cursor.execute('''
                UPDATE products 
                SET "THC test result" = "0.0"
                WHERE "THC test result" IS NULL OR "THC test result" = "" OR "THC test result" = "nan"
            ''')
            thc_updated = cursor.rowcount
            
            # Update products with missing CBD test result
            cursor.execute('''
                UPDATE products 
                SET "CBD test result" = "0.0"
                WHERE "CBD test result" IS NULL OR "CBD test result" = "" OR "CBD test result" = "nan"
            ''')
            cbd_updated = cursor.rowcount
            
            # Update products with missing Product Type
            cursor.execute('''
                UPDATE products 
                SET "Product Type*" = "Unknown"
                WHERE "Product Type*" IS NULL OR "Product Type*" = "" OR "Product Type*" = "nan"
            ''')
            type_updated = cursor.rowcount
            
            # Update products with missing Vendor
            cursor.execute('''
                UPDATE products 
                SET "Vendor/Supplier*" = "Unknown Vendor"
                WHERE "Vendor/Supplier*" IS NULL OR "Vendor/Supplier*" = "" OR "Vendor/Supplier*" = "nan"
            ''')
            vendor_updated = cursor.rowcount
            
            # Update products with missing Units
            cursor.execute('''
                UPDATE products 
                SET "Units" = "each"
                WHERE "Units" IS NULL OR "Units" = "" OR "Units" = "nan"
            ''')
            units_updated = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"Backfilled missing crucial values:")
            logger.info(f"  - Description (missing): {desc_updated} products")
            logger.info(f"  - Description (old Excel format): {old_desc_updated} products")
            logger.info(f"  - Weight: {weight_updated} products")
            logger.info(f"  - Price: {price_updated} products")
            logger.info(f"  - THC test result: {thc_updated} products")
            logger.info(f"  - CBD test result: {cbd_updated} products")
            logger.info(f"  - Product Type: {type_updated} products")
            logger.info(f"  - Vendor: {vendor_updated} products")
            logger.info(f"  - Units: {units_updated} products")
            
            return {
                'description': desc_updated + old_desc_updated,
                'description_missing': desc_updated,
                'description_old_format': old_desc_updated,
                'weight': weight_updated,
                'price': price_updated,
                'thc': thc_updated,
                'cbd': cbd_updated,
                'type': type_updated,
                'vendor': vendor_updated,
                'units': units_updated
            }
            
        except Exception as e:
            logger.error(f"Error backfilling missing crucial values: {e}")
            return None
    
    def _calculate_product_strain_original(self, product_type: str, product_name: str, description: str, ratio: str) -> str:
        """Calculate Product Strain using exact Excel processor logic."""
        from src.core.constants import CLASSIC_TYPES
        
        product_type = str(product_type).strip().lower()
        product_name = str(product_name).strip()
        description = str(description).strip()
        ratio = str(ratio).strip()
        
        # Handle 'nan' values
        if product_name.lower() == 'nan':
            product_name = ''
        if description.lower() == 'nan':
            description = ''
        if ratio.lower() == 'nan':
            ratio = ''
        
        # Classic types don't need Product Strain values set by this logic
        # They use actual strain names from the Product Strain column
        if product_type in CLASSIC_TYPES:
            return ''  # Let the actual strain name be used
        
        # For non-classic types, determine if it's CBD or Mixed
        import re
        
        # Check if product name contains CBD, CBG, CBC, or CBN
        name_contains_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', product_name, re.IGNORECASE))
        
        # Check if description contains CBD, CBG, CBC, or CBN, or ":"
        desc_contains_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', description, re.IGNORECASE)) or ':' in description
        
        # Check if ratio contains CBD, CBG, CBC, or CBN
        ratio_contains_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', ratio, re.IGNORECASE))
        
        # If any of these contain cannabinoids, set to "CBD Blend"
        if name_contains_cbd or desc_contains_cbd or ratio_contains_cbd:
            return "CBD Blend"
        
        # Otherwise, set to "Mixed"
        return "Mixed"
    
    def _extract_ratio_from_product_name(self, product_name: str, product_type: str) -> str:
        """Extract ratio from product name for NonClassic types using same logic as Excel processor."""
        import re
        
        # Define classic types (same as Excel processor)
        classic_types = ["flower", "pre-roll", "infused pre-roll", "concentrate", "solventless concentrate", "vape cartridge", "rso/co2 tankers"]
        
        # Only extract ratio for non-classic types (including capsules)
        if product_type.lower() not in classic_types:
            if product_name and isinstance(product_name, str):
                # Extract text after final dash (cannabinoid content)
                # This is what the Excel processor does - it extracts the part after the dash
                # which contains the actual cannabinoid amounts, not the ratios
                match = re.search(r".*-\s*(.+)", product_name)
                if match:
                    extracted_content = match.group(1).strip()
                    # Replace "/" with space to remove backslash formatting (same as Excel processor)
                    # But preserve the slash in ratios like "10mg THC / 5mg CBD"
                    if "/" in extracted_content and not any(cannabinoid in extracted_content.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                        extracted_content = extracted_content.replace("/", " ")
                    # Replace "nan" values with empty string (same as Excel processor)
                    if extracted_content.lower() == "nan":
                        extracted_content = ""
                    return extracted_content
        
        return ""

    def _calculate_ratio_or_thc_cbd(self, product_type: str, ratio: str, joint_ratio: str, product_name: str = "", thc_value: str = "", cbd_value: str = "") -> str:
        """Calculate Ratio_or_THC_CBD using exact Excel processor logic."""
        import re
        
        def is_real_ratio(text: str) -> bool:
            """Check if a string represents a valid ratio format."""
            if not text or not isinstance(text, str):
                return False
            
            # Clean the text
            text = text.strip()
            
            # Check for common invalid values
            if text in ['', 'CBD', 'THC', 'CBD:', 'THC:', 'CBD:\n', 'THC:\n']:
                return False
            
            # Check for mg values (e.g., '100mg', '500mg THC', '10mg CBD')
            if 'mg' in text.lower():
                return True
            
            # Check for ratio patterns (e.g., '1:1', '2:1', '1:2:1')
            ratio_pattern = r'^\d+(?::\d+)+$'
            if re.match(ratio_pattern, text):
                return True
            
            # Check for percentage patterns (e.g., '20%', '15.5%')
            percent_pattern = r'^\d+(?:\.\d+)?%$'
            if re.match(percent_pattern, text):
                return True
            
            return False
        
        def is_weight_with_unit(text: str) -> bool:
            """Check if a string represents a weight with unit format (e.g., '1g', '3.5g', '1oz')."""
            if not text or not isinstance(text, str):
                return False
            
            # Clean the text
            text = text.strip()
            
            # Check for weight + unit patterns
            weight_patterns = [
                r'^\d+(?:\.\d+)?\s*(?:g|gram|grams|gm|oz|ounce|ounces)$',  # 1g, 3.5g, 1oz, etc.
                r'^\d+(?:\.\d+)?\s*(?:g|gram|grams|gm|oz|ounce|ounces)\s*$',  # with trailing space
            ]
            
            for pattern in weight_patterns:
                if re.match(pattern, text, re.IGNORECASE):
                    return True
            
            return False
        
        product_type = str(product_type).strip().lower()
        ratio = str(ratio).strip()
        
        # Handle 'nan' values by replacing with empty string
        if ratio.lower() == 'nan':
            ratio = ''
        
        # For NonClassic types, extract ratio from product name if no ratio is provided
        if not ratio or ratio in ['', 'nan']:
            extracted_ratio = self._extract_ratio_from_product_name(product_name, product_type)
            if extracted_ratio:
                ratio = extracted_ratio
        
        classic_types = [
            'flower', 'pre-roll', 'infused pre-roll', 'concentrate', 'solventless concentrate', 'vape cartridge', 'rso/co2 tankers'
        ]
        # Note: capsules are NOT classic types for ratio processing - they should be treated as edibles
        BAD_VALUES = {'', 'CBD', 'THC', 'CBD:', 'THC:', 'CBD:\n', 'THC:\n', 'nan'}
        
        # For paraphernalia/hardware products, don't show THC/CBD values
        if product_type in ['paraphernalia', 'hardware', 'accessory']:
            return ''  # Empty for non-cannabis products
        
        # For pre-rolls, infused pre-rolls, concentrates, and solventless concentrates, treat as classic types
        if product_type in ['pre-roll', 'infused pre-roll', 'concentrate', 'solventless concentrate']:
            # Use actual THC/CBD values if available, otherwise use default format
            if thc_value and cbd_value and str(thc_value).strip() not in ['nan', 'NaN', ''] and str(cbd_value).strip() not in ['nan', 'NaN', '']:
                thc_str = str(thc_value).strip()
                cbd_str = str(cbd_value).strip()
                return f"THC: {thc_str}% CBD: {cbd_str}%"
            elif thc_value and str(thc_value).strip() not in ['nan', 'NaN', '']:
                thc_str = str(thc_value).strip()
                return f"THC: {thc_str}%"
            elif cbd_value and str(cbd_value).strip() not in ['nan', 'NaN', '']:
                cbd_str = str(cbd_value).strip()
                return f"CBD: {cbd_str}%"
            else:
                return 'THC: | BR | C'
        
        if product_type in classic_types:
            # For classic types, prioritize THC/CBD values if available
            if thc_value and cbd_value and str(thc_value).strip() not in ['nan', 'NaN', ''] and str(cbd_value).strip() not in ['nan', 'NaN', '']:
                thc_str = str(thc_value).strip()
                cbd_str = str(cbd_value).strip()
                return f"THC: {thc_str}% CBD: {cbd_str}%"
            elif thc_value and str(thc_value).strip() not in ['nan', 'NaN', '']:
                thc_str = str(thc_value).strip()
                return f"THC: {thc_str}%"
            elif cbd_value and str(cbd_value).strip() not in ['nan', 'NaN', '']:
                cbd_str = str(cbd_value).strip()
                return f"CBD: {cbd_str}%"
            elif not ratio or ratio in BAD_VALUES:
                return 'THC: | BR | C'
            # If ratio contains THC/CBD values, use it directly
            elif any(cannabinoid in ratio.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                return ratio
            # If it's a valid ratio format, use it
            elif is_real_ratio(ratio):
                return ratio
            # If it's a weight format (like '1g', '28g'), use it
            elif is_weight_with_unit(ratio):
                return ratio
            # Otherwise, use default THC:CBD format
            else:
                return 'THC: | BR | C'
        
        # For Edibles, Topicals, Tinctures, etc., use the ratio if it contains cannabinoid content
        edible_types = {'edible (solid)', 'edible (liquid)', 'high cbd edible liquid', 'tincture', 'topical', 'capsule'}
        if product_type in edible_types:
            if not ratio or ratio in BAD_VALUES:
                return 'THC: | BR | C'
            # If ratio contains cannabinoid content, use it
            if any(cannabinoid in ratio.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                return ratio
            # If it's a valid ratio format, use it
            if is_real_ratio(ratio):
                return ratio
            # If it's a weight format, use it
            if is_weight_with_unit(ratio):
                return ratio
            # Otherwise, use default THC:CBD format
            return 'THC: | BR | C'
        
        # For any other product type, return the ratio as-is
        return ratio
    
    def _calculate_product_strain_original(self, product_type: str, product_name: str, description: str, ratio: str) -> str:
        """Calculate Product Strain using exact Excel processor logic."""
        import re
        
        product_type = str(product_type).strip().lower()
        product_name = str(product_name).strip() if product_name else ""
        description = str(description).strip() if description else ""
        ratio = str(ratio).strip() if ratio else ""
        
        # Handle 'nan' values
        if product_name.lower() == 'nan':
            product_name = ""
        if description.lower() == 'nan':
            description = ""
        if ratio.lower() == 'nan':
            ratio = ""
        
        # Special case: paraphernalia gets Product Strain set to "Paraphernalia"
        if product_type == "paraphernalia":
            return "Paraphernalia"
        
        # Define classic types (these don't get Product Strain logic applied)
        classic_types = [
            'flower', 'pre-roll', 'infused pre-roll', 'concentrate', 'solventless concentrate', 
            'vape cartridge', 'alcohol/ethanol extract', 'co2 concentrate'
        ]
        
        # If it's a classic type, return blank (classic types don't get Product Strain logic)
        if product_type in classic_types:
            return ""
        
        # Define edible types for special handling
        edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
        
        # For edibles: if ProductName, Description, or Ratio contains CBD, CBG, CBN, CBC, or ":", then Product Strain is "CBD Blend", otherwise "Mixed"
        if product_type in edible_types:
            # Check product name for cannabinoids or ratio patterns
            name_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', product_name, re.IGNORECASE)) or ':' in product_name
            # Check description for cannabinoids or ratio patterns  
            desc_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', description, re.IGNORECASE)) or ':' in description
            # Check ratio for cannabinoids
            ratio_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', ratio, re.IGNORECASE))
            
            if name_has_cbd or desc_has_cbd or ratio_has_cbd:
                return "CBD Blend"
            else:
                return "Mixed"
        
        # For RSO/CO2 Tankers: if ProductName, Description, or Ratio contains CBD, CBG, CBC, CBN, or ":", then Product Strain is "CBD Blend", otherwise "Mixed"
        if product_type == "rso/co2 tankers":
            # Check product name for cannabinoids or ratio patterns
            name_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', product_name, re.IGNORECASE)) or ':' in product_name
            # Check description for cannabinoids or ratio patterns
            desc_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', description, re.IGNORECASE)) or ':' in description
            # Check ratio for cannabinoids
            ratio_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', ratio, re.IGNORECASE))
            
            if name_has_cbd or desc_has_cbd or ratio_has_cbd:
                return "CBD Blend"
            else:
                return "Mixed"
        
        # For all other nonclassic types: check for CBD content in Product Name, Description, or Ratio
        # Check product name for cannabinoids or ratio patterns
        name_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', product_name, re.IGNORECASE)) or ':' in product_name
        # Check description for cannabinoids or ratio patterns
        desc_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', description, re.IGNORECASE)) or ':' in description
        # Check ratio for cannabinoids
        ratio_has_cbd = bool(re.search(r'\b(?:CBD|CBG|CBC|CBN)\b', ratio, re.IGNORECASE))
        
        if name_has_cbd or desc_has_cbd or ratio_has_cbd:
            return "CBD Blend"
        
        # For all other nonclassic types without CBD content, return "Mixed"
        return "Mixed"
    
    def update_all_product_strains(self) -> Dict[str, Any]:
        """Update all products with correct Product Strain values based on Excel logic."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all products that need Product Strain updates
            cursor.execute('''
                SELECT id, "Product Name*", "Product Type*", "Description", "Ratio"
                FROM products
            ''')
            
            products = cursor.fetchall()
            updated_count = 0
            
            for product_id, product_name, product_type, description, ratio in products:
                # Calculate the correct Product Strain value
                new_strain = self._calculate_product_strain_original(
                    product_type or '',
                    product_name or '',
                    description or '',
                    ratio or ''
                )
                
                # Update the Product Strain
                cursor.execute('''
                    UPDATE products 
                    SET "Product Strain" = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_strain, datetime.now().isoformat(), product_id))
                updated_count += 1
            
            conn.commit()
            logger.info(f"Updated {updated_count} products with correct Product Strain values")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} products with correct Product Strain values'
            }
            
        except Exception as e:
            logger.error(f"Error updating Product Strain values: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update Product Strain values: {str(e)}'
            }
    
    @timed_operation("get_all_strains")
    def get_all_strains(self) -> Set[str]:
        """Get all normalized strain names from the database for fast lookup."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            cache_key = self._get_cache_key("all_strains")
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT normalized_name FROM strains')
            
            strains = {row[0] for row in cursor.fetchall() if row[0]}
            
            # Cache the result for 10 minutes (strains don't change often)
            self._set_cache(cache_key, strains, ttl=600)
            return strains
            
        except Exception as e:
            logger.error(f"Error getting all strains: {e}")
            return set()
    
    @timed_operation("get_strain_lineage_map")
    def get_strain_lineage_map(self) -> Dict[str, str]:
        """Get a mapping of normalized strain names to their canonical lineages."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            cache_key = self._get_cache_key("strain_lineage_map")
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT normalized_name, canonical_lineage FROM strains WHERE canonical_lineage IS NOT NULL')
            
            lineage_map = {row[0]: row[1] for row in cursor.fetchall() if row[0] and row[1]}
            
            # Cache the result for 10 minutes
            self._set_cache(cache_key, lineage_map, ttl=600)
            return lineage_map
            
        except Exception as e:
            logger.error(f"Error getting strain lineage map: {e}")
            return {}
    
    def upsert_strain_brand_lineage(self, strain_name: str, brand: str, lineage: str):
        """Insert or update lineage for a (strain_name, brand) pair."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO strain_brand_lineage (strain_name, brand, lineage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(strain_name, brand) DO UPDATE SET lineage=excluded.lineage, updated_at=excluded.updated_at
            ''', (strain_name, brand, lineage, now, now))
            conn.commit()
            logger.info(f"Upserted lineage for ({strain_name}, {brand}) -> {lineage}")
        except Exception as e:
            logger.error(f"Error upserting strain_brand_lineage: {e}")
            raise 

    def update_product_lineage(self, product_name: str, new_lineage: str, vendor: str = None, brand: str = None) -> bool:
        """Update the lineage for a product in the database."""
        try:
            self.init_database()
            normalized_name = self._normalize_product_name(product_name)
            conn = self._get_connection()
            cursor = conn.cursor()
            current_date = datetime.now().isoformat()
            
            # Update by product name, vendor, and brand if provided
            if vendor and brand:
                cursor.execute('''
                    UPDATE products
                    SET lineage = ?, updated_at = ?
                    WHERE normalized_name = ? AND "Vendor/Supplier*" = ? AND "Product Brand" = ?
                ''', (new_lineage, current_date, normalized_name, vendor, brand))
                logger.info(f"Updated lineage for product '{product_name}' (vendor={vendor}, brand={brand}) to '{new_lineage}'")
            else:
                cursor.execute('''
                    UPDATE products
                    SET lineage = ?, updated_at = ?
                    WHERE normalized_name = ?
                ''', (new_lineage, current_date, normalized_name))
                logger.info(f"Updated lineage for product '{product_name}' to '{new_lineage}'")
            
            conn.commit()
            rows_updated = cursor.rowcount
            if rows_updated == 0:
                logger.warning(f"No product found in database to update: '{product_name}' (vendor={vendor}, brand={brand})")
            return rows_updated > 0
        except Exception as e:
            logger.error(f"Error updating product lineage for '{product_name}': {e}")
            return False 

    def get_vendor_strain_lineage(self, strain_name: str, vendor: str = None, brand: str = None) -> Optional[str]:
        """Get vendor-specific lineage for a strain, with fallback to canonical lineage."""
        try:
            self.init_database()
            
            # First, try to get vendor/brand-specific lineage
            if vendor and brand:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Check strain_brand_lineage table first (most specific)
                cursor.execute('''
                    SELECT lineage FROM strain_brand_lineage 
                    WHERE strain_name = ? AND brand = ?
                ''', (strain_name, brand))
                
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Found vendor-specific lineage for {strain_name} + {brand}: {result[0]}")
                    return result[0]
                
                # Check products table for vendor/brand combination
                cursor.execute('''
                    SELECT p."Lineage" FROM products p
                    WHERE p.strain_id = (
                        SELECT id FROM strains WHERE normalized_name = ?
                    ) AND p."Vendor/Supplier*" = ? AND p."Product Brand" = ?
                    ORDER BY p.id DESC
                    LIMIT 1
                ''', (self._normalize_strain_name(strain_name), vendor, brand))
                
                result = cursor.fetchone()
                if result and result[0]:
                    logger.debug(f"Found product-specific lineage for {strain_name} + {vendor} + {brand}: {result[0]}")
                    return result[0]
            
            # Fallback to canonical lineage from strains table
            strain_info = self.get_strain_info(strain_name)
            if strain_info and strain_info.get('canonical_lineage'):
                logger.debug(f"Using canonical lineage for {strain_name}: {strain_info['canonical_lineage']}")
                return strain_info['canonical_lineage']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting vendor strain lineage for '{strain_name}': {e}")
            return None

    def get_vendor_strain_statistics(self) -> Dict[str, Any]:
        """Get statistics about vendor-specific strain lineages."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get vendor-specific lineage counts
            cursor.execute('''
                SELECT brand, COUNT(*) as count, 
                       GROUP_CONCAT(DISTINCT lineage) as lineages
                FROM strain_brand_lineage 
                GROUP BY brand
                ORDER BY count DESC
            ''')
            
            vendor_stats = []
            for row in cursor.fetchall():
                brand, count, lineages = row
                vendor_stats.append({
                    'brand': brand,
                    'strain_count': count,
                    'lineages': lineages.split(',') if lineages else []
                })
            
            # Get strain diversity by vendor
            cursor.execute('''
                SELECT p.vendor, p.brand, s.strain_name, p.lineage
                FROM products p
                JOIN strains s ON p.strain_id = s.id
                WHERE p.lineage IS NOT NULL AND p.lineage != ''
                ORDER BY p.vendor, p.brand, s.strain_name
            ''')
            
            vendor_strains = {}
            for row in cursor.fetchall():
                vendor, brand, strain, lineage = row
                key = f"{vendor} - {brand}" if vendor and brand else (vendor or brand or "Unknown")
                if key not in vendor_strains:
                    vendor_strains[key] = {}
                if strain not in vendor_strains[key]:
                    vendor_strains[key][strain] = set()
                vendor_strains[key][strain].add(lineage)
            
            # Find strains with different lineages across vendors
            strain_vendor_conflicts = {}
            for vendor_key, strains in vendor_strains.items():
                for strain, lineages in strains.items():
                    if len(lineages) > 1:
                        if strain not in strain_vendor_conflicts:
                            strain_vendor_conflicts[strain] = {}
                        strain_vendor_conflicts[strain][vendor_key] = list(lineages)
            
            return {
                'vendor_stats': vendor_stats,
                'vendor_strains': vendor_strains,
                'strain_vendor_conflicts': strain_vendor_conflicts,
                'total_vendors': len(vendor_stats),
                'conflicting_strains': len(strain_vendor_conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor strain statistics: {e}")
            return {}

    def update_product_doh(self, product_name: str, new_doh: str, vendor: str = None, brand: str = None) -> bool:
        """Update the DOH status for a product in the database."""
        try:
            self.init_database()
            normalized_name = self._normalize_product_name(product_name)
            conn = self._get_connection()
            cursor = conn.cursor()
            current_date = datetime.now().isoformat()
            
            # Update both DOH columns to be consistent
            if vendor and brand:
                cursor.execute('''
                    UPDATE products
                    SET "DOH" = ?, "DOH Compliant (Yes/No)" = ?, updated_at = ?
                    WHERE normalized_name = ? AND "Vendor/Supplier*" = ? AND "Product Brand" = ?
                ''', (new_doh, new_doh, current_date, normalized_name, vendor, brand))
                logger.info(f"Updated DOH for product '{product_name}' (vendor={vendor}, brand={brand}) to '{new_doh}'")
            else:
                cursor.execute('''
                    UPDATE products
                    SET "DOH" = ?, "DOH Compliant (Yes/No)" = ?, updated_at = ?
                    WHERE normalized_name = ?
                ''', (new_doh, new_doh, current_date, normalized_name))
                logger.info(f"Updated DOH for product '{product_name}' to '{new_doh}'")
            
            conn.commit()
            rows_updated = cursor.rowcount
            if rows_updated == 0:
                logger.warning(f"No product found in database to update DOH: '{product_name}' (vendor={vendor}, brand={brand})")
            return rows_updated > 0
        except Exception as e:
            logger.error(f"Error updating product DOH for '{product_name}': {e}")
            return False

    def upsert_strain_vendor_lineage(self, strain_name: str, vendor: str, brand: str, lineage: str):
        """Insert or update lineage for a (strain_name, vendor, brand) combination."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # First, ensure the strain exists in the strains table
            strain_id = self.add_or_update_strain(strain_name, lineage)
            
            # Update or insert in products table with vendor/brand specificity
            cursor.execute('''
                INSERT INTO products (
                    product_name, normalized_name, strain_id, product_type, vendor, brand,
                    lineage, first_seen_date, last_seen_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_name, vendor, brand) DO UPDATE SET 
                    lineage = excluded.lineage, 
                    last_seen_date = excluded.last_seen_date,
                    updated_at = excluded.updated_at
            ''', (
                strain_name, self._normalize_product_name(strain_name), strain_id,
                'Unknown', vendor, brand, lineage, now, now, now, now
            ))
            
            # Also update strain_brand_lineage for brand-specific overrides
            cursor.execute('''
                INSERT INTO strain_brand_lineage (strain_name, brand, lineage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(strain_name, brand) DO UPDATE SET 
                    lineage = excluded.lineage, 
                    updated_at = excluded.updated_at
            ''', (strain_name, brand, lineage, now, now))
            
            conn.commit()
            logger.info(f"Upserted vendor-specific lineage: {strain_name} + {vendor} + {brand} = {lineage}")
            
        except Exception as e:
            logger.error(f"Error upserting strain vendor lineage: {e}")
            raise 

    def get_strain_with_products_info(self, strain_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive strain information including all associated products with brand, weight, vendor, and price data."""
        try:
            self.init_database()
            normalized_name = self._normalize_strain_name(strain_name)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get strain basic info
            cursor.execute('''
                SELECT id, strain_name, canonical_lineage, total_occurrences, lineage_confidence, 
                       first_seen_date, last_seen_date, sovereign_lineage
                FROM strains 
                WHERE normalized_name = ?
            ''', (normalized_name,))
            
            strain_result = cursor.fetchone()
            if not strain_result:
                return None
                
            strain_id, strain_name, canonical_lineage, total_occurrences, lineage_confidence, first_seen_date, last_seen_date, sovereign_lineage = strain_result
            
            # Get all products associated with this strain
            cursor.execute('''
                SELECT "Product Name*", "Product Type*", "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units", "Price", "Lineage",
                       total_occurrences, first_seen_date, last_seen_date
                FROM products 
                WHERE strain_id = ?
                ORDER BY total_occurrences DESC
            ''', (strain_id,))
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'product_name': row[0],
                    'product_type': row[1],
                    'vendor': row[2],
                    'brand': row[3],
                    'description': row[4],
                    'weight': row[5],
                    'units': row[6],
                    'price': row[7],
                    'lineage': row[8],
                    'total_occurrences': row[9],
                    'first_seen_date': row[10],
                    'last_seen_date': row[11]
                })
            
            # Get brand-specific lineage overrides
            cursor.execute('''
                SELECT brand, lineage FROM strain_brand_lineage 
                WHERE strain_name = ?
                ORDER BY brand
            ''', (strain_name,))
            
            brand_lineages = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Calculate aggregated information
            brands = list(set(p['brand'] for p in products if p['brand']))
            vendors = list(set(p['vendor'] for p in products if p['vendor']))
            weights = list(set(p['weight'] for p in products if p['weight']))
            units = list(set(p['units'] for p in products if p['units']))
            
            # Get most common values
            brand_counts = {}
            vendor_counts = {}
            weight_counts = {}
            price_counts = {}
            
            for product in products:
                if product['brand']:
                    brand_counts[product['brand']] = brand_counts.get(product['brand'], 0) + product['total_occurrences']
                if product['vendor']:
                    vendor_counts[product['vendor']] = vendor_counts.get(product['vendor'], 0) + product['total_occurrences']
                if product['weight']:
                    weight_counts[product['weight']] = weight_counts.get(product['weight'], 0) + product['total_occurrences']
                if product['price']:
                    price_counts[product['price']] = price_counts.get(product['price'], 0) + product['total_occurrences']
            
            most_common_brand = max(brand_counts.items(), key=lambda x: x[1])[0] if brand_counts else None
            most_common_vendor = max(vendor_counts.items(), key=lambda x: x[1])[0] if vendor_counts else None
            most_common_weight = max(weight_counts.items(), key=lambda x: x[1])[0] if weight_counts else None
            most_common_price = max(price_counts.items(), key=lambda x: x[1])[0] if price_counts else None
            
            # Determine display lineage (sovereign > mode > canonical)
            display_lineage = None
            if sovereign_lineage and sovereign_lineage.strip():
                display_lineage = sovereign_lineage
            else:
                mode_lineage = self.get_mode_lineage(strain_id)
                if mode_lineage:
                    display_lineage = mode_lineage
                else:
                    display_lineage = canonical_lineage
            
            return {
                'strain_info': {
                    'id': strain_id,
                    'strain_name': strain_name,
                    'canonical_lineage': canonical_lineage,
                    'display_lineage': display_lineage,
                    'sovereign_lineage': sovereign_lineage,
                    'total_occurrences': total_occurrences,
                    'lineage_confidence': lineage_confidence,
                    'first_seen_date': first_seen_date,
                    'last_seen_date': last_seen_date
                },
                'products': products,
                'brand_lineages': brand_lineages,
                'aggregated_info': {
                    'brands': brands,
                    'vendors': vendors,
                    'weights': weights,
                    'units': units,
                    'most_common_brand': most_common_brand,
                    'most_common_vendor': most_common_vendor,
                    'most_common_weight': most_common_weight,
                    'most_common_price': most_common_price,
                    'total_products': len(products)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting strain with products info for '{strain_name}': {e}")
            return None

    def get_strain_brand_info(self, strain_name: str, brand: str = None) -> Optional[Dict[str, Any]]:
        """Get strain information with specific brand context, including weight, vendor, and price data."""
        try:
            self.init_database()
            normalized_name = self._normalize_strain_name(strain_name)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get strain basic info
            cursor.execute('''
                SELECT id, strain_name, canonical_lineage, total_occurrences, lineage_confidence, 
                       first_seen_date, last_seen_date, sovereign_lineage
                FROM strains 
                WHERE normalized_name = ?
            ''', (normalized_name,))
            
            strain_result = cursor.fetchone()
            if not strain_result:
                return None
                
            strain_id, strain_name, canonical_lineage, total_occurrences, lineage_confidence, first_seen_date, last_seen_date, sovereign_lineage = strain_result
            
            # Get products for this strain with optional brand filter
            if brand:
                cursor.execute('''
                    SELECT "Product Name*", "Product Type*", "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units", "Price", "Lineage",
                           total_occurrences, first_seen_date, last_seen_date
                    FROM products 
                    WHERE strain_id = ? AND "Product Brand" = ?
                    ORDER BY total_occurrences DESC
                ''', (strain_id, brand))
            else:
                cursor.execute('''
                    SELECT "Product Name*", "Product Type*", "Vendor/Supplier*", "Product Brand", "Description", "Weight*", "Units", "Price", "Lineage",
                           total_occurrences, first_seen_date, last_seen_date
                    FROM products 
                    WHERE strain_id = ?
                    ORDER BY total_occurrences DESC
                ''', (strain_id,))
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'product_name': row[0],
                    'product_type': row[1],
                    'vendor': row[2],
                    'brand': row[3],
                    'description': row[4],
                    'weight': row[5],
                    'units': row[6],
                    'price': row[7],
                    'lineage': row[8],
                    'total_occurrences': row[9],
                    'first_seen_date': row[10],
                    'last_seen_date': row[11]
                })
            
            # Get brand-specific lineage
            brand_lineage = None
            if brand:
                cursor.execute('''
                    SELECT lineage FROM strain_brand_lineage 
                    WHERE strain_name = ? AND brand = ?
                ''', (strain_name, brand))
                result = cursor.fetchone()
                if result:
                    brand_lineage = result[0]
            
            # Determine display lineage (brand-specific > sovereign > mode > canonical)
            display_lineage = None
            if brand_lineage:
                display_lineage = brand_lineage
            elif sovereign_lineage and sovereign_lineage.strip():
                display_lineage = sovereign_lineage
            else:
                mode_lineage = self.get_mode_lineage(strain_id)
                if mode_lineage:
                    display_lineage = mode_lineage
                else:
                    display_lineage = canonical_lineage
            
            # Aggregate product information
            if products:
                weights = list(set(p['weight'] for p in products if p['weight']))
                units = list(set(p['units'] for p in products if p['units']))
                vendors = list(set(p['vendor'] for p in products if p['vendor']))
                prices = list(set(p['price'] for p in products if p['price']))
                
                # Get most common values
                weight_counts = {}
                price_counts = {}
                vendor_counts = {}
                
                for product in products:
                    if product['weight']:
                        weight_counts[product['weight']] = weight_counts.get(product['weight'], 0) + product['total_occurrences']
                    if product['price']:
                        price_counts[product['price']] = price_counts.get(product['price'], 0) + product['total_occurrences']
                    if product['vendor']:
                        vendor_counts[product['vendor']] = vendor_counts.get(product['vendor'], 0) + product['total_occurrences']
                
                most_common_weight = max(weight_counts.items(), key=lambda x: x[1])[0] if weight_counts else None
                most_common_price = max(price_counts.items(), key=lambda x: x[1])[0] if price_counts else None
                most_common_vendor = max(vendor_counts.items(), key=lambda x: x[1])[0] if vendor_counts else None
            else:
                weights = units = vendors = prices = []
                most_common_weight = most_common_price = most_common_vendor = None
            
            return {
                'strain_name': strain_name,
                'canonical_lineage': canonical_lineage,
                'display_lineage': display_lineage,
                'brand_lineage': brand_lineage,
                'sovereign_lineage': sovereign_lineage,
                'total_occurrences': total_occurrences,
                'lineage_confidence': lineage_confidence,
                'products': products,
                'aggregated_info': {
                    'weights': weights,
                    'units': units,
                    'vendors': vendors,
                    'prices': prices,
                    'most_common_weight': most_common_weight,
                    'most_common_price': most_common_price,
                    'most_common_vendor': most_common_vendor,
                    'total_products': len(products)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting strain brand info for '{strain_name}' (brand: {brand}): {e}")
            return None

    def get_strains_with_brand_info(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get a list of strains with their associated brand, weight, vendor, and price information."""
        try:
            self.init_database()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get strains with their most common associated information
            cursor.execute('''
                SELECT s.strain_name, s.canonical_lineage, s.total_occurrences, s.sovereign_lineage,
                       p.brand, p.vendor, p.weight, p.units, p.price, p.lineage
                FROM strains s
                LEFT JOIN products p ON s.id = p.strain_id
                WHERE p.id = (
                    SELECT p2.id FROM products p2 
                    WHERE p2.strain_id = s.id 
                    ORDER BY p2.total_occurrences DESC 
                    LIMIT 1
                )
                ORDER BY s.total_occurrences DESC
                LIMIT ?
            ''', (limit,))
            
            strains = []
            for row in cursor.fetchall():
                strain_name, canonical_lineage, total_occurrences, sovereign_lineage, brand, vendor, weight, units, price, lineage = row
                
                # Get brand-specific lineage
                cursor.execute('''
                    SELECT lineage FROM strain_brand_lineage 
                    WHERE strain_name = ? AND brand = ?
                ''', (strain_name, brand))
                brand_lineage_result = cursor.fetchone()
                brand_lineage = brand_lineage_result[0] if brand_lineage_result else None
                
                # Determine display lineage
                display_lineage = None
                if brand_lineage:
                    display_lineage = brand_lineage
                elif sovereign_lineage and sovereign_lineage.strip():
                    display_lineage = sovereign_lineage
                else:
                    display_lineage = canonical_lineage
                
                strains.append({
                    'strain_name': strain_name,
                    'canonical_lineage': canonical_lineage,
                    'display_lineage': display_lineage,
                    'brand_lineage': brand_lineage,
                    'sovereign_lineage': sovereign_lineage,
                    'total_occurrences': total_occurrences,
                    'brand': brand,
                    'vendor': vendor,
                    'weight': weight,
                    'units': units,
                    'price': price,
                    'lineage': lineage
                })
            
            return strains
            
        except Exception as e:
            logger.error(f"Error getting strains with brand info: {e}")
            return []

    def add_missing_columns(self):
        """Public method to add missing columns to existing database tables."""
        try:
            self.init_database()
            conn = self._get_connection()
            cursor = conn.cursor()
            self._add_missing_columns_safe(cursor, conn)
            logger.info("Missing columns check completed")
        except Exception as e:
            logger.error(f"Error adding missing columns: {e}")
            raise

    @timed_operation("get_products_by_names")
    def get_products_by_names(self, product_names: List[str]) -> List[Dict[str, Any]]:
        """Get information about multiple products by their names (with caching)."""
        try:
            self.init_database()  # Ensure DB is initialized
            
            if not product_names:
                return []
            
            # Normalize all product names
            normalized_names = [self._normalize_product_name(name) for name in product_names]
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use placeholders for the IN clause
            placeholders = ','.join(['?' for _ in normalized_names])
            
            # Fixed query - use products table directly without alias to avoid column issues
            cursor.execute(f'''
                SELECT id, "Product Name*", normalized_name, "Product Type*", "Vendor/Supplier*", "Product Brand", "Lineage",
                       '' as strain_name, '' as canonical_lineage, 0 as total_occurrences, '' as first_seen_date, '' as last_seen_date,
                       "Description", "Weight*", "Weight Unit* (grams/gm or ounces/oz)", "Price* (Tier Name for Bulk)", 
                       '' as thc_test_result, '' as cbd_test_result, "Test result unit (% or mg)",
                       "Quantity*", "DOH", "Concentrate Type", "Ratio", "JointRatio", "State", "Is Sample? (yes/no)",
                       "Is MJ product?(yes/no)", "Discountable? (yes/no)", "Room*", "Batch Number", "Lot Number", "Barcode*",
                       "Medical Only (Yes/No)", "Med Price", "Expiration Date(YYYY-MM-DD)", "Is Archived? (yes/no)", "THC Per Serving", "Allergens",
                       "Solvent", "Accepted Date", "Internal Product Identifier", "Product Tags (comma separated)", "Image URL", "Ingredients",
                       "CombinedWeight", "Ratio_or_THC_CBD", "Description_Complexity", "Total THC", "THCA", "CBDA", "CBN"
                FROM products
                WHERE normalized_name IN ({placeholders})
            ''', normalized_names)
            
            results = cursor.fetchall()
            
            # Create a mapping from normalized names to results
            products_map = {}
            for result in results:
                normalized_name = result[2]  # normalized_name column
                if normalized_name not in products_map:
                    products_map[normalized_name] = []
                products_map[normalized_name].append(result)
            
            # Build the final list maintaining the order of requested product names
            products = []
            for i, product_name in enumerate(product_names):
                normalized_name = normalized_names[i]
                if normalized_name in products_map:
                    # Use the first result for each product (or could implement logic to choose best match)
                    result = products_map[normalized_name][0]
                    
                    product_info = {
                        'id': result[0],
                        'ProductName': result[1],  # product_name
                        'Product Name*': result[1],  # Excel column name compatibility
                        'normalized_name': result[2],
                        'Product Type*': result[3],  # product_type
                        'Vendor': result[4],  # vendor
                        'Vendor/Supplier*': result[4],  # Excel column name compatibility
                        'Product Brand': result[5],  # brand
                        'Lineage': result[6] or 'MIXED',  # lineage
                        'strain_name': result[7],  # strain_name (empty string)
                        'canonical_lineage': result[8],  # canonical_lineage (empty string)
                        'total_occurrences': result[9],
                        'first_seen_date': result[10],
                        'last_seen_date': result[11],
                        'Description': result[12] or result[1],  # description or product_name
                        'Weight*': result[13],  # weight
                        'Units': result[14],  # units
                        'Price': result[15],  # price (Price* (Tier Name for Bulk))
                        'THC test result': result[16],  # thc_test_result
                        'CBD test result': result[17],  # cbd_test_result
                        'Test result unit': result[18],  # test_result_unit
                        'Quantity*': result[19],  # quantity
                        'DOH': result[20],  # doh_compliant
                        'concentrate_type': result[21],  # concentrate_type
                        'Ratio': result[22],  # ratio
                        'JointRatio': result[23],  # joint_ratio
                        'State': result[24],  # state
                        'Is Sample?': result[25],  # is_sample
                        'Is MJ product?': result[26],  # is_mj_product
                        'Discountable?': result[27],  # discountable
                        'Room*': result[28],  # room
                        'batch_number': result[29],  # batch_number
                        'lot_number': result[30],  # lot_number
                        'barcode': result[31],  # barcode
                        'Medical Only': result[32],  # medical_only
                        'med_price': result[33],  # med_price
                        'expiration_date': result[34],  # expiration_date
                        'is_archived': result[35],  # is_archived
                        'thc_per_serving': result[36],  # thc_per_serving
                        'allergens': result[37],  # allergens
                        'solvent': result[38],  # solvent
                        'accepted_date': result[39],  # accepted_date
                        'internal_product_identifier': result[40],  # internal_product_identifier
                        'product_tags': result[41],  # product_tags
                        'image_url': result[42],  # image_url
                        'ingredients': result[43],  # ingredients
                        'combined_weight': result[44],  # combined_weight
                        'ratio_or_thc_cbd': result[45],  # ratio_or_thc_cbd
                        'description_complexity': result[46],  # description_complexity
                        'Total THC': result[47],  # total_thc
                        'THCA': result[48],  # thca
                        'CBDA': result[49],  # cbda
                        'CBN': result[50],  # cbn
                        # Add Excel column name compatibility fields
                        'ProductName': result[1],
                        'ProductBrand': result[5],
                        'ProductStrain': result[7],
                        'WeightWithUnits': f"{result[13]}{result[14]}" if result[13] and result[14] else result[13] or result[14] or '',
                        'displayName': result[1]  # For frontend compatibility
                    }
                    
                    products.append(product_info)
                else:
                    # Product not found in database, create a placeholder
                    logger.warning(f"Product '{product_name}' not found in database")
                    products.append({
                        'ProductName': product_name,
                        'Product Name*': product_name,
                        'Description': product_name,
                        'Vendor': '',
                        'Vendor/Supplier*': '',
                        'Product Brand': '',
                        'Lineage': 'MIXED',
                        'Product Type*': '',
                        'Weight*': '',
                        'Units': '',
                        'Price': '',
                        'displayName': product_name
                    })
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting products by names: {e}")
            return []

    def get_products_by_names_fuzzy(self, product_names: List[str]) -> List[Dict[str, Any]]:
        """Get products by their names with fuzzy matching for better name variations."""
        try:
            if not product_names:
                return []
            
            # First try exact matches
            exact_matches = self.get_products_by_names(product_names)
            
            # Check if exact matches have vendor/brand information
            has_vendor_brand_info = all(
                product.get('Vendor/Supplier*', '').strip() and 
                product.get('Product Brand', '').strip()
                for product in exact_matches
            )
            
            # If we found all products AND they have vendor/brand info, return them
            if len(exact_matches) == len(product_names) and has_vendor_brand_info:
                return exact_matches
            
            # If we didn't find all products, try fuzzy matching
            logger.info(f"Found {len(exact_matches)} exact matches, trying fuzzy matching for remaining products")
            
            # Get all products for fuzzy matching
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY "Product Name*"')
            all_rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            all_products = [dict(zip(columns, row)) for row in all_rows]
            
            # Find fuzzy matches for all products (since exact matches may not have vendor/brand info)
            found_products = []
            found_names = set()
            
            for search_name in product_names:
                # Try fuzzy matching for this search name
                best_match = None
                best_score = 0
                candidates = []
                
                for product in all_products:
                    product_name = product.get('Product Name*', '')
                    if not product_name:
                        continue
                    
                    # Calculate similarity score
                    score = self._calculate_name_similarity(search_name, product_name)
                    
                    if score > 0.3:  # 30% similarity threshold
                        candidates.append((product, score))
                
                # Sort candidates by score (highest first), then prioritize records with processed descriptions
                # (shorter descriptions are more likely to be processed)
                candidates.sort(key=lambda x: (
                    x[1],  # Score (highest first)
                    -len(x[0].get('Description', '')),  # Shorter descriptions first (negative for reverse)
                    x[0].get('Product Name*', '')  # Product name for consistency
                ), reverse=True)
                
                if candidates:
                    best_match, best_score = candidates[0]
                
                if best_match:
                    logger.info(f"Fuzzy match: '{search_name}' -> '{best_match.get('Product Name*', '')}' (score: {best_score:.2f})")
                    # Convert to the same format as get_products_by_names
                    converted_match = self._convert_product_to_standard_format(best_match)
                    found_products.append(converted_match)
                    found_names.add(search_name)
                else:
                    logger.warning(f"No fuzzy match found for: '{search_name}'")
                    # If no fuzzy match found, use exact match if available
                    exact_match = next((p for p in exact_matches if p.get('Product Name*') == search_name), None)
                    if exact_match:
                        found_products.append(exact_match)
                        found_names.add(search_name)
            
            logger.info(f"Found {len(found_products)} total products (exact + fuzzy) for: {product_names}")
            return found_products
            
        except Exception as e:
            logger.error(f"Error getting products by names with fuzzy matching: {e}")
            return []

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names with improved matching."""
        try:
            # Normalize names for comparison
            def normalize(name):
                return ' '.join(name.lower().split())
            
            norm1 = normalize(name1)
            norm2 = normalize(name2)
            
            # Check for exact match after normalization
            if norm1 == norm2:
                return 1.0
            
            # Check for substring matches
            if norm1 in norm2 or norm2 in norm1:
                return 0.9
            
            # Extract key components for better matching
            def extract_components(name):
                # Remove common prefixes and suffixes
                cleaned = name.lower()
                # Remove common cannabis terms for better matching
                cannabis_terms = ['flower', 'wax', 'pre-roll', 'cartridge', 'distillate', 'concentrate', 'edible', 'gummy', 'chocolate', 'beverage', 'topical', 'cream', 'lotion', 'salve', 'balm', 'spray', 'drops', 'syrup', 'sauce', 'dab', 'shatter', 'live', 'rosin', 'resin', 'kief', 'hash', 'bubble', 'ice', 'water', 'solventless', 'full', 'spectrum', 'broad', 'isolate', 'terpene', 'terpenes', 'terp', 'terps']
                
                for term in cannabis_terms:
                    cleaned = cleaned.replace(term, '')
                
                # Remove common weight indicators
                weight_terms = ['28g', '3.5g', '1g', '7g', '14g', '28g', '1oz', '0.5g', '2g', '4g', '8g', '16g', '32g']
                for term in weight_terms:
                    cleaned = cleaned.replace(term, '')
                
                # Remove common separators and clean up
                cleaned = cleaned.replace('(', '').replace(')', '').replace('-', ' ').replace('/', ' ').replace(' by ', ' ').replace('  ', ' ').strip()
                
                return cleaned.split()
            
            comp1 = extract_components(norm1)
            comp2 = extract_components(norm2)
            
            if not comp1 or not comp2:
                return 0.0
            
            # Calculate similarity based on key components
            set1 = set(comp1)
            set2 = set(comp2)
            
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            
            jaccard_score = len(intersection) / len(union) if union else 0.0
            
            # Boost score for strain name matches (most important)
            strain_boost = 0.0
            for comp in comp1:
                if comp in comp2 and len(comp) > 2:  # Avoid single character matches
                    strain_boost += 0.2
            
            # Boost score for brand name matches
            brand_boost = 0.0
            brand_terms = ['hustler', 'ambition', 'mama', 'j\'s', 'blue', 'roots', 'cannabis']
            for term in brand_terms:
                if term in norm1 and term in norm2:
                    brand_boost += 0.1
            
            # Prioritize exact strain name matches
            exact_strain_boost = 0.0
            
            # Check if the strain name components are the same (ignoring order)
            set1 = set(comp1)
            set2 = set(comp2)
            
            # If all components match, it's likely the same strain
            if set1 == set2:
                exact_strain_boost = 0.5
            # If the strain name components match (excluding brand components)
            elif len(set1.intersection(set2)) >= 2:  # At least 2 common components
                # Check if the strain-specific components match
                strain_components1 = set1 - {'hustler\'s', 'ambition', 'mama', 'j\'s', 'blue', 'roots', 'cannabis'}
                strain_components2 = set2 - {'hustler\'s', 'ambition', 'mama', 'j\'s', 'blue', 'roots', 'cannabis'}
                
                if strain_components1 == strain_components2 and len(strain_components1) > 0:
                    exact_strain_boost = 0.3
            
            final_score = jaccard_score + strain_boost + brand_boost + exact_strain_boost
            
            # Don't cap the score at 1.0 to allow for tie-breaking with boosts
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating name similarity: {e}")
            return 0.0

    def _convert_product_to_standard_format(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw database product to the standard format expected by the system."""
        try:
            return {
                'id': product.get('id', ''),
                'ProductName': product.get('Product Name*', ''),
                'Product Name*': product.get('Product Name*', ''),
                'normalized_name': product.get('normalized_name', ''),
                'Product Type*': product.get('Product Type*', ''),
                'Vendor': product.get('Vendor/Supplier*', ''),
                'Vendor/Supplier*': product.get('Vendor/Supplier*', ''),
                'Product Brand': product.get('Product Brand', ''),
                'Lineage': product.get('Lineage', 'MIXED'),
                'strain_name': product.get('Product Strain', ''),
                'canonical_lineage': product.get('Lineage', 'MIXED'),
                'total_occurrences': product.get('total_occurrences', 0),
                'first_seen_date': product.get('first_seen_date', ''),
                'last_seen_date': product.get('last_seen_date', ''),
                'Description': product.get('Description', product.get('Product Name*', '')),
                'Weight*': product.get('Weight*', ''),
                'Units': product.get('Units', ''),
                'Price': product.get('Price', ''),
                'THC test result': product.get('THC test result', ''),
                'CBD test result': product.get('CBD test result', ''),
                'Test result unit': product.get('Test result unit (% or mg)', ''),
                'Quantity*': product.get('Quantity*', ''),
                'DOH': product.get('DOH', ''),
                'concentrate_type': product.get('Concentrate Type', ''),
                'Ratio': product.get('Ratio', ''),
                'JointRatio': product.get('JointRatio', ''),
                'State': product.get('State', ''),
                'Is Sample?': product.get('Is Sample? (yes/no)', ''),
                'Is MJ product?': product.get('Is MJ product?(yes/no)', ''),
                'Discountable?': product.get('Discountable? (yes/no)', ''),
                'Room*': product.get('Room*', ''),
                'batch_number': product.get('Batch Number', ''),
                'lot_number': product.get('Lot Number', ''),
                'barcode': product.get('Barcode*', ''),
                'Medical Only': product.get('Medical Only (Yes/No)', ''),
                'med_price': product.get('Med Price', ''),
                'expiration_date': product.get('Expiration Date(YYYY-MM-DD)', ''),
                'is_archived': product.get('Is Archived? (yes/no)', ''),
                'thc_per_serving': product.get('THC Per Serving', ''),
                'allergens': product.get('Allergens', ''),
                'solvent': product.get('Solvent', ''),
                'accepted_date': product.get('Accepted Date', ''),
                'internal_product_identifier': product.get('Internal Product Identifier', ''),
                'product_tags': product.get('Product Tags (comma separated)', ''),
                'image_url': product.get('Image URL', ''),
                'ingredients': product.get('Ingredients', ''),
                'combined_weight': product.get('CombinedWeight', ''),
                'ratio_or_thc_cbd': product.get('Ratio_or_THC_CBD', ''),
                'description_complexity': product.get('Description_Complexity', ''),
                'Total THC': product.get('Total THC', ''),
                'THCA': product.get('THCA', ''),
                'CBDA': product.get('CBDA', ''),
                'CBN': product.get('CBN', ''),
                # Add Excel column name compatibility fields
                'ProductBrand': product.get('Product Brand', ''),
                'ProductStrain': product.get('Product Strain', ''),
                'WeightWithUnits': f"{product.get('Weight*', '')}{product.get('Units', '')}" if product.get('Weight*') and product.get('Units') else product.get('Weight*', '') or product.get('Units', '') or '',
                'displayName': product.get('Product Name*', '')
            }
        except Exception as e:
            logger.error(f"Error converting product to standard format: {e}")
            return {}

    def find_best_product_match(self, product_name: str, vendor: str = None, product_type: str = None, strain: str = None) -> Optional[Dict[str, Any]]:
        """
        Find the best matching product in the database based on multiple criteria.
        
        Args:
            product_name: The product name to search for
            vendor: The vendor/supplier name
            product_type: The product type/category
            strain: The strain name
            
        Returns:
            Best matching product dictionary or None if no match found
        """
        try:
            self.init_database()  # Ensure DB is initialized
            
            if not product_name:
                return None
            
            # Normalize the product name
            normalized_name = self._normalize_product_name(product_name)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build a flexible search query using the actual column names
            query = '''
                SELECT p.id, p."Product Name*", p."Product Strain", p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                       p."Description", p."Weight*", p."Units", p."Price", p."Quantity*", p."DOH", p."Concentrate Type", p."Ratio", p."JointRatio",
                       p."State", p."Is Sample? (yes/no)", p."Is MJ product?(yes/no)", p."Discountable? (yes/no)", p."Room*", p."Batch Number", p."Lot Number", p."Barcode*",
                       p."Medical Only (Yes/No)", p."Med Price", p."Expiration Date(YYYY-MM-DD)", p."Is Archived? (yes/no)", p."THC Per Serving", p."Allergens", p."Solvent", p."Accepted Date",
                       p."Internal Product Identifier", p."Product Tags (comma separated)", p."Image URL", p."Ingredients", p."CombinedWeight", p."Ratio_or_THC_CBD", 
                       p."Description_Complexity", p."Total THC", p."THCA", p."CBDA", p."CBN", 0 as total_occurrences, '' as first_seen_date, '' as last_seen_date
                FROM products p
                WHERE 1=1
            '''
            
            params = []
            
            # Add search conditions with priority using actual column names
            if normalized_name:
                # Create multiple search patterns for better matching
                # 1. Original normalized name
                # 2. Individual words from the name
                # 3. Partial matches
                
                search_patterns = [normalized_name]
                
                # Add individual words for partial matching
                words = normalized_name.split('_')
                search_patterns.extend(words)
                
                # Add space-separated version
                space_name = normalized_name.replace('_', ' ')
                search_patterns.append(space_name)
                search_patterns.extend(space_name.split())
                
                # Build more intelligent search conditions
                # Priority 1: Exact normalized name match
                # Priority 2: Product name contains the full search term
                # Priority 3: Product name contains the space-separated version
                
                pattern_conditions = []
                
                # Exact match (highest priority)
                pattern_conditions.append("p.normalized_name = ?")
                params.append(normalized_name)
                
                # Full search term in product name (high priority)
                pattern_conditions.append("LOWER(p.\"Product Name*\") LIKE ?")
                params.append(f"%{normalized_name.lower()}%")
                
                # Space-separated version in product name
                space_name = normalized_name.replace('_', ' ')
                pattern_conditions.append("LOWER(p.\"Product Name*\") LIKE ?")
                params.append(f"%{space_name.lower()}%")
                
                # Only add individual word matches for very specific cases
                # Only match individual words if they are meaningful (longer than 4 chars) and not common words
                common_words = {'the', 'and', 'or', 'for', 'with', 'by', 'from', 'to', 'of', 'in', 'on', 'at', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'}
                meaningful_words = [w for w in normalized_name.split('_') if len(w) > 4 and w.lower() not in common_words]
                for word in meaningful_words:
                    pattern_conditions.append("LOWER(p.\"Product Name*\") LIKE ?")
                    params.append(f"%{word.lower()}%")
                
                if pattern_conditions:
                    query += " AND (" + " OR ".join(pattern_conditions) + ")"
            
            # Add product type filtering for better accuracy
            if product_type:
                # Map product types to database values
                product_type_mapping = {
                    'capsule': ['capsule', 'pill', 'cap'],
                    'solid edible': ['solid edible', 'edible', 'gummy', 'chocolate', 'candy', 'cookie', 'brownie'],
                    'topical ointment': ['topical ointment', 'topical', 'cream', 'balm', 'lotion', 'salve'],
                    'liquid edible': ['liquid edible', 'tincture', 'drops'],
                    'core flower': ['core flower', 'flower', 'bud', 'nug']
                }
                
                product_type_lower = product_type.lower().strip()
                if product_type_lower in product_type_mapping:
                    type_conditions = []
                    for db_type in product_type_mapping[product_type_lower]:
                        type_conditions.append("LOWER(p.\"Product Type*\") LIKE ?")
                        params.append(f"%{db_type}%")
                    
                    if type_conditions:
                        query += " AND (" + " OR ".join(type_conditions) + ")"
            
            if vendor:
                # Vendor match
                query += " AND p.\"Vendor/Supplier*\" LIKE ?"
                params.append(f"%{vendor}%")
            
            # Note: Product Type is often empty in the database, so we'll make this optional
            # if product_type:
            #     # Product type match
            #     query += " AND p.\"Product Type*\" LIKE ?"
            #     params.append(f"%{product_type}%")
            
            if strain:
                # Strain match - be more flexible with strain matching
                strain_conditions = []
                
                # Direct strain match
                strain_conditions.append("p.\"Product Strain\" LIKE ?")
                params.append(f"%{strain}%")
                
                # Lineage match
                strain_conditions.append("p.\"Lineage\" LIKE ?")
                params.append(f"%{strain}%")
                
                # Flexible strain matching for common variations
                if strain.lower() in ['mix', 'mixed']:
                    strain_conditions.append("p.\"Product Strain\" LIKE ?")
                    params.append("%Mixed%")
                    strain_conditions.append("p.\"Lineage\" LIKE ?")
                    params.append("%MIXED%")
                elif strain.lower() in ['sativa', 'sat']:
                    strain_conditions.append("p.\"Product Strain\" LIKE ?")
                    params.append("%Sativa%")
                    strain_conditions.append("p.\"Lineage\" LIKE ?")
                    params.append("%SATIVA%")
                elif strain.lower() in ['indica', 'ind']:
                    strain_conditions.append("p.\"Product Strain\" LIKE ?")
                    params.append("%Indica%")
                    strain_conditions.append("p.\"Lineage\" LIKE ?")
                    params.append("%INDICA%")
                
                if strain_conditions:
                    query += " AND (" + " OR ".join(strain_conditions) + ")"
            
            # Store the query for potential fallback
            original_query = query
            original_params = params.copy()
            
            # Order by relevance with product type priority
            if product_type:
                product_type_lower = product_type.lower().strip()
                query += f""" ORDER BY 
                    CASE WHEN LOWER(p."Product Type*") = ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN LOWER(p."Product Type*") LIKE ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p.normalized_name = ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Product Name*" = ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Product Name*" LIKE ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Description" LIKE ? THEN 1 ELSE 0 END DESC,
                    p.id DESC 
                    LIMIT 1"""
                params.extend([product_type_lower, f"%{product_type_lower}%", normalized_name, normalized_name, f"%{normalized_name}%", f"%{normalized_name}%"])
            else:
                query += """ ORDER BY 
                    CASE WHEN p.normalized_name = ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Product Name*" = ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Product Name*" LIKE ? THEN 1 ELSE 0 END DESC,
                    CASE WHEN p."Description" LIKE ? THEN 1 ELSE 0 END DESC,
                    p.id DESC 
                    LIMIT 1"""
                params.extend([normalized_name, normalized_name, f"%{normalized_name}%", f"%{normalized_name}%"])
            
            # DEBUG: Log the actual query being executed
            print(f"🔍 DEBUG: Executing query: {query}")
            print(f"🔍 DEBUG: With params: {params}")
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # DEBUG: Log database query results
            print(f"🔍 DEBUG: Database query returned: {result is not None}")
            if result:
                print(f"🔍 DEBUG: Found database match: {result[1]}")  # Product Name*
            else:
                print(f"🔍 DEBUG: No database match found for '{normalized_name}'")
                
                # FALLBACK: Try without strain matching if strain was specified
                if strain and 'original_query' in locals():
                    print(f"🔍 DEBUG: Trying fallback query without strain matching...")
                    
                    # Remove strain conditions from the query
                    fallback_query = original_query
                    fallback_params = []
                    
                    # Rebuild query without strain conditions
                    if normalized_name:
                        fallback_query += " AND (p.normalized_name = ? OR LOWER(p.\"Product Name*\") LIKE ? OR LOWER(p.\"Product Name*\") LIKE ? OR LOWER(p.\"Product Name*\") LIKE ?)"
                        fallback_params.extend([normalized_name, f"%{normalized_name.lower()}%", f"%{normalized_name.lower()}%", f"%{normalized_name.lower()}%"])
                    
                    if product_type:
                        product_type_lower = product_type.lower().strip()
                        product_type_mapping = {
                            'capsule': ['capsule', 'pill', 'cap'],
                            'solid edible': ['solid edible', 'edible', 'gummy', 'chocolate', 'candy', 'cookie', 'brownie'],
                            'topical ointment': ['topical ointment', 'topical', 'cream', 'balm', 'lotion', 'salve'],
                            'liquid edible': ['liquid edible', 'tincture', 'drops'],
                            'core flower': ['core flower', 'flower', 'bud', 'nug']
                        }
                        
                        if product_type_lower in product_type_mapping:
                            type_conditions = []
                            for db_type in product_type_mapping[product_type_lower]:
                                type_conditions.append("LOWER(p.\"Product Type*\") LIKE ?")
                                fallback_params.append(f"%{db_type}%")
                            
                            if type_conditions:
                                fallback_query += " AND (" + " OR ".join(type_conditions) + ")"
                    
                    if vendor:
                        fallback_query += " AND p.\"Vendor/Supplier*\" LIKE ?"
                        fallback_params.append(f"%{vendor}%")
                    
                    # Add ordering
                    if product_type:
                        fallback_query += f""" ORDER BY 
                            CASE WHEN LOWER(p."Product Type*") = ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN LOWER(p."Product Type*") LIKE ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p.normalized_name = ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Product Name*" = ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Product Name*" LIKE ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Description" LIKE ? THEN 1 ELSE 0 END DESC,
                            p.id DESC 
                            LIMIT 1"""
                        fallback_params.extend([product_type_lower, f"%{product_type_lower}%", normalized_name, normalized_name, f"%{normalized_name}%", f"%{normalized_name}%"])
                    else:
                        fallback_query += """ ORDER BY 
                            CASE WHEN p.normalized_name = ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Product Name*" = ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Product Name*" LIKE ? THEN 1 ELSE 0 END DESC,
                            CASE WHEN p."Description" LIKE ? THEN 1 ELSE 0 END DESC,
                            p.id DESC 
                            LIMIT 1"""
                        fallback_params.extend([normalized_name, normalized_name, f"%{normalized_name}%", f"%{normalized_name}%"])
                    
                    print(f"🔍 DEBUG: Executing fallback query: {fallback_query}")
                    print(f"🔍 DEBUG: With fallback params: {fallback_params}")
                    
                    cursor.execute(fallback_query, fallback_params)
                    result = cursor.fetchone()
                    
                    print(f"🔍 DEBUG: Fallback query returned: {result is not None}")
                    if result:
                        print(f"🔍 DEBUG: Found fallback database match: {result[1]}")  # Product Name*
                
                # DEBUG: Let's see what's actually in the database
                try:
                    debug_cursor = conn.cursor()
                    debug_cursor.execute("SELECT \"Product Name*\", \"Description\" FROM products WHERE \"Product Name*\" LIKE ? OR \"Description\" LIKE ? LIMIT 5", [f"%{normalized_name}%", f"%{normalized_name}%"])
                    debug_results = debug_cursor.fetchall()
                    print(f"🔍 DEBUG: Database search for '{normalized_name}' returned {len(debug_results)} results")
                    for i, row in enumerate(debug_results):
                        print(f"🔍 DEBUG:   {i+1}. Product: '{row[0]}', Description: '{row[1][:50]}...'")
                    
                    # Also check what product names actually exist
                    debug_cursor.execute("SELECT \"Product Name*\" FROM products WHERE \"Product Name*\" LIKE ? LIMIT 10", [f"%{normalized_name.split('_')[0]}%"])  # Search for first word
                    debug_names = debug_cursor.fetchall()
                    print(f"🔍 DEBUG: Products containing '{normalized_name.split('_')[0]}': {[row[0] for row in debug_names]}")
                except Exception as debug_error:
                    print(f"🔍 DEBUG: Debug query failed: {debug_error}")
            
            if result:
                # Convert to the same format as get_products_by_names using actual column indices
                product_info = {
                    'id': result[0],
                    'ProductName': result[1],  # Product Name*
                    'Product Name*': result[1],  # Excel column name compatibility
                    'Product Strain': result[2],  # Product Strain
                    'Product Type*': result[3],  # Product Type*
                    'Vendor': result[4],  # Vendor/Supplier*
                    'Vendor/Supplier*': result[4],  # Excel column name compatibility
                    'Product Brand': result[5],  # Product Brand
                    'Lineage': result[6] or 'MIXED',  # Lineage
                    'Description': result[7] or result[1],  # Description or Product Name*
                    'Weight*': result[8],  # Weight*
                    'Units': result[9],  # Units
                    'Price': result[10],  # Price
                    'Quantity*': result[11],  # Quantity*
                    'DOH': result[12],  # DOH
                    'concentrate_type': result[13],  # Concentrate Type
                    'Ratio': result[14],  # Ratio
                    'JointRatio': result[15],  # Joint Ratio
                    'State': result[16],  # State
                    'Is Sample?': result[17],  # Is Sample
                    'Is MJ product?': result[18],  # Is MJ Product
                    'Discountable?': result[19],  # Discountable
                    'Room*': result[20],  # Room
                    'batch_number': result[21],  # Batch Number
                    'lot_number': result[22],  # Lot Number
                    'barcode': result[23],  # Barcode
                    'Medical Only': result[24],  # Medical Only
                    'med_price': result[25],  # Med Price
                    'expiration_date': result[26],  # Expiration Date
                    'is_archived': result[27],  # Is Archived
                    'thc_per_serving': result[28],  # THC Per Serving
                    'allergens': result[29],  # Allergens
                    'solvent': result[30],  # Solvent
                    'accepted_date': result[31],  # Accepted Date
                    'internal_product_identifier': result[32],  # Internal Product Identifier
                    'product_tags': result[33],  # Product Tags
                    'image_url': result[34],  # Image URL
                    'ingredients': result[35],  # Ingredients
                    'combined_weight': result[36],  # Combined Weight
                    'ratio_or_thc_cbd': result[37],  # Ratio or THC/CBD
                    'description_complexity': result[38],  # Description Complexity
                    'Total THC': result[39],  # Total THC
                    'THCA': result[40],  # THCA
                    'CBDA': result[41],  # CBDA
                    'CBN': result[42],  # CBN
                    'total_occurrences': result[43],
                    'first_seen_date': result[44],
                    'last_seen_date': result[45],
                    # Add Excel column name compatibility fields
                    'ProductBrand': result[5],
                    'ProductStrain': result[2],
                    'WeightWithUnits': f"{result[8]}{result[9]}" if result[8] and result[9] else result[8] or result[9] or '',
                    'displayName': result[1],  # For frontend compatibility
                    'Source': 'Product Database Match'  # Indicate this came from database
                }
                
                logger.info(f"Found database match for '{product_name}': {product_info['ProductName']}")
                return product_info
            
            logger.info(f"No database match found for '{product_name}'")
            return None
            
        except Exception as e:
            logger.error(f"Error finding best product match: {e}")
            return None

    def make_educated_guess(self, product_name: str, vendor: str = None, brand: str = None) -> Optional[Dict[str, Any]]:
        """
        Make an educated guess for a product based primarily on the product name itself.
        Extracts vendor, brand, weight, product type, and strain from the product name.
        
        Args:
            product_name: The product name to make a guess for
            vendor: Optional vendor name (will be extracted from product name if not provided)
            brand: Optional brand name (will be extracted from product name if not provided)
            
        Returns:
            Dictionary with inferred product information or None if no good matches found
        """
        try:
            self.init_database()
            
            logger.info(f"Making educated guess for: {product_name}")
            
            # Extract all information directly from the product name
            extracted_info = self._extract_all_info_from_product_name(product_name, vendor, brand)
            
            if extracted_info:
                logger.info(f"Successfully extracted info from product name: {extracted_info}")
                return extracted_info
            
            # Fallback: Use similar products if direct extraction fails
            logger.info("Direct extraction failed, falling back to similar products approach")
            return self._make_educated_guess_from_similar_products(product_name, vendor, brand)
            
        except Exception as e:
            logger.error(f"Error making educated guess for '{product_name}': {e}")
            return None
    
    def _extract_all_info_from_product_name(self, product_name: str, vendor: str = None, brand: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract all product information directly from the product name.
        Handles patterns like "Liquid Diamond Disposable Vape by Oleum"
        """
        try:
            # Extract vendor and brand from product name if not provided
            extracted_vendor, extracted_brand = self._extract_vendor_and_brand_from_name(product_name, vendor, brand)
            
            # Extract weight and units
            weight_info = self._infer_weight_from_name(product_name)
            
            # Extract product type
            product_type = self._infer_product_type_from_name(product_name)
            
            # Extract strain name
            strain_name = self._extract_strain_from_name(product_name)
            
            # Infer price based on product type and weight
            price = self._infer_price_from_type_and_weight(product_type, float(weight_info['weight']))
            
            # Default lineage to HYBRID if we can't determine it
            lineage = 'HYBRID'
            
            # Create the result
            result = {
                'product_name': product_name,
                'source': 'Educated Guess',
                'confidence': 'high' if extracted_brand else 'medium',
                'weight': weight_info['weight'],
                'units': weight_info['units'],
                'price': str(price),
                'product_type': product_type or 'Unknown',
                'lineage': lineage,
                'strain_name': strain_name or 'Unknown',
                'vendor': extracted_vendor or 'Unknown',
                'brand': extracted_brand or 'Unknown',
                'description': f"{product_name} - {weight_info['weight']}{weight_info['units']}"
            }
            
            logger.info(f"Extracted from product name: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting info from product name '{product_name}': {e}")
            return None
    
    def _extract_vendor_and_brand_from_name(self, product_name: str, vendor: str = None, brand: str = None) -> tuple[str, str]:
        """
        Extract vendor and brand from product name patterns like:
        - "Product Name by Brand"
        - "Brand Product Name"
        - "Product Name - Brand"
        """
        import re
        
        if vendor and brand:
            return vendor, brand
        
        name_lower = product_name.lower()
        
        # Pattern 1: "Product Name by Brand"
        by_match = re.search(r'by\s+([A-Za-z0-9\s&]+)(?:\s|$)', product_name, re.IGNORECASE)
        if by_match:
            brand_name = by_match.group(1).strip()
            return brand_name, brand_name  # Brand and vendor are often the same
        
        # Pattern 2: "Brand Product Name" (brand at the beginning)
        # Common brand names to look for
        common_brands = [
            'oleum', 'dank czar', 'omega labs', 'airo pro', 'jsm', "hustler's ambition",
            'ceres', 'harmony farms', "farmer's daughter", 'greasy runtz', 'kelloggz koffee',
            'trop banana', 'velvet koffee', 'trigonal industries', 'peak supply', 'fk it',
            'conscious cannabis', 'honey tree', 'bodhi high', 'skagit organics', 'super fog',
            'seattle bubble works', 'blue sky farms', 'green and gold brands', 'seatown'
        ]
        
        for brand_name in common_brands:
            if brand_name in name_lower:
                return brand_name.title(), brand_name.title()
        
        # Pattern 3: "Product Name - Brand" (brand at the end)
        if " - " in product_name:
            parts = product_name.split(" - ")
            if len(parts) > 1:
                potential_brand = parts[-1].strip()
                if len(potential_brand) > 2:
                    return potential_brand, potential_brand
        
        return vendor or 'Unknown', brand or 'Unknown'
    
    def _make_educated_guess_from_similar_products(self, product_name: str, vendor: str = None, brand: str = None) -> Optional[Dict[str, Any]]:
        """
        Fallback method: Make educated guess using similar products approach.
        This is the original method logic.
        """
        try:
            # Normalize the product name for comparison
            normalized_name = self._normalize_product_name(product_name)
            name_lower = product_name.lower()
            
            # Extract key terms from product name for matching
            key_terms = self._extract_key_terms(product_name)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Strategy 1: Find products with similar names
            similar_products = []
            
            # Search for products with similar key terms
            for term in key_terms:
                if len(term) > 3:  # Only use meaningful terms
                    cursor.execute('''
                        SELECT p."Product Name*", p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Weight*", p."Weight Unit* (grams/gm or ounces/oz)", p."Price* (Tier Name for Bulk)",
                               p."Lineage", s.strain_name, p."Description"
                        FROM products p
                        LEFT JOIN strains s ON p."Product Strain" = s.strain_name
                        WHERE p."Product Name*" LIKE ? OR p."Product Name*" LIKE ?
                        ORDER BY p.id DESC
                        LIMIT 20
                    ''', (f'%{term}%', f'%{term}%'))
                    
                    results = cursor.fetchall()
                    for result in results:
                        similar_products.append({
                            'product_name': result[0],
                            'product_type': result[1],
                            'vendor': result[2],
                            'brand': result[3],
                            'weight': result[4],
                            'units': result[5],
                            'price': result[6],
                            'lineage': result[7],
                            'strain_name': result[8],
                            'description': result[9],
                            'similarity_score': self._calculate_similarity_score(product_name, result[0])
                        })
            
            # Strategy 2: Find products with similar product types
            product_type = self._infer_product_type_from_name(product_name)
            if product_type:
                cursor.execute('''
                    SELECT p."Product Name*", p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Weight*", p."Weight Unit* (grams/gm or ounces/oz)", p."Price* (Tier Name for Bulk)",
                           p."Lineage", s.strain_name, p."Description"
                    FROM products p
                    LEFT JOIN strains s ON p."Product Strain" = s.strain_name
                    WHERE p."Product Type*" = ?
                    ORDER BY p.id DESC
                    LIMIT 10
                ''', (product_type,))
                
                results = cursor.fetchall()
                for result in results:
                    similar_products.append({
                        'product_name': result[0],
                        'product_type': result[1],
                        'vendor': result[2],
                        'brand': result[3],
                        'weight': result[4],
                        'units': result[5],
                        'price': result[6],
                        'lineage': result[7],
                        'strain_name': result[8],
                        'description': result[9],
                        'similarity_score': 0.3  # Lower score for type-only matches
                    })
            
            # Strategy 3: Find products with similar strains
            strain_name = self._extract_strain_from_name(product_name)
            if strain_name:
                cursor.execute('''
                    SELECT p."Product Name*", p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Weight*", p."Weight Unit* (grams/gm or ounces/oz)", p."Price* (Tier Name for Bulk)",
                           p."Lineage", s.strain_name, p."Description"
                    FROM products p
                    LEFT JOIN strains s ON p."Product Strain" = s.strain_name
                    WHERE s.strain_name LIKE ? OR p."Product Strain" LIKE ?
                    ORDER BY p.id DESC
                    LIMIT 10
                ''', (f'%{strain_name}%', f'%{strain_name}%'))
                
                results = cursor.fetchall()
                for result in results:
                    similar_products.append({
                        'product_name': result[0],
                        'product_type': result[1],
                        'vendor': result[2],
                        'brand': result[3],
                        'weight': result[4],
                        'units': result[5],
                        'price': result[6],
                        'lineage': result[7],
                        'strain_name': result[8],
                        'description': result[9],
                        'similarity_score': 0.4  # Medium score for strain matches
                    })
            
            # Remove duplicates and sort by similarity score
            unique_products = {}
            for product in similar_products:
                key = f"{product['product_name']}_{product['vendor']}_{product['brand']}"
                if key not in unique_products or product['similarity_score'] > unique_products[key]['similarity_score']:
                    unique_products[key] = product
            
            similar_products = list(unique_products.values())
            similar_products.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            if not similar_products:
                logger.warning(f"No similar products found for '{product_name}'")
                return None
            
            logger.info(f"Found {len(similar_products)} similar products for '{product_name}'")
            logger.info(f"Key terms extracted: {key_terms}")
            logger.info(f"Product type inferred: {product_type}")
            logger.info(f"Strain name extracted: {strain_name}")
            
            # Take top 5 most similar products for analysis
            top_similar = similar_products[:5]
            
            # Infer properties from similar products
            inferred_data = self._infer_properties_from_similar_products(product_name, top_similar)
            
            if inferred_data:
                logger.info(f"Made educated guess for '{product_name}': {inferred_data}")
                return inferred_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error making educated guess from similar products for '{product_name}': {e}")
            return None
    
    def _extract_key_terms(self, product_name: str) -> Set[str]:
        """Extract key terms from product name for matching."""
        import re
        
        # Remove common words and punctuation
        name_lower = product_name.lower()
        
        # Remove common product words that don't help with matching
        common_words = {
            'live', 'resin', 'rosin', 'wax', 'shatter', 'hash', 'flower', 'bud', 'pre', 'roll', 
            'joint', 'cartridge', 'vape', 'pen', 'edible', 'gummy', 'chocolate', 'cookie', 
            'brownie', 'candy', 'sweet', 'food', 'drink', 'beverage', 'tincture', 'drops', 
            'capsule', 'pill', 'tablet', 'lozenge', 'mint', 'chew', 'chewing', 'cream', 
            'lotion', 'salve', 'balm', 'ointment', 'gel', 'spray', 'patch', 'transdermal', 
            'skin', 'external', 'apply', 'rub', 'disposable', 'pod', 'battery', 'oil', 
            'extract', 'concentrate', 'distillate', 'sauce', 'terp', 'terpene', 'diamond',
            'crystal', 'powder', 'granule', 'pellet', 'tablet', 'capsule', 'liquid', 'solid'
        }
        
        # Extract words, filter out common words and short words
        words = re.findall(r'\b[a-zA-Z]+\b', name_lower)
        key_terms = {word for word in words if len(word) > 2 and word not in common_words}
        
        # Add broader matching terms for better similarity
        # For example, "Glazed Apricots" should match "Wedding Cake" (both are dessert-like)
        dessert_terms = {'glazed', 'apricots', 'wedding', 'cake', 'cherry', 'lemon', 'blueberry', 'strawberry'}
        if any(term in key_terms for term in dessert_terms):
            # Add dessert-related terms to improve matching
            key_terms.update({'cake', 'dessert', 'fruit', 'sweet'})
        
        # Add strain-related terms for better matching
        strain_terms = {'kush', 'haze', 'diesel', 'og', 'cookies', 'runtz', 'gelato'}
        if any(term in key_terms for term in strain_terms):
            key_terms.update({'strain', 'cannabis', 'marijuana'})
        
        return key_terms
    
    def _calculate_similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two product names."""
        from difflib import SequenceMatcher
        
        # Use sequence matcher for overall similarity
        similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        
        # Boost score for exact word matches
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        word_overlap = len(words1.intersection(words2))
        total_words = len(words1.union(words2))
        
        if total_words > 0:
            word_similarity = word_overlap / total_words
            # Combine overall similarity with word overlap
            final_score = (similarity + word_similarity) / 2
        else:
            final_score = similarity
        
        return final_score
    
    def _infer_product_type_from_name(self, product_name: str) -> Optional[str]:
        """Infer product type from product name using consistent logic."""
        if not isinstance(product_name, str):
            return "Unknown Type"
        
        name_lower = product_name.lower()
        
        # Check TYPE_OVERRIDES first
        from src.core.constants import TYPE_OVERRIDES
        for key, value in TYPE_OVERRIDES.items():
            if key in name_lower:
                return value
        
        # Pattern-based inference - prioritize vape keywords over concentrate keywords
        if any(x in name_lower for x in ["flower", "bud", "nug", "herb", "marijuana", "cannabis"]):
            return "Flower"
        elif any(x in name_lower for x in ["vape", "cart", "cartridge", "disposable", "pod", "battery", "jefe", "twisted", "fire", "pen"]):
            return "Vape Cartridge"
        elif any(x in name_lower for x in ["concentrate", "rosin", "shatter", "wax", "live resin", "diamonds", "sauce", "extract", "oil", "distillate"]):
            return "Concentrate"
        elif any(x in name_lower for x in ["edible", "gummy", "chocolate", "cookie", "brownie", "candy"]):
            return "Edible (Solid)"
        elif any(x in name_lower for x in ["tincture", "oil", "drops", "liquid"]):
            return "Edible (Liquid)"
        elif any(x in name_lower for x in ["pre-roll", "joint", "cigar", "blunt"]):
            return "Pre-roll"
        elif any(x in name_lower for x in ["topical", "cream", "lotion", "salve", "balm"]):
            return "Topical"
        elif any(x in name_lower for x in ["tincture", "sublingual"]):
            return "Tincture"
        else:
            # Default to Vape Cartridge for any remaining unknown types since most products are concentrates
            return "Vape Cartridge"
    
    def _extract_strain_from_name(self, product_name: str) -> Optional[str]:
        """Extract strain name from product name."""
        import re
        
        # Common strain keywords
        strain_keywords = [
            'og', 'kush', 'haze', 'diesel', 'cookies', 'runtz', 'gelato', 'wedding', 'cake',
            'blueberry', 'strawberry', 'banana', 'mango', 'pineapple', 'lemon', 'lime', 'cherry',
            'grape', 'apple', 'orange', 'guava', 'dragon', 'fruit', 'passion', 'peach', 'apricot',
            'watermelon', 'cantaloupe', 'honeydew', 'kiwi', 'plum', 'raspberry', 'blackberry',
            'yoda', 'amnesia', 'afghani', 'hashplant', 'super', 'boof', 'grandy', 'candy',
            'tricho', 'jordan', 'cosmic', 'combo', 'honey', 'bread', 'mintz', 'grinch'
        ]
        
        name_lower = product_name.lower()
        words = name_lower.split()
        
        # Look for multi-word strain names first (e.g., "Wedding Cake", "Sour Diesel")
        multi_word_strains = [
            'wedding cake', 'sour diesel', 'blueberry kush', 'lemon haze', 'strawberry cough',
            'granddaddy purple', 'northern lights', 'white widow', 'jack herer', 'durban poison',
            'trainwreck', 'chemdawg', 'sour cheese', 'dream crack', 'maui wowie', 'bubba kush',
            'master kush', 'hindu kush', 'afghan kush', 'master og', 'sour og', 'cheese og',
            'dream og', 'high life', 'white gummie', 'seattle trophy wife', 'tangerine queen',
            'triangle kush', 'red velvet cake', 'grape goji', 'watermelon mojito', 'candy pound cake',
            'truffle cake', 'emerald apricot', 'bollywood runtz', 'mango punch', 'raspberry lemonade',
            'strawberry burst', 'watermelon wave', 'grape soda', 'strawberry bliss', 'cherry ztripez',
            'metaverse', 'galactic jack', 'gdpunch', 'grape ape', 'rainbow cake', 'strawberry mimosa',
            'yoda og', 'goji og', 'cookies and cream', 'grape gas gelatti', 'maui wowie', 
            'strawberry shortcake', 'grapefruit', 'purple rain', 'crepe ape', 'trunk funk', 
            'sub woofer', 'golden pineapple', 'chicken & waffles'
        ]
        
        for strain in multi_word_strains:
            if strain in name_lower:
                # Return the proper case version
                return strain.title()
        
        # Look for single word strain keywords
        for word in words:
            if word in strain_keywords:
                return word.title()
        
        # Look for capitalized words that might be strain names (but exclude common product words)
        common_product_words = {
            'live', 'resin', 'rosin', 'wax', 'shatter', 'hash', 'flower', 'bud', 'pre', 'roll', 
            'joint', 'cartridge', 'vape', 'pen', 'edible', 'gummy', 'chocolate', 'cookie', 
            'brownie', 'candy', 'sweet', 'food', 'drink', 'beverage', 'tincture', 'drops', 
            'capsule', 'pill', 'tablet', 'lozenge', 'mint', 'chew', 'chewing', 'cream', 
            'lotion', 'salve', 'balm', 'ointment', 'gel', 'spray', 'patch', 'transdermal', 
            'skin', 'external', 'apply', 'rub', 'disposable', 'pod', 'battery', 'oil', 
            'extract', 'concentrate', 'distillate', 'sauce', 'terp', 'terpene', 'diamond',
            'crystal', 'powder', 'granule', 'pellet', 'tablet', 'capsule', 'liquid', 'solid'
        }
        
        for word in product_name.split():
            if (len(word) > 2 and word[0].isupper() and word[1:].islower() and 
                word.lower() not in common_product_words):
                return word
        
        return None
    
    def _infer_properties_from_similar_products(self, product_name: str, similar_products: List[Dict]) -> Optional[Dict[str, Any]]:
        """Infer product properties from similar products."""
        if not similar_products:
            return None
        
        # Extract weight and units
        weights = []
        units = []
        prices = []
        product_types = []
        lineages = []
        strains = []
        vendors = []
        brands = []
        
        for product in similar_products:
            # Weight and units
            if product['weight'] and product['weight'] != 'nan':
                try:
                    weight_val = float(product['weight'])
                    if weight_val > 0:
                        weights.append(weight_val)
                        if product['units'] and product['units'] != 'nan':
                            units.append(product['units'])
                except (ValueError, TypeError):
                    pass
            
            # Price
            if product['price'] and product['price'] != 'nan':
                try:
                    price_val = float(product['price'])
                    if price_val > 0:
                        prices.append(price_val)
                except (ValueError, TypeError):
                    pass
            
            # Product type
            if product['product_type'] and product['product_type'] != 'nan':
                product_types.append(product['product_type'])
            
            # Lineage
            if product['lineage'] and product['lineage'] != 'nan':
                lineages.append(product['lineage'])
            
            # Strain
            if product['strain_name'] and product['strain_name'] != 'nan':
                strains.append(product['strain_name'])
            
            # Vendor
            if product['vendor'] and product['vendor'] != 'nan':
                vendors.append(product['vendor'])
            
            # Brand
            if product['brand'] and product['brand'] != 'nan':
                brands.append(product['brand'])
        
        # Calculate most common values
        from collections import Counter
        
        inferred_data = {
            'product_name': product_name,
            'source': 'Educated Guess',
            'confidence': 'medium'
        }
        
        # Weight and units - PRIORITY: Use weight from product name first, then similar products
        weight_info = self._infer_weight_from_name(product_name)
        if weight_info['weight'] != '1.0' or 'g' not in product_name.lower():  # If we found a specific weight in the name
            inferred_data['weight'] = weight_info['weight']
            inferred_data['units'] = weight_info['units']
            logger.info(f"Using weight from product name: {weight_info['weight']}{weight_info['units']}")
        elif weights:
            # Use median weight from similar products
            weights.sort()
            median_weight = weights[len(weights) // 2]
            inferred_data['weight'] = str(median_weight)
            
            if units:
                most_common_unit = Counter(units).most_common(1)[0][0]
                inferred_data['units'] = most_common_unit
            else:
                inferred_data['units'] = 'g'  # Default
            logger.info(f"Using weight from similar products: {inferred_data['weight']}{inferred_data['units']}")
        else:
            # Fallback weight inference
            inferred_data['weight'] = weight_info['weight']
            inferred_data['units'] = weight_info['units']
            logger.info(f"Using fallback weight: {weight_info['weight']}{weight_info['units']}")
        
        # Price
        if prices:
            # Use median price for more stability
            prices.sort()
            median_price = prices[len(prices) // 2]
            inferred_data['price'] = str(median_price)
        else:
            # Fallback price inference
            inferred_data['price'] = self._infer_price_from_type_and_weight(
                inferred_data.get('product_type', 'Unknown'),
                float(inferred_data['weight'])
            )
        
        # Product type
        if product_types:
            most_common_type = Counter(product_types).most_common(1)[0][0]
            inferred_data['product_type'] = most_common_type
        else:
            inferred_data['product_type'] = self._infer_product_type_from_name(product_name) or 'Unknown'
        
        # Lineage
        if lineages:
            most_common_lineage = Counter(lineages).most_common(1)[0][0]
            inferred_data['lineage'] = most_common_lineage
        else:
            inferred_data['lineage'] = 'HYBRID'  # Default
        
        # Strain - PRIORITY: Extract from product name first, then use similar products
        extracted_strain = self._extract_strain_from_name(product_name)
        if extracted_strain and extracted_strain != 'Unknown':
            inferred_data['strain_name'] = extracted_strain
            logger.info(f"Using strain from product name: {extracted_strain}")
        elif strains:
            most_common_strain = Counter(strains).most_common(1)[0][0]
            inferred_data['strain_name'] = most_common_strain
            logger.info(f"Using strain from similar products: {most_common_strain}")
        else:
            inferred_data['strain_name'] = 'Unknown'
            logger.info("No strain information available")
        
        # Vendor
        if vendors:
            most_common_vendor = Counter(vendors).most_common(1)[0][0]
            inferred_data['vendor'] = most_common_vendor
        else:
            inferred_data['vendor'] = 'Unknown'
        
        # Brand
        if brands:
            most_common_brand = Counter(brands).most_common(1)[0][0]
            inferred_data['brand'] = most_common_brand
        else:
            inferred_data['brand'] = 'Unknown'
        
        # Description
        inferred_data['description'] = f"{product_name} - {inferred_data['weight']}{inferred_data['units']}"
        
        return inferred_data
    
    def _infer_weight_from_name(self, product_name: str) -> Dict[str, str]:
        """Infer weight from product name."""
        import re
        
        # Look for weight patterns in product name
        weight_patterns = [
            r'(\d+\.?\d*)\s*(g|gram|grams|gm)',  # 3.5g, 3.5 gram, etc.
            r'(\d+\.?\d*)\s*(mg|milligram|milligrams)',  # 100mg, etc.
            r'(\d+\.?\d*)\s*(oz|ounce|ounces)',  # 1oz, etc.
            r'(\d+\.?\d*)\s*(lb|pound|pounds)',  # 1lb, etc.
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                weight = match.group(1)
                units = match.group(2).lower()
                if units in ['gram', 'grams', 'gm']:
                    units = 'g'
                elif units in ['milligram', 'milligrams']:
                    units = 'mg'
                elif units in ['ounce', 'ounces']:
                    units = 'oz'
                elif units in ['pound', 'pounds']:
                    units = 'lb'
                return {'weight': weight, 'units': units}
        
        # Default weights based on product type
        product_type = self._infer_product_type_from_name(product_name)
        default_weights = {
            'flower': {'weight': '3.5', 'units': 'g'},
            'pre-roll': {'weight': '1.0', 'units': 'g'},
            'concentrate': {'weight': '1.0', 'units': 'g'},
            'vape': {'weight': '0.5', 'units': 'g'},
            'edible': {'weight': '10', 'units': 'mg'},
            'tincture': {'weight': '30', 'units': 'ml'},
            'topical': {'weight': '30', 'units': 'ml'}
        }
        
        return default_weights.get(product_type, {'weight': '1.0', 'units': 'g'})
    
    def _infer_price_from_type_and_weight(self, product_type: str, weight: float) -> str:
        """Infer price based on product type and weight."""
        product_type_lower = product_type.lower()
        
        if 'pre-roll' in product_type_lower:
            return '20'
        elif 'flower' in product_type_lower:
            if weight <= 1:
                return '35'
            elif weight <= 3.5:
                return '120'
            elif weight <= 7:
                return '220'
            else:
                return '400'
        elif 'concentrate' in product_type_lower:
            if weight <= 1:
                return '50'
            elif weight <= 2:
                return '90'
            else:
                return '150'
        elif 'vape' in product_type_lower:
            return '40'
        elif 'edible' in product_type_lower:
            return '25'
        else:
            return '25'
    
    def search_products_by_name(self, product_name: str) -> List[Dict]:
        """Search for products by exact product name."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Search for products with exact name match
            cursor.execute('''
                SELECT p.id, p."Product Name*", p.normalized_name, p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                       p."Description", p."Weight*", p."Units", p."Price", p."Quantity*", p."DOH", p."Concentrate Type", p."Ratio", p."JointRatio",
                       p."State", p."Is Sample? (yes/no)", p."Is MJ product?(yes/no)", p."Discountable? (yes/no)", p."Room*", p."Batch Number", p."Lot Number", p."Barcode*",
                       p."Medical Only (Yes/No)", p."Med Price", p."Expiration Date(YYYY-MM-DD)", p."Is Archived? (yes/no)", p."THC Per Serving", p."Allergens", p."Solvent", p."Accepted Date",
                       p."Internal Product Identifier", p."Product Tags (comma separated)", p."Image URL", p."Ingredients", p."CombinedWeight", p."Ratio_or_THC_CBD", 
                       p."Description_Complexity", p."Total THC", p."THCA", p."CBDA", p."CBN", p.total_occurrences, p.first_seen_date, p.last_seen_date,
                       s.canonical_lineage, s.sovereign_lineage
                FROM products p
                LEFT JOIN strains s ON p.strain_id = s.id
                WHERE p."Product Name*" = ?
                ORDER BY p.last_seen_date DESC
            ''', (product_name,))
            
            results = []
            for row in cursor.fetchall():
                product = dict(zip([col[0] for col in cursor.description], row))
                results.append(product)
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching products by name: {e}")
            return []
    
    def search_products_by_strain(self, strain_name: str) -> List[Dict]:
        """Search for products by strain name."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Search for products with matching strain
            cursor.execute('''
                SELECT p.id, p."Product Name*", p.normalized_name, p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                       p."Description", p."Weight*", p."Units", p."Price", p."Quantity*", p."DOH", p."Concentrate Type", p."Ratio", p."JointRatio",
                       p."State", p."Is Sample? (yes/no)", p."Is MJ product?(yes/no)", p."Discountable? (yes/no)", p."Room*", p."Batch Number", p."Lot Number", p."Barcode*",
                       p."Medical Only (Yes/No)", p."Med Price", p."Expiration Date(YYYY-MM-DD)", p."Is Archived? (yes/no)", p."THC Per Serving", p."Allergens", p."Solvent", p."Accepted Date",
                       p."Internal Product Identifier", p."Product Tags (comma separated)", p."Image URL", p."Ingredients", p."CombinedWeight", p."Ratio_or_THC_CBD", 
                       p."Description_Complexity", p."Total THC", p."THCA", p."CBDA", p."CBN", p.total_occurrences, p.first_seen_date, p.last_seen_date,
                       s.canonical_lineage, s.sovereign_lineage
                FROM products p
                LEFT JOIN strains s ON p.strain_id = s.id
                WHERE p."Product Strain" LIKE ? OR s.strain_name LIKE ?
                ORDER BY p.last_seen_date DESC
            ''', (f'%{strain_name}%', f'%{strain_name}%'))
            
            results = []
            for row in cursor.fetchall():
                product = dict(zip([col[0] for col in cursor.description], row))
                results.append(product)
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching products by strain: {e}")
            return []
    
    def search_products_by_type_and_strain(self, product_type: str, strain_name: str) -> List[Dict]:
        """Search for products by product type and strain combination."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Search for products with matching type and strain
            cursor.execute('''
                SELECT p.id, p."Product Name*", p.normalized_name, p."Product Type*", p."Vendor/Supplier*", p."Product Brand", p."Lineage",
                       p."Description", p."Weight*", p."Units", p."Price", p."Quantity*", p."DOH", p."Concentrate Type", p."Ratio", p."JointRatio",
                       p."State", p."Is Sample? (yes/no)", p."Is MJ product?(yes/no)", p."Discountable? (yes/no)", p."Room*", p."Batch Number", p."Lot Number", p."Barcode*",
                       p."Medical Only (Yes/No)", p."Med Price", p."Expiration Date(YYYY-MM-DD)", p."Is Archived? (yes/no)", p."THC Per Serving", p."Allergens", p."Solvent", p."Accepted Date",
                       p."Internal Product Identifier", p."Product Tags (comma separated)", p."Image URL", p."Ingredients", p."CombinedWeight", p."Ratio_or_THC_CBD", 
                       p."Description_Complexity", p."Total THC", p."THCA", p."CBDA", p."CBN", p.total_occurrences, p.first_seen_date, p.last_seen_date,
                       s.canonical_lineage, s.sovereign_lineage
                FROM products p
                LEFT JOIN strains s ON p.strain_id = s.id
                WHERE p."Product Type*" = ? AND (p."Product Strain" = ? OR s.strain_name = ?)
                ORDER BY p.last_seen_date DESC
            ''', (product_type, strain_name, strain_name))
            
            results = []
            for row in cursor.fetchall():
                product = dict(zip([col[0] for col in cursor.description], row))
                results.append(product)
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching products by type and strain: {e}")
            return []
    
    def clear_all_data(self):
        """Clear all data from the database tables."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clear all data from tables
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM strains")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='strains'")
            
            conn.commit()
            logging.info("All database data cleared successfully")
            
        except Exception as e:
            logging.error(f"Error clearing database data: {e}")
            raise

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products from the database for export."""
        try:
            self.init_database()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # First, get the actual column names from the database
            cursor.execute("PRAGMA table_info(products)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # Build the SELECT query dynamically based on available columns
            select_columns = []
            for col_name in column_names:
                if col_name != 'id':  # Skip id as it's handled separately
                    select_columns.append(f'p."{col_name}"')
            
            query = f'''
                SELECT p.id, {", ".join(select_columns)}
                FROM products p
                ORDER BY p.id
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            products = []
            
            for result in results:
                product = {'id': result[0]}
                
                # Map remaining columns dynamically
                for i, col_name in enumerate(column_names[1:], 1):  # Skip id column
                    if i < len(result):
                        product[col_name] = result[i]
                    else:
                        product[col_name] = None
                
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []
    
    def update_all_product_strains(self) -> Dict[str, Any]:
        """Update all existing Product Strain column values using the _calculate_product_strain logic."""
        try:
            self.init_database()
            
            with self._write_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get all products with their data
                cursor.execute('''
                    SELECT id, "Product Type*", "Product Name*", "Description", "Ratio"
                    FROM products
                ''')
                products = cursor.fetchall()
                
                updated_count = 0
                for product_id, product_type, product_name, description, ratio in products:
                    # Calculate the correct Product Strain value
                    new_strain = self._calculate_product_strain_original(
                        product_type or '',
                        product_name or '',
                        description or '',
                        ratio or ''
                    )
                    
                    # Update the product
                    cursor.execute('''
                        UPDATE products 
                        SET "Product Strain" = ?
                        WHERE id = ?
                    ''', (new_strain, product_id))
                    updated_count += 1
                
                conn.commit()
                logger.info(f"Updated {updated_count} product strains")
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'Successfully updated {updated_count} product strains'
                }
                
        except Exception as e:
            logger.error(f"Error updating product strains: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update product strains: {e}'
            }
    
    def update_all_ratio_or_thc_cbd(self) -> Dict[str, Any]:
        """Update all existing Ratio_or_THC_CBD column values using the _calculate_ratio_or_thc_cbd logic."""
        try:
            self.init_database()
            
            with self._write_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get all products with their THC/CBD values and Ratio column
                cursor.execute('''
                    SELECT id, "Product Name*", "Product Type*", "THC test result", "CBD test result", "Ratio", "Ratio_or_THC_CBD"
                    FROM products
                ''')
                products = cursor.fetchall()
                
                updated_count = 0
                for product_id, product_name, product_type, thc_value, cbd_value, ratio_value, current_ratio in products:
                    # Only update if current value is placeholder or doesn't contain actual values
                    if (current_ratio in ['THC: | BR | C', 'THC: CBD:', 'THC:\nCBD:', '', "'THC: | BR | C'"] or 
                        (current_ratio and 'THC:' in current_ratio and 'CBD:' in current_ratio and '%' not in current_ratio) or
                        (current_ratio and current_ratio.strip() == 'THC: | BR | C') or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'") or
                        (current_ratio and current_ratio.strip() == "'THC: | BR | C'")):
                        # Use the proper calculation method based on product type
                        new_ratio = self._calculate_ratio_or_thc_cbd(
                            product_type, 
                            ratio_value,  # Use Ratio column for non-classic types
                            '',  # joint_ratio not used in this context
                            product_name,
                            str(thc_value) if thc_value else '',  # Pass THC value for classic types
                            str(cbd_value) if cbd_value else ''   # Pass CBD value for classic types
                        )
                        
                        # Update the product
                        cursor.execute('''
                            UPDATE products 
                            SET "Ratio_or_THC_CBD" = ?
                            WHERE id = ?
                        ''', (new_ratio, product_id))
                        updated_count += 1
                
                conn.commit()
                logger.info(f"Updated {updated_count} ratio_or_thc_cbd values")
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'Successfully updated {updated_count} ratio_or_thc_cbd values'
                }
                
        except Exception as e:
            logger.error(f"Error updating ratio_or_thc_cbd: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update ratio_or_thc_cbd: {e}'
            }
    
    def update_all_joint_ratios(self) -> Dict[str, Any]:
        """Update all JointRatio values to remove ' x 1' suffix."""
        try:
            self.init_database()
            
            with self._write_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get all products with JointRatio values
                cursor.execute('''
                    SELECT id, "JointRatio"
                    FROM products
                    WHERE "JointRatio" LIKE '% x 1'
                ''')
                products = cursor.fetchall()
                
                updated_count = 0
                for product_id, joint_ratio in products:
                    # Remove ' x 1' from the end
                    new_joint_ratio = joint_ratio.replace(' x 1', '')
                    
                    # Update the product
                    cursor.execute('''
                        UPDATE products 
                        SET "JointRatio" = ?
                        WHERE id = ?
                    ''', (new_joint_ratio, product_id))
                    updated_count += 1
                
                conn.commit()
                logger.info(f"Updated {updated_count} joint ratios")
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'Successfully updated {updated_count} joint ratios'
                }
                
        except Exception as e:
            logger.error(f"Error updating joint ratios: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update joint ratios: {e}'
            }

    def _calculate_product_strain(self, product_data):
        """Calculate Product Strain from product_data dictionary (overloaded version)."""
        try:
            # Handle both dict and individual parameter formats
            if isinstance(product_data, dict):
                product_type = product_data.get('Product Type*', '') or product_data.get('product_type', '')
                product_name = product_data.get('Product Name*', '') or product_data.get('product_name', '')
                description = product_data.get('Description', '') or product_data.get('description', '')
                ratio = product_data.get('Ratio', '') or product_data.get('ratio', '')
                
                # Call the original method with extracted parameters
                return self._calculate_product_strain_original(product_type, product_name, description, ratio)
            else:
                # If it's not a dict, assume it's the product_type parameter
                return self._calculate_product_strain_original(product_data, '', '', '')
                
        except Exception as e:
            print(f"Error in overloaded _calculate_product_strain: {e}")
            return 'Mixed'

def get_product_database(store_name=None):
    """Get a ProductDatabase instance for the specified store."""
    return ProductDatabase(store_name=store_name) 

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ProductDatabase admin tools")
    parser.add_argument('--update-canonical-to-mode', action='store_true', help='Update all canonical lineages to mode lineage')
    args = parser.parse_args()
    if args.update_canonical_to_mode:
        # CRITICAL FIX: Use correct database path
        db = ProductDatabase(get_database_path())
        db.update_all_canonical_lineages_to_mode()
        # Canonical lineages updated to mode for all strains. 