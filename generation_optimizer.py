#!/usr/bin/env python3
"""
Generation Optimizer for Custom PythonAnywhere Plan
Optimizes the existing generation endpoint for better performance
"""

import os
import time
import logging
import threading
from functools import wraps

def generation_performance_monitor(func):
    """Performance monitor for generation functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log slow operations
        if execution_time > 2.0:  # Log operations > 2 seconds
            logging.warning(f"🐌 Slow generation operation: {func.__name__} took {execution_time:.2f}s")
        elif execution_time > 0.5:  # Log operations > 0.5 seconds
            logging.info(f"⚡ Generation operation: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper

def optimize_generation_endpoint(app):
    """Optimize the existing generation endpoint"""
    
    # Find the existing generate_labels function
    original_generate_labels = app.view_functions.get('generate_labels')
    if not original_generate_labels:
        logging.warning("generate_labels endpoint not found")
        return app
    
    # Create optimized version
    @app.route('/api/generate-optimized', methods=['POST'])
    @generation_performance_monitor
    def generate_labels_optimized():
        """Optimized version of generate_labels"""
        try:
            start_time = time.time()
            
            # Get request data
            data = request.get_json()
            template_type = data.get('template_type', 'vertical')
            scale_factor = float(data.get('scale_factor', 1.0))
            selected_tags = data.get('selected_tags', [])
            
            if not selected_tags:
                return jsonify({'error': 'No tags selected'}), 400
            
            logging.info(f"⚡ Optimized generation: {len(selected_tags)} tags, {template_type} template")
            
            # Fast database lookup
            records = get_optimized_records(selected_tags)
            if not records:
                return jsonify({'error': 'No records found for selected tags'}), 400
            
            # Optimized template processing
            final_doc = process_optimized_template(records, template_type, scale_factor)
            if final_doc is None:
                return jsonify({'error': 'Failed to generate document'}), 500
            
            # Fast document saving
            from io import BytesIO
            output_buffer = BytesIO()
            final_doc.save(output_buffer)
            output_buffer.seek(0)
            
            # Generate filename
            filename = generate_optimized_filename(template_type, len(records))
            
            # Create response
            from flask import send_file
            response = send_file(
                output_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            generation_time = time.time() - start_time
            logging.info(f"⚡ Optimized generation complete: {generation_time:.2f}s")
            
            return response
            
        except Exception as e:
            logging.error(f"Optimized generation error: {e}")
            return jsonify({'error': f'Generation failed: {str(e)}'}), 500
    
    return app

def get_optimized_records(selected_tags):
    """Optimized database record lookup"""
    try:
        from src.core.data.product_database import get_product_database
        from flask import session
        
        current_store = session.get('selected_store', 'AGT_Bothell')
        product_db = get_product_database(current_store)
        
        if not product_db:
            return []
        
        # Batch lookup with minimal processing
        records = product_db.get_products_by_names(selected_tags)
        
        # Convert to template format efficiently
        template_records = []
        for record in records:
            if record.get('Product Name*'):
                # Minimal field mapping for speed
                template_record = {
                    'Product Name*': record.get('Product Name*', ''),
                    'ProductName': record.get('Product Name*', ''),
                    'ProductType': record.get('Product Type*', ''),
                    'Lineage': record.get('Lineage', 'HYBRID'),
                    'ProductBrand': record.get('Product Brand', ''),
                    'Product Brand': record.get('Product Brand', ''),
                    'Vendor': record.get('Vendor/Supplier*', ''),
                    'Product Strain': record.get('Product Strain', ''),
                    'ProductStrain': record.get('Product Strain', ''),
                    'Price': record.get('Price', ''),
                    'DOH': record.get('DOH', ''),
                    'Ratio': record.get('Ratio', ''),
                    'Weight*': record.get('Weight*', ''),
                    'Units': record.get('Units', ''),
                    'WeightUnits': record.get('Units', ''),
                    'Description': record.get('Description', ''),
                    'DescAndWeight': f"{record.get('Product Name*', '')} - {record.get('Units', '')}",
                    'THC test result': record.get('THC test result', ''),
                    'CBD test result': record.get('CBD test result', ''),
                    'Test result unit (% or mg)': record.get('Test result unit (% or mg)', '%'),
                    'Quantity*': record.get('Quantity*', ''),
                    'Concentrate Type': record.get('Concentrate Type', ''),
                    'JointRatio': record.get('JointRatio', ''),
                    'Ratio_or_THC_CBD': record.get('Ratio_or_THC_CBD', ''),
                    'State': record.get('State', ''),
                    'Is Sample? (yes/no)': record.get('Is Sample? (yes/no)', ''),
                    'Is MJ product?(yes/no)': record.get('Is MJ product?(yes/no)', ''),
                    'Discountable? (yes/no)': record.get('Discountable? (yes/no)', ''),
                    'Room*': record.get('Room*', ''),
                    'Batch Number': record.get('Batch Number', ''),
                    'Lot Number': record.get('Lot Number', ''),
                    'Barcode*': record.get('Barcode*', ''),
                    'Medical Only (Yes/No)': record.get('Medical Only (Yes/No)', ''),
                    'Med Price': record.get('Med Price', ''),
                    'Expiration Date(YYYY-MM-DD)': record.get('Expiration Date(YYYY-MM-DD)', ''),
                    'Is Archived? (yes/no)': record.get('Is Archived? (yes/no)', ''),
                    'THC Per Serving': record.get('THC Per Serving', ''),
                    'Allergens': record.get('Allergens', ''),
                    'Solvent': record.get('Solvent', ''),
                    'Accepted Date': record.get('Accepted Date', ''),
                    'Internal Product Identifier': record.get('Internal Product Identifier', ''),
                    'Product Tags (comma separated)': record.get('Product Tags (comma separated)', ''),
                    'Image URL': record.get('Image URL', ''),
                    'Ingredients': record.get('Ingredients', ''),
                    'CombinedWeight': record.get('CombinedWeight', ''),
                    'Description_Complexity': record.get('Description_Complexity', ''),
                    'Total THC': record.get('Total THC', ''),
                    'THCA': record.get('THCA', ''),
                    'CBDA': record.get('CBDA', ''),
                    'CBN': record.get('CBN', ''),
                    'THC': record.get('THC', ''),
                    'CBD': record.get('CBD', ''),
                    'AI': record.get('Total THC', ''),
                    'AJ': record.get('THCA', ''),
                    'AK': record.get('CBDA', ''),
                    'ProductVendor': record.get('Vendor/Supplier*', ''),
                    'Quantity Received*': record.get('Quantity Received*', ''),
                    'Barcode': record.get('Barcode*', ''),
                    'Quantity': record.get('Quantity*', '')
                }
                template_records.append(template_record)
        
        logging.info(f"⚡ Optimized lookup: {len(template_records)} records")
        return template_records
        
    except Exception as e:
        logging.error(f"Optimized record lookup error: {e}")
        return []

def process_optimized_template(records, template_type, scale_factor):
    """Optimized template processing"""
    try:
        from src.core.generation.template_processor import TemplateProcessor
        from src.core.generation.font_scheme import get_font_scheme
        
        # Get font scheme
        font_scheme = get_font_scheme(template_type)
        
        # Create processor with minimal configuration
        processor = TemplateProcessor(template_type, font_scheme, scale_factor)
        
        # Process records with minimal post-processing
        final_doc = processor.process_records(records)
        
        return final_doc
        
    except Exception as e:
        logging.error(f"Optimized template processing error: {e}")
        return None

def generate_optimized_filename(template_type, tag_count):
    """Generate filename quickly"""
    from datetime import datetime
    
    today_str = datetime.now().strftime('%Y%m%d')
    time_str = datetime.now().strftime('%H%M%S')
    
    template_display = {
        'horizontal': 'HORIZ',
        'vertical': 'VERT', 
        'mini': 'MINI',
        'double': 'DOUBLE'
    }.get(template_type, template_type.upper())
    
    tag_suffix = "tag" if tag_count == 1 else "tags"
    filename = f"AGT_Optimized_{template_display}_{tag_count}{tag_suffix}_{today_str}_{time_str}.docx"
    
    return filename

# Export the function
__all__ = ['optimize_generation_endpoint']
