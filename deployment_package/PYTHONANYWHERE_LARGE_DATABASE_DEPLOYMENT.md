# PythonAnywhere Large Database Deployment Guide

## ⚠️ Important: Large Database Deployment (500MB+)

Your database is **500MB** with **17,841 products** - this requires special handling for PythonAnywhere deployment.

## Database Analysis Results

**Working Databases Found:**
- `uploads/product_database_AGT_Bothell_clean.db` - 499.79 MB, 17,841 products ✅
- `uploads/product_database_AGT_Bothell_web.db` - 499.8 MB, 17,841 products ✅
- `uploads/product_database.db` - 501.03 MB, CORRUPTED ❌

**Tables:** strains, products, lineage_history, strain_brand_lineage, products_backup, _migration_log, lost_and_found

## PythonAnywhere Account Requirements

### ⚠️ Free Tier Limitations
- **Disk Space**: 512MB total (your database alone is 500MB)
- **CPU Seconds**: Limited (database operations will consume quickly)
- **File Upload**: 100MB limit per file

### ✅ Recommended: Upgrade to Paid Plan
- **Hacker Plan ($5/month)**: 3GB disk space, unlimited CPU seconds
- **Web Developer ($20/month)**: 20GB disk space, better performance
- **Startup ($100/month)**: 100GB disk space, dedicated resources

## Deployment Strategy Options

### Option 1: Database Compression & Optimization (Recommended)

#### Step 1: Compress Database
```bash
# On your local machine
cd "/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15"

# Use the clean database
cp uploads/product_database_AGT_Bothell_clean.db product_database.db

# Create compressed SQL dump
python3 -c "
import sqlite3
import gzip

# Create SQL dump
conn = sqlite3.connect('product_database.db')
with open('product_database_dump.sql', 'w') as f:
    for line in conn.iterdump():
        f.write(f'{line}\n')
conn.close()

# Compress the dump
with open('product_database_dump.sql', 'rb') as f_in:
    with gzip.open('product_database_dump.sql.gz', 'wb') as f_out:
        f_out.write(f_in.read())

print('Database compressed successfully')
"
```

#### Step 2: Upload to PythonAnywhere
1. **Upgrade to Hacker plan** ($5/month) - **REQUIRED**
2. Upload compressed files via Files tab:
   - `product_database_dump.sql.gz` (should be ~50-100MB compressed)
   - Or use console upload for larger files

#### Step 3: Restore Database on PythonAnywhere
```bash
# On PythonAnywhere console
cd ~/AGTDesigner

# Decompress and restore
gunzip product_database_dump.sql.gz
python3 -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
with open('product_database_dump.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Database restored successfully')
"
```

### Option 2: Database Optimization & Reduction

#### Step 1: Optimize Database
```bash
# Create optimized version
python3 -c "
import sqlite3

# Connect to clean database
conn = sqlite3.connect('uploads/product_database_AGT_Bothell_clean.db')

# Create optimized database
conn.execute('VACUUM INTO product_database_optimized.db')

# Analyze for better performance
conn.execute('ANALYZE')

conn.close()
print('Database optimized')
"
```

#### Step 2: Remove Unnecessary Data
```bash
# Create production-ready database
python3 -c "
import sqlite3

# Connect to clean database
conn = sqlite3.connect('uploads/product_database_AGT_Bothell_clean.db')

# Create new optimized database
new_conn = sqlite3.connect('product_database_production.db')

# Copy only essential tables
conn.backup(new_conn, pages=1000)

# Remove backup tables and migration logs
new_conn.execute('DROP TABLE IF EXISTS products_backup')
new_conn.execute('DROP TABLE IF EXISTS _migration_log')
new_conn.execute('DROP TABLE IF EXISTS lost_and_found')

# Optimize
new_conn.execute('VACUUM')
new_conn.execute('ANALYZE')

new_conn.close()
conn.close()

print('Production database created')
"
```

### Option 3: External Database (Advanced)

#### Use External PostgreSQL Database
1. **DigitalOcean PostgreSQL** ($15/month)
2. **Railway PostgreSQL** ($5/month)
3. **Supabase** (Free tier available)

```python
# Update your app.py to use PostgreSQL
import psycopg2
from sqlalchemy import create_engine

# Database configuration
DATABASE_URL = "postgresql://username:password@host:port/database"

# Use SQLAlchemy for better performance
engine = create_engine(DATABASE_URL)
```

## Recommended Deployment Steps

### 1. Upgrade PythonAnywhere Account
- **Minimum**: Hacker plan ($5/month)
- **Recommended**: Web Developer ($20/month) for better performance

### 2. Prepare Database for Upload
```bash
# Use the optimized deployment script
python3 migrate_database_to_pythonanywhere.py
```

### 3. Upload Strategy
- **Files Tab**: For files under 100MB
- **Console Upload**: For larger files using `wget` or `curl`
- **Git LFS**: For version control of large files

### 4. Database Restoration
```bash
# On PythonAnywhere
cd ~/AGTDesigner

# Restore from compressed dump
gunzip product_database_dump.sql.gz
python3 -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
with open('product_database_dump.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Database restored')
"

# Test database
python3 -c "
import sqlite3
conn = sqlite3.connect('product_database.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f'Products restored: {count}')
conn.close()
"
```

## Performance Considerations

### Database Optimization
- **Indexing**: Ensure proper indexes on frequently queried columns
- **Query Optimization**: Use LIMIT clauses for large result sets
- **Caching**: Implement Redis or Memcached for frequently accessed data
- **Pagination**: Implement pagination for product listings

### PythonAnywhere Optimizations
- **Static Files**: Use CDN for static assets
- **Caching**: Enable Flask-Caching
- **Compression**: Enable gzip compression
- **Database Connection Pooling**: Use connection pooling

## Cost Analysis

### PythonAnywhere Plans
- **Free**: ❌ Insufficient (512MB disk, 500MB database)
- **Hacker ($5/month)**: ✅ Minimum viable (3GB disk)
- **Web Developer ($20/month)**: ✅ Recommended (20GB disk, better performance)
- **Startup ($100/month)**: ✅ Best performance (100GB disk, dedicated resources)

### Alternative Hosting
- **Railway**: $5/month + PostgreSQL $5/month = $10/month
- **DigitalOcean**: $12/month droplet + $15/month PostgreSQL = $27/month
- **Heroku**: $7/month + PostgreSQL $9/month = $16/month

## Troubleshooting Large Database Issues

### Common Problems
1. **Upload Timeout**: Use chunked uploads
2. **Memory Issues**: Optimize queries, use pagination
3. **Slow Queries**: Add indexes, optimize SQL
4. **Disk Space**: Clean up old files, compress data

### Monitoring
- **Disk Usage**: Monitor in PythonAnywhere dashboard
- **CPU Usage**: Watch CPU seconds consumption
- **Memory Usage**: Monitor RAM usage
- **Query Performance**: Log slow queries

## Next Steps

1. **Choose deployment strategy** (compression recommended)
2. **Upgrade PythonAnywhere account** (Hacker plan minimum)
3. **Prepare optimized database**
4. **Upload and restore database**
5. **Test application performance**
6. **Monitor resource usage**

## Support Commands

```bash
# Check database size
du -h product_database.db

# Compress database
gzip product_database.db

# Test database integrity
sqlite3 product_database.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 product_database.db "VACUUM; ANALYZE;"
```

---

**⚠️ Important**: Your 500MB database requires a paid PythonAnywhere plan. The free tier will not work with this database size.
