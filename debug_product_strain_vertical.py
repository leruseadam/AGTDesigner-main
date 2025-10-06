#!/usr/bin/env python3
"""
Debug script to test ProductStrain processing for vertical templates.
This will help identify if the issue is in data retrieval or template processing.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.generation.template_processor import TemplateProcessor
from src.core.data.excel_processor import ExcelProcessor, get_default_upload_file
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_product_strain_vertical():
    """Test ProductStrain processing for vertical template."""
    
    logger.info("=== TESTING PRODUCT STRAIN FOR VERTICAL TEMPLATE ===")
    
    # Get default file
    default_file = get_default_upload_file()
    if not default_file or not os.path.exists(default_file):
        logger.error("No default Excel file found")
        return
    
    logger.info(f"Using default file: {default_file}")
    
    # Load Excel data
    processor = ExcelProcessor()
    success = processor.load_file(default_file)
    if not success:
        logger.error("Failed to load Excel file")
        return
    
    logger.info(f"Loaded {len(processor.df)} records from Excel")
    
    # Check if ProductStrain column exists and has data
    strain_columns = [col for col in processor.df.columns if 'strain' in col.lower()]
    logger.info(f"Strain-related columns found: {strain_columns}")
    
    # Check first few records for ProductStrain data
    if strain_columns:
        main_strain_col = strain_columns[0]
        logger.info(f"Using main strain column: {main_strain_col}")
        
        sample_records = processor.df.head(3)
        for idx, record in sample_records.iterrows():
            strain_value = record.get(main_strain_col, '')
            logger.info(f"Record {idx}: ProductStrain = '{strain_value}'")
    
    # Test with selected tags (first 3 records)
    processor.selected_tags = processor.df.head(3).to_dict('records')
    logger.info(f"Selected {len(processor.selected_tags)} tags for testing")
    
    # Test vertical template processing
    from src.core.generation.template_processor import TemplateProcessor, get_font_scheme
    font_scheme = get_font_scheme('vertical')
    template_processor = TemplateProcessor('vertical', font_scheme, 1.0)
    
    logger.info("=== BUILDING LABEL CONTEXT FOR VERTICAL TEMPLATE ===")
    
    # Test the first record
    if processor.selected_tags:
        test_record = processor.selected_tags[0]
        logger.info(f"Testing with record: {list(test_record.keys())}")
        
        # Extract ProductStrain from record
        product_strain_from_record = (test_record.get('ProductStrain') or 
                                    test_record.get('Product Strain') or
                                    test_record.get('Strain', ''))
        logger.info(f"ProductStrain from record: '{product_strain_from_record}'")
        
        # Build label context
        label_context = template_processor._build_label_context(test_record)
        
        logger.info(f"Label context ProductStrain: '{label_context.get('ProductStrain', 'NOT_SET')}'")
        
        # Check if it's being processed as classic or non-classic
        product_type = (test_record.get('Product Type*', '').lower() or 
                       test_record.get('ProductType', '').lower())
        logger.info(f"Product type: '{product_type}'")
        logger.info(f"Is classic type: {template_processor._is_classic_type(product_type)}")
        logger.info(f"Is non-classic type: {template_processor._is_non_classic_type(product_type)}")
        
        # Check all fields in label context
        logger.info("=== FULL LABEL CONTEXT ===")
        for key, value in label_context.items():
            if hasattr(value, '_raw_image_data'):
                logger.info(f"  {key}: <QR Code>")
            else:
                logger.info(f"  {key}: '{value}'")

if __name__ == "__main__":
    test_product_strain_vertical()