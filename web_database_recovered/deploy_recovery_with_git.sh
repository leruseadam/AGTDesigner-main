#!/bin/bash

# Git Database Recovery Deployment
# ================================

echo "🔄 Git Database Recovery"
echo "========================"

# Copy to main project uploads
cp product_database_AGT_Bothell.db ../uploads/

# Add to git
cd ..
git add uploads/product_database_AGT_Bothell.db

# Commit
git commit -m "Recover database after corruption

- Repaired/rebuilt database with 11,021 products
- Fixed database corruption issues
- Optimized for web deployment
- Ready for production use"

# Push
git push origin main

echo "✅ Database recovery committed to git!"
echo "📋 On your web server:"
echo "git pull origin main"
echo "Then restart your application"
