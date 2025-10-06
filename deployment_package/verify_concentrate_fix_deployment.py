#!/usr/bin/env python3
"""
Verify concentrate filter fix deployment
Run this script after deploying to verify the fix is working
"""

import sqlite3
import sys
import os

def test_concentrate_fix_deployment():
    """Test that the concentrate filter fix is properly deployed"""
    
    print("🧪 Testing concentrate filter fix deployment...")
    
    # Test 1: Check if app.py has the fix
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
            
        if 'processed_record = process_database_product_for_api(db_record)' in app_content:
            print("✅ app.py contains the fix")
        else:
            print("❌ app.py does not contain the fix")
            return False
            
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False
    
    # Test 2: Check database for concentrate products
    db_path = 'uploads/product_database_AGT_Bothell.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for concentrate products with weight data
        cursor.execute("""
            SELECT ProductName, Description, Weight, Units 
            FROM products 
            WHERE Type = 'Concentrate' 
            AND Weight IS NOT NULL 
            AND Units IS NOT NULL 
            LIMIT 3
        """)
        
        concentrate_products = cursor.fetchall()
        conn.close()
        
        if concentrate_products:
            print(f"✅ Found {len(concentrate_products)} concentrate products with weight data")
            for product in concentrate_products:
                name, desc, weight, units = product
                print(f"   - {name}: {weight}{units}")
        else:
            print("⚠️  No concentrate products with weight data found")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    
    print("\n🎯 Deployment verification complete!")
    print("\n📋 Next steps:")
    print("1. Reload your web application")
    print("2. Test concentrate filter in web interface")
    print("3. Generate labels and verify weights appear")
    
    return True

if __name__ == "__main__":
    success = test_concentrate_fix_deployment()
    sys.exit(0 if success else 1)