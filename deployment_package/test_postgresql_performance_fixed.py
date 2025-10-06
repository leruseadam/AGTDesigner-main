#!/usr/bin/env python3
"""
Fixed PostgreSQL performance test
"""

import time
import psycopg2
from psycopg2.extras import RealDictCursor

def test_postgresql():
    print("🧪 Testing PostgreSQL Connection...")
    print("=" * 40)
    
    # PostgreSQL connection config
    config = {
        'host': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'database': 'postgres',
        'user': 'super',
        'password': '193154life',
        'port': '14822'
    }
    
    # Test connection
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Test search performance
    print("\n🔍 Testing search performance...")
    
    test_queries = [
        "Blue Dream",
        "OG",
        "Indica",
        "Sativa",
        "Hybrid"
    ]
    
    for query in test_queries:
        try:
            conn = psycopg2.connect(**config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            start_time = time.time()
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
            """, (query, query, query, query, f'%{query}%', f'%{query}%', f'%{query}%', 10))
            
            results = cursor.fetchall()
            end_time = time.time()
            
            print(f"   '{query}': {len(results)} results in {end_time - start_time:.3f}s")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"   '{query}': Error - {e}")
    
    # Test database stats
    print("\n📊 Database Statistics:")
    try:
        conn = psycopg2.connect(**config)
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
        
        print(f"   Total products: {total_products:,}")
        print(f"   Product types: {product_types}")
        print(f"   Strains: {strains}")
        print(f"   Vendors: {vendors}")
        print(f"   Database type: PostgreSQL")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   Error getting stats: {e}")
    
    print("\n🎉 PostgreSQL test completed successfully!")
    return True

if __name__ == "__main__":
    test_postgresql()
