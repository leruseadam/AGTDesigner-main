#!/usr/bin/env python3

import sqlite3

def test_ice_cream_cake_database():
    print("🔍 Checking Ice Cream Cake Wax database entry...")
    
    # Connect to the product database
    conn = sqlite3.connect('uploads/product_database.db')
    cursor = conn.cursor()

    # Search for the specific Ice Cream Cake Wax product
    cursor.execute('''
        SELECT "Product Name*", "Product Type*", "Product Brand", "Lineage", "Product Strain" 
        FROM products 
        WHERE "Product Name*" LIKE '%Ice Cream Cake Wax%Ambition%' 
        OR "Product Name*" LIKE '%Ice Cream Cake Wax%'
        ORDER BY "Product Name*"
    ''')

    results = cursor.fetchall()
    print(f'Found {len(results)} Ice Cream Cake Wax products:')
    
    for row in results:
        name, product_type, brand, lineage, strain = row
        print(f'  📋 Product: {name}')
        print(f'      Type: {product_type}')
        print(f'      Brand: {brand}')
        print(f'      Current Lineage: {lineage}')
        print(f'      Product Strain: {strain}')
        print()
        
        # Check if this is the Hustler's Ambition product
        if 'ambition' in name.lower():
            print(f"🎯 Found the target product!")
            print(f"   Current lineage in database: {lineage}")
            if lineage == 'HYBRID':
                print("   ⚠️  Database shows HYBRID - this explains the output!")
                print("   💡 User's UI change to INDICA is not persisting to database")
            elif lineage == 'INDICA':
                print("   ✅ Database shows INDICA - lineage update worked!")
            else:
                print(f"   ❓ Unexpected lineage: {lineage}")

    conn.close()
    
    if len(results) == 0:
        print("❌ No Ice Cream Cake Wax products found in database")
        
        # Try broader search
        cursor = sqlite3.connect('uploads/product_database.db').cursor()
        cursor.execute('''
            SELECT "Product Name*", "Lineage" 
            FROM products 
            WHERE "Product Name*" LIKE '%Ice Cream Cake%'
            AND "Product Type*" = 'Concentrate'
            LIMIT 10
        ''')
        
        broader_results = cursor.fetchall()
        print(f"\n🔍 Found {len(broader_results)} Ice Cream Cake concentrate products:")
        for name, lineage in broader_results:
            print(f"   - {name}: {lineage}")

if __name__ == '__main__':
    test_ice_cream_cake_database()