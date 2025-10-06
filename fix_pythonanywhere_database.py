#!/usr/bin/env python3
"""
Fix PythonAnywhere Database Schema Issues
This script updates the database schema to match the current code expectations
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def fix_database_schema():
    """Fix database schema to match current code expectations"""
    
    print("🔧 Fixing PythonAnywhere Database Schema...")
    print("=" * 50)
    
    # Database connection parameters
    db_config = {
        'host': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'database': 'postgres',
        'user': 'super',
        'password': '193154life',
        'port': '14822'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Check current table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print(f"📋 Current products table has {len(columns)} columns")
        
        # Check if we have the expected columns
        column_names = [col[0] for col in columns]
        
        # Expected columns based on the error messages
        expected_columns = [
            'Vendor/Supplier*',
            'Product Type*'
        ]
        
        missing_columns = []
        for col in expected_columns:
            if col not in column_names:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            print("🔧 Adding missing columns...")
            
            # Add missing columns
            for col in missing_columns:
                try:
                    if col == 'Vendor/Supplier*':
                        cur.execute('ALTER TABLE products ADD COLUMN "Vendor/Supplier*" TEXT;')
                        print(f"✅ Added column: {col}")
                    elif col == 'Product Type*':
                        cur.execute('ALTER TABLE products ADD COLUMN "Product Type*" TEXT;')
                        print(f"✅ Added column: {col}")
                except Exception as e:
                    print(f"⚠️ Could not add column {col}: {e}")
        else:
            print("✅ All expected columns exist")
        
        # Check for any other schema issues
        print("\n🔍 Checking for other potential issues...")
        
        # Check if we have any data
        cur.execute("SELECT COUNT(*) FROM products;")
        product_count = cur.fetchone()[0]
        print(f"📊 Total products in database: {product_count}")
        
        # Check strains table
        cur.execute("SELECT COUNT(*) FROM strains;")
        strain_count = cur.fetchone()[0]
        print(f"🌿 Total strains in database: {strain_count}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Database schema check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")
        return False

if __name__ == "__main__":
    fix_database_schema()