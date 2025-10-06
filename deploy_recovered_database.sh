#!/bin/bash

# AGT Label Maker - Database Recovery Deployment Script
# =====================================================

echo "🚀 AGT Label Maker Database Recovery Deployment"
echo "================================================="

# Configuration
LOCAL_DB="uploads/product_database_AGT_Bothell_web_ready.db"
TARGET_DB="uploads/product_database_AGT_Bothell.db"

# Check if recovered database exists
if [ ! -f "$LOCAL_DB" ]; then
    echo "❌ Recovered database not found: $LOCAL_DB"
    echo "Please run the recovery process first"
    exit 1
fi

# Show database info
echo "📊 Database Information:"
echo "========================"
echo "File: $LOCAL_DB"
echo "Size: $(ls -lh "$LOCAL_DB" | awk '{print $5}')"
echo "Products: $(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM products;")"

echo ""
echo "🔄 Deployment Options:"
echo "======================"
echo "1. Replace local database (for testing)"
echo "2. Show manual deployment instructions"
echo "3. Exit"

read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo "🔄 Replacing local database..."
        
        # Backup existing database
        if [ -f "$TARGET_DB" ]; then
            backup_name="${TARGET_DB%.db}_backup_$(date +%Y%m%d_%H%M%S).db"
            echo "💾 Backing up existing database to: $backup_name"
            mv "$TARGET_DB" "$backup_name"
        fi
        
        # Deploy recovered database
        echo "📥 Installing recovered database..."
        cp "$LOCAL_DB" "$TARGET_DB"
        
        # Set permissions
        chmod 644 "$TARGET_DB"
        
        echo "✅ Local deployment complete!"
        echo "📊 Verify: $(sqlite3 "$TARGET_DB" "SELECT COUNT(*) FROM products;") products in active database"
        ;;
        
    2)
        echo "📋 Manual Deployment Instructions:"
        echo "=================================="
        echo ""
        echo "For Web Server Deployment:"
        echo "--------------------------"
        echo "1. Upload this file to your web server:"
        echo "   $LOCAL_DB"
        echo ""
        echo "2. On your web server, replace the database:"
        echo "   # Backup existing database"
        echo "   mv uploads/product_database_AGT_Bothell.db uploads/product_database_backup_\$(date +%Y%m%d_%H%M%S).db"
        echo ""
        echo "   # Install recovered database"
        echo "   mv $LOCAL_DB uploads/product_database_AGT_Bothell.db"
        echo "   chmod 644 uploads/product_database_AGT_Bothell.db"
        echo ""
        echo "3. Restart your web application"
        echo ""
        echo "Expected Results:"
        echo "- Product count: ~10,949"
        echo "- All product types available"
        echo "- Label generation working"
        echo ""
        ;;
        
    3)
        echo "👋 Deployment cancelled"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎉 Database recovery deployment complete!"
echo "Your AGT Label Maker should now be fully functional."