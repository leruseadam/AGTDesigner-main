#!/usr/bin/env python3
"""
Test PostgreSQL connection and performance
"""

import time
from product_database_postgresql import get_postgresql_database

def test_postgresql():
    print("🧪 Testing PostgreSQL Connection...")
    print("=" * 40)
    
    # Test connection
    db = get_postgresql_database('AGT_Bothell')
    
    if not db.test_connection():
        print("❌ PostgreSQL connection failed")
        return False
    
    print("✅ PostgreSQL connection successful")
    
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
        start_time = time.time()
        results = db.search_products(query, limit=10)
        end_time = time.time()
        
        print(f"   '{query}': {len(results)} results in {end_time - start_time:.3f}s")
    
    # Test database stats
    print("\n📊 Database Statistics:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        if key != 'performance_stats':
            print(f"   {key}: {value}")
    
    # Performance stats
    perf_stats = stats.get('performance_stats', {})
    if perf_stats:
        print("\n⚡ Performance Stats:")
        print(f"   Queries: {perf_stats.get('queries', 0)}")
        print(f"   Cache hits: {perf_stats.get('cache_hits', 0)}")
        print(f"   Cache misses: {perf_stats.get('cache_misses', 0)}")
        if perf_stats.get('queries', 0) > 0:
            avg_time = perf_stats.get('total_time', 0) / perf_stats.get('queries', 1)
            print(f"   Average query time: {avg_time:.3f}s")
    
    print("\n🎉 PostgreSQL test completed successfully!")
    return True

if __name__ == "__main__":
    test_postgresql()
