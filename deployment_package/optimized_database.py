"""
Optimized Database Configuration for Label Maker
Supports both PostgreSQL and SQLite with automatic fallback
"""

import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class OptimizedDatabase:
    def __init__(self):
        self.db_type = "sqlite"  # Default to SQLite
        self.connection = None
        self.cursor = None
        
        # Try to use PostgreSQL if available
        if self._try_postgresql():
            self.db_type = "postgresql"
            logging.info("✅ Using PostgreSQL database")
        else:
            self._init_sqlite()
            logging.info("✅ Using SQLite database")
    
    def _try_postgresql(self) -> bool:
        """Try to initialize PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # PostgreSQL connection config
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'labelmaker'),
                'user': os.getenv('DB_USER', 'labelmaker'),
                'password': os.getenv('DB_PASSWORD', ''),
                'port': os.getenv('DB_PORT', '5432')
            }
            
            # Test connection
            self.connection = psycopg2.connect(**config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Test query
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            
            return True
            
        except Exception as e:
            logging.info(f"PostgreSQL not available: {e}")
            return False
    
    def _init_sqlite(self):
        """Initialize SQLite connection"""
        try:
            import sqlite3
            
            # Use the actual database file
            db_path = '/Users/adamcordova/Desktop/product_database_AGT_Bothell.db'
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            
        except Exception as e:
            logging.error(f"SQLite initialization failed: {e}")
            raise
    
    def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products with optimized query"""
        
        if self.db_type == "postgresql":
            return self._postgresql_search(query, limit)
        else:
            return self._sqlite_search(query, limit)
    
    def _postgresql_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """PostgreSQL full-text search using actual schema"""
        try:
            self.cursor.execute("""
                SELECT *, 
                       ts_rank(to_tsvector('english', "Product Name*"), plainto_tsquery('english', %s)) as rank
                FROM products 
                WHERE to_tsvector('english', "Product Name*") @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', "Product Strain") @@ plainto_tsquery('english', %s)
                   OR to_tsvector('english', "Vendor/Supplier*") @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC, "Product Name*"
                LIMIT %s
            """, (query, query, query, query, limit))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"PostgreSQL search failed: {e}")
            return []
    
    def _sqlite_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """SQLite search with optimization using actual database schema"""
        try:
            # Use multiple search strategies for better results
            search_terms = query.split()
            
            if len(search_terms) == 1:
                # Single term search using actual column names
                self.cursor.execute("""
                    SELECT * FROM products 
                    WHERE "Product Name*" LIKE ? 
                       OR "Product Strain" LIKE ? 
                       OR "Vendor/Supplier*" LIKE ?
                       OR "Product Brand" LIKE ?
                       OR normalized_name LIKE ?
                    ORDER BY 
                        CASE 
                            WHEN "Product Name*" LIKE ? THEN 1
                            WHEN "Product Strain" LIKE ? THEN 2
                            WHEN "Vendor/Supplier*" LIKE ? THEN 3
                            WHEN "Product Brand" LIKE ? THEN 4
                            ELSE 5
                        END,
                        "Product Name*"
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%",
                      f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
            else:
                # Multi-term search
                like_patterns = [f"%{term}%" for term in search_terms]
                where_clause = " OR ".join([f'"Product Name*" LIKE ?'] * len(search_terms))
                
                self.cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE {where_clause}
                    ORDER BY "Product Name*"
                    LIMIT ?
                """, like_patterns + [limit])
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"SQLite search failed: {e}")
            return []
    
    def get_all_products(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all products with pagination"""
        try:
            self.cursor.execute("""
                SELECT * FROM products 
                ORDER BY "Product Name*"
                LIMIT ?
            """, (limit,))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"Get products failed: {e}")
            return []
    
    def get_products_by_type(self, product_type: str) -> List[Dict[str, Any]]:
        """Get products by type"""
        try:
            self.cursor.execute("""
                SELECT * FROM products 
                WHERE "Product Type*" = ?
                ORDER BY "Product Name*"
            """, (product_type,))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"Get products by type failed: {e}")
            return []
    
    def update_product_metadata(self, product_id: int, metadata_updates: Dict[str, Any]) -> bool:
        """Update product metadata"""
        try:
            if self.db_type == "postgresql":
                # PostgreSQL JSON update
                self.cursor.execute("""
                    UPDATE products 
                    SET metadata = metadata || %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(metadata_updates), product_id))
            else:
                # SQLite update
                self.cursor.execute("""
                    UPDATE products 
                    SET metadata = json_patch(COALESCE(metadata, '{}'), ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (json.dumps(metadata_updates), product_id))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logging.error(f"Update metadata failed: {e}")
            self.connection.rollback()
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            self.cursor.execute("SELECT COUNT(*) as total FROM products")
            total_products = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(DISTINCT "Product Type*") as types FROM products')
            product_types = self.cursor.fetchone()[0]
            
            # Get some sample data
            self.cursor.execute('SELECT COUNT(DISTINCT "Product Strain") as strains FROM products WHERE "Product Strain" IS NOT NULL AND "Product Strain" != ""')
            strains = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(DISTINCT "Vendor/Supplier*") as vendors FROM products WHERE "Vendor/Supplier*" IS NOT NULL AND "Vendor/Supplier*" != ""')
            vendors = self.cursor.fetchone()[0]
            
            return {
                'database_type': self.db_type,
                'total_products': total_products,
                'product_types': product_types,
                'strains': strains,
                'vendors': vendors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Get stats failed: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

# Global database instance
db = OptimizedDatabase()

# Convenience functions
def search_products(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search products using the optimized database"""
    return db.search_products(query, limit)

def get_all_products(limit: int = 1000) -> List[Dict[str, Any]]:
    """Get all products using the optimized database"""
    return db.get_all_products(limit)

def get_database_type() -> str:
    """Get the current database type"""
    return db.db_type

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    return db.get_database_stats()
