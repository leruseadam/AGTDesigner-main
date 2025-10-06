#!/usr/bin/env python3
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
    
    print("\n📊 Database Statistics:")
    
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
    
    print("\n📈 Performance Summary:")
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
    
    print("\n✅ Performance test complete!")
    print("📄 Results saved to performance_test_results.json")
    
    return results

if __name__ == "__main__":
    run_performance_test()
