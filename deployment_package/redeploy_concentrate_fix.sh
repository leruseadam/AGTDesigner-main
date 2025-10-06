#!/bin/bash

echo "🚀 Redeploying Concentrate Weight Fix..."
echo "==========================================="

# Get the latest changes
echo "📥 Pulling latest changes from repository..."
git pull origin main

echo ""
echo "🔧 Key Fix Summary:"
echo "✅ Fixed process_database_product_for_api to handle sqlite3.Row objects"
echo "✅ Added proper dict conversion for database records"
echo "✅ Fixed generate_labels function architecture"
echo ""

# Check if the key fix is in place
echo "🔍 Verifying fix is in deployed code..."
if grep -q "if hasattr(db_product, 'keys'):" app.py; then
    echo "✅ sqlite3.Row fix is present in app.py"
else
    echo "❌ Fix not found - may need to pull changes again"
fi

echo ""
echo "🎯 Expected Results After Restart:"
echo "- Grape Slurpee Wax → 'Grape Slurpee Wax - 1g'"
echo "- Afghani Kush Wax → 'Afghani Kush Wax - 1g'"
echo "- Bruce Banner Wax → 'Bruce Banner Wax - 1g'"
echo ""

echo "🔄 Next Steps:"
echo "1. Restart your web server/application"
echo "2. Clear any application cache if applicable"
echo "3. Test concentrate label generation"
echo "4. Verify weights appear in generated labels"
echo ""

echo "✨ Concentrate weight fix deployment ready!"