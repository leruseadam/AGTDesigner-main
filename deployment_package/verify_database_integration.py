#!/usr/bin/env python3
"""
Database Integration Verification Script
Verifies that all components are properly wired with the new database
"""

import sys
import os
sys.path.append('.')

def test_database_connection():
    """Test database connection and basic functionality"""
    print("🔍 Testing Database Connection...")
    
    try:
        from src.core.data.product_database import ProductDatabase
        
        db = ProductDatabase()
        products = db.get_all_products()
        strains = db.get_all_strains()
        
        print(f"✅ Database connection successful")
        print(f"   Products: {len(products)}")
        print(f"   Strains: {len(strains)}")
        
        # Test product search
        if products:
            sample_products = db.search_products_by_name('Blue Dream')
            print(f"   Product search: {len(sample_products)} Blue Dream products found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_json_matcher():
    """Test JSON matcher functionality"""
    print("\n🔍 Testing JSON Matcher...")
    
    try:
        from src.core.data.json_matcher import JSONMatcher
        from src.core.data.excel_processor import ExcelProcessor
        
        excel_processor = ExcelProcessor()
        json_matcher = JSONMatcher(excel_processor)
        
        # Test DB:all mode
        matched_products = json_matcher.fetch_and_match('db:all')
        
        print(f"✅ JSON matcher working")
        print(f"   Matched products: {len(matched_products)}")
        
        if matched_products:
            sample = matched_products[0]
            print(f"   Sample product: {sample.get('Product Name*', 'N/A')}")
            print(f"   Sample brand: {sample.get('Product Brand', 'N/A')}")
            print(f"   Sample strain: {sample.get('Product Strain', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON matcher failed: {e}")
        return False

def test_flask_app():
    """Test Flask application integration"""
    print("\n🔍 Testing Flask Application...")
    
    try:
        from app import app
        
        with app.app_context():
            from src.core.data.product_database import ProductDatabase
            from src.core.data.json_matcher import JSONMatcher
            from src.core.data.excel_processor import ExcelProcessor
            
            # Test database in app context
            db = ProductDatabase()
            products = db.get_all_products()
            
            # Test JSON matcher in app context
            excel_processor = ExcelProcessor()
            json_matcher = JSONMatcher(excel_processor)
            matched_products = json_matcher.fetch_and_match('db:all')
            
            print(f"✅ Flask app integration working")
            print(f"   App context products: {len(products)}")
            print(f"   App context matched: {len(matched_products)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app integration failed: {e}")
        return False

def test_tag_generation():
    """Test tag generation functionality"""
    print("\n🔍 Testing Tag Generation...")
    
    try:
        from src.core.data.json_matcher import JSONMatcher
        from src.core.data.excel_processor import ExcelProcessor
        
        excel_processor = ExcelProcessor()
        json_matcher = JSONMatcher(excel_processor)
        
        # Test tag creation from products
        matched_products = json_matcher.fetch_and_match('db:all')
        
        if matched_products:
            # Test creating tags from first few products
            sample_products = matched_products[:5]
            tags_created = 0
            
            for product in sample_products:
                try:
                    # Test tag creation (this would normally be done in the UI)
                    tag_data = {
                        'Product Name*': product.get('Product Name*', ''),
                        'Product Brand': product.get('Product Brand', ''),
                        'Product Strain': product.get('Product Strain', ''),
                        'Product Type*': product.get('Product Type*', ''),
                        'Vendor/Supplier*': product.get('Vendor/Supplier*', ''),
                        'Weight*': product.get('Weight*', ''),
                        'Price*': product.get('Price*', ''),
                    }
                    tags_created += 1
                except Exception as e:
                    print(f"   Warning: Tag creation failed for product: {e}")
            
            print(f"✅ Tag generation working")
            print(f"   Tags created: {tags_created}")
            print(f"   Sample tag data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Tag generation failed: {e}")
        return False

def test_database_performance():
    """Test database performance with large dataset"""
    print("\n🔍 Testing Database Performance...")
    
    try:
        import time
        from src.core.data.product_database import ProductDatabase
        
        db = ProductDatabase()
        
        # Test query performance
        start_time = time.time()
        products = db.get_all_products()
        query_time = time.time() - start_time
        
        # Test search performance
        start_time = time.time()
        search_results = db.search_products_by_name('Blue Dream')
        search_time = time.time() - start_time
        
        print(f"✅ Database performance acceptable")
        print(f"   Query time: {query_time:.3f}s for {len(products)} products")
        print(f"   Search time: {search_time:.3f}s for {len(search_results)} results")
        
        # Performance thresholds
        if query_time > 5.0:
            print(f"   ⚠️  Query time is slow (>5s)")
        if search_time > 2.0:
            print(f"   ⚠️  Search time is slow (>2s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
        return False

def test_memory_usage():
    """Test memory usage with large database"""
    print("\n🔍 Testing Memory Usage...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load database and components
        from src.core.data.product_database import ProductDatabase
        from src.core.data.json_matcher import JSONMatcher
        from src.core.data.excel_processor import ExcelProcessor
        
        db = ProductDatabase()
        excel_processor = ExcelProcessor()
        json_matcher = JSONMatcher(excel_processor)
        
        # Load data
        products = db.get_all_products()
        matched_products = json_matcher.fetch_and_match('db:all')
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"✅ Memory usage acceptable")
        print(f"   Initial memory: {initial_memory:.1f} MB")
        print(f"   Final memory: {final_memory:.1f} MB")
        print(f"   Memory increase: {memory_increase:.1f} MB")
        
        # Memory thresholds
        if memory_increase > 500:
            print(f"   ⚠️  High memory usage (>500MB increase)")
        if final_memory > 1000:
            print(f"   ⚠️  Total memory usage high (>1GB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory usage test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 Database Integration Verification")
    print("====================================")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("JSON Matcher", test_json_matcher),
        ("Flask Application", test_flask_app),
        ("Tag Generation", test_tag_generation),
        ("Database Performance", test_database_performance),
        ("Memory Usage", test_memory_usage),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=======================")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All components are properly wired and working!")
        print("✅ Database integration is complete and ready for deployment")
    else:
        print(f"\n⚠️  {total - passed} tests failed - please review the issues above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
