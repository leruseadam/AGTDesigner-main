#!/usr/bin/env python3
"""
Common utility functions used across the application.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Constants
WORD_WEIGHT = 2

def calculate_text_complexity(text: str, complexity_type: str = 'standard') -> float:
    """
    Unified text complexity calculation function.
    
    Args:
        text: The text to analyze
        complexity_type: Type of complexity calculation ('standard', 'description', 'mini')
    
    Returns:
        Complexity score as float
    """
    if not text:
        return 0.0
    
    text = str(text or "")
    
    if complexity_type == 'mini':
        return _calculate_mini_complexity(text)
    elif complexity_type == 'description':
        return _calculate_description_complexity(text)
    else:
        return _calculate_standard_complexity(text)

def _calculate_standard_complexity(text: str) -> float:
    """Standard complexity calculation combining character count, word count, and long word penalty."""
    words = text.split()
    char_count = len(text)
    word_count = len(words)
    
    # Penalty for long words
    max_word_length = max((len(word) for word in words), default=0)
    long_word_penalty = max(0, max_word_length - 12) * 2  # 2 points per char over 12
    
    return char_count + word_count * WORD_WEIGHT + long_word_penalty

def _calculate_mini_complexity(text: str) -> float:
    """Complexity calculation optimized for mini tags (small spaces)."""
    # Remove common symbols and normalize
    clean_text = re.sub(r'[^\w\s]', '', text)
    words = clean_text.split()
    
    # For mini tags, we care more about character count than word count
    char_count = len(clean_text)
    word_count = len(words)
    
    # Weighted complexity calculation for mini tags
    complexity = (char_count * 0.7) + (word_count * 0.3)
    
    # Additional penalty for very long words
    if words:
        max_word_length = max(len(word) for word in words)
        if max_word_length > 12:
            complexity += (max_word_length - 12) * 2
    
    return complexity

def _calculate_description_complexity(text: str) -> float:
    """Enhanced complexity calculation specifically for descriptions with edge case handling."""
    # Handle empty or whitespace-only text
    if not text.strip():
        return 0.0
    
    # Clean text for analysis
    clean_text = text.strip()
    words = clean_text.split()
    char_count = len(clean_text)
    word_count = len(words)
    
    # Edge case: Very short descriptions (1-3 words)
    if word_count <= 3:
        return char_count + word_count * 1.5  # Less penalty for short descriptions
    
    # Edge case: Very long single words (like URLs, long product names)
    max_word_length = max((len(word) for word in words), default=0)
    if max_word_length > 20:  # Very long words
        long_word_penalty = max(0, max_word_length - 15) * 3  # Higher penalty for very long words
    else:
        long_word_penalty = max(0, max_word_length - 12) * 2  # Normal penalty
    
    # Edge case: All caps text (often product names or emphasis)
    if clean_text.isupper() and word_count > 1:
        caps_penalty = char_count * 0.3  # Penalty for all caps
    else:
        caps_penalty = 0
    
    # Edge case: Text with many numbers (often product codes, measurements)
    digit_count = sum(1 for char in clean_text if char.isdigit())
    if digit_count > len(clean_text) * 0.3:  # More than 30% digits
        digit_penalty = digit_count * 0.5
    else:
        digit_penalty = 0
    
    # Edge case: Text with special characters (often product codes, measurements)
    special_chars = sum(1 for char in clean_text if not char.isalnum() and not char.isspace())
    if special_chars > len(clean_text) * 0.2:  # More than 20% special chars
        special_penalty = special_chars * 0.3
    else:
        special_penalty = 0
    
    # Edge case: Text with line breaks or multiple sentences
    line_count = clean_text.count('\n') + 1
    if line_count > 1:
        line_penalty = (line_count - 1) * 5  # Penalty for multiple lines
    else:
        line_penalty = 0
    
    # Edge case: Very dense text (lots of characters in few words)
    if word_count > 0:
        density_ratio = char_count / word_count
        if density_ratio > 8:  # Very dense text
            density_penalty = (density_ratio - 8) * 2
        else:
            density_penalty = 0
    else:
        density_penalty = 0
    
    # Calculate final complexity
    base_complexity = char_count + word_count * WORD_WEIGHT
    total_complexity = base_complexity + long_word_penalty + caps_penalty + digit_penalty + special_penalty + line_penalty + density_penalty
    
    logger.debug(f"Description complexity breakdown for '{text}': "
                f"base={base_complexity}, long_word={long_word_penalty}, "
                f"caps={caps_penalty}, digit={digit_penalty}, special={special_penalty}, "
                f"line={line_penalty}, density={density_penalty}, total={total_complexity}")
    
    return total_complexity

# Legacy function for backward compatibility
def _complexity(text: str) -> float:
    """Legacy complexity function - use calculate_text_complexity instead."""
    return calculate_text_complexity(text, 'standard')

def safe_get(obj, key, default=None):
    """
    Safely get a value from an object using a key, with a default value if the key doesn't exist.
    
    Args:
        obj: The object to get the value from
        key: The key to look up
        default: The default value to return if the key doesn't exist
        
    Returns:
        The value if found, otherwise the default value
    """
    try:
        return obj.get(key, default)
    except (AttributeError, TypeError):
        return default 

def cell_contains_doh_image(cell):
    """
    Check if a cell contains a DOH image.
    This utility function can be imported by multiple modules.
    
    Args:
        cell: The table cell to check
        
    Returns:
        bool: True if the cell contains a DOH image, False otherwise
    """
    try:
        from docx.oxml.ns import qn
        
        # Check all paragraphs in the cell for drawing elements (InlineImage)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                if hasattr(run, '_element'):
                    # Check for drawing elements (InlineImage) or picture elements
                    if (run._element.find(qn('w:drawing')) is not None or 
                        run._element.find(qn('w:pict')) is not None):
                        return True
        return False
    except Exception as e:
        logger.warning(f"Error checking for DOH image in cell: {e}")
        return False 