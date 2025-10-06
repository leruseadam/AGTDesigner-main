#!/usr/bin/env python3
"""
Check AGT Bothell database vendor names
"""
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_agt_bothell_vendors():
    """Check what vendor names exist in the AGT Bothell database"""
    try:
        from src.core.data.product_database import ProductDatabase
        
        # Check AGT_Bothell database
        db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        
        if os.path.exists(db_path):
            print(f"Checking AGT Bothell database: {db_path}")
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
                
            # Show sample products to see their vendor field
            print("\\n=== Sample Products ===")
            for i, product in enumerate(products[:5]):
                name = product.get('Product Name*', product.get('ProductName', 'Unknown'))
                for field in vendor_fields:
                    if field in product and product[field]:
                        print(f"  {i+1}. {name} -> {field}: '{product[field]}'")
                        break
                        
        else:
            print("AGT Bothell database not found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_agt_bothell_vendors()