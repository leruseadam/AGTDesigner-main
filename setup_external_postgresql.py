#!/usr/bin/env python3
"""
External PostgreSQL Setup Guide
Options for hosting PostgreSQL externally for better performance
"""

import os
import sys

def setup_external_postgresql():
    """Set up external PostgreSQL options"""
    
    print("🐘 External PostgreSQL Setup Options")
    print("=" * 50)
    
    print("🚀 RECOMMENDED OPTIONS:")
    print()
    
    # Option 1: Railway
    print("1️⃣ RAILWAY (Easiest - $5/month)")
    print("   • Go to: https://railway.app")
    print("   • Sign up with GitHub")
    print("   • Click 'New Project'")
    print("   • Choose 'Database' → 'PostgreSQL'")
    print("   • Copy connection details")
    print("   • Cost: $5/month")
    print("   • Features: Automatic backups, easy scaling")
    print()
    
    # Option 2: DigitalOcean
    print("2️⃣ DIGITALOCEAN (Best Value - $6/month)")
    print("   • Go to: https://digitalocean.com")
    print("   • Create Droplet: Ubuntu 22.04")
    print("   • Size: $6/month (1GB RAM)")
    print("   • Install PostgreSQL")
    print("   • Cost: $6/month")
    print("   • Features: Full control, best performance")
    print()
    
    # Option 3: Supabase
    print("3️⃣ SUPABASE (Free Tier Available)")
    print("   • Go to: https://supabase.com")
    print("   • Create new project")
    print("   • Get connection details")
    print("   • Cost: Free tier available")
    print("   • Features: Real-time, built-in APIs")
    print()
    
    # Option 4: Neon
    print("4️⃣ NEON (Serverless PostgreSQL)")
    print("   • Go to: https://neon.tech")
    print("   • Create database")
    print("   • Copy connection string")
    print("   • Cost: Free tier available")
    print("   • Features: Serverless, auto-scaling")
    print()
    
    print("💡 RECOMMENDATION: Start with Railway ($5/month)")
    print("   • Easiest setup")
    print("   • Good performance")
    print("   • Automatic backups")
    print("   • Easy to migrate later")
    print()
    
    return True

def create_railway_setup_guide():
    """Create Railway setup guide"""
    
    guide_content = '''# Railway PostgreSQL Setup Guide

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
'''
    
    with open('RAILWAY_SETUP_GUIDE.md', 'w') as f:
        f.write(guide_content)
    
    print("✅ Railway setup guide created")

def create_digitalocean_setup_guide():
    """Create DigitalOcean setup guide"""
    
    guide_content = '''# DigitalOcean PostgreSQL Setup Guide

## Step 1: Create Droplet
1. Go to [DigitalOcean](https://digitalocean.com)
2. Create new Droplet
3. Choose Ubuntu 22.04 LTS
4. Size: $6/month (1GB RAM, 1 CPU)
5. Add SSH key
6. Create droplet

## Step 2: Install PostgreSQL
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install PostgreSQL
apt install postgresql postgresql-contrib -y

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql
```

## Step 3: Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE labelmaker;
CREATE USER labelmaker WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE labelmaker TO labelmaker;
ALTER USER labelmaker CREATEDB;
\\q
```

## Step 4: Configure Remote Access
```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/postgresql.conf

# Find and uncomment:
listen_addresses = '*'

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add line:
host    all             all             0.0.0.0/0               md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Step 5: Configure Firewall
```bash
# Allow PostgreSQL port
ufw allow 5432
ufw enable
```

## Step 6: Test Connection
```bash
# From your local machine
psql -h your-droplet-ip -U labelmaker -d labelmaker
```

## Cost: $6/month
- 1GB RAM
- 1 CPU
- 25GB SSD
- Full control
- Best performance
'''
    
    with open('DIGITALOCEAN_POSTGRESQL_SETUP.md', 'w') as f:
        f.write(guide_content)
    
    print("✅ DigitalOcean setup guide created")

def create_connection_test():
    """Create PostgreSQL connection test script"""
    
    test_content = '''#!/usr/bin/env python3
"""
PostgreSQL Connection Test
Tests connection to your PostgreSQL database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    
    print("🧪 Testing PostgreSQL Connection...")
    print("=" * 40)
    
    # Update these with your actual connection details
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'labelmaker'),
        'user': os.getenv('DB_USER', 'labelmaker'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print(f"Host: {config['host']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    print(f"Port: {config['port']}")
    print()
    
    try:
        # Test connection
        conn = psycopg2.connect(**config)
        print("✅ Connection successful!")
        
        # Test query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version['version']}")
        
        # Test database info
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()
        print(f"✅ Connected to database: {db_name['current_database']}")
        
        # Test table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Table creation test passed")
        
        # Test insert
        cursor.execute("INSERT INTO test_table (name) VALUES (%s)", ("test",))
        conn.commit()
        print("✅ Insert test passed")
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        results = cursor.fetchall()
        print(f"✅ Select test passed: {len(results)} rows")
        
        # Clean up
        cursor.execute("DROP TABLE test_table")
        conn.commit()
        print("✅ Cleanup test passed")
        
        cursor.close()
        conn.close()
        
        print("\\n🎉 All PostgreSQL tests passed!")
        print("✅ Your database is ready for migration")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\\n💡 Check your connection details:")
        print("   • Host: Is the server running?")
        print("   • Database: Does it exist?")
        print("   • User: Does the user exist?")
        print("   • Password: Is it correct?")
        print("   • Port: Is it open?")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐘 PostgreSQL Connection Test")
    print("=" * 30)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
        print("✅ PostgreSQL client available")
    except ImportError:
        print("❌ PostgreSQL client not available")
        print("💡 Install with: pip install psycopg2-binary")
        exit(1)
    
    # Run test
    success = test_postgresql_connection()
    
    if success:
        print("\\n🚀 Ready to migrate your data!")
        print("Run: python migrate_to_postgresql_agt.py")
    else:
        print("\\n🔧 Fix connection issues first")
        print("Then run this test again")
'''
    
    with open('test_postgresql_connection.py', 'w') as f:
        f.write(test_content)
    
    print("✅ PostgreSQL connection test created")

if __name__ == "__main__":
    print("🐘 External PostgreSQL Setup Guide")
    print("=" * 40)
    
    setup_external_postgresql()
    create_railway_setup_guide()
    create_digitalocean_setup_guide()
    create_connection_test()
    
    print("\\n🎉 External PostgreSQL setup guides created!")
    print("\\n📋 Files created:")
    print("   • RAILWAY_SETUP_GUIDE.md")
    print("   • DIGITALOCEAN_POSTGRESQL_SETUP.md")
    print("   • test_postgresql_connection.py")
    print("\\n💡 Recommendation: Start with Railway ($5/month)")
    print("   It's the easiest and most reliable option.")
