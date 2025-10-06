"""
PythonAnywhere-specific configuration
Handles missing dependencies gracefully
"""

import os
import logging

# Check for missing dependencies and provide fallbacks
MISSING_DEPENDENCIES = []

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False
    MISSING_DEPENDENCIES.append('jellyfish')
    logging.warning("jellyfish not available - using fallback functions")

try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    MISSING_DEPENDENCIES.append('python-Levenshtein')
    logging.warning("python-Levenshtein not available - using fallback functions")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    MISSING_DEPENDENCIES.append('psutil')
    logging.warning("psutil not available - memory monitoring disabled")

# Fallback functions for missing dependencies
def jaro_winkler_similarity_fallback(s1, s2):
    """Fallback Jaro-Winkler similarity when jellyfish is not available."""
    if not s1 or not s2:
        return 0.0
    
    # Simple character-based similarity
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    
    # Basic character overlap
    common_chars = set(s1) & set(s2)
    if not common_chars:
        return 0.0
    
    # Simple similarity calculation
    max_len = max(len(s1), len(s2))
    return len(common_chars) / max_len

def levenshtein_distance_fallback(s1, s2):
    """Fallback Levenshtein distance when python-Levenshtein is not available."""
    if not s1 or not s2:
        return max(len(s1), len(s2))
    
    # Simple implementation
    if s1 == s2:
        return 0
    
    # Basic character difference
    return abs(len(s1) - len(s2)) + sum(c1 != c2 for c1, c2 in zip(s1, s2))

def get_memory_usage_fallback():
    """Fallback memory usage when psutil is not available."""
    return 0

# PythonAnywhere-specific settings
PYTHONANYWHERE_CONFIG = {
    'debug': False,
    'testing': False,
    'max_content_length': 50 * 1024 * 1024,  # 50MB
    'chunk_size_limit': 10,
    'max_processing_time_per_chunk': 15,
    'max_total_processing_time': 120,
    'enable_compression': True,
    'enable_caching': True,
    'cache_ttl': 300,  # 5 minutes
    'missing_dependencies': MISSING_DEPENDENCIES,
    'disable_product_db_integration': True,  # Disable for performance
    'enable_fast_mode': True  # Enable all performance optimizations
}

def get_pythonanywhere_config():
    """Get PythonAnywhere-specific configuration."""
    return PYTHONANYWHERE_CONFIG

def log_missing_dependencies():
    """Log information about missing dependencies."""
    if MISSING_DEPENDENCIES:
        logging.warning(f"Missing dependencies on PythonAnywhere: {', '.join(MISSING_DEPENDENCIES)}")
        logging.info("Application will use fallback functions for missing dependencies")
    else:
        logging.info("All dependencies available on PythonAnywhere")

def is_pythonanywhere():
    """Check if running on PythonAnywhere."""
    return 'pythonanywhere.com' in os.environ.get('HTTP_HOST', '') or 'PYTHONANYWHERE' in os.environ