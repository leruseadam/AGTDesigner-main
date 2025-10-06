#!/usr/bin/env python3
"""
Fast Tag Generator for Custom PythonAnywhere Plan
Optimized for 6 web workers, 20GB disk, Postgres database
"""

import os
import time
import logging
import threading
from functools import wraps
from flask import Flask, request, jsonify, session
from io import BytesIO
from datetime import datetime
import pandas as pd

def fast_generation_monitor(func):
    """Performance monitor for fast generation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log performance metrics
        if execution_time > 1.0:  # Log operations > 1 second
            logging.info(f"⚡ {func.__name__}: {execution_time:.2f}s")
        
        return result
    return wrapper

def create_fast_tag_generator(app):
    """Create fast tag generation endpoints"""
    
    @app.route('/api/generate-fast', methods=['POST'])
    @fast_generation_monitor
    def generate_labels_fast():
        """Fast label generation - optimized for custom plan"""
        try:
            start_time = time.time()
            
            data = request.get_json()
            template_type = data.get('template_type', 'vertical')
            scale_factor = float(data.get('scale_factor', 1.0))
            selected_tags = data.get('selected_tags', [])
            
            if not selected_tags:
                return jsonify({'error': 'No tags selected'}), 400
            
            logging.info(f"⚡ Fast generation: {len(selected_tags)} tags, {template_type} template")
            
            # Fast database lookup
            records = get_fast_records(selected_tags)
            if not records:
                return jsonify({'error': 'No records found for selected tags'}), 400
            
            # Fast template processing
            final_doc = process_fast_template(records, template_type, scale_factor)
            if final_doc is None:
                return jsonify({'error': 'Failed to generate document'}), 500
            
            # Fast document saving
            output_buffer = BytesIO()
            final_doc.save(output_buffer)
            output_buffer.seek(0)
            
            # Generate filename
            filename = generate_fast_filename(template_type, len(records))
            
            # Create response
            from flask import send_file
            response = send_file(
                output_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            generation_time = time.time() - start_time
            logging.info(f"⚡ Fast generation complete: {generation_time:.2f}s")
            
            return response
            
        except Exception as e:
            logging.error(f"Fast generation error: {e}")
            return jsonify({'error': f'Generation failed: {str(e)}'}), 500
    
    @app.route('/api/generate-parallel', methods=['POST'])
    @fast_generation_monitor
    def generate_labels_parallel():
        """Parallel label generation - uses multiple workers"""
        try:
            start_time = time.time()
            
            data = request.get_json()
            template_type = data.get('template_type', 'vertical')
            scale_factor = float(data.get('scale_factor', 1.0))
            selected_tags = data.get('selected_tags', [])
            
            if not selected_tags:
                return jsonify({'error': 'No tags selected'}), 400
            
            logging.info(f"⚡ Parallel generation: {len(selected_tags)} tags, {template_type} template")
            
            # Parallel processing for large tag sets
            if len(selected_tags) > 50:
                records = get_parallel_records(selected_tags)
            else:
                records = get_fast_records(selected_tags)
            
            if not records:
                return jsonify({'error': 'No records found for selected tags'}), 400
            
            # Parallel template processing
            final_doc = process_parallel_template(records, template_type, scale_factor)
            if final_doc is None:
                return jsonify({'error': 'Failed to generate document'}), 500
            
            # Fast document saving
            output_buffer = BytesIO()
            final_doc.save(output_buffer)
            output_buffer.seek(0)
            
            # Generate filename
            filename = generate_fast_filename(template_type, len(records))
            
            # Create response
            from flask import send_file
            response = send_file(
                output_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            generation_time = time.time() - start_time
            logging.info(f"⚡ Parallel generation complete: {generation_time:.2f}s")
            
            return response
            
        except Exception as e:
            logging.error(f"Parallel generation error: {e}")
            return jsonify({'error': f'Generation failed: {str(e)}'}), 500
    
    return app

def get_fast_records(selected_tags):
    """Fast database record lookup"""
    try:
        from src.core.data.product_database import get_product_database
        
        current_store = session.get('selected_store', 'AGT_Bothell')
        product_db = get_product_database(current_store)
        
        if not product_db:
            return []
        
        # Fast batch lookup
        records = product_db.get_products_by_names(selected_tags)
        
        # Convert to template format efficiently
        template_records = []
        for record in records:
            if record.get('Product Name*'):
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
        
        logging.info(f"⚡ Fast lookup: {len(template_records)} records")
        return template_records
        
    except Exception as e:
        logging.error(f"Fast record lookup error: {e}")
        return []

def get_parallel_records(selected_tags):
    """Parallel record lookup for large tag sets"""
    try:
        import multiprocessing
        
        # Split tags into chunks for parallel processing
        chunk_size = max(1, len(selected_tags) // 6)  # Use 6 workers
        tag_chunks = [selected_tags[i:i + chunk_size] for i in range(0, len(selected_tags), chunk_size)]
        
        # Process chunks in parallel
        with multiprocessing.Pool(processes=6) as pool:
            chunk_results = pool.map(get_fast_records, tag_chunks)
        
        # Combine results
        all_records = []
        for chunk_records in chunk_results:
            all_records.extend(chunk_records)
        
        logging.info(f"⚡ Parallel lookup: {len(all_records)} records")
        return all_records
        
    except Exception as e:
        logging.error(f"Parallel record lookup error: {e}")
        return get_fast_records(selected_tags)  # Fallback to fast lookup

def process_fast_template(records, template_type, scale_factor):
    """Fast template processing"""
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
        logging.error(f"Fast template processing error: {e}")
        return None

def process_parallel_template(records, template_type, scale_factor):
    """Parallel template processing for large record sets"""
    try:
        import multiprocessing
        
        # Split records into chunks for parallel processing
        chunk_size = max(1, len(records) // 6)  # Use 6 workers
        record_chunks = [records[i:i + chunk_size] for i in range(0, len(records), chunk_size)]
        
        # Process chunks in parallel
        with multiprocessing.Pool(processes=6) as pool:
            chunk_docs = pool.starmap(process_fast_template, 
                                    [(chunk, template_type, scale_factor) for chunk in record_chunks])
        
        # Combine documents
        if chunk_docs:
            from src.core.generation.tag_generator import combine_documents
            final_doc = combine_documents([doc for doc in chunk_docs if doc])
            return final_doc
        
        return None
        
    except Exception as e:
        logging.error(f"Parallel template processing error: {e}")
        return process_fast_template(records, template_type, scale_factor)  # Fallback

def generate_fast_filename(template_type, tag_count):
    """Generate filename quickly"""
    today_str = datetime.now().strftime('%Y%m%d')
    time_str = datetime.now().strftime('%H%M%S')
    
    template_display = {
        'horizontal': 'HORIZ',
        'vertical': 'VERT', 
        'mini': 'MINI',
        'double': 'DOUBLE'
    }.get(template_type, template_type.upper())
    
    tag_suffix = "tag" if tag_count == 1 else "tags"
    filename = f"AGT_Fast_{template_display}_{tag_count}{tag_suffix}_{today_str}_{time_str}.docx"
    
    return filename

# Export the function
__all__ = ['create_fast_tag_generator']
