#!/usr/bin/env python3.11
"""
Create a test Excel file for Bothell inventory
This will create a small Excel file with sample data for testing
"""

import os
import pandas as pd
from datetime import datetime

def create_test_excel():
    """Create a test Excel file with sample Bothell inventory data"""
    
    # Detect environment
    if os.path.exists('/home/adamcordova'):
        # PythonAnywhere environment
        project_dir = '/home/adamcordova/AGTDesigner'
        uploads_dir = os.path.join(project_dir, 'uploads')
    else:
        # Local environment
        project_dir = '/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 5'
        uploads_dir = os.path.join(project_dir, 'uploads')
    
    # Ensure uploads directory exists
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Create sample data
    sample_data = [
        {
            'Product Name*': 'Blue Dream',
            'Description': 'Classic sativa-dominant hybrid',
            'Product Type*': 'Flower',
            'Product Brand': 'AGT Premium',
            'Product Strain': 'Blue Dream',
            'Lineage': 'SATIVA',
            'Concentrate Type': '',
            'Quantity*': '1',
            'Weight*': '3.5',
            'Weight Unit* (grams/gm or ounces/oz)': 'grams',
            'THC test result': '18.5',
            'CBD test result': '0.8',
            'Test result unit (% or mg)': '%',
            'Vendor/Supplier*': 'AGT Bothell',
            'Price* (Tier Name for Bulk)': '45.00',
            'Cost*': '25.00',
            'Lot Number': 'BD001',
            'Barcode*': '1234567890123',
            'State': 'WA',
            'Is Sample? (yes/no)': 'no',
            'Is MJ product?(yes/no)': 'yes',
            'Discountable? (yes/no)': 'yes',
            'Room*': 'Flower Room A',
            'Batch Number': 'BD2025001',
            'Product Tags (comma separated)': 'premium, sativa, hybrid',
            'Internal Product Identifier': 'BD-001',
            'Expiration Date(YYYY-MM-DD)': '2025-12-31',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '18.5',
            'Allergens': 'None',
            'Solvent': '',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '40.00',
            'Total THC': '18.5',
            'THCA': '0.2',
            'CBDA': '0.1',
            'CBN': '0.1',
            'Image URL': '',
            'Ingredients': 'Cannabis',
            'DOH Compliant (Yes/No)': 'Yes'
        },
        {
            'Product Name*': 'OG Kush',
            'Description': 'Classic indica strain',
            'Product Type*': 'Flower',
            'Product Brand': 'AGT Premium',
            'Product Strain': 'OG Kush',
            'Lineage': 'INDICA',
            'Concentrate Type': '',
            'Quantity*': '1',
            'Weight*': '3.5',
            'Weight Unit* (grams/gm or ounces/oz)': 'grams',
            'THC test result': '22.3',
            'CBD test result': '0.5',
            'Test result unit (% or mg)': '%',
            'Vendor/Supplier*': 'AGT Bothell',
            'Price* (Tier Name for Bulk)': '50.00',
            'Cost*': '28.00',
            'Lot Number': 'OG001',
            'Barcode*': '1234567890124',
            'State': 'WA',
            'Is Sample? (yes/no)': 'no',
            'Is MJ product?(yes/no)': 'yes',
            'Discountable? (yes/no)': 'yes',
            'Room*': 'Flower Room B',
            'Batch Number': 'OG2025001',
            'Product Tags (comma separated)': 'premium, indica, classic',
            'Internal Product Identifier': 'OG-001',
            'Expiration Date(YYYY-MM-DD)': '2025-12-31',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '22.3',
            'Allergens': 'None',
            'Solvent': '',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '45.00',
            'Total THC': '22.3',
            'THCA': '0.3',
            'CBDA': '0.1',
            'CBN': '0.2',
            'Image URL': '',
            'Ingredients': 'Cannabis',
            'DOH Compliant (Yes/No)': 'Yes'
        },
        {
            'Product Name*': 'CBD Tincture',
            'Description': 'High CBD tincture for wellness',
            'Product Type*': 'Tincture',
            'Product Brand': 'AGT Wellness',
            'Product Strain': 'CBD',
            'Lineage': 'CBD',
            'Concentrate Type': '',
            'Quantity*': '1',
            'Weight*': '30',
            'Weight Unit* (grams/gm or ounces/oz)': 'ml',
            'THC test result': '0.3',
            'CBD test result': '25.0',
            'Test result unit (% or mg)': '%',
            'Vendor/Supplier*': 'AGT Bothell',
            'Price* (Tier Name for Bulk)': '35.00',
            'Cost*': '20.00',
            'Lot Number': 'CBD001',
            'Barcode*': '1234567890125',
            'State': 'WA',
            'Is Sample? (yes/no)': 'no',
            'Is MJ product?(yes/no)': 'yes',
            'Discountable? (yes/no)': 'yes',
            'Room*': 'Extract Room',
            'Batch Number': 'CBD2025001',
            'Product Tags (comma separated)': 'wellness, cbd, tincture',
            'Internal Product Identifier': 'CBD-001',
            'Expiration Date(YYYY-MM-DD)': '2026-01-01',
            'Is Archived? (yes/no)': 'no',
            'THC Per Serving': '0.3',
            'Allergens': 'None',
            'Solvent': 'MCT Oil',
            'Accepted Date': '2025-01-01',
            'Medical Only (Yes/No)': 'No',
            'Med Price': '30.00',
            'Total THC': '0.3',
            'THCA': '0.0',
            'CBDA': '0.0',
            'CBN': '0.0',
            'Image URL': '',
            'Ingredients': 'CBD Extract, MCT Oil',
            'DOH Compliant (Yes/No)': 'Yes'
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%m-%d-%Y_%I_%M_%S_%p')
    filename = f'A Greener Today - Bothell_inventory_{timestamp}.xlsx'
    filepath = os.path.join(uploads_dir, filename)
    
    # Save to Excel
    df.to_excel(filepath, index=False, engine='openpyxl')
    
    print(f"✅ Created test Excel file: {filename}")
    print(f"📁 Location: {filepath}")
    print(f"📊 Rows: {len(df)}")
    print(f"📋 Columns: {len(df.columns)}")
    
    return filepath

if __name__ == "__main__":
    create_test_excel()
