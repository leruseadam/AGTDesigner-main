#!/usr/bin/env python3
"""
Test script to debug lineage changes pipeline
"""

from src.core.data.product_database import ProductDatabase
from src.core.data.excel_processor import ExcelProcessor
import pandas as pd

def test_lineage_pipeline():
    """Test the complete lineage update pipeline"""
    print("=== Testing Lineage Pipeline ===")
    
    # 1. Load data and set up processor
    processor = ExcelProcessor()
    db = ProductDatabase('AGT_Bothell')
    products = db.get_all_products()
    df = pd.DataFrame(products)
    processor.df = df
    
    # 2. Find a flower product with lineage
    flower_products = df[df['Product Type*'].str.contains('flower', case=False, na=False)]
    flower_with_lineage = flower_products[flower_products['Lineage'].notna() & (flower_products['Lineage'] != '') & (flower_products['Lineage'] != 'nan')].head(1)
    
    if len(flower_with_lineage) == 0:
        print("❌ No flower products with lineage found")
        return
    
    test_product = flower_with_lineage.iloc[0]
    product_name = test_product['Product Name*']
    original_lineage = test_product['Lineage']
    
    print(f"📋 Testing with: {product_name}")
    print(f"   Original Lineage: '{original_lineage}'")
    print(f"   Product Type: {test_product['Product Type*']}")
    
    # 3. Change lineage using the update method (simulating web request)
    new_lineage = 'SATIVA' if original_lineage.upper() != 'SATIVA' else 'INDICA'
    print(f"\\n🔄 Updating lineage to: '{new_lineage}'")
    
    success = processor.update_lineage_in_current_data(product_name, new_lineage)
    if not success:
        print("❌ Failed to update lineage")
        return
    
    print("✅ Lineage updated in DataFrame")
    
    # 4. Test get_selected_records
    processor.selected_tags = [product_name]
    result = processor.get_selected_records()
    
    if not result:
        print("❌ No results from get_selected_records")
        return
    
    record = result[0]
    result_lineage = record.get('Lineage', 'NOT FOUND')
    print(f"✅ get_selected_records returned lineage: '{result_lineage}'")
    
    # 5. Test the complete pipeline through template processing
    print("\\n🔍 Testing complete template pipeline...")
    
    # Simulate what happens in generate_labels route
    try:
        from src.core.generation.template_processor import TemplateProcessor
        
        # Create template processor and process the records
        template_processor = TemplateProcessor()
        
        # Process the records (this would normally happen in the generate_labels route)
        final_doc = template_processor.process_records(result)
        
        if final_doc:
            print("✅ Template processing completed successfully")
            
            # Check if the changes made it through
            if result_lineage == new_lineage:
                print(f"✅ SUCCESS: Lineage change '{original_lineage}' → '{new_lineage}' propagated through entire pipeline!")
            else:
                print(f"❌ FAILURE: Expected '{new_lineage}', got '{result_lineage}'")
        else:
            print("❌ Template processing failed")
            
    except Exception as e:
        print(f"❌ Error in template processing: {e}")
    
    # 6. Test direct DataFrame verification
    print("\\n🔍 Verifying DataFrame state...")
    mask = processor.df['Product Name*'] == product_name
    current_lineage = processor.df.loc[mask, 'Lineage'].iloc[0]
    print(f"   DataFrame lineage: '{current_lineage}'")
    
    if current_lineage == new_lineage:
        print("✅ DataFrame correctly updated")
    else:
        print(f"❌ DataFrame not updated correctly")

if __name__ == "__main__":
    test_lineage_pipeline()