#!/usr/bin/env python3
"""
Comprehensive fix for strains data issue
"""

import sqlite3
import psycopg2
import os
from collections import Counter

def comprehensive_strains_fix():
    """Comprehensive fix for strains data"""
    
    print("🔧 Comprehensive Strains Fix")
    print("=" * 50)
    
    # SQLite database path
    sqlite_path = '/home/adamcordova/AGTDesigner/uploads/product_database_AGT_Bothell.db'
    
    # PostgreSQL connection
    postgres_config = {
        'host': 'adamcordova-4822.postgres.pythonanywhere-services.com',
        'database': 'postgres',
        'user': 'super',
        'password': '193154life',
        'port': '14822'
    }
    
    # Connect to SQLite
    print("📦 Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    print("🐘 Connecting to PostgreSQL...")
    postgres_conn = psycopg2.connect(**postgres_config)
    postgres_conn.autocommit = False
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # 1. Investigate SQLite structure
        print("\n🔍 Investigating SQLite structure...")
        sqlite_cursor.execute("PRAGMA table_info(products)")
        columns = sqlite_cursor.fetchall()
        print("Products table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Find strain-related columns
        strain_cols = [col[1] for col in columns if 'strain' in col[1].lower()]
        print(f"\nStrain-related columns: {strain_cols}")
        
        # 2. Check strains table
        print("\n🌿 Checking strains table...")
        sqlite_cursor.execute("SELECT COUNT(*) FROM strains")
        sqlite_strains_count = sqlite_cursor.fetchone()[0]
        print(f"SQLite strains count: {sqlite_strains_count}")
        
        sqlite_cursor.execute("SELECT * FROM strains")
        sqlite_strains = sqlite_cursor.fetchall()
        print("SQLite strains:")
        for strain in sqlite_strains:
            print(f"  {dict(strain)}")
        
        # 3. Check PostgreSQL strains
        print("\n🐘 Checking PostgreSQL strains...")
        postgres_cursor.execute("SELECT COUNT(*) FROM strains")
        postgres_strains_count = postgres_cursor.fetchone()[0]
        print(f"PostgreSQL strains count: {postgres_strains_count}")
        
        # 4. Extract strain data from products
        print("\n📊 Extracting strain data from products...")
        
        # Try different possible strain column names
        possible_strain_columns = [
            'Product Strain',
            'Strain',
            'Cannabis Strain',
            'Strain Name',
            'Product Strain*'
        ]
        
        strain_column = None
        for col in possible_strain_columns:
            if col in [c[1] for c in columns]:
                strain_column = col
                break
        
        if strain_column:
            print(f"Found strain column: {strain_column}")
            
            # Get unique strains from products
            sqlite_cursor.execute(f"SELECT DISTINCT \"{strain_column}\" FROM products WHERE \"{strain_column}\" IS NOT NULL AND \"{strain_column}\" != ''")
            product_strains = [row[0] for row in sqlite_cursor.fetchall()]
            print(f"Unique strains in products: {len(product_strains)}")
            print(f"Sample strains: {product_strains[:10]}")
            
            # Count strain occurrences
            sqlite_cursor.execute(f"SELECT \"{strain_column}\", COUNT(*) as count FROM products WHERE \"{strain_column}\" IS NOT NULL AND \"{strain_column}\" != '' GROUP BY \"{strain_column}\" ORDER BY count DESC LIMIT 20")
            strain_counts = sqlite_cursor.fetchall()
            print("\nTop strains by count:")
            for strain, count in strain_counts:
                print(f"  {strain}: {count}")
            
            # 5. Update PostgreSQL with extracted strains
            print("\n🔄 Updating PostgreSQL with extracted strains...")
            
            # Clear existing strains
            postgres_cursor.execute("DELETE FROM strains")
            
            # Insert strains from products
            strain_id = 1
            for strain_name in product_strains:
                if strain_name and strain_name.strip():
                    # Count occurrences
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM products WHERE \"{strain_column}\" = ?", (strain_name,))
                    count = sqlite_cursor.fetchone()[0]
                    
                    # Insert into PostgreSQL
                    insert_sql = """
                    INSERT INTO strains (
                        strain_name, normalized_name, canonical_lineage, first_seen_date,
                        last_seen_date, total_occurrences, lineage_confidence, sovereign_lineage
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    postgres_cursor.execute(insert_sql, (
                        strain_name,
                        strain_name.lower().replace(' ', '_'),
                        None,  # canonical_lineage
                        '2024-01-01',  # first_seen_date
                        '2024-01-01',  # last_seen_date
                        count,  # total_occurrences
                        0.0,  # lineage_confidence
                        None  # sovereign_lineage
                    ))
                    strain_id += 1
            
            postgres_conn.commit()
            print("✅ Strains updated in PostgreSQL!")
            
            # Verify
            postgres_cursor.execute("SELECT COUNT(*) FROM strains")
            new_count = postgres_cursor.fetchone()[0]
            print(f"📊 New PostgreSQL strains count: {new_count}")
            
            # Show sample strains
            postgres_cursor.execute("SELECT strain_name, total_occurrences FROM strains ORDER BY total_occurrences DESC LIMIT 10")
            top_strains = postgres_cursor.fetchall()
            print("\nTop strains in PostgreSQL:")
            for strain, count in top_strains:
                print(f"  {strain}: {count} products")
        
        else:
            print("❌ No strain column found in products table")
            print("Available columns:", [col[1] for col in columns])
        
        # 6. Update product_strain column in PostgreSQL
        if strain_column:
            print(f"\n🔄 Updating product_strain column in PostgreSQL...")
            
            # Get all products with strain data
            sqlite_cursor.execute(f"SELECT id, \"{strain_column}\" FROM products WHERE \"{strain_column}\" IS NOT NULL AND \"{strain_column}\" != ''")
            product_strains = sqlite_cursor.fetchall()
            
            updated_count = 0
            for product_id, strain_name in product_strains:
                postgres_cursor.execute("UPDATE products SET product_strain = %s WHERE id = %s", (strain_name, product_id))
                updated_count += 1
            
            postgres_conn.commit()
            print(f"✅ Updated {updated_count} products with strain data")
        
        # 7. Final verification
        print("\n📊 Final verification...")
        postgres_cursor.execute("SELECT COUNT(DISTINCT product_strain) FROM products WHERE product_strain IS NOT NULL AND product_strain != ''")
        unique_strains = postgres_cursor.fetchone()[0]
        print(f"Unique product strains: {unique_strains}")
        
        postgres_cursor.execute("SELECT COUNT(*) FROM strains")
        total_strains = postgres_cursor.fetchone()[0]
        print(f"Total strains in strains table: {total_strains}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        postgres_conn.rollback()
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    comprehensive_strains_fix()
