#!/bin/bash

echo "=== Deploying Weight Field Fixes ==="

# Clear any cached data
echo "Clearing caches..."
rm -rf cache/*
rm -rf sessions/*
rm -rf __pycache__/*

# Restart the application to ensure changes take effect
echo "Restarting application..."
if [ -f "wsgi.py" ]; then
    touch wsgi.py
fi

# Clear browser cache instruction
echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "IMPORTANT: To see the weight field fixes:"
echo "1. Clear your browser cache (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Reload the page"
echo "3. Try filtering by concentrate products again"
echo ""
echo "The fixes include:"
echo "- Enhanced weight field extraction in frontend filtering"
echo "- Comprehensive weight field population in backend processing"
echo "- Automatic weight extraction from product names for concentrate products"
echo "- Cache invalidation to ensure fixes take effect immediately"
echo ""
