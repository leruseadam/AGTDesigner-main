#!/usr/bin/env python3
"""
Quick PostgreSQL Setup for Label Maker
This creates a hybrid system that can use PostgreSQL when available
"""

import os
import sys
import json
from datetime import datetime

def create_optimized_database_config():
    """Create an optimized database configuration that can use PostgreSQL or SQLite"""
    
    config_content = '''"""
Optimized Database Configuration for Label Maker
Supports both PostgreSQL and SQLite with automatic fallback
"""

import os
import logging
import json
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
            
            db_path = 'uploads/product_database.db'
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
        """PostgreSQL full-text search"""
        try:
            self.cursor.execute("""
                SELECT *, 
                       ts_rank(to_tsvector('english', name), plainto_tsquery('english', %s)) as rank
                FROM products 
                WHERE to_tsvector('english', name) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC, name
                LIMIT %s
            """, (query, query, limit))
            
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logging.error(f"PostgreSQL search failed: {e}")
            return []
    
    def _sqlite_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """SQLite search with optimization"""
        try:
            # Use multiple search strategies for better results
            search_terms = query.split()
            
            if len(search_terms) == 1:
                # Single term search
                self.cursor.execute("""
                    SELECT * FROM products 
                    WHERE name LIKE ? OR strain LIKE ? OR vendor LIKE ?
                    ORDER BY 
                        CASE 
                            WHEN name LIKE ? THEN 1
                            WHEN strain LIKE ? THEN 2
                            WHEN vendor LIKE ? THEN 3
                            ELSE 4
                        END,
                        name
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", 
                      f"%{query}%", f"%{query}%", f"%{query}%", limit))
            else:
                # Multi-term search
                like_patterns = [f"%{term}%" for term in search_terms]
                where_clause = " OR ".join(["name LIKE ?"] * len(search_terms))
                
                self.cursor.execute(f"""
                    SELECT * FROM products 
                    WHERE {where_clause}
                    ORDER BY name
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
                ORDER BY name
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
                WHERE product_type = ?
                ORDER BY name
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
            
            self.cursor.execute("SELECT COUNT(DISTINCT product_type) as types FROM products")
            product_types = self.cursor.fetchone()[0]
            
            return {
                'database_type': self.db_type,
                'total_products': total_products,
                'product_types': product_types,
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
'''
    
    with open('optimized_database.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Optimized database configuration created")

def create_app_integration():
    """Create integration code for the main app"""
    
    integration_content = '''"""
App Integration for Optimized Database
Add this to your main app.py file
"""

# Add this import at the top of app.py
from optimized_database import db, search_products, get_all_products, get_database_type, get_database_stats

# Replace your existing product search routes with these optimized versions:

@app.route('/api/search-products')
def api_search_products():
    """Optimized product search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 50))
        
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        # Use optimized search
        products = search_products(query, limit)
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products),
            'database_type': get_database_type(),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database-stats')
def api_database_stats():
    """Get database statistics"""
    try:
        stats = get_database_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this to your existing product matching logic:
def optimized_product_matching(product_name, product_type=None):
    """Optimized product matching using the best available database"""
    try:
        # Search for exact matches first
        exact_matches = search_products(product_name, limit=10)
        
        if exact_matches:
            # Return the best match
            return exact_matches[0]
        
        # Search for partial matches
        partial_matches = search_products(product_name.split()[0] if product_name else "", limit=5)
        
        if partial_matches:
            return partial_matches[0]
        
        return None
        
    except Exception as e:
        logging.error(f"Product matching failed: {e}")
        return None
'''
    
    with open('app_integration.py', 'w') as f:
        f.write(integration_content)
    
    print("✅ App integration code created")

def create_performance_test():
    """Create a performance test script"""
    
    test_content = '''#!/usr/bin/env python3
"""
Performance Test for Optimized Database
Tests both SQLite and PostgreSQL performance
"""

import time
import json
from optimized_database import db, search_products, get_database_stats

def test_search_performance():
    """Test search performance"""
    
    print("🔍 Testing search performance...")
    
    test_queries = [
        "Blue Dream",
        "OG Kush", 
        "Sour Diesel",
        "Gelato",
        "Wedding Cake"
    ]
    
    results = []
    
    for query in test_queries:
        start_time = time.time()
        products = search_products(query, limit=20)
        end_time = time.time()
        
        results.append({
            'query': query,
            'results': len(products),
            'time_ms': round((end_time - start_time) * 1000, 2),
            'database_type': db.db_type
        })
        
        print(f"  {query}: {len(products)} results in {results[-1]['time_ms']}ms")
    
    return results

def test_database_stats():
    """Test database statistics"""
    
    print("\\n📊 Database Statistics:")
    
    stats = get_database_stats()
    
    print(f"  Database Type: {stats.get('database_type', 'Unknown')}")
    print(f"  Total Products: {stats.get('total_products', 0)}")
    print(f"  Product Types: {stats.get('product_types', 0)}")
    
    return stats

def run_performance_test():
    """Run complete performance test"""
    
    print("🚀 Starting Performance Test...")
    print(f"Database Type: {db.db_type}")
    print("=" * 50)
    
    # Test search performance
    search_results = test_search_performance()
    
    # Test database stats
    stats = test_database_stats()
    
    # Calculate average search time
    avg_time = sum(r['time_ms'] for r in search_results) / len(search_results)
    
    print("\\n📈 Performance Summary:")
    print(f"  Average Search Time: {avg_time:.2f}ms")
    print(f"  Database Type: {db.db_type}")
    print(f"  Total Products: {stats.get('total_products', 0)}")
    
    # Save results
    results = {
        'timestamp': time.time(),
        'database_type': db.db_type,
        'search_results': search_results,
        'stats': stats,
        'average_search_time_ms': avg_time
    }
    
    with open('performance_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\\n✅ Performance test complete!")
    print("📄 Results saved to performance_test_results.json")
    
    return results

if __name__ == "__main__":
    run_performance_test()
'''
    
    with open('test_database_performance.py', 'w') as f:
        f.write(test_content)
    
    print("✅ Performance test script created")

if __name__ == "__main__":
    print("🚀 Setting up optimized database system...")
    
    create_optimized_database_config()
    create_app_integration()
    create_performance_test()
    
    print("\\n🎉 Setup complete!")
    print("\\n📋 Next steps:")
    print("1. Run: python test_database_performance.py")
    print("2. Add the integration code to your app.py")
    print("3. Test the new search endpoints")
    print("4. For PostgreSQL: Set up a PostgreSQL database and update environment variables")
    
    print("\\n💡 To use PostgreSQL:")
    print("   Set these environment variables:")
    print("   DB_HOST=your_postgres_host")
    print("   DB_NAME=your_database_name") 
    print("   DB_USER=your_username")
    print("   DB_PASSWORD=your_password")
    print("   DB_PORT=5432")
