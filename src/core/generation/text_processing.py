import re
from typing import Optional

# Performance optimization: disable debug logging in production
DEBUG_ENABLED = False

def format_thc_cbd_percentages(text):
    """
    Output the exact, unrounded THC and CBD percentage values from the input, with no custom formatting or rounding logic.
    """
    if not text:
        return text
    text = str(text).strip()
    # Replace THC value with 1 decimal place (if present)
    def replace_thc(match):
        value = match.group(1)
        unit = match.group(2) or ''
        try:
            value_float = float(value)
            value_str = f"{value_float:.1f}"
        except Exception:
            value_str = value
        return f"THC: {value_str}{unit}"
    text = re.sub(r'THC[:\s]*([0-9.]+)(%|mg)?', replace_thc, text, flags=re.IGNORECASE)
    # Replace CBD value with 1 decimal place (if present)
    def replace_cbd(match):
        value = match.group(1)
        unit = match.group(2) or ''
        try:
            value_float = float(value)
            value_str = f"{value_float:.1f}"
        except Exception:
            value_str = value
        return f"CBD: {value_str}{unit}"
    text = re.sub(r'CBD[:\s]*([0-9.]+)(%|mg)?', replace_cbd, text, flags=re.IGNORECASE)
    return text

def insert_newline_every_2nd_space(text):
    """Insert a newline after every 2nd space in the text."""
    if not text:
        return text
    
    words = text.split()
    if len(words) <= 2:
        return text
    
    result = []
    for i, word in enumerate(words):
        result.append(word)
        # Add newline after every 2nd word (except the last word)
        if (i + 1) % 2 == 0 and i < len(words) - 1:
            result.append('\n')
        elif i < len(words) - 1:
            result.append(' ')
    
    return ''.join(result)

def format_ratio_multiline(text):
    """Format ratio text into clean content without markers. Inserts a newline after every 2nd word."""
    if not isinstance(text, str):
        return ""
    
    # First remove all markers completely
    content = text.replace('THC_CBD_START', '').replace('THC_CBD_END', '')
    content = content.replace('RATIO_START', '').replace('RATIO_END', '')
    
    # Clean up whitespace
    content = ' '.join(content.split())
    
    # Handle special cases - but don't filter out single words like "THC"
    if not content:
        return ""
    
    # Handle THC:/CBD: format - keep on same line
    if 'THC:' in content and 'CBD:' in content:
        # Keep THC and CBD on the same line without line breaks
        pass
    
    # Handle mg values consistently
    if 'mg' in content.lower():
        parts = []
        current_part = []
        for word in content.split():
            word = word.strip()
            if 'mg' in word.lower():
                if current_part:
                    parts.append(' '.join(current_part))
                    current_part = []
                parts.append(word)
            else:
                current_part.append(word)
        if current_part:
            parts.append(' '.join(current_part))
        content = ' '.join(parts)
    
    # Handle ratio format (e.g. "1:1:1", "1:1") - add spaces around colons but don't add line breaks
    if ':' in content and any(c.isdigit() for c in content):
        # Add spaces around colons for better readability
        # Handle 3-part ratios first to avoid conflicts
        content = re.sub(r'(\d+):(\d+):(\d+)', r'\1: \2: \3', content)
        # Then handle 2-part ratios
        content = re.sub(r'(\d+):(\d+)', r'\1: \2', content)
        # For ratio formats, don't add line breaks - keep on same line
        return content.strip()
    
    # Apply the automatic line break insertion - insert newline after every 2nd word
    content = insert_newline_every_2nd_space(content)
    
    return content.strip()

def format_cannabinoid_content(text):
    """Format cannabinoid content text."""
    if not text:
        return ""
    
    text = str(text).strip()
    
    # Handle common patterns
    if 'mg' in text.lower():
        # Ensure proper spacing around mg values
        text = re.sub(r'(\d+)mg', r'\1 mg', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s+mg', r'\1 mg', text, flags=re.IGNORECASE)
    
    return text

def format_description_text(text, max_width=40):
    """Format description text with proper wrapping and line breaks."""
    if not text:
        return ""
    
    # Split text into words
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        # Check if adding this word would exceed max width
        if current_length + len(word) + 1 > max_width:
            # Start a new line
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            # Add to current line
            current_line.append(word)
            current_length += len(word) + 1
    
    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def format_price(price):
    """Format price value."""
    if not price:
        return ""
    
    try:
        # Convert to float and format
        price_float = float(str(price).replace('$', '').replace(',', ''))
        if price_float.is_integer():
            return f"${int(price_float)}"
        else:
            return f"${price_float:.2f}"
    except (ValueError, TypeError):
        return str(price).strip()

def remove_marker(value):
    """Remove markers from a value."""
    if not value:
        return ""
    
    text = str(value)
    
    # Remove common markers
    markers = ['THC_CBD_START', 'THC_CBD_END', 'RATIO_START', 'RATIO_END']
    for marker in markers:
        text = text.replace(marker, '')
    
    return text.strip()

def safe_get(record, key, default=''):
    """Safely get a value from a record, handling None and NaN cases."""
    if isinstance(record, dict):
        value = record.get(key, default)
    else:
        value = getattr(record, key, default)
    if value is None or str(value).strip().lower() == 'nan':
        return default
    return str(value).strip()

def safe_get_text(value):
    """Safely get text from a value, handling None and NaN cases."""
    if value is None or str(value).strip().lower() == 'nan':
        return ''
    if isinstance(value, dict):
        return value.get('text', '')
    return str(value).strip()

def fix_description_spacing(desc: str) -> str:
    """Fix spacing issues in description text."""
    if not desc:
        return ""
    
    # Remove extra whitespace
    desc = ' '.join(desc.split())
    
    # Fix common spacing issues
    desc = re.sub(r'\s+', ' ', desc)
    desc = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', desc)
    
    return desc.strip()

def make_nonbreaking_hyphens(text):
    """
    Convert regular hyphens to non-breaking hyphens in text.
    This prevents line breaks at hyphenated words.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Replace regular hyphens with non-breaking hyphens
    # Use Unicode non-breaking hyphen (U+2011)
    text = text.replace('-', '\u2011')
    
    return text

def replace_placeholder_with_markers(doc, placeholder, marker_value):
    """Replace placeholder text with marked content in a document."""
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    full_text = ''.join(run.text for run in para.runs)
                    if placeholder in full_text:
                        # Extract marker type from marker_value
                        match = re.match(r'(\w+)_START.*?(\1)_END', marker_value)
                        if match:
                            marker_type = match.group(1)
                            # Extract content between markers
                            content = re.search(f'{marker_type}_START(.*?){marker_type}_END', marker_value)
                            if content:
                                # Clear existing runs
                                for run in para.runs:
                                    run.text = ''
                                # Set new content
                                para.runs[0].text = content.group(1)

def process_doh_image(doh_value, product_type):
    """
    Determine the correct DOH image path based on product type.
    Returns the image path or an empty string.
    """
    import os
    from src.core.utils import resource_path
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.warning(f"process_doh_image called with doh_value='{doh_value}', product_type='{product_type}'")
        if str(doh_value).upper() == 'YES':
            # Get DOH image path
            doh_image_path = resource_path(os.path.join("templates", "DOH.png"))
            high_cbd_image_path = resource_path(os.path.join("templates", "HighCBD.png"))

            # Use HighCBD.png if product_type contains 'high cbd' (case-insensitive)
            if 'high cbd' in str(product_type).strip().lower():
                logger.warning(f"Using HighCBD image for product type '{product_type}': {high_cbd_image_path}")
                return high_cbd_image_path
            else:
                logger.warning(f"Using DOH image for product type '{product_type}': {doh_image_path}")
                return doh_image_path
        else:
            logger.warning("Skipping DOH image - value is not 'YES'")
            return ""
    except Exception as e:
        logger.error(f"Error processing DOH image path: {str(e)}")
        return "" 

def format_thc_cbd_bold_labels(text, template_type='vertical'):
    """
    Format THC/CBD values with bold labels.
    For vertical/double templates: separate lines with indented values
    For horizontal template: same line format
    """
    if not text:
        return ""
    
    text = str(text).strip()
    
    # Handle the default placeholder format
    if text == "THC: | BR | C":
        if template_type == 'horizontal':
            return "THC:   CBD:"
        else:
            return "THC:\n   \nCBD:\n   "
    
    # Extract THC and CBD values using regex
    import re
    
    # Pattern to match THC and CBD values with percentages or mg
    thc_match = re.search(r'THC[:\s]*([0-9.]+)(%|mg)?', text, re.IGNORECASE)
    cbd_match = re.search(r'CBD[:\s]*([0-9.]+)(%|mg)?', text, re.IGNORECASE)
    
    thc_value = thc_match.group(1) if thc_match else ""
    thc_unit = thc_match.group(2) if thc_match else ""
    cbd_value = cbd_match.group(1) if cbd_match else ""
    cbd_unit = cbd_match.group(2) if cbd_match else ""
    
    # Format based on template type
    if template_type == 'horizontal':
        # Horizontal template: keep on same line
        result = []
        if thc_value:
            result.append(f"THC: {thc_value}{thc_unit}")
        else:
            result.append("THC:")
        
        if cbd_value:
            result.append(f"CBD: {cbd_value}{cbd_unit}")
        else:
            result.append("CBD:")
        
        return "  ".join(result)
    elif template_type == 'mini':
        # Mini template: format like the example with THC and CBD on separate lines
        result = []
        
        if thc_value and cbd_value:
            # THC on first line, value on second line
            result.append("THC:")
            # Add three spaces before the percentage value if the unit is '%'
            if thc_unit == '%':
                result.append(f"   {thc_value}{thc_unit}")
            else:
                result.append(f"{thc_value}{thc_unit}")
            # CBD on third line, value on fourth line
            result.append("CBD:")
            # Add three spaces before the percentage value if the unit is '%'
            if cbd_unit == '%':
                result.append(f"   {cbd_value}{cbd_unit}")
            else:
                result.append(f"{cbd_value}{cbd_unit}")
        elif thc_value:
            result.append("THC:")
            if thc_unit == '%':
                result.append(f"   {thc_value}{thc_unit}")
            else:
                result.append(f"{thc_value}{thc_unit}")
        elif cbd_value:
            result.append("CBD:")
            if cbd_unit == '%':
                result.append(f"   {cbd_value}{cbd_unit}")
            else:
                result.append(f"{cbd_value}{cbd_unit}")
        else:
            result.append("THC:")
            result.append("")
            result.append("CBD:")
            result.append("")
        
        return "\n".join(result)
    else:
        # Vertical/double templates: THC and CBD on separate lines with line break after percentage
        result = []
        
        if thc_value:
            result.append(f"THC: {thc_value}{thc_unit}")
        else:
            result.append("THC:")
        
        if cbd_value:
            result.append(f"CBD: {cbd_value}{cbd_unit}")
        else:
            result.append("CBD:")
        
        return "\n".join(result) 