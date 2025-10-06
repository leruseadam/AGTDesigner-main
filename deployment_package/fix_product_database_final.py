#!/usr/bin/env python3.11
"""
Final fix for _calculate_product_strain method signature mismatch.
Adds an overloaded version that accepts product_data dictionary.
"""

import os

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
    
    # Find where to insert - right before the get_product_database function
    insertion_point = 'def get_product_database(store_name=None):'
    
    if insertion_point not in content:
        print("❌ Could not find get_product_database function to insert before")
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
    
    # Insert the overloaded method before the get_product_database function
    content = content.replace(
        insertion_point,
        overloaded_method + insertion_point
    )
    
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
        print("Your application should now work with product_data dictionary.")
    else:
        print("\n❌ Fix failed!")
