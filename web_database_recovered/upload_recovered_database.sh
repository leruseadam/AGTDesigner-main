#!/bin/bash

# Database Recovery Upload Script
# ===============================

echo "🔄 Uploading Recovered Database"
echo "==============================="

# Check current directory
if [ ! -f "product_database_AGT_Bothell.db" ]; then
    echo "❌ Database file not found!"
    echo "Please run this script from the web_database_recovered directory"
    exit 1
fi

# Create uploads directory
mkdir -p uploads

# Backup existing database
if [ -f "uploads/product_database_AGT_Bothell.db" ]; then
    echo "💾 Backing up existing database..."
    mv uploads/product_database_AGT_Bothell.db uploads/product_database_backup_$(date +%Y%m%d_%H%M%S).db
fi

# Copy recovered database
echo "📥 Installing recovered database..."
cp product_database_AGT_Bothell.db uploads/

# Set proper permissions
chmod 644 uploads/product_database_AGT_Bothell.db

echo "✅ Database uploaded successfully!"
echo "📊 Expected products: 11,021"
echo ""
echo "📋 Next steps:"
echo "1. Restart your web application"
echo "2. Test that products are loading"
echo "3. Verify concentrate products show weights"
