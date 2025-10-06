#!/usr/bin/env python3
"""
Fix strains data in PostgreSQL
"""

import sqlite3
import psycopg2
import os

def fix_strains_data():
    """Fix the strains data in PostgreSQL"""
    
    print("🔧 Fixing strains data in PostgreSQL...")
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
        # Check SQLite strains
        sqlite_cursor.execute("SELECT COUNT(*) FROM strains")
        sqlite_strains_count = sqlite_cursor.fetchone()[0]
        print(f"📊 SQLite strains count: {sqlite_strains_count}")
        
        # Check PostgreSQL strains
        postgres_cursor.execute("SELECT COUNT(*) FROM strains")
        postgres_strains_count = postgres_cursor.fetchone()[0]
        print(f"📊 PostgreSQL strains count: {postgres_strains_count}")
        
        if sqlite_strains_count > postgres_strains_count:
            print(f"⚠️ Missing {sqlite_strains_count - postgres_strains_count} strains!")
            
            # Clear existing strains
            print("🗑️ Clearing existing strains...")
            postgres_cursor.execute("DELETE FROM strains")
            
            # Migrate strains properly
            print("🌿 Migrating strains...")
            sqlite_cursor.execute("SELECT * FROM strains")
            strains = sqlite_cursor.fetchall()
            
            for i, strain in enumerate(strains):
                if i % 100 == 0:
                    print(f"   Processed {i}/{len(strains)} strains...")
                
                strain_dict = dict(strain)
                
                insert_sql = """
                INSERT INTO strains (
                    strain_name, normalized_name, canonical_lineage, first_seen_date,
                    last_seen_date, total_occurrences, lineage_confidence, sovereign_lineage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                postgres_cursor.execute(insert_sql, (
                    strain_dict.get('strain_name'),
                    strain_dict.get('normalized_name'),
                    strain_dict.get('canonical_lineage'),
                    strain_dict.get('first_seen_date'),
                    strain_dict.get('last_seen_date'),
                    strain_dict.get('total_occurrences'),
                    strain_dict.get('lineage_confidence'),
                    strain_dict.get('sovereign_lineage')
                ))
            
            postgres_conn.commit()
            print("✅ Strains migrated successfully!")
            
            # Verify
            postgres_cursor.execute("SELECT COUNT(*) FROM strains")
            new_count = postgres_cursor.fetchone()[0]
            print(f"📊 New PostgreSQL strains count: {new_count}")
            
        else:
            print("✅ Strains count looks correct")
        
        # Check product strains
        print("\n🔍 Checking product strains...")
        postgres_cursor.execute("SELECT COUNT(DISTINCT product_strain) FROM products WHERE product_strain IS NOT NULL AND product_strain != ''")
        unique_product_strains = postgres_cursor.fetchone()[0]
        print(f"📊 Unique product strains: {unique_product_strains}")
        
        # Show sample product strains
        postgres_cursor.execute("SELECT DISTINCT product_strain FROM products WHERE product_strain IS NOT NULL AND product_strain != '' LIMIT 10")
        sample_strains = [row[0] for row in postgres_cursor.fetchall()]
        print(f"📋 Sample product strains: {sample_strains}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        postgres_conn.rollback()
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    fix_strains_data()
