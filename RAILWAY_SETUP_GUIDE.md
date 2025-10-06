# Railway PostgreSQL Setup Guide

## Step 1: Create Railway Account
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Verify your email

## Step 2: Create PostgreSQL Database
1. Click "New Project"
2. Choose "Database" → "PostgreSQL"
3. Wait for database to be created
4. Click on your database

## Step 3: Get Connection Details
1. Go to "Variables" tab
2. Copy these values:
   - `PGHOST` (host)
   - `PGDATABASE` (database name)
   - `PGUSER` (username)
   - `PGPASSWORD` (password)
   - `PGPORT` (port)

## Step 4: Update Your App
```python
# Update your connection config
RAILWAY_CONFIG = {
    'host': 'your-railway-host.railway.app',
    'database': 'railway',
    'user': 'postgres',
    'password': 'your-password',
    'port': '5432'
}
```

## Step 5: Test Connection
```bash
python test_postgresql_connection.py
```

## Step 6: Migrate Data
```bash
python migrate_to_postgresql_agt.py
```

## Cost: $5/month
- 1GB RAM
- 1GB storage
- Automatic backups
- Easy scaling
