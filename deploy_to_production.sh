#!/bin/bash

# Quick Production Deployment Script
# Deploys recovered database to production web server

echo "🚀 AGT Label Maker - Production Deployment"
echo "========================================="
echo ""

# Database info
DB_FILE="uploads/product_database_AGT_Bothell.db"
DB_SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
PRODUCT_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM products;" 2>/dev/null || echo "Unknown")

echo "📊 Database Information:"
echo "  File: $DB_FILE"
echo "  Size: $DB_SIZE"
echo "  Products: $PRODUCT_COUNT"
echo ""

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Error: Database file not found!"
    echo "   Expected: $DB_FILE"
    exit 1
fi

echo "✅ Database file verified"
echo ""

# Deployment options
echo "📋 Deployment Options:"
echo "1) Upload database only (recommended)"
echo "2) Git commit and push"
echo "3) Create deployment package"
echo "4) Test database locally first"
echo ""

read -p "Choose deployment method (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📤 Direct Database Upload"
        echo "========================"
        echo ""
        read -p "Enter your server hostname/IP: " server
        read -p "Enter your username: " username
        read -p "Enter remote path (e.g., /home/username/mysite/uploads/): " remote_path
        
        echo ""
        echo "🔄 Uploading database..."
        scp "$DB_FILE" "$username@$server:$remote_path"
        
        if [ $? -eq 0 ]; then
            echo "✅ Database uploaded successfully!"
            echo ""
            echo "🔧 Next steps:"
            echo "1. SSH to your server: ssh $username@$server"
            echo "2. Restart your web application"
            echo "3. Test the application in your browser"
        else
            echo "❌ Upload failed. Please check your connection and try again."
        fi
        ;;
        
    2)
        echo ""
        echo "📦 Git Deployment"
        echo "================"
        echo ""
        
        # Check if we're in a git repository
        if [ ! -d ".git" ]; then
            echo "❌ Error: Not in a git repository"
            exit 1
        fi
        
        echo "🔄 Committing database..."
        git add "$DB_FILE"
        git commit -m "Database recovery: restored $PRODUCT_COUNT products ($(date))"
        
        echo "🔄 Pushing to remote..."
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo "✅ Git push successful!"
            echo ""
            echo "🔧 Next steps:"
            echo "1. SSH to your server"
            echo "2. Run: git pull origin main"
            echo "3. Restart your web application"
        else
            echo "❌ Git push failed. Please check your repository access."
        fi
        ;;
        
    3)
        echo ""
        echo "📦 Creating Deployment Package"
        echo "=============================="
        echo ""
        
        PACKAGE_NAME="agt_database_deployment_$(date +%Y%m%d_%H%M%S).tar.gz"
        
        echo "🔄 Creating package: $PACKAGE_NAME"
        tar -czf "$PACKAGE_NAME" "$DB_FILE" "PRODUCTION_DEPLOYMENT_GUIDE.md"
        
        if [ $? -eq 0 ]; then
            echo "✅ Package created: $PACKAGE_NAME"
            echo "📊 Package size: $(ls -lh "$PACKAGE_NAME" | awk '{print $5}')"
            echo ""
            echo "🔧 Next steps:"
            echo "1. Upload $PACKAGE_NAME to your server"
            echo "2. Extract: tar -xzf $PACKAGE_NAME"
            echo "3. Move database to your uploads/ directory"
            echo "4. Restart your web application"
        else
            echo "❌ Package creation failed."
        fi
        ;;
        
    4)
        echo ""
        echo "🧪 Local Database Test"
        echo "====================="
        echo ""
        
        echo "🔄 Running database integrity check..."
        integrity_result=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;" 2>/dev/null)
        
        if [ "$integrity_result" = "ok" ]; then
            echo "✅ Database integrity: OK"
        else
            echo "⚠️  Database integrity: $integrity_result"
        fi
        
        echo ""
        echo "🔄 Testing Flask application..."
        python3 -c "
import sys
sys.path.append('.')
try:
    import app
    print('✅ Flask app loads successfully')
    
    # Test database connection
    from src.core.data.product_database import ProductDatabase
    db = ProductDatabase()
    count = db.get_product_count()
    print(f'✅ Database connection: {count:,} products')
    
except Exception as e:
    print(f'❌ Error: {e}')
"
        echo ""
        echo "🔧 If tests pass, choose option 1 or 2 to deploy"
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process complete!"
echo ""
echo "📋 Post-Deployment Checklist:"
echo "  □ Verify web application starts"
echo "  □ Test product search functionality"
echo "  □ Generate a test label"
echo "  □ Check application logs for errors"
echo ""
echo "📞 Need help? Check PRODUCTION_DEPLOYMENT_GUIDE.md"