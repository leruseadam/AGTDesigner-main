#!/usr/bin/env python3.11
"""
Fix missing methods in product_database.py
Adds the missing _calculate_product_strain method and other required methods
"""

import os

def fix_product_database():
    """Add missing methods to the existing product_database.py file"""
    
    file_path = 'src/core/data/product_database.py'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the existing file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the method already exists
    if '_calculate_product_strain' in content:
        print("✅ _calculate_product_strain method already exists")
        return True
    
    # Add the missing methods before the final if __name__ == "__main__": block
    additional_methods = '''
    def _calculate_product_strain(self, product_data):
        """Calculate product strain from product data."""
        try:
            # Extract strain information from product data
            strain_name = product_data.get('Product Strain', '') or product_data.get('strain_name', '')
            lineage = product_data.get('Lineage', '')
            
            if strain_name and strain_name.strip():
                return strain_name.strip()
            
            if lineage and lineage.strip():
                return lineage.strip()
            
            # Default fallback
            return 'Mixed'
            
        except Exception as e:
            print(f"Error calculating product strain: {e}")
            return 'Mixed'
    
    def _normalize_strain_name(self, strain_name):
        """Normalize strain name for consistency."""
        if not strain_name:
            return 'Mixed'
        
        # Basic normalization
        normalized = str(strain_name).strip().title()
        
        # Handle common variations
        variations = {
            'Mixed Strain': 'Mixed',
            'Mixed Hybrid': 'Mixed',
            'Hybrid': 'Mixed',
            'Indica': 'Mixed',
            'Sativa': 'Mixed'
        }
        
        return variations.get(normalized, normalized)
    
    def _get_strain_from_lineage(self, lineage):
        """Extract strain name from lineage information."""
        if not lineage:
            return 'Mixed'
        
        # Simple extraction - could be enhanced
        lineage_str = str(lineage).strip()
        
        # If it looks like a strain name, use it
        if len(lineage_str) > 2 and not lineage_str.lower() in ['hybrid', 'indica', 'sativa']:
            return lineage_str
        
        return 'Mixed'
    
    def add_product_with_strain(self, product_data):
        """Add a product with automatic strain calculation."""
        try:
            # Calculate strain if not provided
            if 'Product Strain' not in product_data or not product_data.get('Product Strain'):
                product_data['Product Strain'] = self._calculate_product_strain(product_data)
            
            # Normalize the strain name
            product_data['Product Strain'] = self._normalize_strain_name(product_data['Product Strain'])
            
            return self.add_product(product_data)
            
        except Exception as e:
            print(f"Error adding product with strain: {e}")
            return False
    
    def update_product_strains(self, products_data):
        """Update product strains for a batch of products."""
        updated_count = 0
        
        for product_data in products_data:
            try:
                strain = self._calculate_product_strain(product_data)
                product_data['Product Strain'] = strain
                updated_count += 1
            except Exception as e:
                print(f"Error updating strain for product: {e}")
                continue
        
        return updated_count
'''
    
    # Insert the methods before the final if __name__ block
    if 'if __name__ == "__main__":' in content:
        content = content.replace(
            'if __name__ == "__main__":',
            additional_methods + '\n\nif __name__ == "__main__":'
        )
    else:
        # Add at the end if no main block
        content += additional_methods
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Added missing methods to {file_path}")
    
    # Test the import
    try:
        import sys
        sys.path.insert(0, '.')
        from src.core.data.product_database import ProductDatabase
        
        # Test the new method
        db = ProductDatabase()
        test_data = {'Product Strain': 'Blue Dream', 'Lineage': 'Hybrid'}
        strain = db._calculate_product_strain(test_data)
        print(f"✅ Test successful: _calculate_product_strain returned '{strain}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing missing methods in product_database.py...")
    success = fix_product_database()
    
    if success:
        print("\n🎉 Fix completed successfully!")
        print("The _calculate_product_strain method has been added.")
        print("Your application should now work without the AttributeError.")
    else:
        print("\n❌ Fix failed!")
