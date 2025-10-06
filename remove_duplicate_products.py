#!/usr/bin/env python3
"""
Remove Duplicate Products Script
Removes duplicate products from the database based on the unique constraint:
UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand")
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def set_environment_variables():
    """Set environment variables for database connection"""
    os.environ['DB_HOST'] = 'adamcordova-4822.postgres.pythonanywhere-services.com'
    os.environ['DB_NAME'] = 'postgres'
    os.environ['DB_USER'] = 'super'
    os.environ['DB_PASSWORD'] = '193154life'
    os.environ['DB_PORT'] = '14822'

def remove_duplicate_products():
    """Remove duplicate products from the database"""
    print("🧹 Removing Duplicate Products from Database")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ['DB_PORT']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # First, let's see how many duplicates we have
        print("\n🔍 Analyzing duplicates...")
        cursor.execute('''
            SELECT "Product Name*", "Vendor/Supplier*", "Product Brand", COUNT(*) as count
            FROM products 
            GROUP BY "Product Name*", "Vendor/Supplier*", "Product Brand"
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        
        duplicates = cursor.fetchall()
        total_duplicates = sum(row[3] - 1 for row in duplicates)  # -1 because we keep one
        
        print(f"📊 Found {len(duplicates)} groups of duplicate products")
        print(f"📊 Total duplicate records to remove: {total_duplicates}")
        
        if total_duplicates == 0:
            print("✅ No duplicates found! Database is clean.")
            return True
        
        # Show some examples
        print("\n📋 Examples of duplicates:")
        for i, (name, vendor, brand, count) in enumerate(duplicates[:5]):
            print(f"   {i+1}. '{name}' by {vendor} ({brand}) - {count} copies")
        
        if len(duplicates) > 5:
            print(f"   ... and {len(duplicates) - 5} more groups")
        
        # Remove duplicates using ROW_NUMBER() window function
        print(f"\n🗑️ Removing {total_duplicates} duplicate records...")
        
        cursor.execute('''
            WITH ranked_products AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY "Product Name*", "Vendor/Supplier*", "Product Brand" 
                           ORDER BY id ASC
                       ) as rn
                FROM products
            )
            DELETE FROM products 
            WHERE id IN (
                SELECT id FROM ranked_products WHERE rn > 1
            )
        ''')
        
        deleted_count = cursor.rowcount
        print(f"✅ Removed {deleted_count} duplicate records")
        
        # Verify the cleanup
        print("\n🔍 Verifying cleanup...")
        cursor.execute('''
            SELECT COUNT(*) FROM products
        ''')
        total_products = cursor.fetchone()[0]
        print(f"📊 Total products remaining: {total_products}")
        
        # Check for remaining duplicates
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT "Product Name*", "Vendor/Supplier*", "Product Brand"
                FROM products 
                GROUP BY "Product Name*", "Vendor/Supplier*", "Product Brand"
                HAVING COUNT(*) > 1
            ) as duplicates
        ''')
        remaining_duplicates = cursor.fetchone()[0]
        
        if remaining_duplicates == 0:
            print("✅ No duplicates remaining! Database cleanup successful.")
        else:
            print(f"⚠️ {remaining_duplicates} duplicate groups still exist")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Duplicate removal completed!")
        print(f"   Removed: {deleted_count} duplicate records")
        print(f"   Remaining: {total_products} unique products")
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing duplicates: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Database Duplicate Cleanup")
    print("=" * 30)
    
    # Set environment variables
    set_environment_variables()
    
    # Remove duplicates
    success = remove_duplicate_products()
    
    if success:
        print("\n✅ Database cleanup completed successfully!")
        print("💡 Your web app should now work without duplicate insertion errors.")
    else:
        print("\n❌ Database cleanup failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
