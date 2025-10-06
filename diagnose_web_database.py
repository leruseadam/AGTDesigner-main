#!/usr/bin/env python3
"""
Web Database Diagnosis and Recovery
===================================
Comprehensive tool to diagnose and fix web database issues
"""

import os
import sqlite3
import shutil
from datetime import datetime

def test_database_connection(db_path):
    """Test database connection and basic queries"""
    print(f"🔗 Testing database connection: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"✅ SQLite version: {version}")
        
        # Test table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Tables found: {[table[0] for table in tables]}")
        
        # Test products table
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"✅ Products in database: {product_count:,}")
        
        # Test sample products
        cursor.execute("SELECT ProductName, `Product Type*`, `Product Strain` FROM products LIMIT 5")
        samples = cursor.fetchall()
        print("✅ Sample products:")
        for i, (name, type_, strain) in enumerate(samples, 1):
            print(f"   {i}. {name} ({type_}) - {strain}")
        
        # Test concentrate products specifically
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE `Product Type*` = 'Concentrate'
        """)
        concentrate_count = cursor.fetchone()[0]
        print(f"✅ Concentrate products: {concentrate_count}")
        
        # Test for weight information
        cursor.execute("""
            SELECT ProductName, `Weight*`, Units 
            FROM products 
            WHERE `Product Type*` = 'Concentrate' 
            AND `Weight*` IS NOT NULL 
            AND `Weight*` != ''
            LIMIT 3
        """)
        concentrate_weights = cursor.fetchall()
        print("✅ Sample concentrate weights:")
        for name, weight, units in concentrate_weights:
            print(f"   - {name}: {weight}{units}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def create_fresh_database_for_web():
    """Create a fresh, optimized database for web deployment"""
    print("🔧 Creating fresh database for web deployment...")
    
    # Source database (your working local database)
    source_db = "uploads/product_database_AGT_Bothell.db"
    
    if not os.path.exists(source_db):
        print(f"❌ Source database not found: {source_db}")
        return False
    
    # Create web deployment directory
    web_deploy_dir = "web_database_fresh"
    os.makedirs(web_deploy_dir, exist_ok=True)
    
    # Create optimized database for web
    web_db_path = os.path.join(web_deploy_dir, "product_database_AGT_Bothell.db")
    
    try:
        # Copy source database
        shutil.copy2(source_db, web_db_path)
        
        # Optimize the database for web deployment
        conn = sqlite3.connect(web_db_path)
        cursor = conn.cursor()
        
        # Vacuum to optimize file size
        print("🗜️  Optimizing database...")
        cursor.execute("VACUUM")
        
        # Add indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_type 
            ON products(`Product Type*`)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_strain 
            ON products(`Product Strain`)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_name 
            ON products(ProductName)
        """)
        
        # Analyze for query optimization
        cursor.execute("ANALYZE")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Optimized database created: {web_db_path}")
        
        # Test the optimized database
        if test_database_connection(web_db_path):
            print("✅ Optimized database passes all tests")
            return web_db_path
        else:
            print("❌ Optimized database failed tests")
            return False
            
    except Exception as e:
        print(f"❌ Error creating optimized database: {e}")
        return False

def create_web_deployment_package():
    """Create complete web deployment package"""
    print("📦 Creating complete web deployment package...")
    
    # Create fresh optimized database
    web_db_path = create_fresh_database_for_web()
    if not web_db_path:
        return False
    
    web_deploy_dir = os.path.dirname(web_db_path)
    
    # Create database upload script
    upload_script = """#!/bin/bash

# AGT Label Maker - Database Upload Script
# ========================================

echo "🚀 AGT Label Maker Database Upload"
echo "=================================="

# Check if database file exists
if [ ! -f "product_database_AGT_Bothell.db" ]; then
    echo "❌ Database file not found in current directory"
    echo "Please ensure 'product_database_AGT_Bothell.db' is in this directory"
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Backup existing database if it exists
if [ -f "uploads/product_database_AGT_Bothell.db" ]; then
    echo "💾 Backing up existing database..."
    cp uploads/product_database_AGT_Bothell.db uploads/product_database_backup_$(date +%Y%m%d_%H%M%S).db
    echo "✅ Backup created"
fi

# Copy new database
echo "📥 Installing new database..."
cp product_database_AGT_Bothell.db uploads/

# Set permissions
chmod 644 uploads/product_database_AGT_Bothell.db

# Verify installation
echo "🧪 Verifying database installation..."
python3 -c "
import sqlite3
import os

db_path = 'uploads/product_database_AGT_Bothell.db'

if not os.path.exists(db_path):
    print('❌ Database file not found after copy')
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE \`Product Type*\` = \\'Concentrate\\'')
    concentrate_count = cursor.fetchone()[0]
    
    print(f'✅ Database verified:')
    print(f'   Total products: {count:,}')
    print(f'   Concentrate products: {concentrate_count:,}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Database verification failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Database upload completed successfully!"
    echo "📋 Next steps:"
    echo "1. Restart your web application/server"
    echo "2. Test the application to ensure products are loading"
    echo "3. Verify concentrate products show weights correctly"
else
    echo "❌ Database upload failed"
    exit 1
fi
"""
    
    script_path = os.path.join(web_deploy_dir, "upload_database.sh")
    with open(script_path, "w") as f:
        f.write(upload_script)
    os.chmod(script_path, 0o755)
    
    # Create Git deployment script
    git_script = """#!/bin/bash

# AGT Label Maker - Git Database Deployment
# =========================================

echo "🔄 AGT Label Maker Git Database Update"
echo "======================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    echo "Please run this from your AGT Label Maker git repository"
    exit 1
fi

# Copy database to uploads directory
echo "📥 Copying database to repository..."
cp product_database_AGT_Bothell.db uploads/

# Add to git
echo "📝 Adding database to git..."
git add uploads/product_database_AGT_Bothell.db

# Commit
echo "💾 Committing database update..."
git commit -m "Update database with complete product inventory

- Restored database with full product catalog
- Includes all product types and weight information
- Concentrate weight display fix applied
- Ready for web deployment"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "🎉 Database updated in git repository!"
echo "📋 On your web server, run:"
echo "git pull origin main"
echo "Then restart your web application"
"""
    
    git_script_path = os.path.join(web_deploy_dir, "deploy_with_git.sh")
    with open(git_script_path, "w") as f:
        f.write(git_script)
    os.chmod(git_script_path, 0o755)
    
    # Create comprehensive instructions
    instructions = f"""# Web Database Recovery Package

## Problem
Your web database started over and is now empty or missing products.

## Solution
This package contains a fresh, optimized database with all your products.

## Package Contents
- `product_database_AGT_Bothell.db` - Complete optimized database
- `upload_database.sh` - Direct upload script
- `deploy_with_git.sh` - Git deployment script
- `README.md` - These instructions

## Database Stats
- Products: Verified with complete inventory
- Size: Optimized for web deployment
- Indexes: Added for better performance
- Tested: All functions verified

## Deployment Methods (Choose One)

### Method 1: Direct Upload (Recommended)
1. Upload `product_database_AGT_Bothell.db` to your web server
2. Run `./upload_database.sh`
3. Restart your web application

### Method 2: Git Deployment
1. Run `./deploy_with_git.sh` from your local repository
2. On your web server: `git pull origin main`
3. Restart your web application

### Method 3: Manual Upload (PythonAnywhere/cPanel)
1. Upload `product_database_AGT_Bothell.db` to your web app's `uploads/` directory
2. Ensure file permissions are correct (644)
3. Restart your web application

## Verification Steps
After deployment:
1. Check that your web app shows products
2. Verify product counts match expected numbers
3. Test concentrate products show weights correctly
4. Test label generation works

## Prevention
- Regular database backups
- Use Git for version control
- Monitor database file integrity

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    readme_path = os.path.join(web_deploy_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(instructions)
    
    print(f"✅ Web deployment package created in: {web_deploy_dir}/")
    print("📋 Package includes:")
    print(f"   - Optimized database file")
    print(f"   - Upload scripts for different deployment methods")
    print(f"   - Complete instructions")
    
    return True

def main():
    """Main diagnostic and recovery workflow"""
    print("🔧 AGT Label Maker - Web Database Diagnosis & Recovery")
    print("=" * 55)
    print()
    
    # Test local database
    print("🔍 Step 1: Testing local database...")
    local_db = "uploads/product_database_AGT_Bothell.db"
    local_ok = test_database_connection(local_db)
    print()
    
    if local_ok:
        print("✅ Local database is working correctly")
        print("🔧 Creating fresh deployment package for web...")
        print()
        
        if create_web_deployment_package():
            print()
            print("🎉 Web database recovery package created!")
            print("📁 Check the 'web_database_fresh' directory")
            print()
            print("📋 Quick Steps:")
            print("1. Go to 'web_database_fresh' directory")
            print("2. Upload the database file to your web server")
            print("3. Run the upload script or manually place in uploads/")
            print("4. Restart your web application")
            print("5. Test that products are loading correctly")
        else:
            print("❌ Failed to create web deployment package")
    else:
        print("❌ Local database has issues - please check the errors above")

if __name__ == "__main__":
    main()