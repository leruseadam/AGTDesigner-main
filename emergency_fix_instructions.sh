#!/bin/bash

echo "🚨 EMERGENCY PYTHONANYWHERE FIX 🚨"
echo "=================================="
echo ""

echo "Your site is showing a 500 Internal Server Error."
echo "This is caused by the WSGI configuration not finding the 'app' module."
echo ""

echo "📋 IMMEDIATE FIX STEPS:"
echo ""
echo "1. Go to PythonAnywhere Dashboard → Web tab"
echo "2. Click on your WSGI configuration file"
echo "3. Replace the entire content with this:"
echo ""

cat wsgi_emergency_fix.py

echo ""
echo "4. IMPORTANT: Update the path on line 7:"
echo "   Change '/home/yourusername/AGTDesigner_deployment' to your actual directory"
echo "   (Look in your Files tab to see the exact path)"
echo ""
echo "5. Click 'Save' and then 'Reload' your web app"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo "- If you're not sure of the exact path, check your Files tab in PythonAnywhere"
echo "- The path should be something like: /home/YOURUSERNAME/AGTDesigner_deployment"
echo "- Make sure all your files are in that directory"
echo ""
echo "✅ After applying this fix, your site should load successfully!"
echo "✅ The weight field fixes for concentrate products will also be active!"
