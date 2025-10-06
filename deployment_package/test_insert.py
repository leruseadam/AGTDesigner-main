#!/usr/bin/env python3
import sqlite3

# Test the exact INSERT that's failing
def test_insert():
    db_path = "uploads/product_database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ProductName column exists
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        print("Available columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Try a simple INSERT with ProductName
        test_data = {
            'Product Name*': 'Test Product Name',
            'normalized_name': 'test_product',
            'Product Type*': 'Flower',
            'ProductName': 'Test Product Name Alternative'
        }
        
        cursor.execute('''
            INSERT INTO products (
                "Product Name*", normalized_name, "Product Type*", ProductName
            ) VALUES (?, ?, ?, ?)
        ''', (
            test_data['Product Name*'],
            test_data['normalized_name'], 
            test_data['Product Type*'],
            test_data['ProductName']
        ))
        
        conn.commit()
        print("✅ INSERT successful!")
        
        # Verify the data
        cursor.execute('SELECT "Product Name*", ProductName FROM products WHERE normalized_name = ?', (test_data['normalized_name'],))
        result = cursor.fetchone()
        if result:
            print(f"✅ Data verified: Product Name* = '{result[0]}', ProductName = '{result[1]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    test_insert()