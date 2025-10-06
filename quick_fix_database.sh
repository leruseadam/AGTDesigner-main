#!/bin/bash
# Quick database corruption fix for PythonAnywhere

echo "🚨 PythonAnywhere Database Quick Fix"
echo "===================================="

USERNAME=$(whoami)
PROJECT_DIR="/home/${USERNAME}/AGTDesigner"

cd "$PROJECT_DIR" || exit 1

echo "🔍 Finding corrupted database files..."

# Find and backup corrupted database files
find . -name "*.db" -o -name "*database*" | while read -r db_file; do
    if [ -f "$db_file" ]; then
        echo "📄 Checking: $db_file"
        
        # Test if file is a valid SQLite database
        if ! sqlite3 "$db_file" "SELECT name FROM sqlite_master LIMIT 1;" >/dev/null 2>&1; then
            echo "   ❌ Corrupted - backing up and removing"
            mv "$db_file" "${db_file}.corrupted_backup"
        else
            echo "   ✅ Valid database"
        fi
    fi
done

echo ""
echo "🔧 Creating fresh database..."

# Create fresh database with Python
python3.11 -c "
import sqlite3
import os

db_path = 'product_database.db'

# Create fresh database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        price REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS strains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        thc_percentage REAL,
        cbd_percentage REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert sample data
sample_data = [
    ('Sample Product', 'Test Brand', 'Accessories', 19.99, 'Test product'),
    ('Dabber Tool', 'AGT', 'Tools', 15.00, 'Standard dabber tool'),
    ('Glass Pipe', 'Generic', 'Smoking', 25.99, 'Basic glass pipe'),
    ('Grinder', 'Premium', 'Accessories', 35.00, '4-piece herb grinder')
]

cursor.executemany('''
    INSERT INTO products (name, brand, category, price, description)
    VALUES (?, ?, ?, ?, ?)
''', sample_data)

sample_strains = [
    ('Blue Dream', 'Hybrid', 18.5, 0.5, 'Popular balanced hybrid'),
    ('OG Kush', 'Indica', 20.0, 0.3, 'Classic indica-dominant strain')
]

cursor.executemany('''
    INSERT INTO strains (name, type, thc_percentage, cbd_percentage, description)
    VALUES (?, ?, ?, ?, ?)
''', sample_strains)

conn.commit()
conn.close()

print('✅ Fresh database created: product_database.db')
print(f'📊 Size: {os.path.getsize(db_path):,} bytes')
"

echo ""
echo "🎯 NEXT STEPS:"
echo "=============="
echo "1. 🔄 Reload your web app in PythonAnywhere"
echo "2. 🧪 Test app functionality"
echo "3. ✅ Once working, switch WSGI to optimized version"
echo ""
echo "✅ Database fix complete!"