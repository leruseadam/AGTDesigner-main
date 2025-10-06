#!/usr/bin/env python3
"""
Quick script to check and fix database issues on PythonAnywhere.
Run this after uploading to diagnose database problems.
"""

import os
import sys
import sqlite3

def check_database():
    """Check if database exists and has data."""
    print("=" * 60)
    print("DATABASE DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Check for database files
    possible_db_paths = [
        'product_database.db',
        'uploads/product_database_AGT_Bothell.db',
        'data/product_database.db',
        '/home/adamcordova/labelMaker/product_database.db',
        '/home/adamcordova/labelMaker/uploads/product_database_AGT_Bothell.db',
    ]
    
    found_dbs = []
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            found_dbs.append(db_path)
            print(f"\n✓ Found database: {db_path}")
            
            # Check size
            size = os.path.getsize(db_path)
            print(f"  Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
            
            # Check contents
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if products table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
                if cursor.fetchone():
                    # Count products
                    cursor.execute("SELECT COUNT(*) FROM products")
                    count = cursor.fetchone()[0]
                    print(f"  Products table: ✓ ({count:,} products)")
                    
                    # Check if Units column exists
                    cursor.execute("PRAGMA table_info(products)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'Units' in columns:
                        print(f"  Units column: ✓")
                        
                        # Check how many have Units data
                        cursor.execute("SELECT COUNT(*) FROM products WHERE Units IS NOT NULL AND Units != ''")
                        units_count = cursor.fetchone()[0]
                        print(f"  Products with Units: {units_count:,} ({units_count/count*100:.1f}%)")
                    else:
                        print(f"  Units column: ✗ MISSING")
                    
                    # Check Weight* column
                    if 'Weight*' in columns:
                        cursor.execute("SELECT COUNT(*) FROM products WHERE \"Weight*\" IS NOT NULL AND \"Weight*\" != ''")
                        weight_count = cursor.fetchone()[0]
                        print(f"  Products with Weight*: {weight_count:,} ({weight_count/count*100:.1f}%)")
                    
                    # Sample product
                    cursor.execute("SELECT \"Product Name*\", \"Weight*\", Units FROM products LIMIT 1")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"  Sample: {sample[0]} - Weight: {sample[1]}, Units: {sample[2]}")
                    
                else:
                    print(f"  Products table: ✗ NOT FOUND")
                
                conn.close()
                
            except Exception as e:
                print(f"  Error reading database: {e}")
        else:
            print(f"\n✗ Not found: {db_path}")
    
    if not found_dbs:
        print("\n❌ NO DATABASES FOUND!")
        print("\nRECOMMENDATION: Upload an Excel file to create the database.")
        return False
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    check_database()

