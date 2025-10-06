#!/usr/bin/env python3
"""
Find the most commonly used vendor names in the database
"""
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def find_popular_vendors():
    """Find the most popular vendor names in the database"""
    try:
        from src.core.data.product_database import ProductDatabase
        
        # Check both databases
        databases = [
            os.path.join(current_dir, 'uploads', 'product_database.db'),
            os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
        ]
        
        all_vendor_counts = {}
        
        for db_path in databases:
            if os.path.exists(db_path):
                print(f"\\nAnalyzing database: {db_path}")
                db = ProductDatabase(db_path)
                
                # Get all products and count vendors
                products = db.get_all_products()
                vendor_counts = {}
                vendor_fields = ['Vendor/Supplier*', 'Vendor', 'Vendor/Supplier', 'vendor', 'supplier']
                
                for product in products:
                    vendor_found = False
                    for field in vendor_fields:
                        if field in product and product[field]:
                            vendor = str(product[field]).strip()
                            if vendor and vendor != 'nan' and vendor != 'None':
                                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                                all_vendor_counts[vendor] = all_vendor_counts.get(vendor, 0) + 1
                                vendor_found = True
                                break
                    
                    if not vendor_found:
                        vendor_counts['Unknown/Missing'] = vendor_counts.get('Unknown/Missing', 0) + 1
                
                # Show top 10 vendors for this database
                sorted_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)
                print(f"Top 10 vendors in this database:")
                for i, (vendor, count) in enumerate(sorted_vendors[:10]):
                    print(f"  {i+1:2d}. {vendor} ({count} products)")
        
        # Show overall top vendors
        print(f"\\n=== OVERALL TOP VENDORS (Combined Databases) ===")
        sorted_all_vendors = sorted(all_vendor_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (vendor, count) in enumerate(sorted_all_vendors[:15]):
            print(f"  {i+1:2d}. '{vendor}' ({count} products)")
        
        # Find vendors with good strain variety
        print(f"\\n=== VENDORS WITH GOOD STRAIN VARIETY ===")
        strain_vendors = []
        for vendor, count in sorted_all_vendors[:20]:
            if count >= 20:  # At least 20 products
                # Check if this vendor has strain-based products
                if any(word in vendor.lower() for word in ['artizen', 'panda', 'roots', 'pagoda', 'cannabis']):
                    strain_vendors.append((vendor, count))
        
        for vendor, count in strain_vendors[:5]:
            print(f"  - '{vendor}' ({count} products)")
            
        return sorted_all_vendors[:10]
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    find_popular_vendors()