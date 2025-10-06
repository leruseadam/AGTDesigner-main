#!/usr/bin/env python3
"""
PostgreSQL ProductDatabase for PythonAnywhere
Replaces SQLite ProductDatabase with PostgreSQL for better performance
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

class PostgreSQLProductDatabase:
    """PostgreSQL database for storing and managing product and strain information."""
    
    def __init__(self, store_name: str = None):
        self.store_name = store_name or 'AGT_Bothell'
        self._connection_pool = {}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._initialized = False
        self._init_lock = threading.Lock()
        self._write_lock = threading.RLock()
        
        # PostgreSQL connection config
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'agt_designer'),
            'user': os.getenv('DB_USER', os.getenv('USER', 'adamcordova')),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        
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
                logging.error(f"PostgreSQL connection failed: {e}")
                return None
        return self._connection_pool[thread_id]
    
    def init_database(self):
        """Initialize the database (PostgreSQL schema already exists from migration)."""
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
                
                # Test if tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'products'
                    )
                """)
                
                if cursor.fetchone()[0]:
                    self._initialized = True
                    logging.info(f"PostgreSQL database initialized for store '{self.store_name}'")
                    return True
                else:
                    logging.error("PostgreSQL tables not found. Run migration first.")
                    return False
                    
            except Exception as e:
                logging.error(f"Error initializing PostgreSQL database: {e}")
                return False
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return True
    
    def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products using PostgreSQL full-text search."""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"search:{query}:{limit}"
        with self._cache_lock:
            if cache_key in self._cache:
                self._timing_stats['cache_hits'] += 1
                self._timing_stats['queries'] += 1
                self._timing_stats['total_time'] += time.time() - start_time
                return self._cache[cache_key]
            self._timing_stats['cache_misses'] += 1
        
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Use PostgreSQL full-text search
            cursor.execute("""
                SELECT *, 
                       ts_rank(to_tsvector('english', COALESCE(product_name, '')), plainto_tsquery('english', %s)) as rank
                FROM products 
                WHERE to_tsvector('english', COALESCE(product_name, '')) @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', COALESCE(product_strain, '')) @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', COALESCE(vendor_supplier, '')) @@ plainto_tsquery('english', %s)
                   OR product_name ILIKE %s
                   OR product_strain ILIKE %s
                   OR vendor_supplier ILIKE %s
                ORDER BY rank DESC, product_name
                LIMIT %s
            """, (query, query, query, query, f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Cache results
            with self._cache_lock:
                self._cache[cache_key] = results
                # Limit cache size
                if len(self._cache) > 100:
                    # Remove oldest entries
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
            
            self._timing_stats['queries'] += 1
            self._timing_stats['total_time'] += time.time() - start_time
            
            return results
            
        except Exception as e:
            logging.error(f"PostgreSQL search failed: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_all_products(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all products."""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM products 
                ORDER BY product_name
                LIMIT %s
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"Get all products failed: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_products_by_type(self, product_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get products by type."""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM products 
                WHERE product_type = %s
                ORDER BY product_name
                LIMIT %s
            """, (product_type, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"Get products by type failed: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self._get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get product count
            cursor.execute("SELECT COUNT(*) as total_products FROM products")
            total_products = cursor.fetchone()['total_products']
            
            # Get product types
            cursor.execute("SELECT COUNT(DISTINCT product_type) as product_types FROM products")
            product_types = cursor.fetchone()['product_types']
            
            # Get strains
            cursor.execute("SELECT COUNT(DISTINCT product_strain) as strains FROM products WHERE product_strain IS NOT NULL")
            strains = cursor.fetchone()['strains']
            
            # Get vendors
            cursor.execute("SELECT COUNT(DISTINCT vendor_supplier) as vendors FROM products WHERE vendor_supplier IS NOT NULL")
            vendors = cursor.fetchone()['vendors']
            
            return {
                'total_products': total_products,
                'product_types': product_types,
                'strains': strains,
                'vendors': vendors,
                'database_type': 'PostgreSQL',
                'store_name': self.store_name,
                'performance_stats': self._timing_stats.copy()
            }
            
        except Exception as e:
            logging.error(f"Get database stats failed: {e}")
            return {}
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def test_connection(self) -> bool:
        """Test PostgreSQL connection."""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception as e:
            logging.error(f"PostgreSQL test failed: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def close_connections(self):
        """Close all connections."""
        for conn in self._connection_pool.values():
            try:
                conn.close()
            except:
                pass
        self._connection_pool.clear()

# Global PostgreSQL database instance
_postgresql_db = None

def get_postgresql_database(store_name: str = None) -> PostgreSQLProductDatabase:
    """Get PostgreSQL database instance."""
    global _postgresql_db
    if _postgresql_db is None or (store_name and _postgresql_db.store_name != store_name):
        _postgresql_db = PostgreSQLProductDatabase(store_name)
        _postgresql_db.init_database()
    return _postgresql_db

# Compatibility function for existing code
def get_product_database(store_name: str = None) -> PostgreSQLProductDatabase:
    """Compatibility function - returns PostgreSQL database instead of SQLite."""
    return get_postgresql_database(store_name)

if __name__ == "__main__":
    # Test the PostgreSQL database
    db = PostgreSQLProductDatabase('AGT_Bothell')
    
    if db.test_connection():
        print("✅ PostgreSQL connection successful")
        
        # Test search
        results = db.search_products("Blue Dream", limit=5)
        print(f"🔍 Search test: Found {len(results)} products")
        
        # Test stats
        stats = db.get_database_stats()
        print(f"📊 Database stats: {stats}")
        
    else:
        print("❌ PostgreSQL connection failed")
