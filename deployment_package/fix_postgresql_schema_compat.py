import os
import sys
import psycopg2
import psycopg2.extras

"""
Run this on PythonAnywhere to ensure the PostgreSQL schema matches the app's expectations.
- Adds missing column "Product Name*" to products if absent, copying from existing alternatives
- Creates lineage_history table if absent
- Ensures essential indexes/constraints exist

Usage on PythonAnywhere Bash console:
    cd /home/adamcordova/AGTDesigner
    workon your-virtualenv  # if applicable
    python fix_postgresql_schema_compat.py
"""

REQUIRED_PRODUCT_COLUMNS = [
    'Product Name*',
    'Product Type*',
    'Vendor/Supplier*',
    'Product Brand',
]

ALTERNATIVE_NAME_CANDIDATES = [
    'ProductName',
    'product_name',
    'name',
]

LINEAGE_HISTORY_DDL = '''
CREATE TABLE IF NOT EXISTS lineage_history (
    id SERIAL PRIMARY KEY,
    strain_id INTEGER,
    old_lineage TEXT,
    new_lineage TEXT,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT
);
'''

PRODUCTS_UNIQUE_CONSTRAINT = 'products_unique_name_vendor_brand'


def get_conn():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT', '5432'),
    )
    conn.autocommit = False
    return conn


def table_has_column(cur, table, column):
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return cur.fetchone() is not None


def find_existing_name_column(cur):
    for candidate in ALTERNATIVE_NAME_CANDIDATES:
        if table_has_column(cur, 'products', candidate):
            return candidate
    return None


def ensure_product_name_star_column(cur):
    if table_has_column(cur, 'products', 'Product Name*'):
        print('✅ Column "Product Name*" already exists')
        return

    existing = find_existing_name_column(cur)
    if existing is None:
        print('⚠️ Could not find an existing name column to copy from; creating empty column')
        cur.execute('ALTER TABLE products ADD COLUMN "Product Name*" TEXT')
        return

    print(f'➡️ Adding "Product Name*" and copying from existing "{existing}"')
    cur.execute('ALTER TABLE products ADD COLUMN "Product Name*" TEXT')
    cur.execute(f'UPDATE products SET "Product Name*" = {psycopg2.extensions.AsIs(existing)}')


def ensure_unique_constraint(cur):
    # Ensure UNIQUE("Product Name*", "Vendor/Supplier*", "Product Brand") exists
    cur.execute(
        """
        SELECT 1 FROM pg_indexes WHERE indexname = %s
        """,
        (PRODUCTS_UNIQUE_CONSTRAINT,)
    )
    if cur.fetchone() is not None:
        print('✅ Unique constraint/index already exists')
        return
    print('➡️ Creating unique index on ("Product Name*", "Vendor/Supplier*", "Product Brand")')
    cur.execute(
        f'CREATE UNIQUE INDEX {PRODUCTS_UNIQUE_CONSTRAINT} ON products ("Product Name*", "Vendor/Supplier*", "Product Brand")'
    )


def ensure_lineage_history(cur):
    print('➡️ Ensuring lineage_history table exists')
    cur.execute(LINEAGE_HISTORY_DDL)


def main():
    try:
        conn = get_conn()
    except Exception as e:
        print(f'❌ Failed to connect to PostgreSQL: {e}')
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            ensure_product_name_star_column(cur)
            ensure_unique_constraint(cur)
            ensure_lineage_history(cur)
        conn.commit()
        print('✅ Schema compatibility adjustments complete')
    except Exception as e:
        conn.rollback()
        print(f'❌ Error applying schema fixes: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
