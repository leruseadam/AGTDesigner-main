#!/usr/bin/env python3
"""
Check vendor names in the database to understand the matching issue
"""
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_vendor_names():
    """Check what vendor names exist in the database"""
    try:
        from src.core.data.product_database import ProductDatabase
        
        # Check main database
        db_path = os.path.join(current_dir, 'uploads', 'product_database.db')
        if not os.path.exists(db_path):
            # Try AGT_Bothell database
            db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        if os.path.exists(db_path):
            print(f"Checking database: {db_path}")
            db = ProductDatabase(db_path)
            
            # Get all products and extract vendor information
            products = db.get_all_products()
            print(f"Total products: {len(products)}")
            
            # Extract vendor names
            vendors = set()
            vendor_fields = ['Vendor/Supplier*', 'Vendor', 'Vendor/Supplier', 'vendor', 'supplier']
            
            for product in products:
                for field in vendor_fields:
                    if field in product and product[field]:
                        vendor = str(product[field]).strip()
                        if vendor and vendor != 'nan' and vendor != 'None':
                            vendors.add(vendor)
            
            print(f"\\nFound {len(vendors)} unique vendors:")
            sorted_vendors = sorted(list(vendors))
            for i, vendor in enumerate(sorted_vendors):
                print(f"  {i+1:3d}. '{vendor}'")
            
            # Look specifically for "A Greener Today" variants
            print("\\n=== A Greener Today Variants ===")
            agt_vendors = [v for v in sorted_vendors if 'greener today' in v.lower() or 'agt' in v.lower()]
            for vendor in agt_vendors:
                print(f"  - '{vendor}'")
            
            # Look for Bothell vendors
            print("\\n=== Bothell Vendors ===")
            bothell_vendors = [v for v in sorted_vendors if 'bothell' in v.lower()]
            for vendor in bothell_vendors:
                print(f"  - '{vendor}'")
            
            print("\\n=== Testing Vendor Normalization ===")
            test_vendor = "A Greener Today - Bothell"
            print(f"Input vendor: '{test_vendor}'")
            normalized = test_vendor.lower().strip()
            print(f"Normalized: '{normalized}'")
            
            # Check what the enhanced matcher does
            from src.core.data.enhanced_json_matcher import EnhancedJSONMatcher
            from src.core.data.excel_processor import ExcelProcessor
            
            excel_processor = ExcelProcessor()
            matcher = EnhancedJSONMatcher(excel_processor)
            
            # Test vendor matching
            matching_products = []
            for product in products[:10]:  # Test first 10 products
                for field in vendor_fields:
                    if field in product and product[field]:
                        product_vendor = str(product[field]).strip().lower()
                        if normalized in product_vendor or product_vendor in normalized:
                            matching_products.append(product)
                            print(f"  MATCH: Product vendor '{product[field]}' matches input vendor")
                            break
            
            print(f"\\nFound {len(matching_products)} products with matching vendor from first 10 products")
                        
        else:
            print("No database found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vendor_names()