def build_context(record, doc, template_type='vertical'):
    """
    Build context dictionary for template rendering.
    
    Args:
        record: The data record to build context from
        doc: The document object
        template_type: Type of template ('vertical', 'horizontal', 'mini')
    
    Returns:
        Dictionary containing context data for template rendering
    """
    context = {}
    
    # Basic product information
    context['product_name'] = record.get('Product Name*', '')
    context['product_type'] = record.get('ProductType', '')
    context['product_brand'] = record.get('ProductBrand', '')
    context['product_strain'] = record.get('ProductStrain', '')
    
    # Pricing and weight
    context['price'] = record.get('Price', '')
    context['weight_units'] = record.get('WeightUnits', '')
    
    # Description and content
    context['description'] = record.get('Description', '')
    context['thc_cbd'] = record.get('THC_CBD', '')
    context['ratio_or_thc_cbd'] = record.get('Ratio_or_THC_CBD', '')
    
    # Lineage and DOH
    context['lineage'] = record.get('Lineage', '')
    context['doh'] = record.get('DOH', '')
    
    # Vendor information - only include for classic types
    product_type = record.get('Product Type*', '').lower()
    classic_types = ["flower", "pre-roll", "infused pre-roll", "concentrate", 
                    "solventless concentrate", "vape cartridge", "rso/co2 tankers"]
    
    if product_type in classic_types:
        context['vendor'] = record.get('Vendor', '')
    else:
        context['vendor'] = ''  # No vendor for non-classic types
    
    return context

def build_label_context(record):
    """
    Build context specifically for label generation.
    
    Args:
        record: The data record to build context from
    
    Returns:
        Dictionary containing label-specific context data
    """
    context = build_context(record, None)
    
    # Add label-specific formatting
    if context.get('price'):
        try:
            price_float = float(str(context['price']).replace('$', '').replace(',', ''))
            if price_float.is_integer():
                context['formatted_price'] = f"${int(price_float)}"
            else:
                context['formatted_price'] = f"${price_float:.2f}"
        except (ValueError, TypeError):
            context['formatted_price'] = str(context['price'])
    
    # Format description for label display
    if context.get('description'):
        context['formatted_description'] = context['description'][:100] + '...' if len(context['description']) > 100 else context['description']
    
    return context

def process_chunk(chunk, orientation='vertical', scale_factor=1.0):
    """
    Process a chunk of data for template rendering.
    
    Args:
        chunk: The data chunk to process
        orientation: Template orientation ('vertical', 'horizontal', 'mini')
        scale_factor: Font scaling factor
    
    Returns:
        Processed chunk data
    """
    if not chunk:
        return {}
    
    # Apply orientation-specific processing
    if orientation == 'mini':
        # Mini tags need compact formatting
        chunk['compact'] = True
        chunk['max_width'] = 30
    elif orientation == 'horizontal':
        # Horizontal tags can be wider
        chunk['compact'] = False
        chunk['max_width'] = 50
    else:  # vertical
        # Vertical tags are standard width
        chunk['compact'] = False
        chunk['max_width'] = 40
    
    # Apply scale factor
    chunk['scale_factor'] = scale_factor
    
    return chunk 