import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, date

"""
Backfill/repair strains on PostgreSQL.
- Creates missing strain rows from distinct Product Strain values in products
- Skips empty/placeholder strains ('' / None)
- Optionally can skip generic buckets like 'Mixed' and 'CBD Blend' (default True)
- Sets products.strain_id by joining on normalized_name
- Recomputes total_occurrences and canonical_lineage (mode lineage) per strain

Usage (PythonAnywhere Bash):
    cd /home/adamcordova/AGTDesigner
    export DB_HOST='adamcordova-4822.postgres.pythonanywhere-services.com'
    export DB_NAME='postgres'
    export DB_USER='super'
    export DB_PASSWORD='193154life'
    export DB_PORT='14822'
    python rebuild_strains_from_products.py
"""

SKIP_GENERIC_BUCKETS = True
GENERIC_BUCKETS = {"mixed", "cbd blend", "", None}


def normalize(text: str) -> str:
    if text is None:
        return ""
    t = str(text).strip().lower()
    # collapse whitespace
    t = " ".join(t.split())
    return t


def get_conn():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT', '5432')
    )


def table_has_column(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        (table, column.strip('"')),
    )
    return cur.fetchone() is not None


def pick_column(cur, candidates):
    for col in candidates:
        # Check both quoted and unquoted by stripping quotes for information_schema
        if table_has_column(cur, 'products', col):
            return col
    return None


def main():
    conn = get_conn()
    conn.autocommit = False
    try:
        cur = conn.cursor()

        # Detect correct column names in products
        strain_col = pick_column(cur, ['Product Strain', 'ProductStrain', 'product_strain', 'strain'])
        if not strain_col:
            raise RuntimeError('Could not find strain column in products table')
        lineage_col = pick_column(cur, ['Lineage', 'lineage'])
        # Build SQL-safe identifier (quoted if contains uppercase/space)
        def col_id(name: str) -> str:
            # If original contains any non-lowercase or spaces, quote it
            if not name.islower() or ' ' in name:
                return f'"{name}"'
            return name
        strain_id = col_id(strain_col)
        lineage_id = col_id(lineage_col) if lineage_col else None

        # Ensure products.strain_id column exists
        if not table_has_column(cur, 'products', 'strain_id'):
            cur.execute('ALTER TABLE products ADD COLUMN strain_id INTEGER')
            # Optional FK (skip if table might not allow due to legacy)
            try:
                cur.execute('ALTER TABLE products ADD CONSTRAINT fk_products_strain FOREIGN KEY (strain_id) REFERENCES strains(id)')
            except Exception:
                pass
            cur.execute('CREATE INDEX IF NOT EXISTS idx_products_strain_id ON products(strain_id)')

        # 1) Gather distinct strain names from products
        cur.execute(
            f'''
            SELECT DISTINCT TRIM({strain_id})
            FROM products
            WHERE {strain_id} IS NOT NULL
              AND TRIM({strain_id}) <> ''
              AND TRIM({strain_id}) <> ' '
            '''
        )
        raw = [r[0] for r in cur.fetchall()]
        candidates = []
        for s in raw:
            n = normalize(s)
            if SKIP_GENERIC_BUCKETS and n in GENERIC_BUCKETS:
                continue
            candidates.append((s, n))
        # Ensure unique by normalized name
        seen = set()
        unique_candidates = []
        for orig, norm in candidates:
            if norm and norm not in seen:
                seen.add(norm)
                unique_candidates.append((orig, norm))

        print(f"Found {len(unique_candidates)} distinct strain candidates from products")

        # Early exit if nothing to do
        if not unique_candidates:
            print('Nothing to insert/update. Exiting.')
            conn.commit()
            return

        # 2) Ensure unique index on strains.normalized_name for upsert
        cur.execute('''
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE tablename = 'strains' AND indexname = 'idx_strains_normalized_name_unique'
                ) THEN
                    CREATE UNIQUE INDEX idx_strains_normalized_name_unique ON strains (normalized_name);
                END IF;
            END $$;
        ''')

        # 3) Upsert strains by normalized_name using proper DATE/TIMESTAMPTZ types
        today = date.today()
        now_ts = datetime.now(timezone.utc)
        values = []
        for orig, norm in unique_candidates:
            values.append((orig, norm, None, today, today, 0.0, None, now_ts, now_ts))
        cur.execute('''
            CREATE TEMP TABLE tmp_strains (
                strain_name TEXT,
                normalized_name TEXT,
                canonical_lineage TEXT,
                first_seen_date DATE,
                last_seen_date DATE,
                lineage_confidence REAL,
                sovereign_lineage TEXT,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ
            ) ON COMMIT DROP
        ''')
        execute_values(cur, 'INSERT INTO tmp_strains VALUES %s', values)
        # Upsert into strains
        cur.execute('''
            INSERT INTO strains (strain_name, normalized_name, canonical_lineage, first_seen_date, last_seen_date, lineage_confidence, sovereign_lineage, created_at, updated_at)
            SELECT t.strain_name, t.normalized_name, t.canonical_lineage, t.first_seen_date, t.last_seen_date, t.lineage_confidence, t.sovereign_lineage, t.created_at, t.updated_at
            FROM tmp_strains t
            ON CONFLICT (normalized_name) DO UPDATE SET
                strain_name = EXCLUDED.strain_name,
                last_seen_date = EXCLUDED.last_seen_date,
                updated_at = EXCLUDED.updated_at
        ''')

        # 4) Link products to strains by normalized name
        cur.execute(
            f'''
            UPDATE products p
            SET strain_id = s.id
            FROM strains s
            WHERE s.normalized_name = LOWER(TRIM(p.{strain_id}))
              AND (p.strain_id IS NULL OR p.strain_id <> s.id)
            '''
        )
        print(f"Linked products to strains: {cur.rowcount} rows updated")

        # 5) Recompute total_occurrences for strains
        cur.execute('''
            WITH counts AS (
                SELECT p.strain_id, COUNT(*) AS c
                FROM products p
                WHERE p.strain_id IS NOT NULL
                GROUP BY p.strain_id
            )
            UPDATE strains s
            SET total_occurrences = c.c,
                updated_at = %s
            FROM counts c
            WHERE s.id = c.strain_id
        ''', (now_ts,))
        print(f"Updated total_occurrences for strains: {cur.rowcount} rows")

        # 6) Set canonical_lineage as mode of non-empty product Lineage per strain (if lineage column exists)
        if lineage_id:
            cur.execute(
                f'''
                WITH ranked AS (
                    SELECT s.id AS strain_id, p.{lineage_id} AS lineage, COUNT(*) AS cnt,
                           ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY COUNT(*) DESC) AS rn
                    FROM strains s
                    JOIN products p ON p.strain_id = s.id
                    WHERE p.{lineage_id} IS NOT NULL AND TRIM(p.{lineage_id}) <> ''
                    GROUP BY s.id, p.{lineage_id}
                )
                UPDATE strains s
                SET canonical_lineage = r.lineage,
                    updated_at = %s
                FROM ranked r
                WHERE r.rn = 1 AND s.id = r.strain_id
                '''
            , (now_ts,))
            print(f"Updated canonical_lineage for strains: {cur.rowcount} rows")

        # 7) Some products may have only generic/empty strain; optionally clear their strain_id
        if SKIP_GENERIC_BUCKETS:
            cur.execute(
                f'''
                UPDATE products
                SET strain_id = NULL
                WHERE LOWER(TRIM({strain_id})) IN (%s, %s)
                '''
            , ("mixed", "cbd blend"))

        # Report
        cur.execute('SELECT COUNT(*) FROM strains')
        print('Strains total:', cur.fetchone()[0])
        cur.execute('SELECT COUNT(DISTINCT strain_id) FROM products WHERE strain_id IS NOT NULL')
        print('Products linked to strain_id:', cur.fetchone()[0])

        conn.commit()
        print('✅ Strain backfill complete')
    except Exception as e:
        conn.rollback()
        print('❌ Error:', e)
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
