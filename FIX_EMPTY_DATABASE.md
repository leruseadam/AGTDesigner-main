# Fix Empty Database on PythonAnywhere

## The Problem
Your PythonAnywhere deployment has an empty database, so no products are showing up in the label maker.

## Solution Options

### Option 1: Quick Database Setup (Recommended)
On PythonAnywhere, run this updated deployment script which now includes database initialization:

```bash
cd ~/AGTDesigner
git pull origin main  # Get the latest database files
./deploy_pythonanywhere_no_venv.sh
```

This will:
- ✅ Install all packages
- ✅ Create empty database with proper schema
- ✅ Import your local database data (4 products)

### Option 2: Manual Database Setup

1. **Pull latest files:**
```bash
cd ~/AGTDesigner
git pull origin main
```

2. **Initialize empty database:**
```bash
python3.11 init_pythonanywhere_database.py
```

3. **Import your data:**
```bash
python3.11 import_pythonanywhere_database.py
```

### Option 3: Create Database with Sample Data

If you want to start fresh with test data:

```bash
cd ~/AGTDesigner
python3.11 init_pythonanywhere_database.py
# When prompted, type 'y' to add sample data
```

## Verify Database Works

Test that the database is working:

```bash
python3.11 -c "
import sqlite3
conn = sqlite3.connect('uploads/product_database.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f'Products in database: {count}')
conn.close()
"
```

## What's Included

Your exported database contains:
- **4 products** from your local development
- **1 strain** definition
- Full schema with all required columns
- Proper table relationships

## Database Location

The database will be created at:
`/home/adamcordova/AGTDesigner/uploads/product_database.db`

## After Database Setup

1. **Reload your PythonAnywhere web app**
2. **Test the label maker** - you should now see products when uploading Excel files
3. **JSON matching should work** with the 0.4 threshold improvements

---

**Need help?** Check the error logs in your PythonAnywhere Web tab if anything fails.