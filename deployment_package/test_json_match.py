#!/usr/bin/env python3
"""
Test script to diagnose JSON matching issues
"""
import os
import sys
import logging

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_json_matcher_import():
    """Test if we can import the JSON matcher classes"""
    try:
        from src.core.data.enhanced_json_matcher import EnhancedJSONMatcher
        print("✓ Successfully imported EnhancedJSONMatcher")
        return True
    except Exception as e:
        print(f"✗ Failed to import EnhancedJSONMatcher: {e}")
        try:
            from src.core.data.json_matcher import JSONMatcher
            print("✓ Successfully imported basic JSONMatcher")
            return True
        except Exception as e2:
            print(f"✗ Failed to import basic JSONMatcher: {e2}")
            return False

def test_excel_processor():
    """Test if we can create an ExcelProcessor"""
    try:
        from src.core.data.excel_processor import ExcelProcessor
        
        # Look for existing Excel files
        uploads_dir = os.path.join(current_dir, 'uploads')
        excel_files = []
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                if file.endswith(('.xlsx', '.xls')):
                    excel_files.append(os.path.join(uploads_dir, file))
        
        if excel_files:
            print(f"Found Excel files: {excel_files}")
            # Try to create processor with first Excel file
            processor = ExcelProcessor(excel_files[0])
            if hasattr(processor, 'df') and processor.df is not None:
                print(f"✓ ExcelProcessor created successfully with {len(processor.df)} rows")
                return processor
            else:
                print("✗ ExcelProcessor created but no data loaded")
        else:
            print("No Excel files found in uploads directory")
            
        return None
    except Exception as e:
        print(f"✗ Failed to create ExcelProcessor: {e}")
        return None

def test_product_database():
    """Test if we can access the product database"""
    try:
        from src.core.data.product_database import ProductDatabase
        
        # Try main database first
        db_path = os.path.join(current_dir, 'uploads', 'product_database.db')
        if not os.path.exists(db_path):
            # Try AGT_Bothell database
            db_path = os.path.join(current_dir, 'AGT_Bothell', 'product_database.db')
        
        if os.path.exists(db_path):
            print(f"Found database at: {db_path}")
            db = ProductDatabase(db_path)
            
            # Test basic functionality
            products = db.get_all_products()
            print(f"✓ ProductDatabase loaded with {len(products)} products")
            
            # Check for strain data
            strains = db.get_all_strains()
            print(f"✓ Database contains {len(strains)} strains")
            
            return db
        else:
            print("✗ No product database found")
            return None
            
    except Exception as e:
        print(f"✗ Failed to access ProductDatabase: {e}")
        return None

def test_json_matcher_creation():
    """Test creating a JSON matcher with available data"""
    try:
        excel_processor = test_excel_processor()
        
        if excel_processor is None:
            print("Creating empty ExcelProcessor for JSON matcher test...")
            from src.core.data.excel_processor import ExcelProcessor
            excel_processor = ExcelProcessor()
        
        # Try Enhanced JSON Matcher first
        try:
            from src.core.data.enhanced_json_matcher import EnhancedJSONMatcher
            json_matcher = EnhancedJSONMatcher(excel_processor)
            
            # Test if it can load database products
            db_products = json_matcher._get_database_products()
            if db_products:
                print(f"✓ EnhancedJSONMatcher created and loaded {len(db_products)} database products")
                
                # Try to build ML models
                import pandas as pd
                json_matcher.excel_processor.df = pd.DataFrame(db_products)
                json_matcher._build_ml_models()
                print("✓ ML models built successfully")
                
                return json_matcher
            else:
                print("✗ EnhancedJSONMatcher created but no database products found")
                
        except Exception as e:
            print(f"Enhanced JSON matcher failed: {e}")
            
            # Fall back to basic matcher
            from src.core.data.json_matcher import JSONMatcher
            json_matcher = JSONMatcher(excel_processor)
            print("✓ Basic JSONMatcher created as fallback")
            return json_matcher
            
    except Exception as e:
        print(f"✗ Failed to create any JSON matcher: {e}")
        return None

def test_sample_json_url():
    """Test JSON matching with a sample URL"""
    json_matcher = test_json_matcher_creation()
    if json_matcher is None:
        print("Cannot test JSON matching - no matcher available")
        return
    
    # Test with a simple JSON URL (you can replace this with actual URL)
    test_url = "https://jsonplaceholder.typicode.com/posts"
    print(f"\nTesting JSON fetch from: {test_url}")
    
    try:
        # Test basic URL fetching
        import requests
        response = requests.get(test_url, timeout=10)
        data = response.json()
        print(f"✓ Successfully fetched JSON with {len(data)} items")
        
        # Test the matcher's fetch_and_match method
        if hasattr(json_matcher, 'fetch_and_match'):
            # This will likely fail with the test URL, but will show us error handling
            result = json_matcher.fetch_and_match(test_url)
            print(f"Matcher returned: {result}")
        else:
            print("✗ JSON matcher missing fetch_and_match method")
            
    except Exception as e:
        print(f"✗ JSON matching test failed: {e}")

if __name__ == "__main__":
    print("=== JSON Matcher Diagnostic Test ===\n")
    
    print("1. Testing imports...")
    test_json_matcher_import()
    
    print("\n2. Testing ExcelProcessor...")
    test_excel_processor()
    
    print("\n3. Testing ProductDatabase...")
    test_product_database()
    
    print("\n4. Testing JSON Matcher creation...")
    test_json_matcher_creation()
    
    print("\n5. Testing sample JSON URL...")
    test_sample_json_url()
    
    print("\n=== Diagnostic Complete ===")