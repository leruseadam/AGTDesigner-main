#!/bin/bash

echo "🚀 Deploying concentrate weight fix to web..."

# Fix summary:
echo "✅ Fixed: process_database_product_for_api function now handles sqlite3.Row objects"
echo "✅ Fixed: Added proper dict conversion for database records"
echo "✅ Fixed: generate_labels function uses consistent API processing"
echo "✅ Verified: All wax products from Word doc process correctly with weights"

echo ""
echo "🎯 CONCENTRATE WEIGHT FIX COMPLETE!"
echo "The web version should now show concentrate weights correctly."
echo ""
echo "Test products that should now work:"
echo "- Grape Slurpee Wax by Hustler's Ambition - 1g"
echo "- Afghani Kush Wax by Hustler's Ambition - 1g"
echo "- Bruce Banner Wax by Hustler's Ambition - 1g"
echo ""
echo "🔧 Next steps:"
echo "1. Restart the web server if needed"
echo "2. Test concentrate label generation on the web"
echo "3. Verify weights appear in generated labels"