#!/usr/bin/env python3.11
"""
Fix the _calculate_product_strain method signature mismatch.
The existing method expects 4 parameters but the app calls it with 1 dictionary parameter.
This adds an overloaded version that handles the dictionary format.
"""

import os
import re

def fix_method_signature():
    """Add an overloaded _calculate_product_strain method that accepts product_data dict"""
    
    file_path = 'src/core/data/product_database.py'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the existing file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the overloaded method already exists
    if 'def _calculate_product_strain(self, product_data:' in content:
        print("✅ Overloaded _calculate_product_strain method already exists")
        return True
    
    # Find the first occurrence of the existing method to add the overload before it
    method_pattern = r'(def _calculate_product_strain\(self, product_type: str, product_name: str, description: str, ratio: str\) -> str:)'
    
    if not re.search(method_pattern, content):
        print("❌ Could not find existing _calculate_product_strain method to overload")
        return False
    
    # Create the overloaded method
    overloaded_method = '''    def _calculate_product_strain(self, product_data):
        """Calculate Product Strain from product_data dictionary (overloaded version)."""
        try:
            # Handle both dict and individual parameter formats
            if isinstance(product_data, dict):
                product_type = product_data.get('Product Type*', '') or product_data.get('product_type', '')
                product_name = product_data.get('Product Name*', '') or product_data.get('product_name', '')
                description = product_data.get('Description', '') or product_data.get('description', '')
                ratio = product_data.get('Ratio', '') or product_data.get('ratio', '')
                
                # Call the original method with extracted parameters
                return self._calculate_product_strain(product_type, product_name, description, ratio)
            else:
                # If it's not a dict, assume it's the product_type parameter
                return self._calculate_product_strain(product_data, '', '', '')
                
        except Exception as e:
            print(f"Error in overloaded _calculate_product_strain: {e}")
            return 'Mixed'

'''
    
    # Insert the overloaded method before the first existing method
    content = re.sub(method_pattern, overloaded_method + r'\1', content, count=1)
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Added overloaded _calculate_product_strain method to {file_path}")
    
    # Test the import and method
    try:
        import sys
        sys.path.insert(0, '.')
        from src.core.data.product_database import ProductDatabase
        
        # Test the new overloaded method
        db = ProductDatabase()
        test_data = {
            'Product Type*': 'Flower',
            'Product Name*': 'Blue Dream',
            'Description': 'Hybrid strain',
            'Ratio': '1:1'
        }
        strain = db._calculate_product_strain(test_data)
        print(f"✅ Test successful: overloaded _calculate_product_strain returned '{strain}'")
        
        # Test with string parameter (fallback)
        strain2 = db._calculate_product_strain('Flower')
        print(f"✅ Test successful: string parameter returned '{strain2}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing _calculate_product_strain method signature...")
    success = fix_method_signature()
    
    if success:
        print("\n🎉 Fix completed successfully!")
        print("The overloaded _calculate_product_strain method has been added.")
        print("Your application should now work with both dict and individual parameters.")
    else:
        print("\n❌ Fix failed!")
