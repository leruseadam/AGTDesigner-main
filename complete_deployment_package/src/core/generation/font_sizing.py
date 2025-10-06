from docx.shared import Pt
import logging
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from src.core.utils.common import calculate_text_complexity

logger = logging.getLogger(__name__)

def _complexity(text):
    """Legacy complexity function - use calculate_text_complexity from common.py instead."""
    return calculate_text_complexity(text, 'standard')

# Legacy function - use calculate_text_complexity from common.py instead
def _description_complexity(text):
    """Legacy function - use calculate_text_complexity from common.py instead."""
    from src.core.utils.common import calculate_text_complexity
    return calculate_text_complexity(text, 'description')

def set_run_font_size(run, font_size):
    """Set font size for both the run and its XML element."""
    if not isinstance(font_size, Pt):
        logger.warning(f"Font size was not Pt: {font_size} (type: {type(font_size)}), converting to Pt.")
        font_size = Pt(font_size)
    run.font.size = font_size
    sz_val = str(int(font_size.pt * 2))
    rPr = run._element.get_or_add_rPr()
    sz = rPr.find(qn('w:sz'))
    if sz is None:
        sz = OxmlElement('w:sz')
        rPr.append(sz)
    sz.set(qn('w:val'), sz_val)
    logger.debug(f"Set font size to {font_size.pt}pt for text: {run.text}")

def get_thresholded_font_size(text, orientation='vertical', scale_factor=1.0, field_type='default'):
    """Get appropriate font size based on text length and field type.
    For ratio fields, use get_thresholded_font_size_ratio instead."""
    if not text:
        result = Pt(12 * scale_factor)
        logger.debug(f"get_thresholded_font_size: returning {result} (type: {type(result)}) for empty text")
        return result
    
    comp = _complexity(text)
    o = orientation.lower()
    
    # Handle different field types
    if field_type in ['weight', 'description', 'DescAndWeight']:
        # Unified logic for weight and description since they stay together
        if o == 'mini':
            if comp < 30:
                size = Pt(16 * scale_factor)
            elif comp < 40:
                size = Pt(15 * scale_factor)
            elif comp < 50:
                size = Pt(14 * scale_factor)
            elif comp < 70:
                size = Pt(13 * scale_factor)
            elif comp < 90:
                size = Pt(12 * scale_factor)
            elif comp < 100:
                size = Pt(11 * scale_factor)
            else:
                size = Pt(9 * scale_factor)
        elif o == 'vertical':
            if comp < 30:
                size = Pt(26 * scale_factor)
            elif comp < 60:
                size = Pt(24 * scale_factor)
            elif comp < 100:
                size = Pt(22 * scale_factor)
            elif comp < 140:
                size = Pt(18 * scale_factor)
            else:
                size = Pt(14 * scale_factor)
        elif o == 'horizontal':
            if comp < 20:
                size = Pt(36 * scale_factor)
            elif comp < 25:
                size = Pt(32 * scale_factor)
            elif comp < 30:
                size = Pt(28 * scale_factor)
            elif comp <40:
                size = Pt(24 * scale_factor)
            elif comp < 50:
                size = Pt(22 * scale_factor)
            elif comp < 60:
                size = Pt(20 * scale_factor)
            elif comp < 70:
                size = Pt(18 * scale_factor)
            else:
                size = Pt(14 * scale_factor)
        else:
            size = Pt(11 * scale_factor)

    elif field_type == 'brand':
        if o == 'mini':
            if comp < 10:
                size = Pt(14 * scale_factor)
            elif comp < 30:
                size = Pt(11 * scale_factor)
            elif comp < 40:
                size = Pt(8 * scale_factor)
            else:
                size = Pt(7 * scale_factor)
        elif o == 'vertical':
            if comp < 20:
                size = Pt(12 * scale_factor)
            elif comp < 30:
                size = Pt(10 * scale_factor)
            elif comp < 40:
                size = Pt(8 * scale_factor)
            else:
                size = Pt(11 * scale_factor)
        elif o == 'horizontal':
            # Special rule: If brand contains more than 20 letters, force font size to 14
            if len(text) > 20:
                size = Pt(14 * scale_factor)
            # Special rule: If brand contains multiple words and is greater than 9 characters, set font to 14
            elif len(text.split()) > 1 and len(text) > 9:
                size = Pt(14 * scale_factor)
            elif comp < 20:
                size = Pt(16 * scale_factor)
            elif comp < 40:
                size = Pt(14 * scale_factor)
            elif comp < 80:
                size = Pt(12 * scale_factor)
            else:
                size = Pt(10 * scale_factor)
        else:
            size = Pt(8 * scale_factor)

    elif field_type == 'price':
        if o == 'mini':
            if comp < 20:
                size = Pt(14 * scale_factor)
            elif comp < 30:
                size = Pt(12 * scale_factor)
            elif comp < 40:
                size = Pt(10 * scale_factor)
            else:
                size = Pt(8 * scale_factor)
        elif o == 'vertical':
            if comp < 10:
                size = Pt(30 * scale_factor)
            elif comp < 20:
                size = Pt(28 * scale_factor)
            elif comp < 30:
                size = Pt(26 * scale_factor)
            else:
                size = Pt(14 * scale_factor)
        elif o == 'horizontal':
            if comp < 20:
                size = Pt(36 * scale_factor)
            elif comp < 40:
                size = Pt(34 * scale_factor)
            elif comp < 80:
                size = Pt(32 * scale_factor)
            else:
                size = Pt(10 * scale_factor)
        else:
            size = Pt(28 * scale_factor)

    elif field_type == 'lineage':
        if o == 'mini':
            if comp < 20:
                size = Pt(12 * scale_factor)
            elif comp < 60:
                size = Pt(10 * scale_factor)
            elif comp < 100:
                size = Pt(8 * scale_factor)
            else:
                size = Pt(6 * scale_factor)
        elif o == 'vertical':
            if comp < 20:
                size = Pt(20 * scale_factor)
            elif comp < 60:
                size = Pt(18 * scale_factor)
            elif comp < 80:
                size = Pt(16 * scale_factor)
            else:
                size = Pt(8 * scale_factor)
        elif o == 'horizontal':
            if comp < 100:
                size = Pt(16 * scale_factor)
            elif comp < 140:
                size = Pt(14 * scale_factor)
            elif comp < 180:
                size = Pt(12 * scale_factor)
            else:
                size = Pt(10 * scale_factor)
        else:
            size = Pt(10 * scale_factor)

    else:
        # Default fallback
        size = Pt(12 * scale_factor)

    return size

def get_thresholded_font_size_brand(text, orientation='vertical', scale_factor=1.0):
    """Calculate font size for brand names."""
    logger.debug(f"Calculating brand font size: {text}")
    
    # Brand names typically need larger font sizes
    base_size = 14 if orientation == 'vertical' else 16
    min_size = 10 if orientation == 'vertical' else 12
    max_size = 20 if orientation == 'vertical' else 24
    
    # Calculate size based on length
    length = len(text)
    if length <= 10:
        size = base_size
    elif length <= 20:
        size = base_size - 2
    else:
        size = base_size - 4
    
    # Apply scale factor
    size = int(size * scale_factor)
    
    # Ensure size is within bounds
    size = max(min_size, min(size, max_size))
    
    final_size = Pt(size)
    logger.debug(f"Calculated brand font size: {final_size.pt}pt")
    return final_size

def get_thresholded_font_size_ratio(text, orientation='vertical', scale_factor=1.0):
    """Calculate appropriate font size for ratio text with multiple tiers."""
    logger.debug(f"Calculating ratio font size for: {text}")

    # Clean the text for analysis
    clean_text = text.replace('THC_CBD_START', '').replace('THC_CBD_END', '').replace('RATIO_START', '').replace('RATIO_END', '')
    clean_text = ' '.join(clean_text.split())
    
    # Base sizes by orientation
    if orientation == 'mini':
        base_size = 9
    elif orientation == 'vertical':
        base_size = 12
    elif orientation == 'horizontal':
        base_size = 14
    else:
        base_size = 12
    
    # Multiple tiers based on content type and length
    length = len(clean_text)
    
    # Tier 1: Very short ratio content (e.g., "1:1", "2:1")
    if length <= 5 and ':' in clean_text and any(c.isdigit() for c in clean_text):
        size = base_size + 1
    
    # Tier 2: Short ratio content (e.g., "1:1:1", "3:1:2")
    elif length <= 8 and ':' in clean_text and any(c.isdigit() for c in clean_text):
        size = base_size
    
    # Tier 3: Medium ratio content (e.g., "1:1:1:1", "5:2:1:1")
    elif length <= 12 and ':' in clean_text and any(c.isdigit() for c in clean_text):
        size = base_size - 2
    
    # Tier 4: Long ratio content (e.g., "10:5:2:1:1", "15:10:5:2:1")
    elif length <= 20 and ':' in clean_text and any(c.isdigit() for c in clean_text):
        size = base_size - 3
    
    # Tier 5: Very long ratio content
    elif length > 20 and ':' in clean_text and any(c.isdigit() for c in clean_text):
        size = base_size - 4
    
    # Tier 6: Other ratio-like content (fallback)
    else:
        size = base_size - 1
    
    # Ensure minimum size
    size = max(6, size)
    
    # Apply scale factor
    final_size = Pt(size * scale_factor)
    
    logger.debug(f"Final ratio font size: {final_size.pt}pt (tier based on length: {length})")
    return final_size

def get_thresholded_font_size_thc_cbd(text, orientation='vertical', scale_factor=1.0):
    """Calculate appropriate font size for THC/CBD text with multiple tiers."""
    logger.debug(f"Calculating THC/CBD font size for: {text}")

    # Clean the text for analysis
    clean_text = text.replace('THC_CBD_START', '').replace('THC_CBD_END', '').replace('RATIO_START', '').replace('RATIO_END', '')
    clean_text = ' '.join(clean_text.split())
    
    # Base sizes by orientation
    if orientation == 'mini':
        base_size = 9
    elif orientation == 'vertical':
        base_size = 10
    elif orientation == 'horizontal':
        base_size = 16
    else:
        base_size = 12
    
    # Multiple tiers based on content type and length
    length = len(clean_text)
    
    # Tier 1: Basic THC/CBD format (e.g., "THC: | BR | C")
    if 'THC:' in clean_text and 'CBD:' in clean_text and length <= 10:
        size = base_size + 1
    
    # Tier 2: THC/CBD with percentages (e.g., "THC: 25%\nCBD: 2%")
    elif 'THC:' in clean_text and 'CBD:' in clean_text and '%' in clean_text and length <= 20:
        size = base_size
    
    # Tier 3: THC/CBD with mg values (e.g., "THC: 100mg\nCBD: 10mg")
    elif 'THC:' in clean_text and 'CBD:' in clean_text and 'mg' in clean_text.lower() and length <= 25:
        size = base_size - 1
    
    # Tier 4: Complex THC/CBD with multiple cannabinoids (e.g., "THC: 25%\nCBD: 2%\nCBC: 1%")
    elif 'THC:' in clean_text and 'CBD:' in clean_text and length <= 35:
        size = base_size - 2
    
    # Tier 5: Very complex THC/CBD content
    elif 'THC:' in clean_text and 'CBD:' in clean_text and length > 35:
        size = base_size - 3
    
    # Tier 6: mg-only content (e.g., "100mg THC", "500mg CBD")
    elif 'mg' in clean_text.lower() and ('THC' in clean_text or 'CBD' in clean_text) and length <= 15:
        size = base_size
    
    # Tier 7: Long mg content
    elif 'mg' in clean_text.lower() and ('THC' in clean_text or 'CBD' in clean_text) and length > 15:
        size = base_size - 1
    
    # Tier 8: Other cannabinoid content (fallback)
    else:
        size = base_size - 1
    
    # Ensure minimum size
    size = max(6, size)
    
    # Apply scale factor
    final_size = Pt(size * scale_factor)
    
    logger.debug(f"Final THC/CBD font size: {final_size.pt}pt (tier based on length: {length})")
    return final_size

def get_thresholded_font_size_lineage(text, orientation='vertical', scale_factor=1.0):
    """Calculate a fixed font size for lineage text."""
    # Set a fixed font size for all lineage text
    fixed_size = 20  # Adjust this value as needed
    
    # Apply scale factor
    final_size = Pt(fixed_size * scale_factor)
    
    logger.debug(f"Applying fixed font size for lineage: {final_size.pt}pt")
    return final_size

def get_thresholded_font_size_description(text, orientation='vertical', scale_factor=1.0):
    """
    Calculate font size for description text with intelligent edge case handling.
    This function now has enhanced logic for various description types and edge cases.
    """
    logger.debug(f"Calculating description font size for: '{text}'")
    
    if not text or not text.strip():
        return Pt(12 * scale_factor)
    
    # Clean text for analysis
    clean_text = text.strip()
    words = clean_text.split()
    word_count = len(words)
    char_count = len(clean_text)
    
    # Special case for vertical template: if any word is longer than 9 characters, reduce font size
    if orientation == 'vertical' and words:
        max_word_length = max(len(word) for word in words)
        if max_word_length > 9:
            # Calculate appropriate font size based on the longest word
            if max_word_length <= 12:
                font_size = 24
            elif max_word_length <= 15:
                font_size = 20
            elif max_word_length <= 18:
                font_size = 16
            else:
                font_size = 12
            
            logger.debug(f"Long word detected in vertical template: max length {max_word_length} characters, using {font_size}pt font")
            return Pt(font_size * scale_factor)
    
    # Edge case: Very short descriptions (1-2 words)
    if word_count <= 2:
        if char_count <= 10:
            # Very short text gets larger font
            base_size = 24 if orientation == 'horizontal' else 18 if orientation == 'vertical' else 16
            return Pt(base_size * scale_factor)
        elif char_count <= 20:
            # Short text gets medium font
            base_size = 20 if orientation == 'horizontal' else 16 if orientation == 'vertical' else 14
            return Pt(base_size * scale_factor)
    
    # Edge case: All caps text (often product names)
    if clean_text.isupper() and word_count > 1:
        # All caps text needs smaller font due to visual weight
        comp = _description_complexity(text)
        o = orientation.lower()
        
        if o == 'mini':
            if comp < 40:
                size = Pt(14 * scale_factor)
            elif comp < 60:
                size = Pt(12 * scale_factor)
            elif comp < 80:
                size = Pt(10 * scale_factor)
            else:
                size = Pt(8 * scale_factor)
        elif o == 'vertical':
            if comp < 40:
                size = Pt(32 * scale_factor)
            elif comp < 80:
                size = Pt(28 * scale_factor)
            elif comp < 120:
                size = Pt(26 * scale_factor)
            else:
                size = Pt(18 * scale_factor)
        elif o == 'horizontal':
            if comp < 30:
                size = Pt(28 * scale_factor)
            elif comp < 50:
                size = Pt(24 * scale_factor)
            elif comp < 70:
                size = Pt(20 * scale_factor)
            else:
                size = Pt(16 * scale_factor)
        else:
            size = Pt(12 * scale_factor)
        
        logger.debug(f"All caps description font size: {size.pt}pt for text: {text}")
        return size
    
    # Edge case: Text with many numbers (product codes, measurements)
    digit_count = sum(1 for char in clean_text if char.isdigit())
    if digit_count > len(clean_text) * 0.3:  # More than 30% digits
        comp = _description_complexity(text)
        o = orientation.lower()
        
        if o == 'mini':
            if comp < 50:
                size = Pt(12 * scale_factor)
            elif comp < 80:
                size = Pt(10 * scale_factor)
            else:
                size = Pt(8 * scale_factor)
        elif o == 'vertical':
            if comp < 60:
                size = Pt(14 * scale_factor)
            elif comp < 100:
                size = Pt(12 * scale_factor)
            else:
                size = Pt(10 * scale_factor)
        elif o == 'horizontal':
            if comp < 40:
                size = Pt(24 * scale_factor)
            elif comp < 60:
                size = Pt(20 * scale_factor)
            else:
                size = Pt(16 * scale_factor)
        else:
            size = Pt(12 * scale_factor)
        
        logger.debug(f"High-digit description font size: {size.pt}pt for text: {text}")
        return size
    
    # Edge case: Text with line breaks (multi-line descriptions)
    if '\n' in clean_text:
        lines = clean_text.split('\n')
        max_line_length = max(len(line.strip()) for line in lines)
        line_count = len(lines)
        
        # Multi-line text needs smaller font
        if line_count == 2:
            if max_line_length <= 20:
                base_size = 18 if orientation == 'horizontal' else 14 if orientation == 'vertical' else 12
            else:
                base_size = 16 if orientation == 'horizontal' else 12 if orientation == 'vertical' else 10
        else:  # 3+ lines
            if max_line_length <= 15:
                base_size = 14 if orientation == 'horizontal' else 12 if orientation == 'vertical' else 10
            else:
                base_size = 12 if orientation == 'horizontal' else 10 if orientation == 'vertical' else 8
        
        size = Pt(base_size * scale_factor)
        logger.debug(f"Multi-line description font size: {size.pt}pt for {line_count} lines")
        return size
    
    # Edge case: Very long single words (URLs, long product names)
    max_word_length = max((len(word) for word in words), default=0)
    if max_word_length > 20:
        comp = _description_complexity(text)
        o = orientation.lower()
        
        if o == 'mini':
            if comp < 60:
                size = Pt(10 * scale_factor)
            elif comp < 100:
                size = Pt(8 * scale_factor)
            else:
                size = Pt(6 * scale_factor)
        elif o == 'vertical':
            if comp < 80:
                size = Pt(12 * scale_factor)
            elif comp < 120:
                size = Pt(10 * scale_factor)
            else:
                size = Pt(8 * scale_factor)
        elif o == 'horizontal':
            if comp < 50:
                size = Pt(20 * scale_factor)
            elif comp < 80:
                size = Pt(16 * scale_factor)
            else:
                size = Pt(12 * scale_factor)
        else:
            size = Pt(10 * scale_factor)
        
        logger.debug(f"Long word description font size: {size.pt}pt for text: {text}")
        return size
    
    # Standard complexity-based sizing for normal descriptions
    comp = _description_complexity(text)
    o = orientation.lower()
    
    # Enhanced thresholds with better edge case handling
    if o == 'mini':
        if comp < 25:
            size = Pt(16 * scale_factor)
        elif comp < 35:
            size = Pt(15 * scale_factor)
        elif comp < 45:
            size = Pt(14 * scale_factor)
        elif comp < 60:
            size = Pt(13 * scale_factor)
        elif comp < 80:
            size = Pt(12 * scale_factor)
        elif comp < 100:
            size = Pt(11 * scale_factor)
        elif comp < 120:
            size = Pt(10 * scale_factor)
        else:
            size = Pt(9 * scale_factor)
    elif o == 'vertical':
        if comp < 25:
            size = Pt(28 * scale_factor)
        elif comp < 50:
            size = Pt(26 * scale_factor)
        elif comp < 80:
            size = Pt(24 * scale_factor)
        elif comp < 120:
            size = Pt(22 * scale_factor)
        elif comp < 160:
            size = Pt(20 * scale_factor)
        elif comp < 200:
            size = Pt(16 * scale_factor)
        else:
            size = Pt(10 * scale_factor)
    elif o == 'horizontal':
        if comp < 15:
            size = Pt(36 * scale_factor)
        elif comp < 25:
            size = Pt(32 * scale_factor)
        elif comp < 35:
            size = Pt(28 * scale_factor)
        elif comp < 45:
            size = Pt(24 * scale_factor)
        elif comp < 55:
            size = Pt(22 * scale_factor)
        elif comp < 70:
            size = Pt(20 * scale_factor)
        elif comp < 85:
            size = Pt(18 * scale_factor)
        elif comp < 100:
            size = Pt(16 * scale_factor)
        elif comp < 120:
            size = Pt(14 * scale_factor)
        else:
            size = Pt(12 * scale_factor)
    else:
        size = Pt(12 * scale_factor)
    
    logger.debug(f"Standard description font size: {size.pt}pt for text: {text} (complexity: {comp})")
    return size

def get_thresholded_font_size_price(*args, **kwargs):
    raise RuntimeError("[DEPRECATED] get_thresholded_font_size_price is disabled. Use src.core.generation.unified_font_sizing.get_font_size instead.")

def get_thresholded_font_size_by_word_count(text, orientation='vertical', scale_factor=1.0):
    """Wrapper function for backward compatibility."""
    return get_thresholded_font_size(text, orientation, scale_factor, 'default')

def get_font_size(text, font_params, scale_factor=1.0):
    """Calculate font size based on text length and font parameters."""
    # DEPRECATED: This function is disabled. Use src.core.generation.unified_font_sizing.get_font_size instead.
    raise RuntimeError("[DEPRECATED] get_font_size from font_sizing.py is disabled. Use src.core.generation.unified_font_sizing.get_font_size instead.")
    
    # Original code (disabled):
    # length = len(text)
    # base_size = font_params["base_size"]
    # max_length = font_params["max_length"]
    # min_size = font_params["min_size"]
    # return Pt(base_size) if length <= max_length else Pt(max(min_size, base_size * (max_length / length)))

def get_thresholded_font_size_strain(text, orientation='vertical', scale_factor=1.0):
    """Calculate font size for product strain text with consistent sizing."""
    # Always return 1pt to make Product Strain nearly invisible
    return Pt(1) 

def get_thresholded_font_size_thc_cbd_label(text, orientation='vertical', scale_factor=1.0):
    """Font size for the 'THC: | BR | C' label, separate from Ratio and THC_CBD content."""
    if orientation == 'mini':
        base_size = 8
    if orientation == 'vertical':
        base_size = 10
    else:
        base_size = 16
    return Pt(base_size * scale_factor) 

# DEPRECATED: Use get_font_size from unified_font_sizing.py for all ratio font sizing.
def get_thresholded_font_size_ratio(*args, **kwargs):
    from src.core.generation.unified_font_sizing import get_font_size
    return get_font_size(*args, field_type='ratio', **kwargs) 
