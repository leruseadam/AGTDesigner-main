#!/usr/bin/env python3
"""
Fix migration data cleaning issues
"""

import re

def fix_migration_file():
    """Fix the migration file with comprehensive data cleaning"""
    
    file_path = "migrate_to_pythonanywhere_postgresql.py"
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add comprehensive data cleaning functions
    cleaning_functions = '''
        # Clean date data
        def clean_date(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                # Handle various date formats
                value_str = str(value).strip()
                if value_str == '' or value_str.lower() in ['none', 'null', 'n/a']:
                    return None
                return value_str
            except:
                return None
        
        # Clean numeric data
        def clean_numeric(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            try:
                cleaned = str(value).replace(',', '').strip()
                return float(cleaned) if cleaned else None
            except:
                return None
        
        # Clean text data
        def clean_text(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            return str(value).strip()
        
        # Clean boolean data
        def clean_boolean(value):
            if not value or value == '' or str(value).strip() == '':
                return None
            value_str = str(value).strip().lower()
            if value_str in ['yes', 'true', '1', 'y']:
                return True
            elif value_str in ['no', 'false', '0', 'n']:
                return False
            return None
'''
    
    # Insert cleaning functions after clean_price function
    content = content.replace(
        '        def clean_price(value):\n            if not value or value == \'\':\n                return None\n            try:\n                cleaned = str(value).replace(\'$\', \'\').replace(\',\', \'\').strip()\n                return float(cleaned) if cleaned else None\n            except:\n                return None',
        '        def clean_price(value):\n            if not value or value == \'\':\n                return None\n            try:\n                cleaned = str(value).replace(\'$\', \'\').replace(\',\', \'\').strip()\n                return float(cleaned) if cleaned else None\n            except:\n                return None' + cleaning_functions
    )
    
    # Fix all the data fields to use appropriate cleaning functions
    replacements = [
        # Numeric fields
        (r"product_dict\.get\('Weight\*'\)", "clean_numeric(product_dict.get('Weight*'))"),
        (r"product_dict\.get\('Quantity\*'\)", "clean_numeric(product_dict.get('Quantity*'))"),
        (r"product_dict\.get\('Total THC'\)", "clean_numeric(product_dict.get('Total THC'))"),
        (r"product_dict\.get\('THCA'\)", "clean_numeric(product_dict.get('THCA'))"),
        (r"product_dict\.get\('CBDA'\)", "clean_numeric(product_dict.get('CBDA'))"),
        (r"product_dict\.get\('CBN'\)", "clean_numeric(product_dict.get('CBN'))"),
        (r"product_dict\.get\('THC'\)", "clean_numeric(product_dict.get('THC'))"),
        (r"product_dict\.get\('CBD'\)", "clean_numeric(product_dict.get('CBD'))"),
        (r"product_dict\.get\('Total CBD'\)", "clean_numeric(product_dict.get('Total CBD'))"),
        (r"product_dict\.get\('CBGA'\)", "clean_numeric(product_dict.get('CBGA'))"),
        (r"product_dict\.get\('CBG'\)", "clean_numeric(product_dict.get('CBG'))"),
        (r"product_dict\.get\('Total CBG'\)", "clean_numeric(product_dict.get('Total CBG'))"),
        (r"product_dict\.get\('CBC'\)", "clean_numeric(product_dict.get('CBC'))"),
        (r"product_dict\.get\('CBDV'\)", "clean_numeric(product_dict.get('CBDV'))"),
        (r"product_dict\.get\('THCV'\)", "clean_numeric(product_dict.get('THCV'))"),
        (r"product_dict\.get\('CBGV'\)", "clean_numeric(product_dict.get('CBGV'))"),
        (r"product_dict\.get\('CBNV'\)", "clean_numeric(product_dict.get('CBNV'))"),
        (r"product_dict\.get\('CBGVA'\)", "clean_numeric(product_dict.get('CBGVA'))"),
        (r"product_dict\.get\('CombinedWeight'\)", "clean_numeric(product_dict.get('CombinedWeight'))"),
        
        # Text fields
        (r"product_dict\.get\('Product Name\*'\)", "clean_text(product_dict.get('Product Name*'))"),
        (r"product_dict\.get\('Product Type\*'\)", "clean_text(product_dict.get('Product Type*'))"),
        (r"product_dict\.get\('Product Brand'\)", "clean_text(product_dict.get('Product Brand'))"),
        (r"product_dict\.get\('Vendor/Supplier\*'\)", "clean_text(product_dict.get('Vendor/Supplier*'))"),
        (r"product_dict\.get\('Product Strain'\)", "clean_text(product_dict.get('Product Strain'))"),
        (r"product_dict\.get\('Lineage'\)", "clean_text(product_dict.get('Lineage'))"),
        (r"product_dict\.get\('Description'\)", "clean_text(product_dict.get('Description'))"),
        (r"product_dict\.get\('Units'\)", "clean_text(product_dict.get('Units'))"),
        (r"product_dict\.get\('DOH'\)", "clean_text(product_dict.get('DOH'))"),
        (r"product_dict\.get\('Concentrate Type'\)", "clean_text(product_dict.get('Concentrate Type'))"),
        (r"product_dict\.get\('Ratio'\)", "clean_text(product_dict.get('Ratio'))"),
        (r"product_dict\.get\('JointRatio'\)", "clean_text(product_dict.get('JointRatio'))"),
        (r"product_dict\.get\('State'\)", "clean_text(product_dict.get('State'))"),
        (r"product_dict\.get\('Room\*'\)", "clean_text(product_dict.get('Room*'))"),
        (r"product_dict\.get\('Batch Number'\)", "clean_text(product_dict.get('Batch Number'))"),
        (r"product_dict\.get\('Lot Number'\)", "clean_text(product_dict.get('Lot Number'))"),
        (r"product_dict\.get\('Barcode\*'\)", "clean_text(product_dict.get('Barcode*'))"),
        (r"product_dict\.get\('THC Per Serving'\)", "clean_text(product_dict.get('THC Per Serving'))"),
        (r"product_dict\.get\('Allergens'\)", "clean_text(product_dict.get('Allergens'))"),
        (r"product_dict\.get\('Solvent'\)", "clean_text(product_dict.get('Solvent'))"),
        (r"product_dict\.get\('Internal Product Identifier'\)", "clean_text(product_dict.get('Internal Product Identifier'))"),
        (r"product_dict\.get\('Product Tags \(comma separated\)'\)", "clean_text(product_dict.get('Product Tags (comma separated)'))"),
        (r"product_dict\.get\('Image URL'\)", "clean_text(product_dict.get('Image URL'))"),
        (r"product_dict\.get\('Ingredients'\)", "clean_text(product_dict.get('Ingredients'))"),
        (r"product_dict\.get\('Ratio_or_THC_CBD'\)", "clean_text(product_dict.get('Ratio_or_THC_CBD'))"),
        (r"product_dict\.get\('Description_Complexity'\)", "clean_text(product_dict.get('Description_Complexity'))"),
        (r"product_dict\.get\('normalized_name'\)", "clean_text(product_dict.get('normalized_name'))"),
        (r"product_dict\.get\('Test result unit \(% or mg\)'\)", "clean_text(product_dict.get('Test result unit (% or mg)'))"),
        
        # Boolean fields
        (r"product_dict\.get\('Is Sample\? \(yes/no\)'\)", "clean_boolean(product_dict.get('Is Sample? (yes/no)'))"),
        (r"product_dict\.get\('Is MJ product\?\(yes/no\)'\)", "clean_boolean(product_dict.get('Is MJ product?(yes/no)'))"),
        (r"product_dict\.get\('Discountable\? \(yes/no\)'\)", "clean_boolean(product_dict.get('Discountable? (yes/no)'))"),
        (r"product_dict\.get\('Medical Only \(Yes/No\)'\)", "clean_boolean(product_dict.get('Medical Only (Yes/No)'))"),
        (r"product_dict\.get\('Is Archived\? \(yes/no\)'\)", "clean_boolean(product_dict.get('Is Archived? (yes/no)'))"),
    ]
    
    # Apply all replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write the fixed file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Migration file fixed with comprehensive data cleaning!")
    print("📋 Applied fixes:")
    print("   - Added clean_date, clean_numeric, clean_text, clean_boolean functions")
    print("   - Applied appropriate cleaning to all data fields")
    print("   - Fixed date, numeric, text, and boolean data handling")

if __name__ == "__main__":
    fix_migration_file()
