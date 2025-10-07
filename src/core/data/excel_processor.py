import os
import re
import logging
import traceback
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import datetime
from flask import send_file
from src.core.formatting.markers import wrap_with_marker, unwrap_marker
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from src.core.generation.text_processing import (
    format_cannabinoid_content,
    safe_get,
    safe_get_text,
    format_ratio_multiline,
    make_nonbreaking_hyphens,
)
from collections import OrderedDict
from src.core.constants import CLASSIC_TYPES, VALID_CLASSIC_LINEAGES, EXCLUDED_PRODUCT_TYPES, EXCLUDED_PRODUCT_PATTERNS, TYPE_OVERRIDES
from src.core.utils.common import calculate_text_complexity

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add at the top of the file (after imports)
VALID_LINEAGES = [
    "SATIVA", "INDICA", "HYBRID", "HYBRID/SATIVA", "HYBRID/INDICA", "CBD", "MIXED", "PARAPHERNALIA"
]

def normalize_lineage(lineage: str) -> str:
    """Normalize lineage to proper ALL CAPS format."""
    if not lineage or pd.isna(lineage):
        return "HYBRID"  # Default to HYBRID
    
    lineage = str(lineage).strip().lower()
    
    # Map common variations to standard ALL CAPS format
    lineage_mapping = {
        'hybrid': 'HYBRID',
        'indica_hybrid': 'HYBRID/INDICA',
        'indica': 'INDICA',
        'sativa': 'SATIVA',
        'sativa_hybrid': 'HYBRID/SATIVA',
        'cbd': 'CBD',
        'mixed': 'HYBRID',  # Default mixed to hybrid
        'unknown': 'HYBRID',  # Default unknown to hybrid
        'none': 'HYBRID',  # Default none to hybrid
        '': 'HYBRID'  # Default empty to hybrid
    }
    
    return lineage_mapping.get(lineage, 'HYBRID')

# Performance optimization flags - STANDARDIZED FOR BOTH LOCAL AND PYTHONANYWHERE
ENABLE_STRAIN_SIMILARITY_PROCESSING = True  # ALWAYS ENABLED: Lineage persistence is critical
ENABLE_FAST_LOADING = True
ENABLE_LAZY_PROCESSING = False  # DISABLED: Ensure consistent processing
ENABLE_MINIMAL_PROCESSING = True  # ENABLED: For ultra-fast uploads
ENABLE_BATCH_OPERATIONS = False  # DISABLED: Ensure consistent processing
ENABLE_VECTORIZED_OPERATIONS = False  # DISABLED: Ensure consistent processing
ENABLE_LINEAGE_PERSISTENCE = True  # ENABLED: Enhanced lineage persistence with product name fallback

# Performance constants - STANDARDIZED
BATCH_SIZE = 1000  # Standard batch size
MAX_STRAINS_FOR_SIMILARITY = 50  # Limit strain similarity processing
CACHE_SIZE = 128  # Standard cache size
LINEAGE_BATCH_SIZE = 100  # Batch size for lineage database operations

# Optimized helper functions for performance
def vectorized_string_operations(series, operations):
    """Apply multiple string operations efficiently using vectorized operations."""
    if not ENABLE_VECTORIZED_OPERATIONS:
        return series
    
    result = series.astype(str)
    
    for op_type, params in operations:
        if op_type == 'strip':
            result = result.str.strip()
        elif op_type == 'lower':
            result = result.str.lower()
        elif op_type == 'upper':
            result = result.str.upper()
        elif op_type == 'replace':
            result = result.str.replace(params['old'], params['new'], regex=params.get('regex', False))
        elif op_type == 'fillna':
            result = result.fillna(params['value'])
    
    return result

def batch_process_dataframe(df, batch_size=BATCH_SIZE):
    """Process DataFrame in batches for better memory management."""
    if not ENABLE_BATCH_OPERATIONS:
        return df
    
    processed_chunks = []
    for i in range(0, len(df), batch_size):
        chunk = df.iloc[i:i + batch_size].copy()
        # Process chunk here if needed
        processed_chunks.append(chunk)
    
    return pd.concat(processed_chunks, ignore_index=True)

def optimized_column_processing(df, column_configs):
    """Apply optimized column processing configurations."""
    from .field_mapping import get_canonical_field
    for col, config in column_configs.items():
        canonical_col = get_canonical_field(col)
        if canonical_col in df.columns:
            operations = config.get('operations', [])
            df[canonical_col] = vectorized_string_operations(df[canonical_col], operations)
    return df

def fast_ratio_extraction(product_names, product_types, classic_types):
    """Fast ratio extraction using vectorized operations."""
    if not ENABLE_VECTORIZED_OPERATIONS:
        return product_names
    
    # Vectorized ratio extraction logic
    ratios = pd.Series([''] * len(product_names))
    
    # Apply ratio extraction rules vectorized
    classic_mask = product_types.isin(classic_types)
    ratios[classic_mask] = 'THC: | BR | CBD:'
    
    return ratios

def optimized_lineage_assignment(df, product_types, lineages, classic_types):
    """Optimized lineage assignment using vectorized operations."""
    if not ENABLE_VECTORIZED_OPERATIONS:
        return lineages
    
    # Vectorized lineage assignment
    result = lineages.copy()
    
    # Enhanced check for missing lineage (includes NaN, null, empty, and 'nan' strings)
    empty_lineage_mask = (
        lineages.isna() | 
        (lineages.astype(str).str.strip() == '') |
        (lineages.astype(str).str.lower().str.strip() == 'nan')
    )
    
    # Apply lineage rules vectorized
    classic_mask = product_types.isin(classic_types)
    nonclassic_mask = ~classic_mask
    
    # Set default lineage for classic types with empty lineage (HYBRID)
    classic_default_mask = classic_mask & empty_lineage_mask
    result[classic_default_mask] = 'HYBRID'
    
    # Use Product Strain to determine lineage for ALL non-classic types (override existing lineage)
    if 'Product Strain' in df.columns:
        product_strain = df['Product Strain'].astype(str)
        
        # CBD Blend products -> CBD lineage (yellow) - override existing lineage
        cbd_blend_mask = nonclassic_mask & (product_strain.str.contains('CBD Blend', case=False, na=False))
        result[cbd_blend_mask] = 'CBD'
        
        # Paraphernalia products -> PARAPHERNALIA lineage (pink) - override existing lineage
        paraphernalia_mask = nonclassic_mask & (product_strain.str.contains('Paraphernalia', case=False, na=False))
        result[paraphernalia_mask] = 'PARAPHERNALIA'
        
        # Mixed products -> MIXED lineage (blue) - override existing lineage
        mixed_mask = nonclassic_mask & (product_strain.str.contains('Mixed', case=False, na=False))
        result[mixed_mask] = 'MIXED'
        
        # Default fallback for any remaining non-classic types
        remaining_nonclassic_mask = nonclassic_mask & ~(cbd_blend_mask | paraphernalia_mask | mixed_mask)
        
        # Only set default for empty lineages in remaining non-classic types
        remaining_empty_mask = remaining_nonclassic_mask & empty_lineage_mask
        result[remaining_empty_mask] = 'MIXED'
    else:
        # Fallback if Product Strain column doesn't exist - only for empty lineages
        nonclassic_default_mask = nonclassic_mask & empty_lineage_mask
        result[nonclassic_default_mask] = 'MIXED'
    
    return result

def handle_duplicate_columns(df):
    """Handle duplicate columns efficiently."""
    cols = df.columns.tolist()
    unique_cols = []
    seen_cols = set()
    
    for col in cols:
        if col not in seen_cols:
            unique_cols.append(col)
            seen_cols.add(col)
        else:
            # Keep the first occurrence, remove duplicates
            pass
        
    if len(unique_cols) != len(cols):
        df = df[unique_cols]
        
    return df
    
def optimized_lineage_persistence(processor, df):
    """Optimized lineage persistence that's always enabled and performs well."""
    if not ENABLE_LINEAGE_PERSISTENCE:
        return df
    
    try:
        from .product_database import ProductDatabase
        from src.core.constants import CLASSIC_TYPES
        product_db = ProductDatabase(store_name=processor._store_name)
        
        # Process lineage persistence in batches for performance
        classic_mask = df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)
        classic_df = df[classic_mask].copy()
        
        # Immediately fix any MIXED lineage for classic types in the current DataFrame
        mixed_lineage_mask = (df["Lineage"] == "MIXED") & classic_mask
        if mixed_lineage_mask.any():
            df.loc[mixed_lineage_mask, "Lineage"] = "HYBRID"
            processor.logger.info(f"Fixed {mixed_lineage_mask.sum()} classic products with MIXED lineage, changed to HYBRID")
        
        if classic_df.empty:
            return df
        
        # Get unique strains for batch processing
        unique_strains = classic_df["Product Strain"].dropna().unique()
        valid_strains = [s for s in unique_strains if normalize_strain_name(s)]
        
        if not valid_strains:
            return df
        
        # Use constant for valid lineages for classic types
        valid_classic_lineages = VALID_CLASSIC_LINEAGES
        
        # Process strains in batches
        strain_batches = [valid_strains[i:i + LINEAGE_BATCH_SIZE] 
                         for i in range(0, len(valid_strains), LINEAGE_BATCH_SIZE)]
        
        for batch in strain_batches:
            # Get lineage information from database for this batch
            strain_lineage_map = {}
            
            for strain_name in batch:
                strain_info = product_db.get_strain_info(strain_name)
                if strain_info and strain_info.get('display_lineage'):
                    db_lineage = strain_info['display_lineage']
                    # Only use database lineage if it's valid for classic types
                    # Explicitly reject MIXED lineage for classic types
                    if db_lineage and db_lineage.upper() in valid_classic_lineages and db_lineage.upper() != 'MIXED':
                        strain_lineage_map[strain_name] = db_lineage
                    else:
                        # Log invalid lineage for classic types
                        processor.logger.warning(f"Invalid lineage '{db_lineage}' for classic strain '{strain_name}', skipping database update")
            
            # Apply lineage updates vectorized
            if strain_lineage_map:
                for strain_name, db_lineage in strain_lineage_map.items():
                    strain_mask = (df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)) & \
                                (df["Product Strain"] == strain_name)
                    
                    # Only update if current lineage is empty or different
                    current_lineage_mask = (df.loc[strain_mask, "Lineage"].isna()) | \
                                         (df.loc[strain_mask, "Lineage"].astype(str).str.strip() == '') | \
                                         (df.loc[strain_mask, "Lineage"] != db_lineage)
                    
                    update_mask = strain_mask & current_lineage_mask
                    if update_mask.any():
                        df.loc[update_mask, "Lineage"] = db_lineage
                        
                        # Log the updates
                        updated_count = update_mask.sum()
                        if updated_count > 0:
                            processor.logger.debug(f"Updated {updated_count} products with strain '{strain_name}' to lineage '{db_lineage}' from database")
        
        return df
        
    except Exception as e:
        processor.logger.error(f"Error in optimized lineage persistence: {e}")
        return df

def batch_lineage_database_update(processor, df):
    """Batch update lineage information in the database."""
    if not ENABLE_LINEAGE_PERSISTENCE:
        return
    
    try:
        from .product_database import ProductDatabase
        from src.core.constants import CLASSIC_TYPES
        product_db = ProductDatabase(store_name=processor._store_name)
        
        # Process in batches for performance
        classic_mask = df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)
        classic_df = df[classic_mask]
        
        if classic_df.empty:
            return
        
        # Group by strain for efficient batch processing
        strain_groups = classic_df.groupby('Product Strain')
        
        for strain_name, group in strain_groups:
            if not strain_name or pd.isna(strain_name):
                continue
                
            # Get the most common lineage for this strain in this dataset
            lineage_counts = group['Lineage'].value_counts()
            if not lineage_counts.empty:
                most_common_lineage = lineage_counts.index[0]
                
                # Validate lineage for classic types - never save MIXED lineage
                from src.core.constants import VALID_CLASSIC_LINEAGES
                if most_common_lineage and str(most_common_lineage).strip():
                    lineage_to_save = most_common_lineage
                    
                    # For classic types, ensure we never save MIXED lineage
                    if most_common_lineage.upper() == 'MIXED':
                        lineage_to_save = 'HYBRID'
                        processor.logger.warning(f"Preventing MIXED lineage save for classic strain '{strain_name}', using HYBRID instead")
                    
                    # Only save if it's a valid lineage for classic types
                    if lineage_to_save.upper() in VALID_CLASSIC_LINEAGES:
                        product_db.add_or_update_strain(strain_name, lineage_to_save, sovereign=True)
                    else:
                        processor.logger.warning(f"Invalid lineage '{lineage_to_save}' for classic strain '{strain_name}', skipping database save")
        
    except Exception as e:
        processor.logger.error(f"Error in batch lineage database update: {e}")

def get_default_upload_file() -> Optional[str]:
    """
    Returns the path to the most recent "A Greener Today" Excel file.
    STANDARDIZED for both local and PythonAnywhere environments.
    """
    import os
    from pathlib import Path
    
    # Check if we should disable default file loading for testing or performance
    DISABLE_DEFAULT_FOR_TESTING = False
    DISABLE_DEFAULT_FOR_PERFORMANCE = os.environ.get('DISABLE_DEFAULT_FILE_LOADING', 'False').lower() == 'true'
    
    # Also check for the global flag from app.py
    try:
        import app
        DISABLE_STARTUP_FILE_LOADING = getattr(app, 'DISABLE_STARTUP_FILE_LOADING', False)
    except (ImportError, AttributeError):
        DISABLE_STARTUP_FILE_LOADING = False
    
    if DISABLE_DEFAULT_FOR_TESTING or DISABLE_DEFAULT_FOR_PERFORMANCE or DISABLE_STARTUP_FILE_LOADING:
        logger.info("Default file loading disabled for testing/performance optimization")
        return None
    
    # Get the current working directory and home directory
    current_dir = os.getcwd()
    home_dir = os.path.expanduser('~')
    logger.debug(f"Current working directory: {current_dir}")
    logger.debug(f"Home directory: {home_dir}")
    
    # STANDARDIZED environment detection for both local and PythonAnywhere
    is_pythonanywhere = (
        os.path.exists("/home/adamcordova") or
        'PYTHONANYWHERE_SITE' in os.environ or
        'PYTHONANYWHERE_DOMAIN' in os.environ or
        os.path.exists('/var/log/pythonanywhere') or
        'pythonanywhere.com' in os.environ.get('HTTP_HOST', '') or
        "pythonanywhere" in current_dir.lower() or
        "/home/adamcordova" in current_dir
    )
    
    logger.debug(f"Running on PythonAnywhere: {is_pythonanywhere}")
    
    # STANDARDIZED search locations - check both uploads and Downloads for both environments
    search_locations = []
    
    # Both environments: Check uploads folder first, then Downloads
    standard_paths = [
        os.path.join(current_dir, "uploads"),  # Uploads folder first
        os.path.join(home_dir, "Downloads"),  # Downloads folder as backup
    ]
    search_locations.extend(standard_paths)
    logger.debug("STANDARDIZED: Searching uploads folder first, then Downloads for both environments")
    
    # Find all Excel files (not just "A Greener Today")
    excel_files = []
    
    for location in search_locations:
        if os.path.exists(location):
            logger.debug(f"Searching in: {location}")
            try:
                for filename in os.listdir(location):
                    # Look for any Excel file, prioritize "A Greener Today"
                    # Skip temporary Excel files (starting with ~$)
                    if filename.lower().endswith(('.xlsx', '.xls')) and not filename.startswith('~$'):
                        file_path = os.path.join(location, filename)
                        if os.path.isfile(file_path):
                            mod_time = os.path.getmtime(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            # Give priority to "A Greener Today" files
                            priority = 0
                            if "a greener today" in filename.lower():
                                priority = 1
                            
                            # Skip files that are too small (likely corrupted)
                            if file_size > 1000:  # Minimum 1KB
                                excel_files.append((file_path, filename, mod_time, file_size, priority))
                                logger.debug(f"Found Excel file: {filename} (modified: {mod_time}, size: {file_size:,} bytes, priority: {priority})")
                            else:
                                logger.debug(f"Skipping small file (likely corrupted): {filename} (size: {file_size:,} bytes)")
            except Exception as e:
                logger.error(f"Error searching {location}: {e}")
        else:
            logger.warning(f"Location does not exist: {location}")
    
    if not excel_files:
        logger.warning("No Excel files found in any search location")
        logger.info("Please upload an Excel file using the file upload feature")
        return None
    
    # Sort by filename priority (A Greener Today), then modification time
    excel_files.sort(key=lambda x: (x[4], x[2]), reverse=True)
    
    # Return the highest priority, most recent file
    best_file_path, best_filename, best_mod_time, best_file_size, best_priority = excel_files[0]
    logger.info(f"Found best Excel file: {best_filename} (modified: {best_mod_time}, size: {best_file_size:,} bytes, priority: {best_priority})")
    return best_file_path

def _complexity(text):
    """Legacy complexity function - use calculate_text_complexity from common.py instead."""
    return calculate_text_complexity(text, 'standard')



def safe_product_name(name):
    """Safely process product names to prevent 'NO NAME' issues."""
    if not name or pd.isna(name):
        return "Unknown Product"
    
    # Convert to string and clean
    name_str = str(name).strip()
    
    if not name_str or name_str.lower() in ['nan', 'none', 'null', '']:
        return "Unknown Product"
    
    # Remove problematic characters
    name_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name_str)
    
    return name_str

def safe_product_type(product_type):
    """Safely process product types."""
    if not product_type or pd.isna(product_type):
        return "Vape Cartridge"  # Default to Vape Cartridge for concentrates
    
    type_str = str(product_type).strip()
    
    if not type_str or type_str.lower() in ['nan', 'none', 'null', '']:
        return "Vape Cartridge"  # Default to Vape Cartridge for concentrates
    
    return type_str


def normalize_name(name):
    """Normalize product names for robust matching."""
    if not isinstance(name, str):
        return ""
    # Lowercase, strip, replace multiple spaces/hyphens, remove non-breaking hyphens, etc.
    name = name.lower().strip()
    name = name.replace('\u2011', '-')  # non-breaking hyphen to normal
    name = re.sub(r'[-\s]+', ' ', name)  # collapse hyphens and spaces
    name = re.sub(r'[^\w\s-]', '', name)  # remove non-alphanumeric except hyphen/space
    return name


def is_real_ratio(text: str) -> bool:
    """Check if a string represents a valid ratio format."""
    if not text or not isinstance(text, str):
        return False
    
    # Clean the text
    text = text.strip()
    
    # Check for common invalid values
    if text in ["", "CBD", "THC", "CBD:", "THC:", "CBD:\n", "THC:\n"]:
        return False
    
    # Check for mg values (e.g., "100mg", "500mg THC", "10mg CBD")
    if 'mg' in text.lower():
        return True
    
    # Check for ratio format with numbers and separators
    if any(c.isdigit() for c in text) and any(sep in text for sep in [":", "/", "-"]):
        return True
    
    # Check for specific cannabinoid patterns
    cannabinoid_patterns = [
        r'\b(?:THC|CBD|CBC|CBG|CBN)\b',
        r'\d+mg',
        r'\d+:\d+',
        r'\d+:\d+:\d+'
    ]
    
    for pattern in cannabinoid_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def is_weight_with_unit(text: str) -> bool:
    """Check if a string represents a weight with unit format (e.g., '1g', '3.5g', '1oz')."""
    if not text or not isinstance(text, str):
        return False
    
    # Clean the text
    text = text.strip()
    
    # Check for weight + unit patterns
    weight_patterns = [
        r'^\d+(?:\.\d+)?\s*(?:g|gram|grams|gm|oz|ounce|ounces)$',  # 1g, 3.5g, 1oz, etc.
        r'^\d+(?:\.\d+)?\s*(?:g|gram|grams|gm|oz|ounce|ounces)\s*$',  # with trailing space
    ]
    
    for pattern in weight_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    return False


def normalize_strain_name(strain):
    """Normalize strain names for accurate matching."""
    if not isinstance(strain, str):
        return ""
    
    # Convert to string and clean
    strain = str(strain).strip()
    
    # Skip invalid strains
    if not strain or strain.lower() in ['mixed', 'unknown', 'n/a', 'none', '']:
        return ""
    
    # Normalize the strain name
    strain = strain.lower()
    
    # Remove common prefixes/suffixes that don't affect strain identity
    strain = re.sub(r'^(strain|variety|cultivar)\s+', '', strain)
    strain = re.sub(r'\s+(strain|variety|cultivar)$', '', strain)
    
    # Normalize common abbreviations and variations
    strain = re.sub(r'\bog\b', 'og kush', strain)  # "OG" -> "OG Kush"
    strain = re.sub(r'\bblue\s*dream\b', 'blue dream', strain)
    strain = re.sub(r'\bwhite\s*widow\b', 'white widow', strain)
    strain = re.sub(r'\bpurple\s*haze\b', 'purple haze', strain)
    strain = re.sub(r'\bjack\s*herer\b', 'jack herer', strain)
    strain = re.sub(r'\bnorthern\s*lights\b', 'northern lights', strain)
    strain = re.sub(r'\bsour\s*diesel\b', 'sour diesel', strain)
    strain = re.sub(r'\bafghan\s*kush\b', 'afghan kush', strain)
    strain = re.sub(r'\bcheese\b', 'uk cheese', strain)
    strain = re.sub(r'\bamnesia\s*haze\b', 'amnesia haze', strain)
    
    # Remove extra spaces and normalize punctuation
    strain = re.sub(r'\s+', ' ', strain)
    strain = re.sub(r'[^\w\s-]', '', strain)  # Keep only alphanumeric, spaces, and hyphens
    
    return strain.strip()


def get_strain_similarity(strain1, strain2):
    """Calculate similarity between two strain names. Optimized for performance."""
    if not strain1 or not strain2:
        return 0.0
    
    # Fast exact match check first
    if strain1 == strain2:
        return 1.0
    
    norm1 = normalize_strain_name(strain1)
    norm2 = normalize_strain_name(strain2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Fast substring check (most common case)
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Only do expensive similarity calculation for very similar strings
    if abs(len(norm1) - len(norm2)) <= 3:  # Only compare strings of similar length
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity if similarity > 0.8 else 0.0  # Only return high similarity
    
    return 0.0


def group_similar_strains(strains, similarity_threshold=0.8):
    """Group similar strain names together. Optimized for performance."""
    if not strains:
        return {}
    
    # Fast path: if similarity processing is disabled, return empty groups
    if not ENABLE_STRAIN_SIMILARITY_PROCESSING:
        return {}
    
    # Limit the number of strains to process to avoid O(n²) complexity
    max_strains = 100  # Only process first 100 strains to avoid performance issues
    if len(strains) > max_strains:
        strains = list(strains)[:max_strains]
    
    # Normalize all strains
    normalized_strains = {}
    for strain in strains:
        norm = normalize_strain_name(strain)
        if norm:
            normalized_strains[strain] = norm
    
    # Group similar strains (optimized algorithm)
    groups = {}
    processed = set()
    
    # Sort strains by length to process shorter ones first (better for substring matching)
    sorted_strains = sorted(normalized_strains.items(), key=lambda x: len(x[1]))
    
    for strain1, norm1 in sorted_strains:
        if strain1 in processed:
            continue
            
        # Start a new group
        group_key = strain1
        groups[group_key] = [strain1]
        processed.add(strain1)
        
        # Find similar strains (only check unprocessed strains)
        for strain2, norm2 in sorted_strains:
            if strain2 in processed:
                continue
                
            # Fast similarity check
            similarity = get_strain_similarity(strain1, strain2)
            if similarity >= similarity_threshold:
                groups[group_key].append(strain2)
                processed.add(strain2)
    
    return groups


class ExcelProcessor:
    """Processes Excel files containing product data."""

    def __init__(self, store_name='AGT_Bothell'):
        self.df = None
        self.dropdown_cache = {}
        self.selected_tags = []
        self.logger = logger
        self._last_loaded_file = None
        self._file_cache = {}
        self._max_cache_size = 5  # Keep only 5 files in cache
        self._product_db_enabled = True  # Enable product database integration by default
        self._debug_count = 0  # Initialize debug count
        self._store_name = store_name  # Store name for database operations

    def clear_file_cache(self):
        """Clear the file cache to free memory."""
        self._file_cache.clear()
        self.logger.debug("File cache cleared")
    
    def apply_strain_extraction(self):
        """Apply strain extraction logic to loaded data."""
        if self.df is None or self.df.empty:
            self.logger.warning("No data loaded to apply strain extraction")
            return
        
        self.logger.info("Applying strain extraction logic for Moonshot products...")
        
        # Find products with "Moonshot" in Product Strain
        if "Product Strain" in self.df.columns:
            moonshot_mask = self.df["Product Strain"].astype(str).str.contains("Moonshot", case=False, na=False)
            
            if moonshot_mask.any():
                # Apply strain extraction to these products
                for idx in self.df[moonshot_mask].index:
                    original_strain = str(self.df.loc[idx, "Product Strain"])
                    if 'Moonshot' in original_strain:
                        # Extract the strain name (everything before "Moonshot")
                        strain_name = original_strain.replace(' Moonshot', '').strip()
                        if strain_name:
                            self.df.loc[idx, "Product Strain"] = strain_name
                            self.logger.debug(f"Extracted strain '{strain_name}' from '{original_strain}' for product '{self.df.loc[idx, 'ProductName']}'")
                
                self.logger.info(f"Applied strain extraction to {moonshot_mask.sum()} Moonshot products")
            else:
                self.logger.info("No Moonshot products found for strain extraction")
        else:
            self.logger.warning("Product Strain column not found for strain extraction")

    def _manage_cache_size(self):
        """Keep cache size under control."""
        if len(self._file_cache) > self._max_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self._file_cache.keys())[:len(self._file_cache) - self._max_cache_size]
            for key in oldest_keys:
                del self._file_cache[key]
    
    def _schedule_product_db_integration(self):
        """Schedule product database integration in background to avoid blocking file load."""
        # Check if integration is enabled
        if not getattr(self, '_product_db_enabled', True):
            self.logger.debug("[ProductDB] Integration disabled, skipping background processing")
            return
            
        try:
            import threading
            import time
            
            def background_integration():
                """Background task for product database integration."""
                try:
                    # Add a small delay to ensure main file load completes first
                    time.sleep(0.1)
                    
                    from .product_database import ProductDatabase
                    product_db = ProductDatabase(store_name=self._store_name)
                    
                    # Add retry logic for database locking issues
                    max_retries = 3
                    
                    # Process in batches for better performance
                    batch_size = 50
                    total_rows = len(self.df)
                    product_count = 0
                    strain_count = 0
                    
                    # Count classic types for logging
                    classic_types_count = sum(1 for _, row in self.df.iterrows() 
                                            if row.get('Product Type*', '').strip().lower() in [c.lower() for c in CLASSIC_TYPES])
                    self.logger.info(f"[ProductDB] Starting background integration for {total_rows} records ({classic_types_count} classic types for strain processing)...")
                    
                    for i in range(0, total_rows, batch_size):
                        batch_end = min(i + batch_size, total_rows)
                        batch_df = self.df.iloc[i:batch_end]
                        
                        # Process batch with retry logic for database locking
                        for _, row in batch_df.iterrows():
                            row_dict = row.to_dict()
                            
                            # Only process classic types through the strain database
                            product_type = row_dict.get('Product Type*', '').strip().lower()
                            if product_type in [c.lower() for c in CLASSIC_TYPES]:
                                # Add or update strain (only if strain name exists)
                                strain_name = row_dict.get('Product Strain', '')
                                if strain_name and str(strain_name).strip():
                                    # Retry logic for strain operations
                                    strain_retry_delay = 0.5
                                    for attempt in range(max_retries):
                                        try:
                                            strain_id = product_db.add_or_update_strain(strain_name, row_dict.get('Lineage', ''))
                                            if strain_id:
                                                strain_count += 1
                                            break
                                        except Exception as e:
                                            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                                                self.logger.warning(f"[ProductDB] Database locked for strain '{strain_name}', retrying in {strain_retry_delay}s (attempt {attempt + 1}/{max_retries})")
                                                time.sleep(strain_retry_delay)
                                                strain_retry_delay *= 2  # Exponential backoff
                                            else:
                                                self.logger.error(f"[ProductDB] Failed to add/update strain '{strain_name}' after {max_retries} attempts: {e}")
                                                break
                                
                                # Add or update product with retry logic
                                product_retry_delay = 0.5
                                for attempt in range(max_retries):
                                    try:
                                        product_id = product_db.add_or_update_product(row_dict)
                                        if product_id:
                                            product_count += 1
                                        break
                                    except Exception as e:
                                        if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                                            self.logger.warning(f"[ProductDB] Database locked for product, retrying in {product_retry_delay}s (attempt {attempt + 1}/{max_retries})")
                                            time.sleep(product_retry_delay)
                                            product_retry_delay *= 2  # Exponential backoff
                                        else:
                                            self.logger.error(f"[ProductDB] Failed to add/update product after {max_retries} attempts: {e}")
                                            break
                            else:
                                # For non-classic types, only add/update the product (no strain processing)
                                non_classic_retry_delay = 0.5
                                for attempt in range(max_retries):
                                    try:
                                        product_id = product_db.add_or_update_product(row_dict)
                                        if product_id:
                                            product_count += 1
                                        break
                                    except Exception as e:
                                        if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                                            self.logger.warning(f"[ProductDB] Database locked for non-classic product, retrying in {non_classic_retry_delay}s (attempt {attempt + 1}/{max_retries})")
                                            time.sleep(non_classic_retry_delay)
                                            non_classic_retry_delay *= 2  # Exponential backoff
                                        else:
                                            self.logger.error(f"[ProductDB] Failed to add/update non-classic product after {max_retries} attempts: {e}")
                                            break
                        
                        # Log progress for large files
                        if total_rows > 100:
                            progress = (batch_end / total_rows) * 100
                            self.logger.debug(f"[ProductDB] Progress: {progress:.1f}% ({batch_end}/{total_rows})")
                    
                    self.logger.info(f"[ProductDB] Background integration complete: {strain_count} strains processed, {product_count} products added/updated")
                    
                except Exception as e:
                    self.logger.error(f"[ProductDB] Background integration error: {e}")
            
            # Start background thread
            thread = threading.Thread(target=background_integration, daemon=True)
            thread.start()
            
        except Exception as e:
            self.logger.error(f"[ProductDB] Failed to schedule background integration: {e}")
    
    def _load_lineage_from_database(self):
        """Load lineage data from database to ensure changes persist after reload."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            return
            
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            if not hasattr(self, 'df') or self.df is None or 'Product Strain' not in self.df.columns:
                return
            
            self.logger.info("[ProductDB] Loading lineage data from database...")
            
            # Get all unique strain names from the loaded data
            strain_names = self.df['Product Strain'].dropna().unique()
            strain_names = [str(name).strip() for name in strain_names if str(name).strip()]
            
            lineage_updates = 0
            
            for strain_name in strain_names:
                try:
                    strain_info = product_db.get_strain_info(strain_name)
                    if strain_info and strain_info.get('sovereign_lineage'):
                        # Update lineage in the dataframe for this strain
                        strain_mask = self.df['Product Strain'] == strain_name
                        if strain_mask.any():
                            self.df.loc[strain_mask, 'Lineage'] = strain_info['sovereign_lineage']
                            lineage_updates += strain_mask.sum()
                            self.logger.debug(f"[ProductDB] Loaded lineage for '{strain_name}': {strain_info['sovereign_lineage']}")
                except Exception as e:
                    self.logger.warning(f"[ProductDB] Failed to load lineage for strain '{strain_name}': {e}")
            
            if lineage_updates > 0:
                self.logger.info(f"[ProductDB] Loaded {lineage_updates} lineage updates from database")
            else:
                self.logger.debug("[ProductDB] No lineage updates loaded from database")
                
        except Exception as e:
            self.logger.error(f"[ProductDB] Failed to load lineage from database: {e}")
    
    def enable_product_db_integration(self, enable: bool = True):
        """Enable or disable product database integration."""
        self._product_db_enabled = enable
        self.logger.info(f"[ProductDB] Integration {'enabled' if enable else 'disabled'}")
    
    def set_processing_mode(self, mode: str):
        """Set processing mode for performance optimization."""
        self._processing_mode = mode
        self.logger.info(f"[Processing] Mode set to: {mode}")
    
    def apply_minimal_processing(self):
        """Apply minimal processing for web server performance."""
        if self.df is None or self.df.empty:
            self.logger.warning("[Minimal] No data to process")
            return
        
        self.logger.info("[Minimal] Applying minimal processing for web server performance")
        
        # Only perform essential processing
        try:
            # 1. Basic column cleaning
            self.df = self.df.fillna('')
            
            # 2. Essential column processing only
            if 'Product Name*' in self.df.columns:
                self.df['Product Name*'] = self.df['Product Name*'].astype(str).apply(safe_product_name)
            
            if 'Product Type*' in self.df.columns:
                self.df['Product Type*'] = self.df['Product Type*'].astype(str).apply(safe_product_type)
            
            # 3. Cache essential dropdown values
            self._cache_dropdown_values()
            
            self.logger.info("[Minimal] Minimal processing completed successfully")
            
        except Exception as e:
            self.logger.error(f"[Minimal] Error in minimal processing: {e}")
            raise
    
    def get_product_db_stats(self):
        """Get product database statistics."""
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            return product_db.get_performance_stats()
        except Exception as e:
            self.logger.error(f"[ProductDB] Error getting stats: {e}")
            return {}
    
    def get_product_strain_from_db(self, product_name: str, product_type: str, description: str, ratio: str) -> str:
        """Get Product Strain value from database using the database's calculation logic."""
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            # Use the database's calculation method to get the Product Strain
            product_strain = product_db._calculate_product_strain(
                product_type or '',
                product_name or '',
                description or '',
                ratio or ''
            )
            
            return product_strain
            
        except Exception as e:
            self.logger.error(f"[ProductDB] Error getting Product Strain from database: {e}")
            return ""
    
    def _apply_database_product_strain_values(self):
        """Apply database Product Strain values to all products in the DataFrame."""
        try:
            if not hasattr(self, 'df') or self.df is None or len(self.df) == 0:
                self.logger.warning("[ProductDB] No DataFrame to process for Product Strain values")
                return
            
            self.logger.info(f"[ProductDB] Applying database Product Strain values to {len(self.df)} products")
            
            # Get the database instance
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            # Process each product and get its Product Strain from database
            updated_count = 0
            for idx, row in self.df.iterrows():
                try:
                    # Get the required fields
                    product_name = row.get('Product Name*', '') or row.get('Product Name', '') or row.get('Product_Name', '')
                    product_type = row.get('Product Type*', '')
                    description = row.get('Description', '')
                    ratio = row.get('Ratio', '')
                    
                    # Get Product Strain from database
                    db_product_strain = product_db._calculate_product_strain(
                        product_type or '',
                        product_name or '',
                        description or '',
                        ratio or ''
                    )
                    
                    # Update the DataFrame with database value
                    self.df.loc[idx, 'Product Strain'] = db_product_strain
                    updated_count += 1
                    
                    # Log some examples for debugging
                    if idx < 5 or db_product_strain in ['CBD Blend', 'Mixed']:
                        self.logger.debug(f"[ProductDB] {product_name} ({product_type}) -> {db_product_strain}")
                        
                except Exception as e:
                    self.logger.error(f"[ProductDB] Error processing product at index {idx}: {e}")
                    continue
            
            self.logger.info(f"[ProductDB] Successfully updated {updated_count} products with database Product Strain values")
            
            # Log some statistics
            if 'Product Strain' in self.df.columns:
                strain_counts = self.df['Product Strain'].value_counts()
                self.logger.info(f"[ProductDB] Product Strain distribution: {strain_counts.to_dict()}")
            
        except Exception as e:
            self.logger.error(f"[ProductDB] Error applying database Product Strain values: {e}")
            raise

    def fast_load_file(self, file_path: str) -> bool:
        """ULTRA-FAST file loading with minimal processing for maximum upload speed."""
        try:
            self.logger.debug(f"[ULTRA-FAST] Loading file: {file_path}")
            
            # Minimal validation for speed
            import os
            if not os.path.exists(file_path):
                self.logger.error(f"[ULTRA-FAST] File not found: {file_path}")
                return False
            
            # Clear previous data efficiently
            if hasattr(self, 'df') and self.df is not None:
                del self.df
            
            # Use optimized Excel reading with minimal processing
            excel_engines = ['openpyxl']
            df = None
            
            for engine in excel_engines:
                try:
                    self.logger.debug(f"Attempting to read with engine: {engine}")
                    
                    # Use optimized reading settings - minimal dtype specification for speed
                    dtype_dict = {
                        "Product Name*": "string",
                        "Product Type*": "string",
                        "Lineage": "string"
                    }
                    
                    # Read with minimal processing - no NA filtering for speed
                    df = pd.read_excel(
                        file_path, 
                        engine=engine,
                        dtype=dtype_dict,
                        na_filter=False,  # Don't filter NA values for speed
                        keep_default_na=False  # Don't use default NA values
                    )
                    
                    self.logger.info(f"Successfully read file with {engine} engine: {len(df)} rows, {len(df.columns)} columns")
                    break
                    
                except Exception as e:
                    self.logger.warning(f"Failed to read with {engine} engine: {e}")
                    if engine == excel_engines[-1]:  # Last engine
                        self.logger.error(f"All Excel engines failed to read file: {file_path}")
                        return False
                    continue
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            # Handle duplicate columns efficiently
            df = handle_duplicate_columns(df)
            
            # Remove duplicates efficiently - use product name as primary key for deduplication
            initial_count = len(df)
            
            # First, ensure we have a product name column
            product_name_col = None
            for col in ['Product Name*', 'ProductName', 'Product Name', 'Description']:
                if col in df.columns:
                    product_name_col = col
                    break
            
            if product_name_col:
                # Use product name as primary key for deduplication to prevent UI duplicates
                df.drop_duplicates(subset=[product_name_col], inplace=True)
                self.logger.info(f"Removed duplicates based on product name column: {product_name_col}")
            else:
                # Fallback to general deduplication if no product name column found
                df.drop_duplicates(inplace=True)
                self.logger.info("No product name column found, using general deduplication")
            
            df.reset_index(drop=True, inplace=True)
            final_count = len(df)
            if initial_count != final_count:
                self.logger.info(f"Removed {initial_count - final_count} duplicate rows")

            # Log all available columns for debugging
            self.logger.info(f"All columns in uploaded file: {df.columns.tolist()}")
            
            # Keep all columns but ensure only truly essential ones exist
            essential_columns = [
                'Product Name*', 'ProductName',  # Product name (at least one variant)
                'Product Type*',  # Product type
                'Vendor/Supplier*', 'Vendor'  # Vendor (at least one variant)
            ]
            
            # Check which essential columns are missing, but only warn if ALL variants are missing
            missing_columns = []
            has_product_name = any(col in df.columns for col in ['Product Name*', 'ProductName', 'Product Name'])
            has_vendor = any(col in df.columns for col in ['Vendor/Supplier*', 'Vendor', 'Vendor/Supplier'])
            has_product_type = 'Product Type*' in df.columns
            
            if not has_product_name:
                missing_columns.extend(['Product Name*', 'ProductName'])
            if not has_vendor:
                missing_columns.extend(['Vendor/Supplier*', 'Vendor'])
            if not has_product_type:
                missing_columns.append('Product Type*')
            
            # Only warn if we're actually missing essential columns
            if missing_columns:
                self.logger.warning(f"Missing essential columns: {missing_columns}")
            else:
                self.logger.info("All essential columns found")
            
            # Apply minimal processing only if ENABLE_MINIMAL_PROCESSING is True
            if ENABLE_MINIMAL_PROCESSING:
                # Only do essential processing for uploads
                self.logger.debug("Applying minimal processing for fast upload")
                
                # 1. Basic column normalization (vectorized for speed)
                if "Product Name*" in df.columns:
                    df["Product Name*"] = df["Product Name*"].str.lstrip()
                
                # 2. Ensure required columns exist
                for col in ["Product Type*", "Lineage", "Product Brand"]:
                    if col not in df.columns:
                        df[col] = "Unknown"
                
                # 3. Basic filtering (exclude sample rows) - vectorized for speed
                initial_count = len(df)
                df = df[~df["Product Type*"].isin(EXCLUDED_PRODUCT_TYPES)]
                df.reset_index(drop=True, inplace=True)
                final_count = len(df)
                if initial_count != final_count:
                    self.logger.info(f"Excluded {initial_count - final_count} products by type")
                
                # 4. Basic column renaming
                rename_mapping = {}
                if "Product Name*" in df.columns and "ProductName" not in df.columns:
                    rename_mapping["Product Name*"] = "ProductName"
                if "Weight Unit* (grams/gm or ounces/oz)" in df.columns and "Units" not in df.columns:
                    rename_mapping["Weight Unit* (grams/gm or ounces/oz)"] = "Units"
                if "Price* (Tier Name for Bulk)" in df.columns and "Price" not in df.columns:
                    rename_mapping["Price* (Tier Name for Bulk)"] = "Price"
                if "Vendor/Supplier*" in df.columns and "Vendor" not in df.columns:
                    rename_mapping["Vendor/Supplier*"] = "Vendor"
                    self.logger.info(f"Renaming column 'Vendor/Supplier*' to 'Vendor' during minimal processing")
                elif "Vendor/Supplier*" in df.columns:
                    self.logger.info(f"Column 'Vendor/Supplier*' found but 'Vendor' already exists - keeping both columns")
                elif "Vendor" in df.columns:
                    self.logger.info(f"Column 'Vendor' found - no renaming needed")
                else:
                    self.logger.warning(f"No vendor column found in DataFrame. Available columns: {[col for col in df.columns if 'vendor' in col.lower() or 'supplier' in col.lower()]}")
                if "DOH Compliant (Yes/No)" in df.columns and "DOH" not in df.columns:
                    rename_mapping["DOH Compliant (Yes/No)"] = "DOH"
                if "Concentrate Type" in df.columns and "Ratio" not in df.columns:
                    rename_mapping["Concentrate Type"] = "Ratio"
                # Excel compatibility column mappings
                if "Joint Ratio" in df.columns and "JointRatio" not in df.columns:
                    rename_mapping["Joint Ratio"] = "JointRatio"
                if "Quantity Received*" in df.columns and "Quantity*" not in df.columns:
                    rename_mapping["Quantity Received*"] = "Quantity*"
                if "qty" in df.columns and "Quantity*" not in df.columns:
                    rename_mapping["qty"] = "Quantity*"
                
                if rename_mapping:
                    df.rename(columns=rename_mapping, inplace=True)
                
                # 5. Basic lineage standardization (vectorized)
                if "Lineage" in df.columns:
                    from src.core.constants import CLASSIC_TYPES
                    # Normalize all lineage values to ALL CAPS format
                    df["Lineage"] = df["Lineage"].apply(normalize_lineage)
                    df["Lineage"] = optimized_lineage_assignment(
                        df, 
                        df["Product Type*"], 
                        df["Lineage"], 
                        CLASSIC_TYPES
                    )
                
                # 6. Basic product strain handling
                if "Product Strain" not in df.columns:
                    df["Product Strain"] = ""
                df["Product Strain"] = df["Product Strain"].fillna("Mixed")
                
                # 7. Process THC/CBD values for database storage
                if "THC test result" in df.columns:
                    # Convert THC test result to numeric, handling errors
                    df["THC test result"] = pd.to_numeric(df["THC test result"], errors='coerce').fillna(0.0)
                    self.logger.debug("Processed THC test result column")
                else:
                    df["THC test result"] = 0.0
                    self.logger.debug("Added default THC test result column")
                
                if "CBD test result" in df.columns:
                    # Convert CBD test result to numeric, handling errors
                    df["CBD test result"] = pd.to_numeric(df["CBD test result"], errors='coerce').fillna(0.0)
                    self.logger.debug("Processed CBD test result column")
                else:
                    df["CBD test result"] = 0.0
                    self.logger.debug("Added default CBD test result column")
                
                # Add test result unit if missing
                if "Test result unit (% or mg)" not in df.columns:
                    df["Test result unit (% or mg)"] = "%"
                    self.logger.debug("Added default test result unit column")
                
                # 8. Convert key fields to categorical for memory efficiency
                for col in ["Product Type*", "Lineage", "Product Brand", "Vendor", "Product Strain"]:
                    if col in df.columns:
                        df[col] = df[col].fillna("Unknown")
                        df[col] = df[col].astype("category")
                
                self.logger.debug("Minimal processing complete")
            else:
                self.logger.debug("Skipping minimal processing - using raw data")
                # Even in non-minimal mode, ensure THC/CBD columns exist for database storage
                if "THC test result" not in df.columns:
                    df["THC test result"] = 0.0
                if "CBD test result" not in df.columns:
                    df["CBD test result"] = 0.0
                if "Test result unit (% or mg)" not in df.columns:
                    df["Test result unit (% or mg)"] = "%"

            self.df = df
            self.logger.debug(f"Original columns: {self.df.columns.tolist()}")
            
            # Duplicate Product Strain column to "Strain Names" for processing
            if 'Product Strain' in self.df.columns:
                self.df['Strain Names'] = self.df['Product Strain'].copy()
                self.logger.info("Duplicated 'Product Strain' column to 'Strain Names' for processing")
            
            # Apply strain extraction for Moonshot products
            self.apply_strain_extraction()
            
            # Process Description values using our established formula
            self._process_descriptions_from_product_names()
            
            self._last_loaded_file = file_path
            self.logger.info(f"Ultra-fast load successful: {len(self.df)} rows, {len(self.df.columns)} columns")
            return True
                
        except Exception as e:
            self.logger.error(f"Error in ultra-fast_load_file: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Try to provide more specific error information
            if "No module named" in str(e):
                self.logger.error("Missing required module - this might be a dependency issue")
            elif "Permission denied" in str(e):
                self.logger.error("File permission issue - check file permissions")
            elif "Memory" in str(e):
                self.logger.error("Memory issue - file might be too large")
            return False

    def minimal_load_file(self, file_path: str) -> bool:
        """Ultra-minimal file loading for maximum speed - skips all heavy processing"""
        try:
            self.logger.debug(f"Minimal loading file: {file_path}")
            
            # Basic file validation
            import os
            if not os.path.exists(file_path):
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            if not os.access(file_path, os.R_OK):
                self.logger.error(f"File not readable: {file_path}")
                return False
            
            # Clear previous data
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                import gc
                gc.collect()
            
            # Minimal Excel reading - just get the data
            df = pd.read_excel(
                file_path, 
                engine='openpyxl',
                na_filter=False,
                keep_default_na=False,
                nrows=5000  # Limit rows for speed
            )
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            # Only essential processing - no heavy operations
            df = df.dropna(how='all')  # Remove completely empty rows
            df.reset_index(drop=True, inplace=True)
            
            # CRITICAL FIX: Add minimal JointRatio processing for pre-roll products
            try:
                if 'Product Type*' in df.columns:
                    # Add JointRatio column if it doesn't exist
                    if 'JointRatio' not in df.columns:
                        df['JointRatio'] = ''
                    
                    # Process JointRatio for pre-roll products
                    preroll_mask = df['Product Type*'].str.strip().str.lower().isin(['pre-roll', 'infused pre-roll'])
                    
                    if preroll_mask.any():
                        self.logger.info(f"Processing JointRatio for {preroll_mask.sum()} pre-roll products")
                        
                        # Simple JointRatio extraction from product names
                        import re
                        for idx in df[preroll_mask].index:
                            if df.loc[idx, 'JointRatio'] == '' or pd.isna(df.loc[idx, 'JointRatio']):
                                # Get product name
                                product_name_col = 'Product Name*' if 'Product Name*' in df.columns else 'ProductName'
                                if product_name_col in df.columns:
                                    product_name = str(df.loc[idx, product_name_col])
                                    
                                    # Extract joint ratio patterns like "0.5g x 2", "1g x 28 Pack"
                                    pattern = r'(\d*\.?\d+g)\s*x\s*(\d+)(?:\s*Pack)?'
                                    match = re.search(pattern, product_name, re.IGNORECASE)
                                    if match:
                                        weight = match.group(1)
                                        count = match.group(2)
                                        df.loc[idx, 'JointRatio'] = f"{weight} x {count}"
                                    else:
                                        # Try just weight pattern
                                        weight_pattern = r'(\d*\.?\d+g)'
                                        weight_match = re.search(weight_pattern, product_name, re.IGNORECASE)
                                        if weight_match:
                                            df.loc[idx, 'JointRatio'] = weight_match.group(1)
                                        elif 'Weight*' in df.columns and pd.notna(df.loc[idx, 'Weight*']):
                                            # Fallback to Weight* column
                                            weight_val = df.loc[idx, 'Weight*']
                                            try:
                                                weight_float = float(weight_val)
                                                df.loc[idx, 'JointRatio'] = f"{weight_float:g}g"
                                            except (ValueError, TypeError):
                                                df.loc[idx, 'JointRatio'] = '1g'  # Default
                        
                        self.logger.info(f"JointRatio processing completed for pre-roll products")
                
            except Exception as joint_error:
                self.logger.warning(f"JointRatio processing failed in minimal load: {joint_error}")
            
            self.df = df
            self._last_loaded_file = file_path
            
            self.logger.info(f"Minimal load complete: {len(df)} rows, {len(df.columns)} columns")
            return True
            
        except Exception as e:
            self.logger.error(f"Minimal load failed: {e}")
            return False

    def load_file(self, file_path: str) -> bool:
        """Load Excel file and prepare data exactly like MAIN.py. STANDARDIZED for both local and PythonAnywhere."""
        try:
            # Check if we've already loaded this exact file
            if (self._last_loaded_file == file_path and 
                self.df is not None and 
                not self.df.empty):
                self.logger.debug(f"File {file_path} already loaded, skipping reload")
                return True
            
            self.logger.debug(f"Loading file: {file_path}")
            
            # Validate file exists and is accessible
            import os
            if not os.path.exists(file_path):
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            if not os.access(file_path, os.R_OK):
                self.logger.error(f"File not readable: {file_path}")
                return False
            
            # Check file size (standard limit for both environments)
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB limit (standard for both environments)
            if file_size > max_size:
                self.logger.error(f"File too large: {file_size} bytes (max: {max_size})")
                return False
            
            self.logger.info(f"File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            # Check file modification time for cache invalidation
            file_mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}_{file_mtime}"
            
            if cache_key in self._file_cache:
                self.logger.debug(f"Using cached data for {file_path}")
                self.df = self._file_cache[cache_key].copy()
                self._last_loaded_file = file_path
                return True
            
            # Clear previous data to free memory
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                import gc
                gc.collect()
            
            # 1) Read & dedupe, force-key columns to string for .str ops
            # Use standard settings for both environments
            dtype_dict = {
                "Product Type*": "string",
                "Lineage": "string",
                "Product Brand": "string",
                "Vendor": "string",
                "Weight Unit* (grams/gm or ounces/oz)": "string",
                "Product Name*": "string"
            }
            
            # Use standard Excel engine (openpyxl) for both environments
            excel_engine = 'openpyxl'
            df = None
            
            try:
                self.logger.debug(f"Reading with engine: {excel_engine}")
                
                # Standard reading approach for both environments
                # Prevent pandas from converting empty cells to NaN values
                df = pd.read_excel(
                    file_path, 
                    engine=excel_engine, 
                    dtype=dtype_dict,
                    na_filter=False,  # Don't filter NA values
                    keep_default_na=False  # Don't use default NA values
                )
                
                self.logger.info(f"Successfully read file with {excel_engine} engine: {len(df)} rows, {len(df.columns)} columns")
                    
            except Exception as e:
                self.logger.error(f"Failed to read with {excel_engine} engine: {e}")
                # Try xlrd as fallback
                try:
                    df = pd.read_excel(
                        file_path, 
                        engine='xlrd', 
                        dtype=dtype_dict,
                        na_filter=False,  # Don't filter NA values
                        keep_default_na=False  # Don't use default NA values
                    )
                    self.logger.info(f"Successfully read file with xlrd engine: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e2:
                    self.logger.error(f"All Excel engines failed to read file: {file_path}")
                    self.logger.error(f"openpyxl error: {e}")
                    self.logger.error(f"xlrd error: {e2}")
                    return False
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            # Handle duplicate columns before processing
            df = handle_duplicate_columns(df)
            
            # Remove duplicates and reset index to avoid duplicate labels
            initial_count = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)  # Reset index to avoid duplicate labels
            final_count = len(df)
            if initial_count != final_count:
                self.logger.info(f"Removed {initial_count - final_count} duplicate rows")

            # Log all available columns for debugging
            self.logger.info(f"All columns in uploaded file: {df.columns.tolist()}")
            
            # Keep all columns but ensure only truly essential ones exist
            essential_columns = [
                'Product Name*', 'ProductName',  # Product name (at least one variant)
                'Product Type*',  # Product type
                'Vendor/Supplier*', 'Vendor'  # Vendor (at least one variant)
            ]
            
            # Check which essential columns are missing, but only warn if ALL variants are missing
            missing_columns = []
            has_product_name = any(col in df.columns for col in ['Product Name*', 'ProductName', 'Product Name'])
            has_vendor = any(col in df.columns for col in ['Vendor/Supplier*', 'Vendor', 'Vendor/Supplier'])
            has_product_type = 'Product Type*' in df.columns
            
            if not has_product_name:
                missing_columns.extend(['Product Name*', 'ProductName'])
            if not has_vendor:
                missing_columns.extend(['Vendor/Supplier*', 'Vendor'])
            if not has_product_type:
                missing_columns.append('Product Type*')
            
            # Only warn if we're actually missing essential columns
            if missing_columns:
                self.logger.warning(f"Missing essential columns: {missing_columns}")
            else:
                self.logger.info("All essential columns found")
            
            # Keep all columns - don't filter them out
            # df = df[existing_required]  # REMOVED - this was causing column loss

            self.df = df
            # Handle duplicate columns before any operations
            self.df = handle_duplicate_columns(self.df)
            # Reset index immediately after assignment to prevent duplicate labels
            self.df.reset_index(drop=True, inplace=True)
            self.logger.debug(f"Original columns: {self.df.columns.tolist()}")
            
            # 2) Trim product names
            if "Product Name*" in self.df.columns:
                self.df["Product Name*"] = self.df["Product Name*"].str.lstrip()
            elif "Product Name" in self.df.columns:
                self.df["Product Name*"] = self.df["Product Name"].str.lstrip()
            elif "ProductName" in self.df.columns:
                self.df["Product Name*"] = self.df["ProductName"].str.lstrip()
            else:
                self.logger.error("No product name column found")
                self.df["Product Name*"] = "Unknown"

            # 3) Ensure required columns exist
            for col in ["Product Type*", "Lineage", "Product Brand"]:
                if col not in self.df.columns:
                    self.df[col] = "Unknown"

            # 3.5) Determine product name column early (needed for lineage processing)
            product_name_col = 'Product Name*'
            if product_name_col not in self.df.columns:
                product_name_col = 'ProductName' if 'ProductName' in self.df.columns else None

            # 4) Exclude sample rows and deactivated products
            initial_count = len(self.df)
            excluded_by_type = self.df[self.df["Product Type*"].isin(EXCLUDED_PRODUCT_TYPES)]
            self.df = self.df[~self.df["Product Type*"].isin(EXCLUDED_PRODUCT_TYPES)]
            # Reset index after filtering to prevent duplicate labels
            self.df.reset_index(drop=True, inplace=True)
            self.logger.info(f"Excluded {len(excluded_by_type)} products by product type: {excluded_by_type['Product Type*'].unique().tolist()}")
            
            # Also exclude products with excluded patterns in the name
            for pattern in EXCLUDED_PRODUCT_PATTERNS:
                pattern_mask = self.df["Product Name*"].str.contains(pattern, case=False, na=False)
                excluded_by_pattern = self.df[pattern_mask]
                self.df = self.df[~pattern_mask]
                if len(excluded_by_pattern) > 0:
                    self.logger.info(f"Excluded {len(excluded_by_pattern)} products containing pattern '{pattern}': {excluded_by_pattern['Product Name*'].tolist()}")
            
            # Reset index after all filtering to prevent duplicate labels
            self.df.reset_index(drop=True, inplace=True)
            final_count = len(self.df)
            self.logger.info(f"Product filtering complete: {initial_count} -> {final_count} products (excluded {initial_count - final_count})")

            # 5) Rename for convenience (only if target columns don't already exist)
            rename_mapping = {}
            if "Product Name*" in self.df.columns and "ProductName" not in self.df.columns:
                rename_mapping["Product Name*"] = "ProductName"
            if "Weight Unit* (grams/gm or ounces/oz)" in self.df.columns and "Units" not in self.df.columns:
                rename_mapping["Weight Unit* (grams/gm or ounces/oz)"] = "Units"
            if "Price* (Tier Name for Bulk)" in self.df.columns and "Price" not in self.df.columns:
                rename_mapping["Price* (Tier Name for Bulk)"] = "Price"
            if "Vendor/Supplier*" in self.df.columns and "Vendor" not in self.df.columns:
                rename_mapping["Vendor/Supplier*"] = "Vendor"
                self.logger.info(f"Renaming column 'Vendor/Supplier*' to 'Vendor' during regular processing")
            elif "Vendor/Supplier*" in self.df.columns:
                self.logger.info(f"Column 'Vendor/Supplier*' found but 'Vendor' already exists - keeping both columns")
            elif "Vendor" in self.df.columns:
                self.logger.info(f"Column 'Vendor' found - no renaming needed")
            else:
                self.logger.warning(f"No vendor column found in DataFrame. Available columns: {[col for col in self.df.columns if 'vendor' in col.lower() or 'supplier' in col.lower()]}")
            if "DOH Compliant (Yes/No)" in self.df.columns and "DOH" not in self.df.columns:
                rename_mapping["DOH Compliant (Yes/No)"] = "DOH"
            if "Concentrate Type" in self.df.columns and "Ratio" not in self.df.columns:
                rename_mapping["Concentrate Type"] = "Ratio"
            # Excel compatibility column mappings
            if "Joint Ratio" in self.df.columns and "JointRatio" not in self.df.columns:
                rename_mapping["Joint Ratio"] = "JointRatio"
            if "Quantity Received*" in self.df.columns and "Quantity*" not in self.df.columns:
                rename_mapping["Quantity Received*"] = "Quantity*"
            if "qty" in self.df.columns and "Quantity*" not in self.df.columns:
                rename_mapping["qty"] = "Quantity*"
            
            if rename_mapping:
                self.df.rename(columns=rename_mapping, inplace=True)

            # Handle duplicate columns after renaming
            self.df = handle_duplicate_columns(self.df)

            # 5.5) Normalize product types using TYPE_OVERRIDES
            if "Product Type*" in self.df.columns:
                self.logger.info("Applying product type normalization...")
                # First trim whitespace from product types
                self.df["Product Type*"] = self.df["Product Type*"].str.strip()
                # Apply TYPE_OVERRIDES to normalize product types
                self.df["Product Type*"] = self.df["Product Type*"].replace(TYPE_OVERRIDES)
                self.logger.info(f"Product type normalization complete. Sample types: {self.df['Product Type*'].unique()[:10].tolist()}")

            # Update product_name_col after renaming
            if product_name_col == 'Product Name*':
                product_name_col = 'ProductName'

            # 6) Normalize units
            if "Units" in self.df.columns:
                self.df["Units"] = self.df["Units"].str.lower().replace(
                    {"ounces": "oz", "grams": "g"}, regex=True
                )

            # 7) Standardize Lineage
            # Reset index before lineage processing to prevent duplicate labels
            self.df.reset_index(drop=True, inplace=True)
            if "Lineage" in self.df.columns:
                self.logger.info("Starting lineage standardization process...")
                # First, standardize existing values
                self.df["Lineage"] = (
                    self.df["Lineage"]
                    .str.lower()
                    .replace({
                        "indica_hybrid": "HYBRID/INDICA",
                        "sativa_hybrid": "HYBRID/SATIVA",
                        "sativa": "SATIVA",
                        "hybrid": "HYBRID",
                        "indica": "INDICA",
                        "cbd": "CBD"
                    })
                    .str.upper()
                )
                
                # Fix invalid lineage assignments for classic types
                # Classic types should never have "MIXED" lineage
                from src.core.constants import CLASSIC_TYPES
                
                classic_mask = self.df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)
                mixed_lineage_mask = self.df["Lineage"] == "MIXED"
                classic_with_mixed_mask = classic_mask & mixed_lineage_mask
                
                if classic_with_mixed_mask.any():
                    self.df.loc[classic_with_mixed_mask, "Lineage"] = "HYBRID"
                    self.logger.info(f"Fixed {classic_with_mixed_mask.sum()} classic products with invalid MIXED lineage, changed to HYBRID")
                
                # For classic types, set empty lineage to HYBRID
                # For non-classic types, set empty lineage to MIXED or CBD based on content
                
                # Create mask for classic types
                classic_mask = self.df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)
                
                # Set empty lineage values based on product type
                empty_lineage_mask = self.df["Lineage"].isnull() | (self.df["Lineage"].astype(str).str.strip() == "")
                
                # For classic types, set to HYBRID (never MIXED)
                classic_empty_mask = classic_mask & empty_lineage_mask
                if classic_empty_mask.any():
                    self.df.loc[classic_empty_mask, "Lineage"] = "HYBRID"
                    self.logger.info(f"Assigned HYBRID lineage to {classic_empty_mask.sum()} classic products with empty lineage")
                
                # For non-classic types, check for CBD content first
                non_classic_empty_mask = ~classic_mask & empty_lineage_mask
                if non_classic_empty_mask.any():
                    # Define edible types
                    edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
                    
                    # Create mask for edible products
                    edible_mask = self.df["Product Type*"].str.strip().str.lower().isin(edible_types)
                    
                    # For edibles, be more conservative about CBD lineage assignment
                    if edible_mask.any():
                        # Only assign CBD lineage to edibles if they are explicitly CBD-focused
                        cbd_edible_mask = (
                            (self.df["Product Type*"].str.strip().str.lower() == "high cbd edible liquid") |
                            (self.df["Product Strain"].astype(str).str.lower().str.strip() == "cbd blend") |
                            (self.df[product_name_col].str.contains(r"\bCBD\b", case=False, na=False) if product_name_col else False)
                        )
                        
                        # Edibles with explicit CBD focus get CBD lineage
                        cbd_edible_empty = non_classic_empty_mask & edible_mask & cbd_edible_mask
                        if cbd_edible_empty.any():
                            self.df.loc[cbd_edible_empty, "Lineage"] = "CBD"
                            self.logger.info(f"Assigned CBD lineage to {cbd_edible_empty.sum()} CBD-focused edible products")
                        
                        # All other edibles get MIXED lineage
                        non_cbd_edible_empty = non_classic_empty_mask & edible_mask & ~cbd_edible_mask
                        if non_cbd_edible_empty.any():
                            self.df.loc[non_cbd_edible_empty, "Lineage"] = "MIXED"
                            self.logger.info(f"Assigned MIXED lineage to {non_cbd_edible_empty.sum()} edible products")
                    
                    # For non-edible non-classic types, use the original logic
                    non_edible_mask = ~edible_mask
                    non_edible_empty = non_classic_empty_mask & non_edible_mask
                    if non_edible_empty.any():
                        # Check if non-edible non-classic products contain CBD-related content
                        cbd_content_mask = (
                            self.df["Description"].str.contains(r"CBD|CBG|CBN|CBC", case=False, na=False) |
                            (self.df[product_name_col].str.contains(r"CBD|CBG|CBN|CBC", case=False, na=False) if product_name_col else False) |
                            (self.df["Product Strain"].astype(str).str.lower().str.strip() == "cbd blend")
                        )
                        
                        # Non-edible non-classic products with CBD content get CBD lineage
                        cbd_non_edible_empty = non_edible_empty & cbd_content_mask
                        if cbd_non_edible_empty.any():
                            self.df.loc[cbd_non_edible_empty, "Lineage"] = "CBD"
                        
                        # Non-edible non-classic products without CBD content get MIXED lineage
                        non_cbd_non_edible_empty = non_edible_empty & ~cbd_content_mask
                        if non_cbd_non_edible_empty.any():
                            self.df.loc[non_cbd_non_edible_empty, "Lineage"] = "MIXED"

            # 8) Build Description & Ratio & Strain
            if "ProductName" in self.df.columns:
                self.logger.debug("Building Description and Ratio columns")

                def get_description(name):
                    # Handle pandas Series and other non-string types
                    if name is None:
                        return ""
                    if isinstance(name, pd.Series):
                        if pd.isna(name).any():
                            return ""
                        name = name.iloc[0] if len(name) > 0 else ""
                    elif pd.isna(name):
                        return ""
                    name = str(name).strip()
                    if not name:
                        return ""
                    if ' by ' in name:
                        return name.split(' by ')[0].strip()
                    if ' - ' in name:
                        # Only split on dashes followed by weight information (numbers, decimals, units)
                        # This preserves product names like "Pre-Roll" while removing weight parts
                        import re
                        # Check if the dash is followed by weight information
                        if re.search(r' - [\d.]', name):
                            # Remove weight part but preserve the dash in product names
                            return re.sub(r' - [\d.].*$', '', name).strip()
                        else:
                            # No weight information, return the name as-is
                            return name.strip()
                    return name.strip()

                # Ensure Product Name* is string type before applying
                if product_name_col:
                    # Reset index to avoid duplicate labels before applying operations
                    self.df.reset_index(drop=True, inplace=True)
                    
                    # Ensure we get a Series, not a DataFrame
                    if isinstance(product_name_col, list):
                        product_name_col = product_name_col[0] if product_name_col else None
                    
                    if product_name_col and product_name_col in self.df.columns:
                        self.df[product_name_col] = self.df[product_name_col].astype(str)
                        # Ensure we get a Series by using .iloc[:, 0] if it's a DataFrame
                        product_names = self.df[product_name_col]
                        if isinstance(product_names, pd.DataFrame):
                            product_names = product_names.iloc[:, 0]
                        product_names = product_names.astype(str)
                        # Debug: Check if product_names is a Series or DataFrame
                        self.logger.debug(f"product_names type: {type(product_names)}, shape: {getattr(product_names, 'shape', 'N/A')}")
                        
                        # Ensure product_names is a Series before calling .str
                        if isinstance(product_names, pd.Series):
                            # CRITICAL FIX: Replace ALL Description values with processed Product Name
                            # This ensures consistent Description formatting using our established formula
                            self.df["Description"] = product_names.str.strip()
                            self.logger.debug(f"Replaced all Description values with processed Product Name")
                        else:
                            # Fallback: convert to string and strip manually
                            self.df["Description"] = product_names.astype(str).str.strip()
                            self.logger.debug(f"Replaced all Description values with processed Product Name (fallback)")
                        
                        # Handle ' by ' pattern for all Description values
                        mask_by = self.df["Description"].str.contains(' by ', na=False)
                        self.df.loc[mask_by, "Description"] = self.df.loc[mask_by, "Description"].str.split(' by ').str[0].str.strip()
                        
                        # Handle weight removal from Description - only remove weight parts, preserve product names with hyphens
                        # Use regex to find dashes followed by weight information (numbers, decimals, units)
                        mask_weight_dash = self.df["Description"].str.contains(r' - [\d.]', na=False)
                        if mask_weight_dash.any():
                            # Remove weight part but preserve the dash in product names like "Pre-Roll"
                            df_temp = self.df.loc[mask_weight_dash, "Description"].copy()
                            # Use regex to find the weight part and remove it (handles both " - 1g" and " - .5g")
                            df_temp = df_temp.str.replace(r' - [\d.].*$', '', regex=True)
                            self.df.loc[mask_weight_dash, "Description"] = df_temp
                        

                    else:
                        # Fallback to empty descriptions
                        self.df["Description"] = ""
                    
                    # Reset index again after operations to prevent duplicate labels
                    self.df.reset_index(drop=True, inplace=True)
                
                mask_para = self.df["Product Type*"].str.strip().str.lower() == "paraphernalia"
                self.df.loc[mask_para, "Description"] = (
                    self.df.loc[mask_para, "Description"]
                    .str.replace(r"\s*-\s*\d+g$", "", regex=True)
                )

                # Calculate complexity for Description column using vectorized operations
                # Reset index before applying to prevent duplicate labels
                self.df.reset_index(drop=True, inplace=True)
                # Use a safer approach for applying the complexity function
                try:
                    self.df["Description_Complexity"] = self.df["Description"].apply(_complexity)
                except Exception as e:
                    self.logger.warning(f"Error applying complexity function: {e}")
                    # Fallback: create a simple complexity based on length
                    self.df["Description_Complexity"] = self.df["Description"].str.len().fillna(0)
                # Reset index after apply operation to prevent duplicate labels
                self.df.reset_index(drop=True, inplace=True)

                # Build cannabinoid content info
                self.logger.debug("Extracting cannabinoid content from Product Name")
                # Extract text following the FINAL hyphen only, but not for classic types
                if product_name_col:
                    # Ensure we get a Series, not a DataFrame
                    product_names_for_ratio = self.df[product_name_col]
                    if isinstance(product_names_for_ratio, pd.DataFrame):
                        product_names_for_ratio = product_names_for_ratio.iloc[:, 0]
                    
                    # Don't extract weight for classic types (including rso/co2 tankers)
                    # Note: capsules are NOT classic types for ratio extraction - they should extract ratio like edibles
                    classic_types = ["flower", "pre-roll", "infused pre-roll", "concentrate", "solventless concentrate", "vape cartridge", "rso/co2 tankers"]
                    classic_mask = self.df["Product Type*"].str.strip().str.lower().isin(classic_types)
                    
                    # Extract ratio for non-classic types only (including capsules)
                    # For classic types, preserve existing ratio values from the file
                    non_classic_mask = ~classic_mask
                    if non_classic_mask.any():
                        extracted_ratios = product_names_for_ratio.loc[non_classic_mask].str.extract(r".*-\s*(.+)").fillna("")
                        # Ensure we get the first column as a Series
                        if isinstance(extracted_ratios, pd.DataFrame):
                            extracted_ratios = extracted_ratios.iloc[:, 0]
                        self.df.loc[non_classic_mask, "Ratio"] = extracted_ratios
                else:
                    self.df["Ratio"] = ""
                if 'Ratio' in self.df.columns:
                    self.logger.debug(f"Sample cannabinoid content values before processing: {self.df['Ratio'].head()}")
                else:
                    self.logger.debug("Ratio column not found, skipping ratio processing")
                
                # Replace "/" with space to remove backslash formatting
                if 'Ratio' in self.df.columns:
                    self.df["Ratio"] = self.df["Ratio"].str.replace(r"/", " ", regex=True)
                    
                    # Replace "nan" values with empty string to trigger default THC: CBD: formatting
                    self.df["Ratio"] = self.df["Ratio"].replace("nan", "")
                
                if 'Ratio' in self.df.columns:
                    self.logger.debug(f"Sample cannabinoid content values after processing: {self.df['Ratio'].head()}")

                # Set Ratio_or_THC_CBD based on product type
                def set_ratio_or_thc_cbd(row):
                    product_type = str(row.get("Product Type*", "")).strip().lower()
                    ratio = str(row.get("Ratio", "")).strip()
                    
                    # Handle "nan" values by replacing with empty string
                    if ratio.lower() == "nan":
                        ratio = ""
                    
                    # If product type is empty, treat as classic type (flower)
                    if not product_type:
                        product_type = "flower"
                    
                    classic_types = [
                        "flower", "pre-roll", "infused pre-roll", "concentrate", "solventless concentrate", "vape cartridge", "rso/co2 tankers"
                    ]
                    # Note: capsules are NOT classic types for ratio processing - they should be treated as edibles
                    BAD_VALUES = {"", "CBD", "THC", "CBD:", "THC:", "CBD:\n", "THC:\n", "nan"}
                    
                    # For pre-rolls and infused pre-rolls, use JointRatio if available, otherwise default format
                    if product_type in ["pre-roll", "infused pre-roll"]:
                        joint_ratio = str(row.get("JointRatio", "")).strip()
                        if joint_ratio and joint_ratio not in BAD_VALUES:
                            # Remove leading dash if present
                            if joint_ratio.startswith("- "):
                                joint_ratio = joint_ratio[2:]
                            return joint_ratio
                        return "THC: | BR | CBD:"
                    
                    # For solventless concentrate, check if ratio is a weight + unit format
                    if product_type == "solventless concentrate":
                        if not ratio or ratio in BAD_VALUES or not is_weight_with_unit(ratio):
                            return "1g"
                        return ratio
                    
                    if product_type in classic_types:
                        if not ratio or ratio in BAD_VALUES:
                            return "THC: | BR | CBD:"
                        # If ratio contains THC/CBD values, use it directly
                        if any(cannabinoid in ratio.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                            return ratio
                        # If it's a valid ratio format, use it
                        if is_real_ratio(ratio):
                            return ratio
                        # If it's a weight format (like "1g", "28g"), use it
                        if is_weight_with_unit(ratio):
                            return ratio
                        # Otherwise, use default THC:CBD format
                        return "THC: | BR | CBD:"
                    
                    # For Edibles, Topicals, Tinctures, etc., use the ratio if it contains cannabinoid content
                    edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
                    if product_type in edible_types:
                        if not ratio or ratio in BAD_VALUES:
                            return "THC: | BR | CBD:"
                        # If ratio contains cannabinoid content, use it
                        if any(cannabinoid in ratio.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                            return ratio
                        # If it's a weight format, use it
                        if is_weight_with_unit(ratio):
                            return ratio
                        # Otherwise, use default THC:CBD format
                        return "THC: | BR | CBD:"
                    
                    # For any other product type, return the ratio as-is
                    return ratio

                # Reset index before applying to prevent duplicate labels
                self.df.reset_index(drop=True, inplace=True)
                # Use a safer approach for applying the ratio function
                try:
                    self.df["Ratio_or_THC_CBD"] = self.df.apply(set_ratio_or_thc_cbd, axis=1)
                except Exception as e:
                    self.logger.warning(f"Error applying ratio function: {e}")
                    # Fallback: use default values
                    self.df["Ratio_or_THC_CBD"] = "THC: | BR | CBD:"
                # Reset index after apply operation to prevent duplicate labels
                self.df.reset_index(drop=True, inplace=True)
                self.logger.debug(f"Ratio_or_THC_CBD values: {self.df['Ratio_or_THC_CBD'].head()}")

                # Ensure Product Strain exists and is categorical
                if "Product Strain" not in self.df.columns:
                    self.df["Product Strain"] = ""
                # Fill null values before converting to categorical
                self.df["Product Strain"] = self.df["Product Strain"].fillna("Mixed")
                # Don't convert to categorical yet - wait until after all Product Strain logic is complete

                # Special case: paraphernalia gets Product Strain set to "Mixed" (not "Paraphernalia")
                # This prevents ProductStrain from matching ProductBrand for paraphernalia products
                mask_para = self.df["Product Type*"].str.strip().str.lower() == "paraphernalia"
                if mask_para.any():
                    # Set paraphernalia products to "Mixed" instead of "Paraphernalia"
                    # This prevents ProductStrain from matching ProductBrand
                    self.df.loc[mask_para, "Product Strain"] = "Mixed"
                    self.logger.info(f"Set ProductStrain to 'Mixed' for {mask_para.sum()} paraphernalia products")

                # Force CBD Blend for any ratio containing CBD, CBC, CBN or CBG
                if 'Ratio' in self.df.columns:
                    mask_cbd_ratio = self.df["Ratio"].str.contains(
                        r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False
                    )
                else:
                    mask_cbd_ratio = pd.Series([False] * len(self.df), index=self.df.index)
                # Use .any() to avoid Series boolean ambiguity
                if mask_cbd_ratio.any():
                    self.df.loc[mask_cbd_ratio, "Product Strain"] = "CBD Blend"
                    # Debug: Log which products got CBD Blend from ratio
                    cbd_products = self.df[mask_cbd_ratio]
                    for idx, row in cbd_products.iterrows():
                        self.logger.info(f"Assigned CBD Blend from ratio: {row.get('Product Name*', 'NO NAME')} (Type: {row.get('Product Type*', 'NO TYPE')})")
                
                # If Description, Product Name, or Ratio contains ":" or "CBD", set Product Strain to 'CBD Blend' 
                # Excluding most edibles but including tinctures (since tinctures are nonclassic types that should get CBD Blend designations)
                edible_types_exclude = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "topical", "capsule"}
                non_edible_or_tincture_mask = ~self.df["Product Type*"].str.strip().str.lower().isin(edible_types_exclude)
                
                # Check Description, Product Name, and Ratio for CBD content or ratio patterns
                description_cbd_mask = (self.df["Description"].str.contains(":", na=False) | self.df["Description"].str.contains("CBD", case=False, na=False))
                
                # Check if Product Name column exists (it might have different naming)
                product_name_cbd_mask = pd.Series([False] * len(self.df), index=self.df.index)
                if "Product Name*" in self.df.columns:
                    product_name_cbd_mask = (self.df["Product Name*"].str.contains(":", na=False) | self.df["Product Name*"].str.contains("CBD", case=False, na=False))
                elif "Product Name" in self.df.columns:
                    product_name_cbd_mask = (self.df["Product Name"].str.contains(":", na=False) | self.df["Product Name"].str.contains("CBD", case=False, na=False))
                elif "Product_Name" in self.df.columns:
                    product_name_cbd_mask = (self.df["Product_Name"].str.contains(":", na=False) | self.df["Product_Name"].str.contains("CBD", case=False, na=False))
                
                ratio_cbd_mask = (self.df["Ratio"].str.contains(":", na=False) | self.df["Ratio"].str.contains("CBD", case=False, na=False))
                
                mask_cbd_blend = (description_cbd_mask | product_name_cbd_mask | ratio_cbd_mask) & non_edible_or_tincture_mask
                # Use .any() to avoid Series boolean ambiguity
                if mask_cbd_blend.any():
                    self.df.loc[mask_cbd_blend, "Product Strain"] = "CBD Blend"
                    # Debug: Log which products got CBD Blend from description
                    cbd_desc_products = self.df[mask_cbd_blend]
                    for idx, row in cbd_desc_products.iterrows():
                        self.logger.info(f"Assigned CBD Blend from description: {row.get('Product Name*', 'NO NAME')} (Type: {row.get('Product Type*', 'NO TYPE')})")
                
                # NEW: If no strain in column, check if product contains CBD CBN CBG or CBC, or a ":" in description
                # This applies when Product Strain is empty, null, or "Mixed" (excluding edibles which have their own logic)
                no_strain_mask = (
                    self.df["Product Strain"].isnull() | 
                    (self.df["Product Strain"].astype(str).str.strip() == "") |
                    (self.df["Product Strain"].astype(str).str.lower().str.strip() == "mixed")
                )
                
                # Check if description, product name, or ratio contains cannabinoids or ":"
                description_cannabinoid_mask = (
                    self.df["Description"].str.contains(r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False) |
                    self.df["Description"].str.contains(":", na=False)
                )
                # Check if Product Name column exists (it might have different naming)
                product_name_cannabinoid_mask = pd.Series([False] * len(self.df), index=self.df.index)
                if "Product Name*" in self.df.columns:
                    product_name_cannabinoid_mask = (
                        self.df["Product Name*"].str.contains(r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False) |
                        self.df["Product Name*"].str.contains(":", na=False)
                    )
                elif "Product Name" in self.df.columns:
                    product_name_cannabinoid_mask = (
                        self.df["Product Name"].str.contains(r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False) |
                        self.df["Product Name"].str.contains(":", na=False)
                    )
                elif "Product_Name" in self.df.columns:
                    product_name_cannabinoid_mask = (
                        self.df["Product_Name"].str.contains(r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False) |
                        self.df["Product_Name"].str.contains(":", na=False)
                    )
                ratio_cannabinoid_mask = (
                    self.df["Ratio"].str.contains(r"\b(?:CBD|CBC|CBN|CBG)\b", case=False, na=False) |
                    self.df["Ratio"].str.contains(":", na=False)
                )
                cannabinoid_mask = description_cannabinoid_mask | product_name_cannabinoid_mask | ratio_cannabinoid_mask
                
                # Apply CBD Blend to non-edible products (including tinctures) with no strain that contain cannabinoids or ":"
                combined_cbd_mask = no_strain_mask & cannabinoid_mask & non_edible_or_tincture_mask
                if combined_cbd_mask.any():
                    self.df.loc[combined_cbd_mask, "Product Strain"] = "CBD Blend"
                    # Debug: Log which products got CBD Blend from combined logic
                    combined_cbd_products = self.df[combined_cbd_mask]
                    for idx, row in combined_cbd_products.iterrows():
                        self.logger.info(f"Assigned CBD Blend from combined logic: {row.get('Product Name*', 'NO NAME')} (Type: {row.get('Product Type*', 'NO TYPE')})")
                
                # TINCTURES: Special handling for tinctures as nonclassic types that should get CBD Blend/Mixed designations
                tincture_mask = self.df["Product Type*"].str.strip().str.lower() == "tincture"
                if tincture_mask.any():
                    tincture_products = self.df[tincture_mask]
                    self.logger.info(f"=== Tincture Product Strain Assignment ===")
                    
                    for idx, row in tincture_products.iterrows():
                        product_name = row.get('Product Name*', 'NO NAME')
                        current_strain = row.get('Product Strain', 'NO STRAIN')
                        description = row.get('Description', '')
                        ratio = row.get('Ratio', '')
                        
                        # Check if tincture should get CBD Blend designation
                        should_get_cbd_blend = False
                        
                        # Check ratio for cannabinoid content
                        BAD_VALUES = {"", "CBD", "THC", "CBD:", "THC:", "CBD:\n", "THC:\n", "nan"}
                        if ratio and pd.notna(ratio) and str(ratio).strip() not in BAD_VALUES:
                            if any(cannabinoid in str(ratio).upper() for cannabinoid in ['CBD', 'CBC', 'CBN', 'CBG']):
                                should_get_cbd_blend = True
                                self.logger.info(f"Tincture {product_name}: CBD Blend from ratio '{ratio}'")
                        
                        # Check description for cannabinoid content or ":"
                        if not should_get_cbd_blend and description:
                            if (':' in str(description) or 
                                any(cannabinoid in str(description).upper() for cannabinoid in ['CBD', 'CBC', 'CBN', 'CBG'])):
                                should_get_cbd_blend = True
                                self.logger.info(f"Tincture {product_name}: CBD Blend from description '{description}'")
                        
                        # Check product name for cannabinoid content or ":" (if column exists)
                        if not should_get_cbd_blend and product_name:
                            if (':' in str(product_name) or 
                                any(cannabinoid in str(product_name).upper() for cannabinoid in ['CBD', 'CBC', 'CBN', 'CBG'])):
                                should_get_cbd_blend = True
                                self.logger.info(f"Tincture {product_name}: CBD Blend from product name '{product_name}'")
                        
                        # Apply CBD Blend if criteria met, otherwise Mixed
                        if should_get_cbd_blend:
                            self.df.loc[idx, "Product Strain"] = "CBD Blend"
                        else:
                            self.df.loc[idx, "Product Strain"] = "Mixed"
                            self.logger.info(f"Tincture {product_name}: Mixed (no cannabinoid content found)")
                    
                    self.logger.info(f"=== End Tincture Product Strain Assignment ===")

                # Debug: Log final Product Strain values for RSO/CO2 Tankers
                rso_co2_mask = self.df["Product Type*"].str.strip().str.lower() == "rso/co2 tankers"
                if rso_co2_mask.any():
                    rso_co2_products = self.df[rso_co2_mask]
                    self.logger.info(f"=== RSO/CO2 Tankers Product Strain Debug ===")
                    for idx, row in rso_co2_products.iterrows():
                        self.logger.info(f"RSO/CO2 Tanker: {row.get('Product Name*', 'NO NAME')} -> Product Strain: '{row.get('Product Strain', 'NO STRAIN')}'")
                    self.logger.info(f"=== End RSO/CO2 Tankers Debug ===")
                
                # RSO/CO2 Tankers: if Description, Product Name, or Ratio contains CBD, CBG, CBC, CBN, or ":", then Product Strain is "CBD Blend", otherwise "Mixed"
                rso_co2_mask = self.df["Product Type*"].str.strip().str.lower() == "rso/co2 tankers"
                if rso_co2_mask.any():
                    # Check if Description, Product Name, or Ratio contains CBD, CBG, CBC, CBN, or ":"
                    description_cbd_content_mask = (
                        self.df["Description"].str.contains(r"CBD|CBG|CBC|CBN", case=False, na=False) |
                        self.df["Description"].str.contains(":", na=False)
                    )
                    # Check if Product Name column exists (it might have different naming)
                    product_name_cbd_content_mask = pd.Series([False] * len(self.df), index=self.df.index)
                    if "Product Name*" in self.df.columns:
                        product_name_cbd_content_mask = (
                            self.df["Product Name*"].str.contains(r"CBD|CBG|CBC|CBN", case=False, na=False) |
                            self.df["Product Name*"].str.contains(":", na=False)
                        )
                    elif "Product Name" in self.df.columns:
                        product_name_cbd_content_mask = (
                            self.df["Product Name"].str.contains(r"CBD|CBG|CBC|CBN", case=False, na=False) |
                            self.df["Product Name"].str.contains(":", na=False)
                        )
                    elif "Product_Name" in self.df.columns:
                        product_name_cbd_content_mask = (
                            self.df["Product_Name"].str.contains(r"CBD|CBG|CBC|CBN", case=False, na=False) |
                            self.df["Product_Name"].str.contains(":", na=False)
                        )
                    ratio_cbd_content_mask = (
                        self.df["Ratio"].str.contains(r"CBD|CBG|CBC|CBN", case=False, na=False) |
                        self.df["Ratio"].str.contains(":", na=False)
                    )
                    cbd_content_mask = description_cbd_content_mask | product_name_cbd_content_mask | ratio_cbd_content_mask
                    
                    # For RSO/CO2 Tankers with cannabinoid content or ":" in Description, set to "CBD Blend"
                    rso_co2_cbd_mask = rso_co2_mask & cbd_content_mask
                    if rso_co2_cbd_mask.any():
                        self.df.loc[rso_co2_cbd_mask, "Product Strain"] = "CBD Blend"
                        self.logger.info(f"Assigned 'CBD Blend' to {rso_co2_cbd_mask.sum()} RSO/CO2 Tankers with cannabinoid content or ':' in Description")
                    
                    # For RSO/CO2 Tankers without cannabinoid content or ":" in Description, set to "Mixed"
                    rso_co2_mixed_mask = rso_co2_mask & ~cbd_content_mask
                    if rso_co2_mixed_mask.any():
                        self.df.loc[rso_co2_mixed_mask, "Product Strain"] = "Mixed"
                        self.logger.info(f"Assigned 'Mixed' to {rso_co2_mixed_mask.sum()} RSO/CO2 Tankers without cannabinoid content or ':' in Description")

                # Edibles: if ProductName contains CBD, CBG, CBN, or CBC, then Product Strain is "CBD Blend", otherwise "Mixed"
                edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
                edible_mask = self.df["Product Type*"].str.strip().str.lower().isin(edible_types)
                if edible_mask.any():
                    # Check if ProductName contains CBD, CBG, CBN, or CBC (same as UI logic)
                    # Use the correct column name - try ProductName first, then Product Name*
                    product_name_col = "ProductName" if "ProductName" in self.df.columns else "Product Name*"
                    edible_cbd_content_mask = (
                        self.df[product_name_col].str.contains(r"CBD|CBG|CBN|CBC", case=False, na=False)
                    )
                    
                    # For edibles with cannabinoid content in ProductName, set to "CBD Blend"
                    edible_cbd_mask = edible_mask & edible_cbd_content_mask
                    if edible_cbd_mask.any():
                        self.df.loc[edible_cbd_mask, "Product Strain"] = "CBD Blend"
                        self.logger.info(f"Assigned 'CBD Blend' to {edible_cbd_mask.sum()} edibles with cannabinoid content in ProductName")
                    
                    # For edibles without cannabinoid content in ProductName, set to "Mixed"
                    edible_mixed_mask = edible_mask & ~edible_cbd_content_mask
                    if edible_mixed_mask.any():
                        self.df.loc[edible_mixed_mask, "Product Strain"] = "Mixed"
                        self.logger.info(f"Assigned 'Mixed' to {edible_mixed_mask.sum()} edibles without cannabinoid content in ProductName")

            # 8.5) Apply strain extraction logic for product names containing "Moonshot"
            # Call the dedicated method to ensure consistency
            self.apply_strain_extraction()
            
            # 8.6) OVERRIDE: Use database Product Strain values instead of Excel processor logic
            self.logger.info("=== OVERRIDING: Using Database Product Strain Values ===")
            self._apply_database_product_strain_values()
            self.logger.info("=== End Database Product Strain Override ===")
            
            # 8.7) Convert Product Strain to categorical after all logic is complete
            if "Product Strain" in self.df.columns:
                self.df["Product Strain"] = self.df["Product Strain"].astype("category")

            # 9) Convert key fields to categorical
            for col in ["Product Type*", "Lineage", "Product Brand", "Vendor"]:
                if col in self.df.columns:
                    # Fill null values before converting to categorical
                    self.df[col] = self.df[col].fillna("Unknown")
                    self.df[col] = self.df[col].astype("category")

            # 10) CBD and Mixed overrides (with edible lineage protection)
            if "Lineage" in self.df.columns:
                # Define edible types for protection
                edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
                edible_mask = self.df["Product Type*"].str.strip().str.lower().isin(edible_types)
                
                # If Product Strain is 'CBD Blend', set Lineage to 'CBD' (but protect edibles that already have proper lineage)
                if "Product Strain" in self.df.columns and "Lineage" in self.df.columns:
                    cbd_blend_mask = self.df["Product Strain"].astype(str).str.lower().str.strip() == "cbd blend"
                    # Only apply to non-edibles or edibles that don't already have a proper lineage
                    non_edible_cbd_blend = cbd_blend_mask & ~edible_mask
                    edible_cbd_blend_no_lineage = cbd_blend_mask & edible_mask & (
                        self.df["Lineage"].isnull() | 
                        (self.df["Lineage"].astype(str).str.strip() == "") |
                        (self.df["Lineage"].astype(str).str.strip() == "Unknown")
                    )
                    
                    combined_cbd_blend_mask = non_edible_cbd_blend | edible_cbd_blend_no_lineage
                    
                    if combined_cbd_blend_mask.any() and "Lineage" in self.df.columns:
                        if "CBD" not in self.df["Lineage"].cat.categories:
                            self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["CBD"])
                        self.df.loc[combined_cbd_blend_mask, "Lineage"] = "CBD"
                        self.logger.info(f"Assigned CBD lineage to {combined_cbd_blend_mask.sum()} products with CBD Blend strain")

                # If Description or Product Name* contains CBD, CBG, CBN, CBC, set Lineage to 'CBD' (but protect edibles)
                # Fix: ensure product_name_col is always a Series for .str methods
                if product_name_col:
                    product_names_for_cbd = self.df[product_name_col]
                    if isinstance(product_names_for_cbd, pd.DataFrame):
                        product_names_for_cbd = product_names_for_cbd.iloc[:, 0]
                else:
                    product_names_for_cbd = pd.Series("")
                cbd_mask = (
                    self.df["Description"].str.contains(r"CBD|CBG|CBN|CBC", case=False, na=False) |
                    (product_names_for_cbd.str.contains(r"CBD|CBG|CBN|CBC", case=False, na=False) if product_name_col else False)
                )
                # Only apply to non-edibles or edibles that don't already have a proper lineage
                non_edible_cbd = cbd_mask & ~edible_mask
                edible_cbd_no_lineage = cbd_mask & edible_mask & (
                    (self.df["Lineage"].isnull() if "Lineage" in self.df.columns else True) | 
                    (self.df["Lineage"].astype(str).str.strip() == "" if "Lineage" in self.df.columns else True) |
                    (self.df["Lineage"].astype(str).str.strip() == "Unknown" if "Lineage" in self.df.columns else True)
                )
                
                combined_cbd_mask = non_edible_cbd | edible_cbd_no_lineage
                
                # Use .any() to avoid Series boolean ambiguity
                if combined_cbd_mask.any() and "Lineage" in self.df.columns:
                    self.df.loc[combined_cbd_mask, "Lineage"] = "CBD"
                    self.logger.info(f"Assigned CBD lineage to {combined_cbd_mask.sum()} products with cannabinoid content")

                # DISABLED: If Lineage is missing or empty, set to 'MIXED'
                # empty_lineage_mask = self.df["Lineage"].isnull() | (self.df["Lineage"].astype(str).str.strip() == "")
                # if "MIXED" not in self.df["Lineage"].cat.categories:
                #     self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["MIXED"])
                # # Use .any() to avoid Series boolean ambiguity
                # if empty_lineage_mask.any():
                #     self.df.loc[empty_lineage_mask, "Lineage"] = "MIXED"

                # DISABLED: For all edibles, set Lineage to 'MIXED' unless already 'CBD'
                # edible_types = {"edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule"}
                # if "Product Type*" in self.df.columns:
                #     edible_mask = self.df["Product Type*"].str.strip().str.lower().isin([e.lower() for e in edible_types])
                #     not_cbd_mask = self.df["Lineage"].astype(str).str.upper() != "CBD"
                #     if "MIXED" not in self.df["Lineage"].cat.categories:
                #         self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["MIXED"])
                #     # Use .any() to avoid Series boolean ambiguity
                #     combined_mask = edible_mask & not_cbd_mask
                #     if combined_mask.any():
                #         self.df.loc[combined_mask, "Lineage"] = "MIXED"

            # 11) Normalize Weight* and CombinedWeight
            if "Weight*" in self.df.columns:
                def format_weight_value(x):
                    if pd.isna(x) or x is None or x == '':
                        return ''
                    try:
                        float_val = float(x)
                        if float_val.is_integer():
                            return str(int(float_val))
                        else:
                            # Round to 2 decimal places and remove trailing zeros
                            return f"{float_val:.2f}".rstrip("0").rstrip(".")
                    except (ValueError, TypeError):
                        return str(x)
                
                self.df["Weight*"] = self.df["Weight*"].apply(format_weight_value)
            if "Weight*" in self.df.columns and "Units" in self.df.columns:
                # Fill null values before converting to categorical
                combined_weight = (self.df["Weight*"] + self.df["Units"]).fillna("Unknown")
                self.df["CombinedWeight"] = combined_weight.astype("category")

            # 12) Format Price
            if "Price" in self.df.columns:
                def format_p(p):
                    if pd.isna(p) or p == '':
                        return ""
                    s = str(p).strip().lstrip("$").replace("'", "").strip()
                    try:
                        v = float(s)
                        if v.is_integer():
                            return f"${int(v)}"
                        else:
                            # Round to 2 decimal places and remove trailing zeros
                            return f"${v:.2f}".rstrip('0').rstrip('.')
                    except:
                        return f"${s}"
                self.df["Price"] = self.df["Price"].apply(lambda x: format_p(x) if pd.notnull(x) else "")
                self.df["Price"] = self.df["Price"].astype("string")

            # 13) Special pre-roll Ratio logic
            def process_ratio(row):
                t = str(row.get("Product Type*", "")).strip().lower()
                if t in ["pre-roll", "infused pre-roll"]:
                    # For pre-rolls, extract the weight/quantity part after the last hyphen
                    ratio_str = str(row.get("Ratio", ""))
                    if " - " in ratio_str:
                        parts = ratio_str.split(" - ")
                        if len(parts) >= 2:
                            # Take everything after the last hyphen
                            weight_part = parts[-1].strip()
                            return f" - {weight_part}" if weight_part and not weight_part.startswith(" - ") else weight_part
                    return ratio_str
                return row.get("Ratio", "")
            
            self.logger.debug("Applying special pre-roll ratio logic")
            self.df["Ratio"] = self.df.apply(process_ratio, axis=1)
            if 'Ratio' in self.df.columns:
                self.logger.debug(f"Final Ratio values after pre-roll processing: {self.df['Ratio'].head()}")

            # Create JointRatio column for Pre-Roll and Infused Pre-Roll products
            preroll_mask = self.df["Product Type*"].str.strip().str.lower().isin(["pre-roll", "infused pre-roll"])
            self.df["JointRatio"] = ""
            
            if preroll_mask.any():
                # Extract joint ratio from Product Name since there's no separate "Joint Ratio" column
                # Look for patterns like "0.5g x 2 Pack", "1g x 28 Pack", etc. in the product name
                def extract_joint_ratio_from_name(product_name):
                    if pd.isna(product_name) or str(product_name).strip() == '':
                        return ''
                    
                    product_name_str = str(product_name)
                    
                    # Look for patterns like "0.5g x 2 Pack", "1g x 28 Pack", etc.
                    import re
                    
                    # Pattern 1: "weight x count Pack" (e.g., "0.5g x 2 Pack", ".75g x 5 Pack")
                    pattern1 = r'(\d*\.?\d+g)\s*x\s*(\d+)\s*Pack'
                    match1 = re.search(pattern1, product_name_str, re.IGNORECASE)
                    if match1:
                        weight = match1.group(1)
                        count = match1.group(2)
                        return f"{weight} x {count} Pack"
                    
                    # Pattern 2: "weight x count" (e.g., "0.5g x 2", ".75g x 5")
                    pattern2 = r'(\d*\.?\d+g)\s*x\s*(\d+)'
                    match2 = re.search(pattern2, product_name_str, re.IGNORECASE)
                    if match2:
                        weight = match2.group(1)
                        count = match2.group(2)
                        return f"{weight} x {count}"
                    
                    # Pattern 3: Just weight (e.g., "1g", "0.5g", ".75g")
                    pattern3 = r'(\d*\.?\d+g)'
                    match3 = re.search(pattern3, product_name_str, re.IGNORECASE)
                    if match3:
                        weight = match3.group(1)
                        return weight
                    
                    return ''
                
                # Apply the extraction function to pre-roll products
                preroll_products = self.df[preroll_mask]
                for idx in preroll_products.index:
                    # Use the correct column name - check if ProductName exists, otherwise use Product Name*
                    product_name_col = 'ProductName' if 'ProductName' in self.df.columns else 'Product Name*'
                    if product_name_col in self.df.columns:
                        product_name = self.df.loc[idx, product_name_col]
                        joint_ratio = extract_joint_ratio_from_name(product_name)
                        if joint_ratio:
                            self.df.loc[idx, 'JointRatio'] = joint_ratio
                            # self.logger.debug(f"Extracted JointRatio '{joint_ratio}' from product name: '{product_name}'")
                
                # For remaining pre-rolls without valid JointRatio, try to generate from Weight
                remaining_preroll_mask = preroll_mask & (self.df["JointRatio"] == '')
                for idx in self.df[remaining_preroll_mask].index:
                    weight_value = self.df.loc[idx, 'Weight*']
                    if pd.notna(weight_value) and str(weight_value).strip() != '' and str(weight_value).lower() != 'nan':
                        try:
                            weight_float = float(weight_value)
                            # Generate simplified format: "1g" for single units
                            if weight_float == 1.0:
                                default_joint_ratio = "1g"
                            else:
                                # Format weight similar to price formatting - no decimals unless original has decimals
                                if weight_float.is_integer():
                                    default_joint_ratio = f"{int(weight_float)}g"
                                else:
                                    # Round to 2 decimal places and remove trailing zeros
                                    default_joint_ratio = f"{weight_float:.2f}".rstrip("0").rstrip(".") + "g"
                            self.df.loc[idx, 'JointRatio'] = default_joint_ratio
                            # self.logger.debug(f"Generated JointRatio for record {idx}: '{default_joint_ratio}' from Weight {weight_value}")
                        except (ValueError, TypeError):
                            pass
            
            # Ensure no NaN values remain in JointRatio column
            self.df["JointRatio"] = self.df["JointRatio"].fillna('')
            
            # Fix: Replace any 'nan' string values with empty strings
            nan_string_mask = (self.df["JointRatio"].astype(str).str.lower() == 'nan')
            self.df.loc[nan_string_mask, "JointRatio"] = ''
            
            # Fix: For still empty JointRatio, generate default from Weight (no Ratio fallback)
            still_empty_mask = preroll_mask & (self.df["JointRatio"] == '')
            for idx in self.df[still_empty_mask].index:
                weight_value = self.df.loc[idx, 'Weight*']
                if pd.notna(weight_value) and str(weight_value).strip() != '' and str(weight_value).lower() != 'nan':
                    try:
                        weight_float = float(weight_value)
                        # Generate simplified format: "1g" for single units
                        if weight_float == 1.0:
                            default_joint_ratio = "1g"
                        else:
                            # Format weight similar to price formatting - no decimals unless original has decimals
                            if weight_float.is_integer():
                                default_joint_ratio = f"{int(weight_float)}g"
                            else:
                                # Round to 2 decimal places and remove trailing zeros
                                default_joint_ratio = f"{weight_float:.2f}".rstrip("0").rstrip(".") + "g"
                        self.df.loc[idx, 'JointRatio'] = default_joint_ratio
                        # self.logger.debug(f"Fixed JointRatio for record {idx}: Generated default '{default_joint_ratio}' from Weight")
                    except (ValueError, TypeError):
                        pass
            
            # JointRatio: preserve original spacing exactly as in Excel - no normalization
            # self.logger.debug(f"Sample JointRatio values after NaN fixes: {self.df.loc[preroll_mask, 'JointRatio'].head()}")
            # Add detailed logging for JointRatio values
            if preroll_mask.any():
                sample_values = self.df.loc[preroll_mask, 'JointRatio'].head(10)
                for idx, value in sample_values.items():
                    # self.logger.debug(f"JointRatio value '{value}' (length: {len(str(value))}, repr: {repr(str(value))})")
                    pass

            # Reorder columns to place JointRatio next to Ratio
            if "Ratio" in self.df.columns and "JointRatio" in self.df.columns:
                ratio_col_idx = self.df.columns.get_loc("Ratio")
                cols = self.df.columns.tolist()
                
                # Remove duplicates first
                unique_cols = []
                seen_cols = set()
                for col in cols:
                    if col not in seen_cols:
                        unique_cols.append(col)
                        seen_cols.add(col)
                    else:
                        self.logger.warning(f"Removing duplicate column in JointRatio reorder: {col}")
                
                cols = unique_cols
                cols.remove("JointRatio")
                cols.insert(ratio_col_idx + 1, "JointRatio")
                # Ensure Description_Complexity is preserved
                if "Description_Complexity" not in cols:
                    cols.append("Description_Complexity")
                self.df = self.df[cols]

            # --- Reorder columns: move Description_Complexity, Ratio_or_THC_CBD, CombinedWeight after Lineage ---
            # First, remove any duplicate column names to prevent DataFrame issues
            cols = self.df.columns.tolist()
            unique_cols = []
            seen_cols = set()
            for col in cols:
                if col not in seen_cols:
                    unique_cols.append(col)
                    seen_cols.add(col)
                else:
                    self.logger.warning(f"Removing duplicate column: {col}")
            
            cols = unique_cols
            
            def move_after(col_to_move, after_col):
                if col_to_move in cols and after_col in cols:
                    cols.remove(col_to_move)
                    idx = cols.index(after_col)
                    cols.insert(idx+1, col_to_move)
            move_after('Description_Complexity', 'Lineage')
            move_after('Ratio_or_THC_CBD', 'Lineage')
            move_after('CombinedWeight', 'Lineage')
            self.df = self.df[cols]

            # Normalize Joint Ratio column name for consistency
            if "Joint Ratio" in self.df.columns and "JointRatio" not in self.df.columns:
                self.df.rename(columns={"Joint Ratio": "JointRatio"}, inplace=True)
            # self.logger.debug(f"Columns after JointRatio normalization: {self.df.columns.tolist()}")

            # 14) Optimized Lineage Persistence - ALWAYS ENABLED
            if ENABLE_LINEAGE_PERSISTENCE:
                self.logger.debug("Applying optimized lineage persistence from database")
                
                # Apply lineage persistence from database
                self.df = optimized_lineage_persistence(self, self.df)
                
                # Update database with current lineage information
                batch_lineage_database_update(self, self.df)
                
                self.logger.debug("Optimized lineage persistence complete")
            else:
                self.logger.debug("Lineage persistence disabled")

            # Optimize memory usage for PythonAnywhere
            self.logger.debug("Optimizing memory usage for PythonAnywhere")
            
            # Convert string columns to categorical where appropriate to save memory
            categorical_columns = ['Product Type*', 'Lineage', 'Product Brand', 'Vendor', 'Product Strain']
            for col in categorical_columns:
                if col in self.df.columns:
                    # Only convert if the column has reasonable number of unique values
                    unique_count = self.df[col].nunique()
                    if unique_count < len(self.df) * 0.5:  # Less than 50% unique values
                        self.df[col] = self.df[col].astype('category')
                        self.logger.debug(f"Converted {col} to categorical (unique values: {unique_count})")
            
            # Final cleanup: remove any remaining duplicate columns
            cols = self.df.columns.tolist()
            unique_cols = []
            seen_cols = set()
            for col in cols:
                if col not in seen_cols:
                    unique_cols.append(col)
                    seen_cols.add(col)
                else:
                    self.logger.warning(f"Final cleanup: removing duplicate column: {col}")
            
            if len(unique_cols) != len(cols):
                self.df = self.df[unique_cols]
                self.logger.info(f"Final cleanup: removed {len(cols) - len(unique_cols)} duplicate columns")
            
            # Cache dropdown values
            self._cache_dropdown_values()
            self.logger.debug(f"Final columns after all processing: {self.df.columns.tolist()}")
            self.logger.debug(f"Sample data after all processing:\n{self.df[['ProductName', 'Description', 'Ratio', 'Product Strain']].head()}")
            
            # Log memory usage for PythonAnywhere monitoring
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                self.logger.info(f"Memory usage after file load: {memory_info.rss / (1024*1024):.2f} MB")
            except ImportError:
                self.logger.debug("psutil not available for memory monitoring")
            
            # --- Product/Strain Database Integration (Background Processing) ---
            # Re-enabled to ensure lineage changes persist after reload
            self._schedule_product_db_integration()
            
            # Load lineage data from database to ensure changes persist
            self._load_lineage_from_database()
            
            # Cache the processed file
            self._file_cache[cache_key] = self.df.copy()
            self._last_loaded_file = file_path
            
            # Manage cache size
            self._manage_cache_size()
            
            # Force garbage collection to free memory
            import gc
            gc.collect()

            # --- After classic type lineage logic, enforce non-classic type rules ---
            if "Product Type*" in self.df.columns and "Lineage" in self.df.columns:
                # Define specific non-classic types that should always use MIXED or CBD Blend
                nonclassic_product_types = [
                    "edible (solid)", "edible (liquid)", "Edible (Solid)", "Edible (Liquid)",
                    "tincture", "Tincture", "topical", "Topical", 
                    "capsule", "Capsule", "suppository", "Suppository", "transdermal", "Transdermal",
                    "beverage", "Beverage", "powder", "Powder",
                    "gummy", "Gummy", "chocolate", "Chocolate", "cookie", "Cookie", 
                    "brownie", "Brownie", "candy", "Candy", "drink", "Drink",
                    "tea", "Tea", "coffee", "Coffee", "soda", "Soda", "juice", "Juice", 
                    "smoothie", "Smoothie", "shot", "Shot"
                ]
                
                # Identify non-classic types - products that are NOT in CLASSIC_TYPES
                from src.core.constants import CLASSIC_TYPES
                nonclassic_mask = ~self.df["Product Type*"].str.strip().str.lower().isin([c.lower() for c in CLASSIC_TYPES])
                
                # Add debugging
                self.logger.info(f"Non-classic type processing: Found {nonclassic_mask.sum()} non-classic products")
                if nonclassic_mask.any():
                    sample_types = self.df.loc[nonclassic_mask, "Product Type*"].unique()
                    self.logger.info(f"Sample non-classic product types: {sample_types}")
                
                # Identify CBD Blend products
                is_cbd_blend = (
                    self.df["Product Strain"].astype(str).str.lower().str.strip() == "cbd blend"
                ) | (
                    self.df["Description"].astype(str).str.lower().str.contains("cbd blend", na=False)
                )
                
                # Set Lineage to 'CBD' for blends (not 'CBD Blend')
                if "CBD" not in self.df["Lineage"].cat.categories:
                    self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["CBD"])
                self.df.loc[nonclassic_mask & is_cbd_blend, "Lineage"] = "CBD"
                
                # For all other non-classic types, set Lineage to 'MIXED' unless already 'CBD'
                if "MIXED" not in self.df["Lineage"].cat.categories:
                    self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["MIXED"])
                not_cbd = ~self.df["Lineage"].astype(str).str.upper().isin(["CBD"])
                self.df.loc[nonclassic_mask & not_cbd, "Lineage"] = "MIXED"
                
                # Never allow 'HYBRID' for non-classic types
                hybrid_mask = nonclassic_mask & (self.df["Lineage"].astype(str).str.upper() == "HYBRID")
                if hybrid_mask.any():
                    self.logger.info(f"Converting {hybrid_mask.sum()} non-classic products from HYBRID to MIXED")
                    self.df.loc[hybrid_mask, "Lineage"] = "MIXED"

            # --- Set default lineage for ALL products with missing lineage ---
            if "Product Type*" in self.df.columns and "Lineage" in self.df.columns:
                # Enhanced check for missing lineage (includes NaN, null, empty, and 'nan' strings)
                empty_lineage_mask = (
                    self.df["Lineage"].isnull() | 
                    (self.df["Lineage"].astype(str).str.strip() == "") |
                    (self.df["Lineage"].astype(str).str.lower().str.strip() == "nan")
                )
                
                classic_mask = self.df["Product Type*"].str.strip().str.lower().isin([c.lower() for c in CLASSIC_TYPES])
                nonclassic_mask = ~classic_mask
                
                # Add categories if they don't exist
                if "HYBRID" not in self.df["Lineage"].cat.categories:
                    self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["HYBRID"])
                if "MIXED" not in self.df["Lineage"].cat.categories:
                    self.df["Lineage"] = self.df["Lineage"].cat.add_categories(["MIXED"])
                
                # Set default lineage for classic types (HYBRID)
                set_hybrid_mask = classic_mask & empty_lineage_mask
                if set_hybrid_mask.any():
                    self.df.loc[set_hybrid_mask, "Lineage"] = "HYBRID"
                    self.logger.info(f"Set HYBRID lineage for {set_hybrid_mask.sum()} classic products with missing lineage")
                
                # Set default lineage for non-classic types (MIXED)
                set_mixed_mask = nonclassic_mask & empty_lineage_mask
                if set_mixed_mask.any():
                    self.df.loc[set_mixed_mask, "Lineage"] = "MIXED"
                    self.logger.info(f"Set MIXED lineage for {set_mixed_mask.sum()} non-classic products with missing lineage")
                
                # Fix any MIXED lineage for classic types
                mixed_lineage_mask = (self.df["Lineage"] == "MIXED") & classic_mask
                if mixed_lineage_mask.any():
                    self.df.loc[mixed_lineage_mask, "Lineage"] = "HYBRID"
                    self.logger.info(f"Fixed {mixed_lineage_mask.sum()} classic products with MIXED lineage, changed to HYBRID")

            self.logger.info(f"File loaded successfully: {len(self.df)} rows, {len(self.df.columns)} columns")
            return True
            
        except MemoryError as me:
            self.logger.error(f"Memory error loading file: {str(me)}")
            # Clear any partial data
            if hasattr(self, 'df'):
                del self.df
                self.df = None
            import gc
            gc.collect()
            return False
            
        except Exception as e:
            self.logger.error(f"Error loading file: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Clear any partial data
            if hasattr(self, 'df'):
                del self.df
                self.df = None
            return False

    def apply_filters(self, filters: Optional[Dict[str, str]] = None):
        """Apply filters to the DataFrame."""
        if self.df is None or not filters:
            return self.df

        self.logger.debug(f"apply_filters received filters: {filters}")
        filtered_df = self.df.copy()
        column_mapping = {
            'vendor': 'Vendor',
            'brand': 'Product Brand',
            'productType': 'Product Type*',
            'lineage': 'Lineage',
            'weight': 'Weight*',
            'strain': 'Product Strain',
            'doh': 'DOH',
            'highCbd': 'Product Type*'  # Will be processed specially
        }
        for filter_key, value in filters.items():
            if value and value != 'All':
                if filter_key == 'highCbd':
                    # Special handling for High CBD filter
                    if value == 'High CBD Products':
                        filtered_df = filtered_df[
                            filtered_df['Product Type*'].astype(str).str.lower().str.strip().str.startswith('high cbd')
                        ]
                    elif value == 'Non-High CBD Products':
                        filtered_df = filtered_df[
                            ~filtered_df['Product Type*'].astype(str).str.lower().str.strip().str.startswith('high cbd')
                        ]
                else:
                    column = column_mapping.get(filter_key)
                    if column and column in filtered_df.columns:
                        # Convert both the column and the filter value to lowercase for case-insensitive comparison
                        filtered_df = filtered_df[
                            filtered_df[column].astype(str).str.lower().str.strip() == value.lower().strip()
                        ]
        return filtered_df

    def _cache_dropdown_values(self):
        """Cache unique values for dropdown filters."""
        if self.df is None:
            logger.warning("No DataFrame loaded, cannot cache dropdown values")
            return

        filter_columns = {
            'vendor': 'Vendor',
            'brand': 'Product Brand',
            'productType': 'Product Type*',
            'lineage': 'Lineage',
            'weight': 'Weight*',
            'strain': 'Product Strain',
            'doh': 'DOH',
            'highCbd': 'Product Type*'  # Will be processed specially
        }
        self.dropdown_cache = {}
        for filter_id, column in filter_columns.items():
            if column in self.df.columns:
                values = self.df[column].dropna().unique().tolist()
                values = [str(v) for v in values if str(v).strip()]
                # Exclude unwanted product types from dropdown
                if filter_id == 'productType':
                    filtered_values = []
                    for v in values:
                        v_lower = v.strip().lower()
                        if (('trade sample' in v_lower and 'not for sale' in v_lower) or 'deactivated' in v_lower):
                            continue
                        filtered_values.append(v)
                    values = filtered_values
                self.dropdown_cache[filter_id] = sorted(values)
            else:
                self.dropdown_cache[filter_id] = []

    def get_available_tags(self, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Return a list of tag objects with all necessary data."""
        if self.df is None:
            logger.warning("DataFrame is None in get_available_tags")
            return []
        
        filtered_df = self.apply_filters(filters) if filters else self.df
        logger.info(f"get_available_tags: DataFrame shape {self.df.shape}, filtered shape {filtered_df.shape}")
        
        tags = []
        seen_product_keys = set()  # Track seen product keys to prevent duplicates
        
        for _, row in filtered_df.iterrows():
            # Get quantity from various possible column names
            quantity = row.get('Quantity*', '') or row.get('Quantity Received*', '') or row.get('Quantity', '') or row.get('qty', '') or ''
            
            # Get formatted weight with units
            weight_with_units = self._format_weight_units(row, excel_priority=True)
            raw_weight = row.get('Weight*', '')
            
            # Helper function to safely get values and handle NaN
            def safe_get_value(value, default=''):
                if value is None:
                    return default
                if isinstance(value, pd.Series):
                    if pd.isna(value).any():
                        return default
                    value = value.iloc[0] if len(value) > 0 else default
                elif pd.isna(value):
                    return default
                return str(value).strip()
            
            # Use the dynamically detected product name column
            product_name_col = 'Product Name*'
            if product_name_col not in self.df.columns:
                possible_cols = ['ProductName', 'Product Name', 'Description']
                product_name_col = next((col for col in possible_cols if col in self.df.columns), None)
                if not product_name_col:
                    product_name_col = 'Description'  # Fallback to Description
            
            # Get the product name
            product_name = safe_get_value(row.get(product_name_col, '')) or safe_get_value(row.get('Description', '')) or 'Unnamed Product'
            
            # Get vendor and brand for deduplication
            vendor_value = (
                safe_get_value(row.get('Vendor/Supplier*', '')) or  # Primary column name
                safe_get_value(row.get('Vendor', '')) or           # Alternative column name
                safe_get_value(row.get('Vendor/Supplier', ''))     # Fallback column name
            )
            brand_value = safe_get_value(row.get('Product Brand', ''))
            weight_value = safe_get_value(raw_weight)
            
            # Create a unique key that includes vendor/brand/weight to allow same product names with different weights
            product_key = f"{product_name}|{vendor_value}|{brand_value}|{weight_value}"
            
            # Skip if we've already seen this product key (deduplication)
            if product_key in seen_product_keys:
                logger.debug(f"Skipping exact duplicate product: {product_key}")
                continue
            
            # Add to seen set
            seen_product_keys.add(product_key)
            
            # Get vendor from multiple possible column names
            vendor_value = (
                safe_get_value(row.get('Vendor/Supplier*', '')) or  # Primary column name
                safe_get_value(row.get('Vendor', '')) or           # Alternative column name
                safe_get_value(row.get('Vendor/Supplier', ''))     # Fallback column name
            )
            
            # Debug logging for vendor field detection
            if not vendor_value and product_name:
                logger.debug(f"Vendor field is empty for product '{product_name}'. Available vendor columns: {[col for col in row.index if 'vendor' in col.lower() or 'supplier' in col.lower()]}")
                logger.debug(f"Row vendor values: Vendor/Supplier*='{row.get('Vendor/Supplier*', '')}', Vendor='{row.get('Vendor', '')}', Vendor/Supplier='{row.get('Vendor/Supplier', '')}'")
            
            # Extract THC/CBD values from the appropriate columns
            # Use the actual column names from the Excel file
            total_thc_value = safe_get_value(row.get('Total THC', ''))
            thc_content_value = safe_get_value(row.get('THC Content', ''))  # Use THC Content
            thc_test_result = safe_get_value(row.get('THC Content', ''))  # Use THC Content
            total_cbd_value = safe_get_value(row.get('Total CBD', ''))  # Use Total CBD
            cbd_content_value = safe_get_value(row.get('CBD Content', ''))  # Use CBD Content
            
            # Helper function to safely convert to float for comparison
            def safe_float(value):
                if not value or value in ['nan', 'NaN', '']:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # For THC: Use the highest value among Total THC, THC test result, and THCA
            total_thc_float = safe_float(total_thc_value)
            thc_test_float = safe_float(thc_test_result)
            thc_content_float = safe_float(thc_content_value)
            
            if total_thc_float > 0:
                if thc_test_float > total_thc_float:
                    ai_value = thc_test_result
                else:
                    ai_value = total_thc_value
            else:
                # Total THC is 0 or empty, compare THCA vs THC test result
                if thc_content_float > 0 and thc_content_float >= thc_test_float:
                    ai_value = thc_content_value
                elif thc_test_float > 0:
                    ai_value = thc_test_result
                else:
                    ai_value = ''
            
            # For CBD: merge CBDA with CBD test result, use highest value
            total_cbd_float = safe_float(total_cbd_value)
            cbd_content_float = safe_float(cbd_content_value)
            
            if cbd_content_float > total_cbd_float:
                ak_value = cbd_content_value
            else:
                ak_value = total_cbd_value
            
            # Clean up the values (remove 'nan', empty strings, etc.)
            if ai_value in ['nan', 'NaN', '']:
                ai_value = ''
            if ak_value in ['nan', 'NaN', '']:
                ak_value = ''
            
            # Get price value - use the actual column name from Excel file
            price_value = safe_get_value(row.get('Price*', '')) or safe_get_value(row.get('Price', '')) or safe_get_value(row.get('Price* (Tier Name for Bulk)', ''))
            
            tag = {
                'Product Name*': product_name,
                'Vendor': vendor_value,
                'Vendor/Supplier*': vendor_value,
                'Product Brand': safe_get_value(row.get('Product Brand', '')),
                'ProductBrand': safe_get_value(row.get('Product Brand', '')),
                'Lineage': safe_get_value(row.get('Lineage', 'MIXED')),
                'Product Type*': safe_get_value(row.get('Product Type*', '')),
                'Product Type': safe_get_value(row.get('Product Type*', '')),
                'Weight*': safe_get_value(raw_weight),
                'Weight': safe_get_value(raw_weight),
                'Units': safe_get_value(row.get('Units', '')),  # Add Units field for label generation
                'WeightWithUnits': safe_get_value(weight_with_units),
                'WeightUnits': safe_get_value(weight_with_units),  # Add WeightUnits for frontend compatibility
                'Quantity*': safe_get_value(quantity),
                'Quantity Received*': safe_get_value(quantity),
                'quantity': safe_get_value(quantity),
                'DOH': safe_get_value(row.get('DOH', '')) or safe_get_value(row.get('DOH Compliant (Yes/No)', '')),  # Add DOH field for UI display
                'DOH Compliant (Yes/No)': safe_get_value(row.get('DOH Compliant (Yes/No)', '')) or safe_get_value(row.get('DOH', '')),  # Add alternative DOH field
                'Price': price_value,  # Add Price field
                'THC': ai_value,  # Add THC value
                'CBD': ak_value,  # Add CBD value
                'AI': ai_value,  # Add AI field for THC
                'AJ': thc_content_value,  # Add AJ field for THC Content
                'AK': ak_value,  # Add AK field for CBD
                'Total THC': total_thc_value,  # Add Total THC field
                'THCA': thc_content_value,  # Add THC Content field
                'CBDA': total_cbd_value,  # Add Total CBD field
                'THC test result': thc_test_result,  # Add THC test result field
                'CBD test result': cbd_content_value,  # Add CBD Content field
                # Also include the lowercase versions for backward compatibility
                'vendor': vendor_value,
                'productBrand': safe_get_value(row.get('Product Brand', '')),
                'lineage': safe_get_value(row.get('Lineage', 'MIXED')),
                'productType': safe_get_value(row.get('Product Type*', '')),
                'weight': safe_get_value(raw_weight),
                'weightWithUnits': safe_get_value(weight_with_units),
                'displayName': product_name
            }
            # --- Filtering logic ---
            product_brand = str(tag['productBrand']).strip().lower()
            product_type = str(tag['productType']).strip().lower().replace('  ', ' ')
            weight = str(tag['weight']).strip().lower()

            # Sanitize lineage - prioritize existing lineage, fall back to inference from name  
            existing_lineage = str(row.get('Lineage', '') or '').strip().upper()
            if existing_lineage and existing_lineage in VALID_LINEAGES:
                lineage = existing_lineage
            else:
                # No valid lineage column - infer from product name and type
                product_type_for_inference = safe_get_value(row.get('Product Type*', ''))
                lineage = self._infer_lineage_from_name(product_name, product_type_for_inference)
            
            tag['Lineage'] = lineage
            tag['lineage'] = lineage

            # Filter out samples and invalid products
            product_name_lower = product_name.lower()
            product_type_lower = product_type.lower()
            if (
                weight == '-1g' or  # Invalid weight
                'trade sample' in product_type_lower or  # Filter any trade sample product types
                'sample' in product_name_lower or  # Filter products with "Sample" in name
                'trade sample' in product_name_lower or  # Filter products with "Trade Sample" in name
                any(pattern.lower() in product_name_lower for pattern in EXCLUDED_PRODUCT_PATTERNS) or  # Filter based on excluded patterns
                any(pattern.lower() in product_type_lower for pattern in EXCLUDED_PRODUCT_PATTERNS)  # Filter product types based on excluded patterns
            ):
                continue  # Skip this tag
            tags.append(tag)
        
        # Sort tags by vendor first, then by brand, then by weight
        def sort_key(tag):
            vendor = str(tag.get('vendor', '')).strip().lower()
            brand = str(tag.get('productBrand', '')).strip().lower()
            weight = ExcelProcessor.parse_weight_str(tag.get('weight', ''), tag.get('weightWithUnits', ''))
            return (vendor, brand, weight)
        
        sorted_tags = sorted(tags, key=sort_key)
        logger.info(f"get_available_tags: Returning {len(sorted_tags)} tags (removed {len(filtered_df) - len(sorted_tags)} duplicates)")
        return sorted_tags

    def select_tags(self, tags):
        """Add tags to the selected set, preserving order and avoiding duplicates."""
        if not isinstance(tags, (list, set)):
            tags = [tags]
        for tag in tags:
            if tag not in self.selected_tags:
                self.selected_tags.append(tag)
        
        # Final deduplication to ensure no duplicates exist
        seen = set()
        deduplicated_tags = []
        for tag in self.selected_tags:
            if tag not in seen:
                deduplicated_tags.append(tag)
                seen.add(tag)
        self.selected_tags = deduplicated_tags
        
        logger.debug(f"Selected tags after selection: {self.selected_tags}")

    def unselect_tags(self, tags):
        """Remove tags from the selected set."""
        if not isinstance(tags, (list, set)):
            tags = [tags]
        self.selected_tags = [tag for tag in self.selected_tags if tag not in tags]
        logger.debug(f"Selected tags after unselection: {self.selected_tags}")

    def get_selected_tags(self) -> List[str]:
        """Return the list of selected tag names in order."""
        return self.selected_tags if self.selected_tags else []

    def get_selected_records(self, template_type: str = 'vertical') -> List[Dict[str, Any]]:
        """Get selected records from the DataFrame, ordered by lineage."""
        try:
            # Get selected tags in the order they were selected
            selected_tags = list(self.selected_tags)
            if not selected_tags:
                logger.warning("No tags selected")
                return []
            
            # CRITICAL FIX: Log the selected tags for debugging
            logger.info(f"CRITICAL FIX: get_selected_records called with {len(selected_tags)} selected tags")
            logger.info(f"CRITICAL FIX: Selected tags: {selected_tags}")
            
            # Convert selected tags to simple strings if they're dictionaries
            selected_tag_names = []
            for tag in selected_tags:
                if isinstance(tag, dict):
                    # Extract product name from dictionary
                    product_name = tag.get('Product Name*') or tag.get('displayName') or tag.get('ProductName', '')
                    if product_name and product_name.strip():
                        selected_tag_names.append(str(product_name).strip())
                elif isinstance(tag, str):
                    # Already a string
                    selected_tag_names.append(tag.strip())
                else:
                    logger.warning(f"Unexpected tag format: {type(tag)} - {tag}")
            
            if not selected_tag_names:
                logger.warning("No valid tag names found after conversion")
                return []
            
            logger.debug(f"Selected tag names: {selected_tag_names}")
            
            # TEMPORARY FIX: Skip database lookup and use Excel data directly
            # This ensures we get the correct price and THC/CBD values
            logger.info("Using Excel data directly for template generation (bypassing database)")
            
            # Fallback to Excel data if database lookup fails or returns no results
            logger.info("Using Excel data for selected records")
            
            # Build a mapping from normalized product names to canonical names
            product_name_col = 'ProductName'  # The actual column name in the DataFrame
            if product_name_col not in self.df.columns:
                possible_cols = ['Product Name*', 'Product Name', 'Description']
                product_name_col = next((col for col in possible_cols if col in self.df.columns), None)
                if not product_name_col:
                    logger.error(f"Product name column not found. Available columns: {list(self.df.columns)}")
                    return []
            
            # CRITICAL FIX: Log column information for debugging
            logger.info(f"CRITICAL FIX: Using product name column: '{product_name_col}'")
            logger.info(f"CRITICAL FIX: Available columns: {list(self.df.columns)}")
            logger.info(f"CRITICAL FIX: DataFrame shape: {self.df.shape}")
            
            # Check if we have JSON matched products
            if 'Source' in self.df.columns:
                json_matched_count = (self.df['Source'] == 'JSON Match').sum()
                logger.info(f"CRITICAL FIX: Found {json_matched_count} JSON matched products in DataFrame")
            
            canonical_map = {normalize_name(name): name for name in self.df[product_name_col]}
            logger.debug(f"Canonical map sample: {dict(list(canonical_map.items())[:5])}")
            
            # Map incoming selected tags to canonical names
            # CRITICAL FIX: Preserve all selected tags, not just the first match
            canonical_selected = []
            for tag in selected_tag_names:
                normalized_tag = normalize_name(tag)
                if normalized_tag in canonical_map:
                    canonical_selected.append(canonical_map[normalized_tag])
                    logger.debug(f"CRITICAL FIX: Mapped '{tag}' -> '{canonical_map[normalized_tag]}'")
                else:
                    logger.warning(f"CRITICAL FIX: No canonical match for '{tag}' (normalized: '{normalized_tag}')")
            
            logger.debug(f"Selected tag names: {selected_tag_names}")
            logger.debug(f"Canonical selected tags: {canonical_selected}")
            
            # CRITICAL FIX: Log which tags were matched and which were not
            matched_tags = []
            unmatched_tags = []
            for tag in selected_tag_names:
                normalized_tag = normalize_name(tag)
                if normalized_tag in canonical_map:
                    matched_tags.append(tag)
                else:
                    unmatched_tags.append(tag)
            
            logger.info(f"CRITICAL FIX: Matched {len(matched_tags)} tags: {matched_tags}")
            if unmatched_tags:
                logger.warning(f"CRITICAL FIX: Unmatched {len(unmatched_tags)} tags: {unmatched_tags}")
                logger.warning(f"CRITICAL FIX: Available product names (sample): {list(self.df[product_name_col])[:10]}")
            
            # Fallback: try case-insensitive and whitespace-insensitive matching if no canonical matches
            if not canonical_selected:
                logger.warning("No canonical matches for selected tags, trying fallback matching...")
                available_names = list(self.df[product_name_col])
                fallback_selected = []
                for tag in selected_tag_names:
                    tag_norm = tag.strip().lower().replace(' ', '')
                    for name in available_names:
                        name_norm = str(name).strip().lower().replace(' ', '')
                        if tag_norm == name_norm:
                            fallback_selected.append(name)
                            logger.debug(f"CRITICAL FIX: Fallback match '{tag}' -> '{name}'")
                            break
                    else:
                        logger.warning(f"CRITICAL FIX: No fallback match found for '{tag}'")
                canonical_selected = fallback_selected
                logger.debug(f"Fallback canonical selected tags: {canonical_selected}")
            
            # CRITICAL FIX: If still no matches and we have JSON matched products, try direct matching
            if not canonical_selected and 'Source' in self.df.columns:
                logger.warning("CRITICAL FIX: No matches found, trying direct matching for JSON products...")
                json_matched_products = self.df[self.df['Source'] == 'JSON Match']
                if not json_matched_products.empty:
                    logger.info(f"CRITICAL FIX: Found {len(json_matched_products)} JSON matched products")
                    direct_matches = []
                    for tag in selected_tag_names:
                        # Try exact match first
                        exact_match = json_matched_products[json_matched_products[product_name_col] == tag]
                        if not exact_match.empty:
                            direct_matches.append(tag)
                            logger.info(f"CRITICAL FIX: Direct match found for '{tag}'")
                        else:
                            # Try case-insensitive match
                            case_insensitive_match = json_matched_products[
                                json_matched_products[product_name_col].str.lower() == tag.lower()
                            ]
                            if not case_insensitive_match.empty:
                                direct_matches.append(tag)
                                logger.info(f"CRITICAL FIX: Case-insensitive match found for '{tag}'")
                            else:
                                logger.warning(f"CRITICAL FIX: No direct match found for '{tag}'")
                    
                    if direct_matches:
                        canonical_selected = direct_matches
                        logger.info(f"CRITICAL FIX: Found {len(canonical_selected)} direct matches: {canonical_selected}")
                    else:
                        logger.warning(f"CRITICAL FIX: No direct matches found for any of the {len(selected_tag_names)} selected tags")
            
            # CRITICAL FIX: If still no matches, try to get JSON matched products from cache/session
            if not canonical_selected:
                logger.warning("CRITICAL FIX: No matches found in DataFrame, trying to get JSON matched products from cache...")
                try:
                    from flask import session, cache
                    # Try to get JSON matched products from session cache
                    json_matched_cache_key = session.get('json_matched_cache_key')
                    if json_matched_cache_key:
                        json_matched_products = cache.get(json_matched_cache_key)
                        if json_matched_products:
                            logger.info(f"CRITICAL FIX: Found {len(json_matched_products)} JSON matched products in cache")
                            # Create records directly from cached JSON matched products with DATABASE PRIORITY
                            records = []
                            for product in json_matched_products:
                                if isinstance(product, dict):
                                    # DATABASE PRIORITY: Ensure all fields come from database with safe defaults
                                    record = {
                                        'ProductName': product.get('Product Name*', product.get('ProductName', '')),
                                        'Product Name*': product.get('Product Name*', product.get('ProductName', '')),
                                        'Description': product.get('Description', product.get('Product Name*', product.get('ProductName', ''))),
                                        'DescAndWeight': self._process_description_from_product_name(product.get('Product Name*', product.get('ProductName', ''))),  # Use Excel processor formula
                                        'Product Type*': product.get('Product Type*', 'Edible (Solid)'),  # Database default
                                        'Product Brand': product.get('Product Brand', 'CERES'),  # Database default
                                        'Product Strain': product.get('Product Strain', 'Mixed'),  # Database default
                                        'Lineage': product.get('Lineage', 'MIXED'),  # Database default
                                        'Vendor': product.get('Vendor/Supplier*', product.get('Vendor', 'A Greener Today')),  # Database default
                                        'Price': product.get('Price', '25.00'),  # Database default price
                                        'Weight*': product.get('Weight*', '1'),  # Database default weight
                                        'Quantity*': product.get('Quantity*', '1'),  # Database default quantity
                                        'Units': product.get('Units', 'g'),  # Database default units
                                        'THC test result': product.get('THC test result', '0.00'),  # Database default
                                        'CBD test result': product.get('CBD test result', '0.00'),  # Database default
                                        'Test result unit (% or mg)': product.get('Test result unit (% or mg)', '%'),  # Database default
                                        'Source': product.get('Source', 'Database Priority (100% DB)')  # Updated source
                                    }
                                    records.append(record)
                            
                            if records:
                                logger.info(f"DATABASE PRIORITY: Created {len(records)} records from cached database-priority products")
                                return records
                            else:
                                logger.warning("DATABASE PRIORITY: No valid records created from cached database-priority products")
                        else:
                            logger.warning("CRITICAL FIX: No JSON matched products found in cache")
                    else:
                        logger.warning("CRITICAL FIX: No JSON matched cache key found in session")
                except Exception as e:
                    logger.warning(f"CRITICAL FIX: Error getting JSON matched products from cache: {e}")
            
            if not canonical_selected:
                logger.warning("No canonical matches for selected tags after fallback")
                logger.warning(f"Available canonical keys (sample): {list(canonical_map.keys())[:10]}")
                normalized_selected = [normalize_name(tag) for tag in selected_tag_names]
                logger.warning(f"Normalized selected tags: {normalized_selected}")
                logger.warning(f"Available product names: {list(self.df[product_name_col])[:10]}")
                return []
            
            logger.debug(f"Canonical selected tags: {canonical_selected}")
            
            # Filter DataFrame to only include selected records by canonical ProductName
            filtered_df = self.df[self.df[product_name_col].isin(canonical_selected)]
            logger.debug(f"Found {len(filtered_df)} matching records")
            
            # Convert to list of dictionaries
            records = filtered_df.to_dict('records')
            logger.debug(f"Converted to {len(records)} records")
            
            # Sort records by lineage order, then by the order they appear in selected_tags
            lineage_order = [
                'SATIVA', 'INDICA', 'HYBRID', 'HYBRID/SATIVA',
                'HYBRID/INDICA', 'CBD', 'MIXED', 'PARAPHERNALIA'
            ]
            
            def get_lineage(rec):
                lineage = str(rec.get('Lineage', '')).upper()
                return lineage if lineage in lineage_order else 'MIXED'
            
            def get_selected_order(rec):
                product_name = rec.get(product_name_col, '').strip()
                # Try exact match first
                try:
                    return selected_tag_names.index(product_name)
                except ValueError:
                    # Try case-insensitive match
                    product_name_lower = product_name.lower()
                    for i, tag in enumerate(selected_tag_names):
                        if tag.lower() == product_name_lower:
                            return i
                    return len(selected_tag_names)  # Put unknown tags at the end
            
            # Sort by selected order only (respecting user's drag-and-drop order)
            records_sorted = sorted(records, key=lambda r: get_selected_order(r))
            
            processed_records = []
            
            for record in records_sorted:
                try:
                    # Use the correct product name column
                    product_name = record.get(product_name_col, '').strip()
                    # Use the calculated Description field (which is processed from Product Name*)
                    description = record.get('Description', '')
                    if not description:
                        description = product_name or record.get(product_name_col, '')
                    product_type = record.get('Product Type*', '').strip().lower()
                    
                    # Look up database weight and units as fallback
                    db_weight = ''
                    db_units = ''
                    try:
                        from src.core.data.product_database import get_product_database
                        product_db = get_product_database()
                        if product_db:
                            db_products = product_db.get_products_by_names([product_name])
                            if db_products and len(db_products) > 0:
                                db_product = db_products[0]
                                db_weight = db_product.get('Weight*', '')
                                db_units = db_product.get('Units', '')
                                logger.debug(f"Found database weight/units for '{product_name}': {db_weight}/{db_units}")
                    except Exception as e:
                        logger.debug(f"Could not lookup database weight/units for '{product_name}': {e}")
                    
                    # Add database weight and units to record for _format_weight_units
                    record['db_weight'] = db_weight
                    record['db_units'] = db_units
                    
                    # Get ratio text and ensure it's a string
                    ratio_text = str(record.get('Ratio', '')).strip()
                    # Handle 'nan' values
                    if ratio_text in ['nan', 'NaN', '']:
                        ratio_text = ''
                    
                    # Define classic types
                    classic_types = [
                        "flower", "pre-roll", "infused pre-roll", "concentrate", 
                        "solventless concentrate", "vape cartridge", "rso/co2 tankers"
                    ]
                    
                    # For classic types, ensure proper ratio format
                    if product_type in classic_types:
                        # Check if we have a valid ratio, otherwise use default
                        if not ratio_text or ratio_text in ["", "CBD", "THC", "CBD:", "THC:", "CBD:\n", "THC:\n"]:
                            ratio_text = "THC: | BR | CBD:"
                        # If ratio contains THC/CBD values, use it directly
                        elif any(cannabinoid in ratio_text.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                            ratio_text = ratio_text  # Keep as is
                        # If it's a valid ratio format, use it
                        elif is_real_ratio(ratio_text):
                            ratio_text = ratio_text  # Keep as is
                        # Otherwise, use default THC:CBD format
                        else:
                            ratio_text = "THC: | BR | CBD:"
                    
                    # For non-classic types, preserve the ratio value from Excel
                    # This ensures that edibles, tinctures, etc. show their actual ratio values
                    else:
                        # Keep the original ratio value from Excel for non-classic types
                        if not ratio_text or ratio_text in ["", "nan", "NaN"]:
                            ratio_text = ""  # Empty for non-classic types without ratio
                        # Otherwise, keep the ratio value as-is
                    
                    # Don't apply ratio formatting here - let the template processor handle it
                    # For classic types (including RSO/CO2 Tankers), the template processor will handle the classic formatting
                    
                    # Ensure we have a valid ratio text
                    if not ratio_text:
                        if product_type in classic_types:
                            ratio_text = "THC: | BR | CBD:"
                        else:
                            ratio_text = ""
                    
                    product_name = self.make_nonbreaking_hyphens(product_name)
                    description = self.make_nonbreaking_hyphens(description)
                    
                    # Get DOH value without normalization
                    doh_value = str(record.get('DOH', '')).strip().upper()
                    logger.debug(f"Processing DOH value: {doh_value}")
                    
                    # Get original values
                    product_brand = record.get('Product Brand', '').upper()
                    
                    # If no brand name, try to extract from product name or use vendor
                    if not product_brand or product_brand.strip() == '':
                        product_name = record.get('ProductName', '') or record.get('Product Name*', '')
                        if product_name:
                            # Look for common brand patterns in product name
                            import re
                            # Pattern: product name followed by brand name (e.g., "White Widow CBG Platinum Distillate")
                            brand_patterns = [
                                r'(.+?)\s+(Platinum|Premium|Gold|Silver|Elite|Select|Reserve|Craft|Artisan|Boutique|Signature|Limited|Exclusive|Private|Custom|Special|Deluxe|Ultra|Super|Mega|Max|Pro|Plus|X)\s+(Distillate|Extract|Concentrate|Oil|Tincture|Gel|Capsule|Edible|Gummy|Chocolate|Beverage|Topical|Cream|Lotion|Salve|Balm|Spray|Drops|Syrup|Sauce|Dab|Wax|Shatter|Live|Rosin|Resin|Kief|Hash|Bubble|Ice|Water|Solventless|Full\s+Spectrum|Broad\s+Spectrum|Isolate|Terpene|Terpenes|Terp|Terps)',
                                r'(.+?)\s+(Distillate|Extract|Concentrate|Oil|Tincture|Gel|Capsule|Edible|Gummy|Chocolate|Beverage|Topical|Cream|Lotion|Salve|Balm|Spray|Drops|Syrup|Sauce|Dab|Wax|Shatter|Live|Rosin|Resin|Kief|Hash|Bubble|Ice|Water|Solventless|Full\s+Spectrum|Broad\s+Spectrum|Isolate|Terpene|Terpenes|Terp|Terps)',
                                r'(.+?)\s+(Platinum|Premium|Gold|Silver|Elite|Select|Reserve|Craft|Artisan|Boutique|Signature|Limited|Exclusive|Private|Custom|Special|Deluxe|Ultra|Super|Mega|Max|Pro|Plus|X)',
                            ]
                            
                            for pattern in brand_patterns:
                                match = re.search(pattern, product_name, re.IGNORECASE)
                                if match:
                                    # Extract the brand part (everything after the product name)
                                    full_match = match.group(0)
                                    product_part = match.group(1).strip()
                                    brand_part = full_match[len(product_part):].strip()
                                    if brand_part:
                                        product_brand = brand_part.upper()
                                        break
                        
                        # If still no brand, try vendor as fallback
                        if not product_brand or product_brand.strip() == '':
                            vendor = record.get('Vendor', '') or record.get('Vendor/Supplier*', '')
                            if vendor and vendor.strip() != '':
                                product_brand = vendor.strip().upper()
                    
                    original_lineage = str(record.get('Lineage', '')).upper()
                    original_product_strain = record.get('Product Strain', '')
                    
                    # Extract strain from product name if Product Strain contains the full product name
                    # This handles cases like "Grape Moonshot" where the strain should be "Grape"
                    extracted_strain = original_product_strain
                    if original_product_strain and 'Moonshot' in original_product_strain:
                        # Extract the strain name (everything before "Moonshot")
                        strain_name = original_product_strain.replace(' Moonshot', '').strip()
                        if strain_name:
                            extracted_strain = strain_name
                            logger.debug(f"Extracted strain '{extracted_strain}' from '{original_product_strain}'")
                    elif original_product_strain and product_name:
                        # Check if Product Strain contains the full product name (common with brand names)
                        if original_product_strain in product_name and len(original_product_strain) > len(product_name.split()[0]):
                            # Extract just the first word as the strain (e.g., "Grape" from "Grape Moonshot")
                            extracted_strain = product_name.split()[0]
                            logger.debug(f"Extracted strain '{extracted_strain}' from '{original_product_strain}' for product '{product_name}'")
                    
                    # For RSO/CO2 Tankers and Capsules, use Product Brand in place of Lineage
                    if product_type in ["rso/co2 tankers", "capsule"]:
                        final_lineage = product_brand if product_brand else original_lineage
                        final_product_strain = extracted_strain  # Use extracted strain
                    else:
                        # For other product types, use the actual Lineage value
                        final_lineage = original_lineage
                        final_product_strain = extracted_strain  # Use extracted strain
                    
                    lineage_needs_centering = False  # Lineage should not be centered
                    
                    # Debug print for verification
                    logger.debug(f"LINEAGE DEBUG: Product '{product_name}', Type: '{product_type}', Original Lineage: '{original_lineage}', Final Lineage: '{final_lineage}', ProductStrain: '{final_product_strain}'")
                    
                    # CRITICAL FIX: Log lineage value being used in final output
                    if 'Lineage' in record:
                        logger.info(f"LINEAGE TRACKING: Product '{product_name}' -> Final lineage value: '{final_lineage}' (from record: '{record.get('Lineage', 'NOT_IN_RECORD')}')")
                    
                    # Debug ProductStrain logic
                    include_product_strain = (product_type in ["rso/co2 tankers", "capsule"] or product_type not in classic_types)
                    # ProductStrain logic: product_type='{product_type}', in special list={product_type in ['rso/co2 tankers', 'capsule']}, not in classic_types={product_type not in classic_types}, include_product_strain={include_product_strain}")
                    
                    # Extract AI and AK column values for THC and CBD
                    # Extract THC/CBD values from actual columns
                    # For THC: merge Total THC (AI) with THC test result (K), use highest value
                    total_thc_value = str(record.get('Total THC', '')).strip()
                    thc_content_value = str(record.get('THCA', '')).strip()  # Use THC Content
                    thc_test_result = str(record.get('THCA', '')).strip()  # Use THC Content
                    
                    # Clean up THC test result value
                    if thc_test_result in ['nan', 'NaN', '']:
                        thc_test_result = ''
                    
                    # Convert to float for comparison, handling empty/invalid values
                    def safe_float(value):
                        if not value or value in ['nan', 'NaN', '']:
                            return 0.0
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return 0.0
                    
                    # Compare Total THC vs THC test result, use highest
                    total_thc_float = safe_float(total_thc_value)
                    thc_test_float = safe_float(thc_test_result)
                    thc_content_float = safe_float(thc_content_value)
                    
                    # For THC: Use the highest value among Total THC, THC Content, and THC test result
                    # But if Total THC is 0 or empty, prefer THC Content over THC test result
                    if total_thc_float > 0:
                        # Total THC has a valid value, compare with THC test result
                        if thc_test_float > total_thc_float:
                            ai_value = thc_test_result
                            logger.debug(f"Using THC test result ({thc_test_result}) over Total THC ({total_thc_value}) for product: {product_name}")
                        else:
                            ai_value = total_thc_value
                    else:
                        # Total THC is 0 or empty, compare THC Content vs THC test result
                        if thc_content_float > 0 and thc_content_float >= thc_test_float:
                            ai_value = thc_content_value
                        elif thc_test_float > 0:
                            ai_value = thc_test_result
                        else:
                            ai_value = ''
                    
                    # For CBD: merge Total CBD with CBD test result, use highest value
                    total_cbd_value = str(record.get('Total CBD', '')).strip()  # Use Total CBD
                    cbd_test_result_value = str(record.get('CBDA', '')).strip()  # Use CBDA as content
                    cbd_content_value = str(record.get('CBDA', '')).strip()  # Use CBDA as content
                    
                    # Clean up CBD values
                    if cbd_test_result_value in ['nan', 'NaN', '']:
                        cbd_test_result_value = ''
                    if cbd_content_value in ['nan', 'NaN', '']:
                        cbd_content_value = ''
                    
                    # Compare Total CBD vs CBD test result vs CBD Content, use highest
                    total_cbd_float = safe_float(total_cbd_value)
                    cbd_test_result_float = safe_float(cbd_test_result_value)
                    cbd_content_float = safe_float(cbd_content_value)
                    
                    # Use the highest CBD value from all sources
                    if cbd_test_result_float > 0 and cbd_test_result_float >= total_cbd_float and cbd_test_result_float >= cbd_content_float:
                        ak_value = cbd_test_result_value
                        logger.debug(f"Using CBD test result ({cbd_test_result_value}) for product: {product_name}")
                    elif cbd_content_float > total_cbd_float:
                        ak_value = cbd_content_value
                        logger.debug(f"Using CBD Content ({cbd_content_value}) over Total CBD ({total_cbd_value}) for product: {product_name}")
                    else:
                        ak_value = total_cbd_value
                    
                    # Clean up the values (remove 'nan', empty strings, etc.)
                    if ai_value in ['nan', 'NaN', '']:
                        ai_value = ''
                    if ak_value in ['nan', 'NaN', '']:
                        ak_value = ''
                    
                    # Get vendor information
                    vendor = record.get('Vendor', '') or record.get('Vendor/Supplier*', '')
                    if pd.isna(vendor) or str(vendor).lower() == 'nan':
                        vendor = ''
                    
                    # Define classic types
                    classic_types = [
                        "flower", "pre-roll", "infused pre-roll", "concentrate", 
                        "solventless concentrate", "vape cartridge", "rso/co2 tankers"
                    ]
                    
                    # If product type is empty, treat as classic type (flower)
                    if not product_type:
                        product_type = "flower"
                    
                    # Build the processed record with raw values (no markers)
                    processed = {
                        'ProductName': product_name,  # Keep this for compatibility
                        product_name_col: product_name,  # Also store with original column name
                        'Description': description,
                        'WeightUnits': record.get('JointRatio', '') if product_type in {"pre-roll", "infused pre-roll"} else self._format_weight_units(record, excel_priority=True),
                        'ProductBrand': product_brand,
                        'Price': str(record.get('Price*', '')).strip() or str(record.get('Price', '')).strip(),
                        'Lineage': str(final_lineage) if str(final_lineage) else "",
                        'DOH': doh_value,  # Keep DOH as raw value
                        'Ratio_or_THC_CBD': self._construct_thc_cbd_field(ai_value, ak_value, product_type) if product_type in classic_types else ratio_text,  # Use THC_CBD for classic types, ratio for non-classic
                        'ProductStrain': wrap_with_marker(final_product_strain, "PRODUCTSTRAIN") if include_product_strain else '',
                        'ProductType': record.get('Product Type*', ''),
                        'Ratio': str(record.get('Ratio_or_THC_CBD', '')).strip(),
                        'THC': ai_value,  # Direct THC value for template processor
                        'CBD': ak_value,  # Direct CBD value for template processor
                        'THC_wrapped': self.wrap_with_marker(self._format_individual_thc_cbd(ai_value, 'THC'), "THC"),  # Wrapped THC for display
                        'CBD_wrapped': self.wrap_with_marker(self._format_individual_thc_cbd(ak_value, 'CBD'), "CBD"),  # Wrapped CBD for display
                        'THC_CBD': self._construct_thc_cbd_field(ai_value, ak_value, product_type),  # Construct combined THC_CBD field
                        'AI': ai_value,  # Total THC or THCA value for THC
                        'AJ': str(record.get('THCA', '')).strip(),  # THC Content value for alternative THC
                        'AK': ak_value,  # CBDA value for CBD
                        'Vendor': vendor,  # Add vendor information
                    }
                    # Ensure leading space before hyphen is a non-breaking space to prevent Word from stripping it
                    joint_ratio = record.get('JointRatio', '')
                    # Handle NaN values properly
                    if pd.isna(joint_ratio) or joint_ratio == 'nan' or joint_ratio == 'NaN':
                        joint_ratio = ''
                    elif joint_ratio.startswith(' -'):
                        joint_ratio = ' -\u00A0' + joint_ratio[2:]
                    processed['JointRatio'] = joint_ratio
                    
                    logger.info(f"Rendered label for record: {product_name if product_name else '[NO NAME]'}")
                    logger.debug(f"Processed record DOH value: {processed['DOH']}")
                    logger.debug(f"Product Type: {product_type}, Classic: {product_type in classic_types}")
                    logger.debug(f"Original Lineage: {original_lineage}, Final Lineage: {final_lineage}")
                    logger.debug(f"Original Product Strain: {original_product_strain}, Final Product Strain: {final_product_strain}")
                    logger.debug(f"Lineage needs centering: {lineage_needs_centering}")
                    processed_records.append(processed)
                except Exception as e:
                    logger.error(f"Error processing record {product_name}: {str(e)}")
                    continue
                
            # Debug log the final processed records
            logger.debug(f"Processed {len(processed_records)} records")
            for record in processed_records:
                logger.debug(f"Processed record: {record.get('ProductName', 'NO NAME')}")
                logger.debug(f"Record DOH value: {record.get('DOH', 'NO DOH')}")
            
            return processed_records
        except Exception as e:
            logger.error(f"Error in get_selected_records: {str(e)}")
            return []

    def _construct_thc_cbd_field(self, thc_value, cbd_value, product_type):
        """
        Construct the THC_CBD field from separate THC and CBD values.
        This ensures the template processor has access to the combined field.
        """
        if not thc_value and not cbd_value:
            return ""
        
        # Clean up the values
        thc_clean = str(thc_value).strip() if thc_value else ""
        cbd_clean = str(cbd_value).strip() if cbd_value else ""
        
        # Remove 'nan' values
        if thc_clean in ['nan', 'NaN', '']:
            thc_clean = ""
        if cbd_clean in ['nan', 'NaN', '']:
            cbd_clean = ""
        
        # Construct the combined field using exact values, no rounding or formatting
        # Always show both THC and CBD, even if one is 0
        thc_display = thc_clean if thc_clean else "0"
        cbd_display = cbd_clean if cbd_clean else "0"
        
        return f"THC: {thc_display}% CBD: {cbd_display}%"

    def _format_individual_thc_cbd(self, value, cannabinoid_type):
        """
        Format individual THC or CBD values with percentage formatting rules.
        
        Args:
            value: The raw THC or CBD value
            cannabinoid_type: Either 'THC' or 'CBD'
        
        Returns:
            Formatted value with percentage formatting rules applied
        """
        # Always return the exact value as a string, including zeros, with no formatting
        if value == 0 or value == '0' or value == '0.0':
            return "0"
        if not value or str(value).strip() in ['nan', 'NaN', '']:
            return ""
        return str(value).strip()

    def _find_identical_product_ounce_weight(self, product_name, product_type):
        """Find identical products with existing ounce weights in the database."""
        try:
            # Import here to avoid circular imports
            from src.core.data.product_database import ProductDatabase
            
            # Get database connection with store name
            db = ProductDatabase(store_name=self._store_name)
            db.init_database()
            
            # Search for products with similar names and ounce weights
            with db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Look for products with similar names that have ounce weights or similar weights
                # Use LIKE with wildcards to find similar product names
                query = """
                    SELECT "Weight*", "Units", "Product Name*", "Product Type*"
                    FROM products 
                    WHERE "Product Name*" LIKE ? 
                    AND "Product Type*" = ?
                    AND ("Units" = 'oz' OR "Units" = 'ounces' OR "Weight*" LIKE '%oz%' OR "Units" = 'each')
                    LIMIT 5
                """
                
                # Create search pattern - look for products that contain key words from the current product
                product_words = product_name.lower().split()
                if len(product_words) >= 2:
                    # Use the first two words as the main search pattern
                    search_pattern = f"%{product_words[0]}%{product_words[1]}%"
                else:
                    search_pattern = f"%{product_name}%"
                
                cursor.execute(query, (search_pattern, product_type))
                results = cursor.fetchall()
                
                if results:
                    # Return the most recent result (first in the list due to ORDER BY)
                    weight, units, found_name, found_type = results[0]
                    
                    # If the found product has "each" units but a similar weight value, convert to ounces
                    if units == 'each' and weight:
                        try:
                            weight_float = float(weight)
                            # If the weight is around 1.7-2.0, it's likely the same as 1.7oz
                            if 1.5 <= weight_float <= 2.5:
                                self.logger.info(f"Found identical product with similar weight: {found_name} -> {weight}{units}, using as 1.7oz")
                                return "1.7oz"
                        except (ValueError, TypeError):
                            pass
                    
                    self.logger.info(f"Found identical product with ounce weight: {found_name} -> {weight}{units}")
                    return f"{weight}{units}"
                
                return None
                
        except Exception as e:
            self.logger.warning(f"Error looking up identical product weight: {str(e)}")
            return None

    def _find_most_likely_ounce_weight(self, product_name, product_type):
        """
        Find the most common ounce weight for similar nonclassic products.
        This helps maintain consistency with actual product packaging rather than mathematical conversion.
        """
        # Common ounce weights for nonclassic products based on typical packaging
        common_oz_weights = {
            # Edibles - common sizes
            'edible (liquid)': ['2.5oz', '3.53oz', '1.7oz'],
            'edible (solid)': ['1oz', '2.5oz', '3.5oz'],
            'gummy': ['1oz', '2oz', '3.5oz'],
            'chocolate': ['1oz', '2oz', '3.5oz'],
            'cookie': ['1oz', '2oz'],
            'brownie': ['1oz', '2oz'],
            'candy': ['1oz', '2oz', '3.5oz'],
            
            # Tinctures and oils
            'tincture': ['1oz', '2oz', '4oz'],
            'drops': ['1oz', '2oz'],
            'liquid': ['1oz', '2oz', '4oz'],
            
            # Topicals
            'topical': ['1oz', '2oz', '4oz'],
            'cream': ['1oz', '2oz', '4oz'],
            'lotion': ['1oz', '2oz', '4oz'],
            'salve': ['1oz', '2oz'],
            'balm': ['1oz', '2oz'],
            
            # Capsules
            'capsule': ['1oz', '2oz'],
            
            # Beverages
            'beverage': ['12oz', '16oz', '20oz'],
            'drink': ['12oz', '16oz', '20oz'],
            'soda': ['12oz', '16oz'],
            'juice': ['12oz', '16oz'],
            
            # Default fallback
            'default': ['1oz', '2oz', '3.5oz']
        }
        
        # Get the most common weight for this product type
        product_type_lower = product_type.lower().strip()
        
        # Try exact match first
        if product_type_lower in common_oz_weights:
            return common_oz_weights[product_type_lower][0]  # Return the first (most common) weight
        
        # Try partial matches for product types that might have variations
        for key, weights in common_oz_weights.items():
            if key != 'default' and key in product_type_lower:
                return weights[0]
        
        # Special handling for Moonshot products (they seem to be 2.5oz or 3.53oz based on the image)
        if 'moonshot' in product_name.lower():
            return '2.5oz'  # Most common Moonshot size
        
        # Default fallback
        return common_oz_weights['default'][0]  # Return '1oz' as default

    def _format_weight_units(self, record, excel_priority=True):
        # Handle pandas Series and NA values properly
        def safe_get_value(value, default=''):
            if value is None or pd.isna(value):
                return default
            if isinstance(value, pd.Series):
                if pd.isna(value).any():
                    return default
                value = value.iloc[0] if len(value) > 0 else default
            return str(value).strip()
        
        # Get weight and units from Excel data first (priority)
        excel_weight = safe_get_value(record.get('Weight*', None))
        excel_units = safe_get_value(record.get('Units', ''))
        product_type = safe_get_value(record.get('Product Type*', '')).lower()
        product_name = safe_get_value(record.get('Product Name*', ''))
        
        # Get database weight and units as fallback
        db_weight = safe_get_value(record.get('db_weight', None))
        db_units = safe_get_value(record.get('db_units', ''))
        
        # Special handling for Moonshot products - use database values as priority
        is_moonshot = 'moonshot' in product_name.lower()
        
        # Priority logic: Database first for Moonshot products, Excel first for others
        if is_moonshot:
            # For Moonshot products, prioritize database values to get correct 1.7oz weights
            weight_val = db_weight if db_weight and db_weight not in ['', 'nan', 'NaN'] else excel_weight
            units_val = db_units if db_units and db_units not in ['', 'nan', 'NaN'] else excel_units
        elif excel_priority:
            weight_val = excel_weight if excel_weight and excel_weight not in ['', 'nan', 'NaN'] else db_weight
            units_val = excel_units if excel_units and excel_units not in ['', 'nan', 'NaN'] else db_units
        else:
            weight_val = db_weight if db_weight and db_weight not in ['', 'nan', 'NaN'] else excel_weight
            units_val = db_units if db_units and db_units not in ['', 'nan', 'NaN'] else excel_units
        
        # Debug: Log first few records
        if hasattr(self, '_debug_count'):
            self._debug_count += 1
        else:
            self._debug_count = 1
            
        if self._debug_count <= 5:  # Log first 5 records for debugging
            self.logger.info(f"Record {self._debug_count}: excel_weight={excel_weight}, excel_units={excel_units}, db_weight={db_weight}, db_units={db_units}, final_weight={weight_val}, final_units={units_val}, product_type={product_type}")
        
        # Import CLASSIC_TYPES to determine nonclassic products
        from src.core.constants import CLASSIC_TYPES
        
        # Determine if this is a nonclassic product type
        is_nonclassic = product_type not in [ct.lower() for ct in CLASSIC_TYPES]
        
        preroll_types = {"pre-roll", "infused pre-roll"}

        # FIRST: Check if Weight* already contains units (like "1g", "3.5oz", etc.)
        if weight_val and any(unit in weight_val.lower() for unit in ['g', 'oz', 'gram', 'ounce']):
            # Special override for Moonshot products - force to 2.5oz
            if 'moonshot' in product_name.lower() and 'g' in weight_val.lower():
                self.logger.info(f"FORCING Moonshot conversion: {product_name} {weight_val} -> 2.5oz")
                return "2.5oz"
            # Weight* already has units embedded, return as-is
            result = weight_val
        elif product_type in preroll_types:
            # For pre-rolls and infused pre-rolls, use JointRatio if available
            joint_ratio = safe_get_value(record.get('JointRatio', ''))
            
            # Check if JointRatio is valid (not NaN, not empty, and looks like a pack format)
            if (joint_ratio and 
                joint_ratio != 'nan' and 
                joint_ratio != 'NaN' and 
                not pd.isna(joint_ratio) and
                ('g' in str(joint_ratio).lower() and 'pack' in str(joint_ratio).lower())):
                
                # Use the JointRatio as-is for pre-rolls
                result = str(joint_ratio)
            else:
                # For pre-rolls with invalid JointRatio, generate from Weight
                if weight_val and weight_val not in ['nan', 'NaN'] and not pd.isna(weight_val):
                    try:
                        weight_float = float(weight_val)
                        result = f"{weight_float}g"
                    except (ValueError, TypeError):
                        result = ""
                else:
                    result = ""
        else:
            # Handle normal weight + units combination
            try:
                weight_float = float(weight_val) if weight_val not in (None, '', 'nan') else None
            except Exception:
                weight_float = None

            # Apply unit conversion for ALL nonclassic product types
            if (weight_float is not None and units_val and 
                is_nonclassic and 
                units_val.lower() in ['g', 'grams', 'gram']):
                
                # FIRST: Check if there are identical products with existing ounce weights
                if product_name:
                    identical_ounce_weight = self._find_identical_product_ounce_weight(product_name, product_type)
                    if identical_ounce_weight:
                        self.logger.info(f"Using identical product ounce weight for {product_name}: {identical_ounce_weight}")
                        return identical_ounce_weight
                
                # If no identical product found, use most likely ounce weight
                most_likely_oz_weight = self._find_most_likely_ounce_weight(product_name, product_type)
                if most_likely_oz_weight:
                    self.logger.info(f"Using most likely ounce weight for {product_name}: {most_likely_oz_weight}")
                    return most_likely_oz_weight
                else:
                    # Fallback: force conversion for Moonshot products
                    if 'moonshot' in product_name.lower():
                        self.logger.info(f"Forcing Moonshot conversion for {product_name}: 2.5oz")
                        return "2.5oz"

            # Now combine weight and units properly
            if weight_float is not None and units_val:
                # Format weight similar to price formatting - no decimals unless needed
                if weight_float.is_integer():
                    weight_str = f"{int(weight_float)}"
                else:
                    # Round to 2 decimal places and remove trailing zeros
                    weight_str = f"{weight_float:.2f}".rstrip("0").rstrip(".")
                result = f"{weight_str}{units_val}"
            elif weight_float is not None:
                result = str(int(weight_float) if weight_float.is_integer() else weight_float)
            elif units_val:
                result = str(units_val)
            else:
                result = ""
        
        # Debug: Log result for first few records
        if self._debug_count <= 5:
            self.logger.info(f"Record {self._debug_count} result: '{result}'")
            
        return result

    def get_dynamic_filter_options(self, current_filters: Dict[str, str]) -> Dict[str, list]:
        if self.df is None:
            # Return empty options if no data is loaded
            return {
                "vendor": [],
                "brand": [],
                "productType": [],
                "lineage": [],
                "weight": [],
                "strain": [],
                "doh": [],
                "highCbd": []
            }
        df = self.df.copy()
        filter_map = {
            "vendor": "Vendor",
            "brand": "Product Brand",
            "productType": "Product Type*",
            "lineage": "Lineage",
            "weight": "CombinedWeight",  # Reverted back to "CombinedWeight" as requested
            "strain": "Product Strain",
            "doh": "DOH",
            "highCbd": "Product Type*"  # Will be processed specially for high CBD detection
        }
        options = {}
        import math
        def clean_list(lst):
            return ['' if (v is None or (isinstance(v, float) and math.isnan(v))) else v for v in lst]
        # For each filter type, generate options by applying all other filters except itself
        for filter_key, col in filter_map.items():
            temp_df = df.copy()
            # Apply all other filters except the current one
            for key, value in current_filters.items():
                if key == filter_key:
                    continue  # Skip filtering by itself
                if value and value != "All":
                    filter_col = filter_map.get(key)
                    if filter_col and filter_col in temp_df.columns:
                        temp_df = temp_df[
                            temp_df[filter_col].astype(str).str.lower().str.strip() == value.lower().strip()
                        ]
            # Get unique values for this filter type
            if col in temp_df.columns:
                if filter_key == "weight":
                    # For weight, use the properly formatted weight with units
                    values = []
                    for _, row in temp_df.iterrows():
                        # Convert row to dict for _format_weight_units
                        row_dict = row.to_dict()
                        weight_with_units = self._format_weight_units(row_dict, excel_priority=True)
                        if weight_with_units and weight_with_units.strip():
                            weight_str = weight_with_units.strip()
                            
                            # Only include values that look like actual weights (with units like g, oz, mg)
                            # Exclude THC/CBD content, ratios, and other non-weight content
                            import re
                            weight_pattern = re.compile(r'^\d+\.?\d*\s*(g|oz|mg|grams?|ounces?)$', re.IGNORECASE)
                            
                            if weight_pattern.match(weight_str):
                                values.append(weight_str)
                            elif not any(keyword in weight_str.lower() for keyword in ['thc', 'cbd', 'ratio', '|br|', ':']):
                                # If it doesn't match weight pattern but also doesn't contain THC/CBD keywords, include it
                                values.append(weight_str)
                    
                    # Debug: Log what weight values are being generated
                    if values:
                        self.logger.info(f"Weight filter values generated: {values[:5]}...")  # Log first 5 values
                    else:
                        self.logger.warning("No weight values generated for filter dropdown")
                else:
                    values = temp_df[col].dropna().unique().tolist()
                    values = [str(v) for v in values if str(v).strip()]
                
                # Exclude unwanted product types from dropdown and apply product type normalization
                if filter_key == "productType":
                    filtered_values = []
                    for v in values:
                        v_lower = v.strip().lower()
                        if ("trade sample" in v_lower or "deactivated" in v_lower):
                            continue
                        # Apply product type normalization (same as TYPE_OVERRIDES)
                        normalized_v = TYPE_OVERRIDES.get(v_lower, v)
                        filtered_values.append(normalized_v)
                    values = filtered_values
                
                # Special processing for DOH filter
                elif filter_key == "doh":
                    # Only include "YES" and "NO" values, normalize case
                    filtered_values = []
                    for v in values:
                        v_upper = v.strip().upper()
                        if v_upper in ["YES", "NO"]:
                            filtered_values.append(v_upper)
                    values = filtered_values
                
                # Special processing for High CBD filter
                elif filter_key == "highCbd":
                    # Check if any product types start with "high cbd"
                    has_high_cbd = any(v.strip().lower().startswith('high cbd') for v in values)
                    values = ["High CBD Products", "Non-High CBD Products"] if has_high_cbd else ["Non-High CBD Products"]
                
                # Remove duplicates and sort
                values = list(set(values))
                values.sort()
                options[filter_key] = clean_list(values)
            else:
                options[filter_key] = []
        
        return options

    @staticmethod
    def parse_weight_str(w, u=None):
        import re
        w = str(w).strip() if w is not None else ''
        u = str(u).strip().lower() if u is not None else ''
        # Try to extract numeric value and units from weight or weightWithUnits
        match = re.match(r"([\d.]+)\s*(g|oz)?", w.lower())
        if not match and u:
            match = re.match(r"([\d.]+)\s*(g|oz)?", u)
        if match:
            val = float(match.group(1))
            unit = match.group(2)
            if unit == 'oz':
                val = val * 28.3495
            return val
        return float('inf')  # Non-numeric weights go last

    def update_lineage_in_database(self, strain_name: str, new_lineage: str):
        """Update lineage for a specific strain in the database."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            self.logger.warning("Lineage persistence is disabled")
            return False
        
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            # Update strain with sovereign lineage
            strain_id = product_db.add_or_update_strain(strain_name, new_lineage, sovereign=True)
            
            if strain_id:
                self.logger.info(f"Updated lineage for strain '{strain_name}' to '{new_lineage}' in database")
                
                # Note: Only updating database, not Excel file (for performance)
                # Excel file is source data, database is authoritative for lineage
                
                return True
            else:
                self.logger.error(f"Failed to update lineage for strain '{strain_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating lineage for strain '{strain_name}': {e}")
            return False

    def batch_update_lineages(self, lineage_updates: Dict[str, str]):
        """Batch update multiple lineage changes in the database."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            self.logger.warning("Lineage persistence is disabled")
            return False
        
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            success_count = 0
            total_count = len(lineage_updates)
            
            for strain_name, new_lineage in lineage_updates.items():
                try:
                    strain_id = product_db.add_or_update_strain(strain_name, new_lineage, sovereign=True)
                    if strain_id:
                        success_count += 1
                        
                        # Note: Only updating database, not Excel file (for performance)
                        # Excel file is source data, database is authoritative for lineage
                                
                except Exception as e:
                    self.logger.error(f"Error updating lineage for strain '{strain_name}': {e}")
            
            self.logger.info(f"Batch lineage update complete: {success_count}/{total_count} successful")
            return success_count == total_count
            
        except Exception as e:
            self.logger.error(f"Error in batch lineage update: {e}")
            return False

    def update_lineage_in_database_enhanced(self, identifier: str, new_lineage: str, is_strain: bool = True) -> bool:
        """Enhanced database update that handles both strain names and product names."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            self.logger.warning("Lineage persistence is disabled")
            return False
        
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            if is_strain:
                # Traditional strain-based update
                strain_id = product_db.add_or_update_strain(identifier, new_lineage, sovereign=True)
                if strain_id:
                    self.logger.info(f"Updated lineage for strain '{identifier}' to '{new_lineage}' in database")
                    return True
                else:
                    self.logger.warning(f"Failed to update strain '{identifier}' in database")
                    return False
            else:
                # Product name-based update - directly update products table
                conn = product_db._get_connection()
                cursor = conn.cursor()
                
                # Update the lineage for the specific product by name
                cursor.execute('''
                    UPDATE products 
                    SET "Lineage" = ? 
                    WHERE "Product Name*" = ?
                ''', (new_lineage, identifier))
                
                updated_rows = cursor.rowcount
                conn.commit()
                
                if updated_rows > 0:
                    self.logger.info(f"Updated lineage for product '{identifier}' to '{new_lineage}' in database ({updated_rows} rows)")
                    return True
                else:
                    self.logger.warning(f"No products found with name '{identifier}' for lineage update")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error updating lineage for '{identifier}': {e}")
            return False

    def get_lineage_suggestions(self, strain_name: str) -> Dict[str, Any]:
        """Get lineage suggestions for a strain from the database."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            return {"suggestion": None, "confidence": 0.0, "reason": "Lineage persistence disabled"}
        
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            return product_db.validate_and_suggest_lineage(strain_name)
            
        except Exception as e:
            self.logger.error(f"Error getting lineage suggestions for strain '{strain_name}': {e}")
            return {"suggestion": None, "confidence": 0.0, "reason": f"Error: {e}"}

    def ensure_lineage_persistence(self):
        """Ensure all lineage changes are persisted to the database."""
        if not ENABLE_LINEAGE_PERSISTENCE:
            self.logger.warning("Lineage persistence is disabled")
            return {"message": "Lineage persistence disabled", "updated_count": 0}
        
        try:
            if not hasattr(self, 'df') or self.df is None:
                return {"message": "No data loaded", "updated_count": 0}
            
            # Get all classic type products with strains
            from src.core.constants import CLASSIC_TYPES
            classic_mask = self.df["Product Type*"].str.strip().str.lower().isin(CLASSIC_TYPES)
            classic_df = self.df[classic_mask]
            
            if classic_df.empty:
                return {"message": "No classic type products found", "updated_count": 0}
            
            # Group by strain and get lineage information
            strain_groups = classic_df.groupby('Product Strain')
            updated_count = 0
            
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            for strain_name, group in strain_groups:
                if not strain_name or pd.isna(strain_name):
                    continue
                
                # Get the most common lineage for this strain
                lineage_counts = group['Lineage'].value_counts()
                if not lineage_counts.empty:
                    most_common_lineage = lineage_counts.index[0]
                    
                    # Update strain in database
                    if most_common_lineage and str(most_common_lineage).strip():
                        strain_id = product_db.add_or_update_strain(strain_name, most_common_lineage, sovereign=True)
                        if strain_id:
                            updated_count += 1
            
            message = f"Ensured lineage persistence for {updated_count} strains"
            self.logger.info(message)
            
            return {"message": message, "updated_count": updated_count}
            
        except Exception as e:
            error_msg = f"Error ensuring lineage persistence: {e}"
            self.logger.error(error_msg)
            return {"message": error_msg, "updated_count": 0}

    def save_data(self, file_path: Optional[str] = None) -> bool:
        """Save the current DataFrame to an Excel file."""
        try:
            if self.df is None or self.df.empty:
                self.logger.warning("No data to save")
                return False
            
            # Use the current file path if none provided
            if file_path is None:
                file_path = self.current_file_path
            
            if not file_path:
                self.logger.error("No file path specified for saving")
                return False
            
            # Save to Excel file
            self.df.to_excel(file_path, index=False, engine='openpyxl')
            self.logger.info(f"Data saved successfully to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def update_lineage_in_current_data(self, tag_name: str, new_lineage: str) -> bool:
        """Update lineage for a specific product in the current data."""
        try:
            if self.df is None:
                self.logger.error("No data loaded")
                return False
            
            # Find the tag in the DataFrame and update its lineage
            self.logger.info(f"Looking for tag: '{tag_name}'")
            
            # Try different column names for product names
            product_name_columns = ['ProductName', 'Product Name*', 'Product Name']
            mask = None
            
            for col in product_name_columns:
                if col in self.df.columns:
                    mask = self.df[col] == tag_name
                    if mask.any():
                        break
            
            if mask is None or not mask.any():
                self.logger.error(f"Tag '{tag_name}' not found in any product name column")
                return False
            
            # Get the original lineage for logging
            original_lineage = 'Unknown'
            try:
                original_lineage = self.df.loc[mask, 'Lineage'].iloc[0]
            except (IndexError, KeyError):
                original_lineage = 'Unknown'
            
            # Check if this is a paraphernalia product and enforce PARAPHERNALIA lineage
            try:
                product_type = self.df.loc[mask, 'Product Type*'].iloc[0]
                if str(product_type).strip().lower() == 'paraphernalia':
                    new_lineage = 'PARAPHERNALIA'
                    self.logger.info(f"Enforcing PARAPHERNALIA lineage for paraphernalia product: {tag_name}")
                    
                    # Ensure PARAPHERNALIA is in the categorical categories
                    if 'Lineage' in self.df.columns and hasattr(self.df['Lineage'], 'cat'):
                        current_categories = list(self.df['Lineage'].cat.categories)
                        if 'PARAPHERNALIA' not in current_categories:
                            self.df['Lineage'] = self.df['Lineage'].cat.add_categories(['PARAPHERNALIA'])
            except (IndexError, KeyError):
                pass  # If we can't determine product type, proceed with user's choice
            
            # Update the lineage in the DataFrame
            self.df.loc[mask, 'Lineage'] = new_lineage
            
            self.logger.info(f"Updated lineage for tag '{tag_name}' from '{original_lineage}' to '{new_lineage}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating lineage in current data: {e}")
            return False

    def get_strain_name_for_product(self, tag_name: str) -> Optional[str]:
        """Get the strain name for a specific product."""
        try:
            if self.df is None:
                return None
            
            # Try different column names for product names
            product_name_columns = ['ProductName', 'Product Name*', 'Product Name']
            mask = None
            
            for col in product_name_columns:
                if col in self.df.columns:
                    mask = self.df[col] == tag_name
                    if mask.any():
                        break
            
            if mask is None or not mask.any():
                return None
            
            # Get the strain name
            try:
                strain_name = self.df.loc[mask, 'Product Strain'].iloc[0]
                return str(strain_name) if strain_name else None
            except (IndexError, KeyError):
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting strain name for product '{tag_name}': {e}")
            return None

    def update_doh_in_current_data(self, tag_name: str, new_doh: str) -> bool:
        """Update DOH status for a specific product in the current data."""
        try:
            if self.df is None:
                self.logger.error("No data loaded")
                return False
            
            # Find the tag in the DataFrame and update its DOH status
            self.logger.info(f"Looking for tag: '{tag_name}' to update DOH to: '{new_doh}'")
            
            # Try different column names for product names
            product_name_columns = ['ProductName', 'Product Name*', 'Product Name']
            mask = None
            
            for col in product_name_columns:
                if col in self.df.columns:
                    mask = self.df[col] == tag_name
                    if mask.any():
                        break
            
            if mask is None or not mask.any():
                self.logger.error(f"Tag '{tag_name}' not found in any product name column")
                return False
            
            # Get the original DOH status for logging
            original_doh = 'Unknown'
            try:
                # Check both DOH column variants
                if 'DOH' in self.df.columns:
                    original_doh = self.df.loc[mask, 'DOH'].iloc[0]
                elif 'DOH Compliant (Yes/No)' in self.df.columns:
                    original_doh = self.df.loc[mask, 'DOH Compliant (Yes/No)'].iloc[0]
            except (IndexError, KeyError):
                original_doh = 'Unknown'
            
            # Update DOH status in both possible columns
            updated_count = 0
            if 'DOH' in self.df.columns:
                self.df.loc[mask, 'DOH'] = new_doh
                updated_count += 1
                
            if 'DOH Compliant (Yes/No)' in self.df.columns:
                self.df.loc[mask, 'DOH Compliant (Yes/No)'] = new_doh
                updated_count += 1
            
            if updated_count > 0:
                self.logger.info(f"Successfully updated DOH for '{tag_name}' from '{original_doh}' to '{new_doh}' ({updated_count} columns updated)")
                return True
            else:
                self.logger.error(f"No DOH columns found to update for '{tag_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating DOH for '{tag_name}': {e}")
            return False

    def update_doh_in_database(self, tag_name: str, new_doh: str) -> bool:
        """Update DOH status for a specific product in the database."""
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase(store_name=self._store_name)
            
            # Update product DOH status in database
            success = product_db.update_product_doh(tag_name, new_doh)
            
            if success:
                self.logger.info(f"Updated DOH for product '{tag_name}' to '{new_doh}' in database")
                return True
            else:
                self.logger.error(f"Failed to update DOH for product '{tag_name}' in database")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating DOH for product '{tag_name}' in database: {e}")
            return False

    def pythonanywhere_fast_load(self, file_path: str) -> bool:
        """Ultra-fast loading specifically optimized for PythonAnywhere environment."""
        try:
            self.logger.info(f"[PYTHONANYWHERE-FAST] Loading file: {file_path}")
            
            # Apply PythonAnywhere-specific optimizations
            self._apply_pythonanywhere_optimizations()
            
            # Clear previous data efficiently
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                import gc
                gc.collect()
            
            # Use minimal Excel reading settings
            dtype_dict = {
                "Product Name*": "string",
                "Product Type*": "string",
                "Lineage": "string",
                "Product Brand": "string"
            }
            
            # Read with minimal processing
            df = pd.read_excel(
                file_path, 
                engine='openpyxl',
                dtype=dtype_dict,
                na_filter=False,  # Don't filter NA values for speed
                keep_default_na=False  # Don't use default NA values
            )
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            self.logger.info(f"[PYTHONANYWHERE-FAST] Successfully read {len(df)} rows, {len(df.columns)} columns")
            
            # Handle duplicate columns efficiently
            df = handle_duplicate_columns(df)
            
            # Remove duplicates efficiently
            initial_count = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            final_count = len(df)
            
            if initial_count != final_count:
                self.logger.info(f"[PYTHONANYWHERE-FAST] Removed {initial_count - final_count} duplicate rows")
            
            # Apply minimal processing only
            df = self._minimal_pythonanywhere_processing(df)
            
            # Set the dataframe
            self.df = df
            self._last_loaded_file = file_path
            
            # Cache the result
            self._cache_file_result(file_path, df)
            
            self.logger.info(f"[PYTHONANYWHERE-FAST] Fast load completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"[PYTHONANYWHERE-FAST] Error in fast load: {e}")
            return False
    
    def _apply_pythonanywhere_optimizations(self):
        """Apply PythonAnywhere-specific optimizations."""
        # Reduce pandas memory usage
        pd.options.mode.chained_assignment = None
        pd.options.mode.use_inf_as_na = True
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Disable product database integration for faster loading
        self._product_db_enabled = False
        
        self.logger.info("[PYTHONANYWHERE-FAST] Applied PythonAnywhere optimizations")
    
    def _minimal_pythonanywhere_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply minimal processing for PythonAnywhere fast loading."""
        try:
            # Only essential processing
            if len(df) == 0:
                return df
            
            # Ensure required columns exist
            required_columns = ['Product Name*', 'Product Type*', 'Lineage', 'Product Brand']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = "Unknown"
            
            # Basic string cleaning for key columns
            for col in required_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Remove excluded product types (minimal check)
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            self.logger.info(f"[PYTHONANYWHERE-FAST] Minimal processing completed: {len(df)} rows remaining")
            return df
            
        except Exception as e:
            self.logger.error(f"[PYTHONANYWHERE-FAST] Error in minimal processing: {e}")
            return df
    
    def _cache_file_result(self, file_path: str, df: pd.DataFrame):
        """Cache the file result for faster subsequent loads."""
        try:
            import hashlib
            import pickle
            
            # Create cache key based on file path and modification time
            file_mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}_{file_mtime}"
            
            # Store in memory cache (limited size for PythonAnywhere)
            if len(self._file_cache) >= 3:  # Keep only 3 files in cache
                # Remove oldest entry
                oldest_key = next(iter(self._file_cache))
                del self._file_cache[oldest_key]
            
            self._file_cache[cache_key] = df.copy()
            self.logger.info(f"[PYTHONANYWHERE-FAST] Cached file result for {file_path}")
            
        except Exception as e:
            self.logger.warning(f"[PYTHONANYWHERE-FAST] Error caching file result: {e}")
    
    def enable_pythonanywhere_mode(self, enable: bool = True):
        """Enable PythonAnywhere-specific optimizations."""
        if enable:
            self._product_db_enabled = False  # Disable for faster loading
            self.logger.info("[PYTHONANYWHERE-FAST] PythonAnywhere mode enabled")
        else:
            self._product_db_enabled = True
            self.logger.info("[PYTHONANYWHERE-FAST] PythonAnywhere mode disabled")

    def repair_missing_data_for_json_matches(self, json_matched_products):
        """
        Intelligently repair missing data for JSON matched products using Excel data logic.
        
        Args:
            json_matched_products (list): List of product dictionaries from JSON matching
            
        Returns:
            list: List of repaired product dictionaries with complete data
        """
        if not json_matched_products:
            logger.warning("No JSON matched products to repair")
            return []
        
        logger.info(f"Starting data repair for {len(json_matched_products)} JSON matched products")
        
        repaired_products = []
        
        for product in json_matched_products:
            try:
                # Create a copy to avoid modifying the original
                repaired_product = product.copy()
                
                # Get the product name for identification
                product_name = (repaired_product.get('Product Name*', '') or 
                              repaired_product.get('ProductName', '') or 
                              repaired_product.get('product_name', '')).strip()
                
                if not product_name:
                    logger.warning(f"Skipping product with no name: {product}")
                    continue
                
                logger.debug(f"Repairing data for product: {product_name}")
                
                # Debug: Log the current state of the product
                logger.debug(f"Current product state: {repaired_product}")
                
                # 1. REPAIR PRODUCT TYPE - Use intelligent matching from existing data
                if not repaired_product.get('Product Type*') or repaired_product.get('Product Type*') == 'Unknown':
                    logger.debug(f"Repairing Product Type* for {product_name}")
                    inferred_type = self._infer_product_type_from_existing_data(product_name)
                    if not inferred_type:
                        inferred_type = self._infer_product_type(product_name)  # Fallback to pattern matching
                    logger.debug(f"Inferred product type: {inferred_type}")
                    repaired_product['Product Type*'] = inferred_type
                else:
                    logger.debug(f"Product Type* already set: {repaired_product.get('Product Type*')}")
                
                # 2. REPAIR PRODUCT BRAND - Use intelligent matching from existing data
                if not repaired_product.get('Product Brand') or repaired_product.get('Product Brand') == 'Unknown':
                    logger.debug(f"Repairing Product Brand for {product_name}")
                    inferred_brand = self._infer_brand_from_existing_data(product_name)
                    if not inferred_brand:
                        inferred_brand = self._extract_brand_from_name(product_name)  # Fallback to pattern matching
                    logger.debug(f"Inferred brand: {inferred_brand}")
                    repaired_product['Product Brand'] = inferred_brand
                else:
                    logger.debug(f"Product Brand already set: {repaired_product.get('Product Brand')}")
                
                # 3. REPAIR VENDOR - Use intelligent matching from existing data
                if not repaired_product.get('Vendor') or repaired_product.get('Vendor') == 'Unknown':
                    logger.debug(f"Repairing Vendor for {product_name}")
                    inferred_vendor = self._infer_vendor_from_existing_data(product_name)
                    if not inferred_vendor:
                        inferred_vendor = self._infer_vendor_from_context(product_name)  # Fallback to pattern matching
                    logger.debug(f"Inferred vendor: {inferred_vendor}")
                    repaired_product['Vendor'] = inferred_vendor
                else:
                    logger.debug(f"Vendor already set: {repaired_product.get('Vendor')}")
                
                # 4. REPAIR PRODUCT STRAIN - Use intelligent matching from existing data
                if not repaired_product.get('Product Strain') or repaired_product.get('Product Strain') == 'Unknown':
                    logger.debug(f"Repairing Product Strain for {product_name}")
                    inferred_strain = self._infer_strain_from_existing_data(product_name)
                    if not inferred_strain:
                        inferred_strain = self._infer_strain_from_name(product_name)  # Fallback to pattern matching
                    logger.debug(f"Inferred strain: {inferred_strain}")
                    repaired_product['Product Strain'] = inferred_strain
                else:
                    logger.debug(f"Product Strain already set: {repaired_product.get('Product Strain')}")
                
                # 5. REPAIR LINEAGE - Use intelligent matching from existing data
                if not repaired_product.get('Lineage') or repaired_product.get('Lineage') == 'MIXED':
                    logger.debug(f"Repairing Lineage for {product_name}")
                    inferred_lineage = self._infer_lineage_from_existing_data(product_name)
                    if not inferred_lineage:
                        inferred_lineage = self._infer_lineage_from_name(product_name, repaired_product.get('Product Type*'))  # Fallback to pattern matching
                    logger.debug(f"Inferred lineage: {inferred_lineage}")
                    repaired_product['Lineage'] = inferred_lineage
                else:
                    logger.debug(f"Lineage already set: {repaired_product.get('Lineage')}")
                
                # 6. REPAIR PRICE
                if not repaired_product.get('Price') or repaired_product.get('Price') == '$0':
                    logger.debug(f"Repairing Price for {product_name}")
                    inferred_price = self._infer_price_from_type(repaired_product['Product Type*'])
                    logger.debug(f"Inferred price: {inferred_price}")
                    repaired_product['Price'] = inferred_price
                else:
                    logger.debug(f"Price already set: {repaired_product.get('Price')}")
                
                # 7. REPAIR WEIGHT AND UNITS
                if not repaired_product.get('Weight*') or repaired_product.get('Weight*') == '0':
                    logger.debug(f"Repairing Weight and Units for {product_name}")
                    weight_info = self._infer_weight_from_name(product_name, repaired_product['Product Type*'])
                    logger.debug(f"Inferred weight info: {weight_info}")
                    repaired_product['Weight*'] = weight_info['weight']
                    repaired_product['Units'] = weight_info['units']
                else:
                    logger.debug(f"Weight and Units already set: {repaired_product.get('Weight*')} {repaired_product.get('Units')}")
                
                # 8. REPAIR THC/CBD VALUES - Use intelligent matching from existing data
                if not repaired_product.get('THC test result') or repaired_product.get('THC test result') == 0.0:
                    logger.debug(f"Repairing THC for {product_name}")
                    inferred_thc = self._infer_thc_from_existing_data(product_name)
                    if not inferred_thc:
                        inferred_thc = self._infer_thc_from_type(repaired_product['Product Type*'])  # Fallback to type-based inference
                    logger.debug(f"Inferred THC: {inferred_thc}")
                    # Convert to float for proper numeric handling
                    repaired_product['THC test result'] = float(inferred_thc)
                else:
                    logger.debug(f"THC already set: {repaired_product.get('THC test result')}")
                
                if not repaired_product.get('CBD test result') or repaired_product.get('CBD test result') == 0.0:
                    logger.debug(f"Repairing CBD for {product_name}")
                    inferred_cbd = self._infer_cbd_from_existing_data(product_name)
                    if not inferred_cbd:
                        inferred_cbd = self._infer_cbd_from_type(repaired_product['Product Type*'])  # Fallback to type-based inference
                    logger.debug(f"Inferred CBD: {inferred_cbd}")
                    # Convert to float for proper numeric handling
                    repaired_product['CBD test result'] = float(inferred_cbd)
                else:
                    logger.debug(f"CBD already set: {repaired_product.get('CBD test result')}")
                
                # 9. REPAIR RATIO
                if not repaired_product.get('Ratio') or repaired_product.get('Ratio') == '':
                    logger.debug(f"Repairing Ratio for {product_name}")
                    if repaired_product.get('THC test result') and repaired_product.get('CBD test result'):
                        ratio = f"{repaired_product['THC test result']}:{repaired_product['CBD test result']}"
                        repaired_product['Ratio'] = ratio
                        logger.debug(f"Calculated ratio: {ratio}")
                else:
                    logger.debug(f"Ratio already set: {repaired_product.get('Ratio')}")
                
                # 10. REPAIR DESCRIPTION
                if not repaired_product.get('Description') or repaired_product.get('Description') == '':
                    logger.debug(f"Repairing Description for {product_name}")
                    inferred_desc = self._infer_description_from_name(product_name, repaired_product['Product Type*'])
                    logger.debug(f"Inferred description: {inferred_desc}")
                    repaired_product['Description'] = inferred_desc
                else:
                    logger.debug(f"Description already set: {repaired_product.get('Description')}")
                
                # 11. REPAIR WEIGHT UNITS
                if not repaired_product.get('WeightUnits') or repaired_product.get('WeightUnits') == '':
                    logger.debug(f"Repairing WeightUnits for {product_name}")
                    repaired_product['WeightUnits'] = repaired_product.get('Units', 'g')
                    logger.debug(f"Set WeightUnits to: {repaired_product['WeightUnits']}")
                else:
                    logger.debug(f"WeightUnits already set: {repaired_product.get('WeightUnits')}")
                
                # 12. MARK AS REPAIRED
                repaired_product['DataRepaired'] = True
                repaired_product['RepairTimestamp'] = datetime.datetime.now().isoformat()
                
                repaired_products.append(repaired_product)
                logger.debug(f"Successfully repaired product: {product_name}")
                
            except Exception as e:
                logger.error(f"Error repairing product {product_name}: {e}")
                # Add the original product even if repair failed
                repaired_products.append(product)
        
        logger.info(f"Data repair completed. {len(repaired_products)} products processed")
        return repaired_products
    
    def _infer_product_type(self, product_name):
        """Infer product type from product name using intelligent pattern matching."""
        name_lower = product_name.lower()
        
        # Flower types
        if any(word in name_lower for word in ['flower', 'bud', 'nug', 'herb', 'cannabis']):
            return 'Flower'
        
        # Pre-roll types
        if any(word in name_lower for word in ['pre-roll', 'preroll', 'joint', 'roll', 'cigarette']):
            return 'Pre-roll'
        
        # Concentrate types
        if any(word in name_lower for word in ['concentrate', 'wax', 'shatter', 'live resin', 'rosin', 'budder', 'crumble']):
            return 'Concentrate'
        
        # Vape types
        if any(word in name_lower for word in ['vape', 'cartridge', 'cart', 'pen', 'disposable']):
            return 'Vape Cartridge'
        
        # Edible types
        if any(word in name_lower for word in ['edible', 'gummy', 'chocolate', 'cookie', 'brownie', 'candy', 'food']):
            return 'Edible (Solid)'
        
        # Liquid edible types
        if any(word in name_lower for word in ['tincture', 'oil', 'drops', 'liquid', 'drink', 'beverage']):
            return 'Edible (Liquid)'
        
        # Topical types
        if any(word in name_lower for word in ['topical', 'cream', 'lotion', 'salve', 'balm', 'ointment']):
            return 'Topical'
        
        # Capsule types
        if any(word in name_lower for word in ['capsule', 'pill', 'tablet', 'supplement']):
            return 'Capsule'
        
        # RSO/CO2 types
        if any(word in name_lower for word in ['rso', 'co2', 'tanker', 'syringe']):
            return 'rso/co2 tankers'
        
        # Default to flower if no clear indication
        return 'Flower'
    
    def _extract_brand_from_name(self, product_name):
        """Extract brand information from product name using pattern matching."""
        name_lower = product_name.lower()
        
        # Common brand patterns
        brand_patterns = [
            r'by\s+([A-Za-z\s&]+?)(?:\s|$)',
            r'from\s+([A-Za-z\s&]+?)(?:\s|$)',
            r'([A-Za-z\s&]+?)\s+strain',
            r'([A-Za-z\s&]+?)\s+line',
            r'([A-Za-z\s&]+?)\s+collection'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, name_lower)
            if match:
                brand = match.group(1).strip().title()
                if len(brand) > 2:  # Avoid very short matches
                    return brand
        
        # Try to extract from common brand names in the dataset
        if self.df is not None and 'Product Brand' in self.df.columns:
            available_brands = self.df['Product Brand'].dropna().unique()
            for brand in available_brands:
                if str(brand).lower() in name_lower:
                    return str(brand)
        
        # Default brand based on product type
        return 'Premium Cannabis'
    
    def _infer_strain_from_name(self, product_name):
        """Infer strain information from product name."""
        name_lower = product_name.lower()
        
        # Common strain patterns
        strain_patterns = [
            r'([A-Za-z\s]+?)\s+(?:strain|variety|cultivar)',
            r'([A-Za-z\s]+?)\s+(?:kush|haze|diesel|og|gelato|cookies)',
            r'([A-Za-z\s]+?)\s+(?:berry|fruit|citrus|mint|vanilla)'
        ]
        
        for pattern in strain_patterns:
            match = re.search(pattern, name_lower)
            if match:
                strain = match.group(1).strip().title()
                if len(strain) > 2:
                    return strain
        
        # Try to extract from common strain names in the dataset
        if self.df is not None and 'Product Strain' in self.df.columns:
            available_strains = self.df['Product Strain'].dropna().unique()
            for strain in available_strains:
                if str(strain).lower() in name_lower:
                    return str(strain)
        
        # Default strain
        return 'Premium Blend'
    
    def _infer_lineage_from_name(self, product_name, product_type=None):
        """Infer lineage from product name and strain information."""
        # Import constants to check product type classification
        from src.core.constants import CLASSIC_TYPES
        
        name_lower = product_name.lower()
        
        # CRITICAL FIX: Check for explicit lineage indicators FIRST, regardless of product type
        # This ensures JSON matched tags like "Indica Salted Caramel" get proper lineage
        if any(word in name_lower for word in ['sativa', 'sativa-dominant']):
            return 'SATIVA'
        elif any(word in name_lower for word in ['indica', 'indica-dominant']):
            return 'INDICA'
        elif any(word in name_lower for word in ['hybrid', 'balanced']):
            return 'HYBRID'
        elif any(word in name_lower for word in ['cbd', 'hemp', 'low-thc']):
            return 'CBD'
        
        # If product type is provided and no explicit lineage found, check if it's a classic type
        if product_type:
            product_type_lower = product_type.strip().lower()
            if product_type_lower not in CLASSIC_TYPES:
                # Nonclassic types without explicit lineage indicators default to MIXED
                return 'MIXED'
        
        # Try to infer from strain name patterns
        strain = self._infer_strain_from_name(product_name)
        strain_lower = strain.lower()
        
        # Known sativa strains
        sativa_strains = ['haze', 'diesel', 'jack', 'lemon', 'sour', 'durban', 'maui', 'hawaiian']
        if any(s in strain_lower for s in sativa_strains):
            return 'SATIVA'
        
        # Known indica strains
        indica_strains = ['kush', 'og', 'purple', 'granddaddy', 'afghani', 'hash', 'northern']
        if any(s in strain_lower for s in indica_strains):
            return 'INDICA'
        
        # Default to hybrid
        return 'HYBRID'
    
    def _infer_vendor_from_context(self, product_name):
        """Infer vendor information from context and available data."""
        # Try to find vendor from existing data
        if self.df is not None and 'Vendor' in self.df.columns:
            available_vendors = self.df['Vendor'].dropna().unique()
            if len(available_vendors) > 0:
                # Return the most common vendor
                vendor_counts = self.df['Vendor'].value_counts()
                return str(vendor_counts.index[0])
        
        # Default vendor
        return 'Premium Supplier'
    
    def _infer_price_from_type(self, product_type):
        """Infer price based on product type and market standards."""
        price_ranges = {
            'Flower': '$45.00',
            'Pre-roll': '$12.00',
            'Concentrate': '$35.00',
            'Vape Cartridge': '$25.00',
            'Edible (Solid)': '$20.00',
            'Edible (Liquid)': '$30.00',
            'Topical': '$25.00',
            'Capsule': '$25.00',
            'rso/co2 tankers': '$40.00'
        }
        
        return price_ranges.get(product_type, '$25.00')
    
    def _infer_weight_from_name(self, product_name, product_type):
        """Infer weight and units from product name and type."""
        name_lower = product_name.lower()
        
        # Extract weight from name patterns
        weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*(g|gram|grams|oz|ounce|ounces)',
            r'(\d+(?:\.\d+)?)\s*(pack|packs|pk)',
            r'(\d+(?:\.\d+)?)\s*(piece|pieces)',
            r'(\d+(?:\.\d+)?)\s*(roll|rolls)'
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, name_lower)
            if match:
                weight = match.group(1)
                unit = match.group(2)
                
                # Standardize units
                if unit in ['g', 'gram', 'grams']:
                    return {'weight': weight, 'units': 'g'}
                elif unit in ['oz', 'ounce', 'ounces']:
                    return {'weight': weight, 'units': 'oz'}
                elif unit in ['pack', 'packs', 'pk']:
                    return {'weight': weight, 'units': 'pack'}
                elif unit in ['piece', 'pieces']:
                    return {'weight': weight, 'units': 'piece'}
                elif unit in ['roll', 'rolls']:
                    return {'weight': weight, 'units': 'roll'}
        
        # Default weights by product type
        default_weights = {
            'Flower': {'weight': '3.5', 'units': 'g'},
            'Pre-roll': {'weight': '1', 'units': 'pack'},
            'Concentrate': {'weight': '1', 'units': 'g'},
            'Vape Cartridge': {'weight': '1', 'units': 'piece'},
            'Edible (Solid)': {'weight': '1', 'units': 'piece'},
            'Edible (Liquid)': {'weight': '30', 'units': 'ml'},
            'Topical': {'weight': '1', 'units': 'oz'},
            'Capsule': {'weight': '30', 'units': 'piece'},
            'rso/co2 tankers': {'weight': '1', 'units': 'g'}
        }
        
        return default_weights.get(product_type, {'weight': '1', 'units': 'piece'})
    
    def _infer_thc_from_type(self, product_type):
        """Infer THC content based on product type."""
        thc_ranges = {
            'Flower': '18.5',
            'Pre-roll': '20.0',
            'Concentrate': '75.0',
            'Vape Cartridge': '85.0',
            'Edible (Solid)': '10.0',
            'Edible (Liquid)': '15.0',
            'Topical': '0.0',
            'Capsule': '25.0',
            'rso/co2 tankers': '80.0'
        }
        
        return thc_ranges.get(product_type, '20.0')
    
    def _infer_cbd_from_type(self, product_type):
        """Infer CBD content based on product type."""
        cbd_ranges = {
            'Flower': '0.5',
            'Pre-roll': '0.8',
            'Concentrate': '2.0',
            'Vape Cartridge': '1.5',
            'Edible (Solid)': '5.0',
            'Edible (Liquid)': '8.0',
            'Topical': '100.0',
            'Capsule': '25.0',
            'rso/co2 tankers': '5.0'
        }
        
        return cbd_ranges.get(product_type, '1.0')
    
    def _infer_ratio_from_thc_cbd(self, thc_value, cbd_value):
        """Infer THC:CBD ratio from THC and CBD values."""
        try:
            thc = float(thc_value) if thc_value else 0
            cbd = float(cbd_value) if cbd_value else 0
            
            if thc > 0 and cbd > 0:
                ratio = thc / cbd
                if ratio >= 10:
                    return f"{thc:.0f}:1"
                elif ratio >= 2:
                    return f"{ratio:.1f}:1"
                elif ratio >= 0.5:
                    return f"1:{1/ratio:.1f}"
                else:
                    return f"1:{1/ratio:.0f}"
            elif thc > 0:
                return f"{thc:.0f}:0"
            elif cbd > 0:
                return f"0:{cbd:.0f}"
            else:
                return "0:0"
        except:
            return "20:1"  # Default ratio
    
    def _generate_description(self, product_name, product_type, product_brand):
        """Generate a descriptive description for the product."""
        descriptions = {
            'Flower': f"Premium {product_brand} cannabis flower featuring {product_name}. Hand-crafted and carefully cultivated for exceptional quality and potency.",
            'Pre-roll': f"Convenient {product_brand} pre-roll featuring {product_name}. Perfect for on-the-go consumption with premium cannabis quality.",
            'Concentrate': f"High-potency {product_brand} concentrate featuring {product_name}. Extracted using advanced methods for maximum terpene preservation.",
            'Vape Cartridge': f"Premium {product_brand} vape cartridge featuring {product_name}. Clean, smooth vaping experience with authentic cannabis flavor.",
            'Edible (Solid)': f"Delicious {product_brand} edible featuring {product_name}. Carefully dosed for consistent effects and great taste.",
            'Edible (Liquid)': f"Premium {product_brand} liquid edible featuring {product_name}. Fast-acting and precisely dosed for optimal results.",
            'Topical': f"Effective {product_brand} topical featuring {product_name}. Formulated for targeted relief and skin nourishment.",
            'Capsule': f"Convenient {product_brand} capsule featuring {product_name}. Consistent dosing in an easy-to-take format.",
            'rso/co2 tankers': f"High-potency {product_brand} extract featuring {product_name}. Full-spectrum benefits in a concentrated form."
        }
        
        return descriptions.get(product_type, f"Premium {product_brand} product featuring {product_name}.")

    def _infer_product_type_from_existing_data(self, product_name):
        """
        Intelligently infer product type by finding similar products in existing Excel data.
        This method uses enhanced matching strategies to find more similar products.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their product type
            if similar_products:
                # Get the most common product type from similar products
                product_types = []
                for product in similar_products:
                    product_type = product.get('Product Type*', '') or product.get('ProductType', '')
                    if product_type and product_type != 'nan':
                        product_types.append(str(product_type).strip())
                
                if product_types:
                    # Return the most common product type
                    from collections import Counter
                    type_counter = Counter(product_types)
                    most_common_type = type_counter.most_common(1)[0][0]
                    logger.debug(f"Found {len(similar_products)} similar products, using most common type: {most_common_type}")
                    return most_common_type
            
            # If no similar products found, try to infer from the name itself
            logger.debug(f"No similar products found for {product_name}, falling back to pattern matching")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent product type inference: {e}")
            return None
    
    def _infer_brand_from_existing_data(self, product_name):
        """
        Intelligently infer product brand by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their brand
            if similar_products:
                # Get the most common brand from similar products
                brands = []
                for product in similar_products:
                    brand = product.get('Product Brand', '') or product.get('Brand', '')
                    if brand and brand != 'nan':
                        brands.append(str(brand).strip())
                
                if brands:
                    # Return the most common brand
                    from collections import Counter
                    brand_counter = Counter(brands)
                    most_common_brand = brand_counter.most_common(1)[0][0]
                    logger.debug(f"Found {len(similar_products)} similar products, using most common brand: {most_common_brand}")
                    return most_common_brand
            
            # If no similar products found, try to extract brand from name
            logger.debug(f"No similar products found for {product_name}, falling back to pattern matching")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent brand inference: {e}")
            return None
    
    def _infer_vendor_from_existing_data(self, product_name):
        """
        Intelligently infer vendor by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their vendor
            if similar_products:
                # Get the most common vendor from similar products
                vendors = []
                for product in similar_products:
                    vendor = product.get('Vendor', '') or product.get('Supplier*', '')
                    if vendor and vendor != 'nan':
                        vendors.append(str(vendor).strip())
                
                if vendors:
                    # Return the most common vendor
                    from collections import Counter
                    vendor_counter = Counter(vendors)
                    most_common_vendor = vendor_counter.most_common(1)[0][0]
                    logger.debug(f"Found {len(similar_products)} similar products, using most common vendor: {most_common_vendor}")
                    return most_common_vendor
            
            # If no similar products found, try to infer from context
            logger.debug(f"No similar products found for {product_name}, falling back to pattern matching")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent vendor inference: {e}")
            return None

    def _infer_description_from_name(self, product_name, product_type):
        """
        Infer description from product name and type.
        """
        try:
            # Basic description generation based on product type
            descriptions = {
                'Flower': f'Premium {product_type} featuring {product_name}',
                'Pre-roll': f'Handcrafted {product_type} with {product_name}',
                'Concentrate': f'High-potency {product_type} extract of {product_name}',
                'Edible': f'Delicious {product_type} infused with {product_name}',
                'Vape': f'Smooth {product_type} cartridge with {product_name}',
                'Tincture': f'Potent {product_type} tincture of {product_name}',
                'Topical': f'Soothing {product_type} with {product_name}'
            }
            
            return descriptions.get(product_type, f'Premium {product_type} product featuring {product_name}.')
            
        except Exception as e:
            logger.error(f"Error inferring description: {e}")
            return f'Premium {product_type} product'
    
    def _infer_weight_from_name(self, product_name, product_type):
        """
        Infer weight and units from product name.
        """
        try:
            import re
            
            # Look for weight patterns in the name
            weight_pattern = r'(\d+\.?\d*)\s*(g|gram|grams|ml|oz|ounce|ounces)'
            match = re.search(weight_pattern, product_name.lower())
            
            if match:
                weight = match.group(1)
                units = match.group(2)
                
                # Normalize units
                if units in ['g', 'gram', 'grams']:
                    units = 'g'
                elif units in ['ml']:
                    units = 'ml'
                elif units in ['oz', 'ounce', 'ounces']:
                    units = 'oz'
                
                return {'weight': weight, 'units': units}
            
            # Default weights based on product type
            default_weights = {
                'Flower': {'weight': '3.5', 'units': 'g'},
                'Pre-roll': {'weight': '1.0', 'units': 'g'},
                'Concentrate': {'weight': '1.0', 'units': 'g'},
                'Edible': {'weight': '10', 'units': 'mg'},
                'Vape': {'weight': '0.5', 'units': 'g'},
                'Tincture': {'weight': '30', 'units': 'ml'},
                'Topical': {'weight': '30', 'units': 'ml'}
            }
            
            return default_weights.get(product_type, {'weight': '1.0', 'units': 'g'})
            
        except Exception as e:
            logger.error(f"Error inferring weight: {e}")
            return {'weight': '1.0', 'units': 'g'}
    
    def _infer_thc_from_type(self, product_type):
        """
        Infer THC content based on product type.
        """
        try:
            # Default THC values based on product type
            default_thc = {
                'Flower': 18.0,
                'Pre-roll': 20.0,
                'Concentrate': 80.0,
                'Edible': 10.0,
                'Vape': 70.0,
                'Tincture': 25.0,
                'Topical': 0.0
            }
            
            return default_thc.get(product_type, 15.0)
            
        except Exception as e:
            logger.error(f"Error inferring THC: {e}")
            return 15.0
    
    def _infer_cbd_from_type(self, product_type):
        """
        Infer CBD content based on product type.
        """
        try:
            # Default CBD values based on product type
            default_cbd = {
                'Flower': 0.5,
                'Pre-roll': 0.8,
                'Concentrate': 5.0,
                'Edible': 5.0,
                'Vape': 2.0,
                'Tincture': 15.0,
                'Topical': 50.0
            }
            
            return default_cbd.get(product_type, 0.5)
            
        except Exception as e:
            logger.error(f"Error inferring CBD: {e}")
            return 0.5

    def _infer_lineage_from_existing_data(self, product_name):
        """
        Intelligently infer lineage by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their lineage
            if similar_products:
                # Get the most common lineage from similar products
                lineages = []
                for product in similar_products:
                    lineage = product.get('Lineage', '') or product.get('lineage', '')
                    if lineage and lineage != 'nan' and lineage != 'MIXED':
                        lineages.append(str(lineage).strip())
                
                if lineages:
                    # Return the most common lineage
                    from collections import Counter
                    lineage_counter = Counter(lineages)
                    most_common_lineage = lineage_counter.most_common(1)[0][0]
                    logger.debug(f"Found {len(similar_products)} similar products, using most common lineage: {most_common_lineage}")
                    return most_common_lineage
            
            # If no similar products found, try to infer from the name itself
            logger.debug(f"No similar products found for {product_name}, falling back to pattern matching")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent lineage inference: {e}")
            return None

    def _infer_strain_from_existing_data(self, product_name):
        """
        Intelligently infer product strain by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their strain
            if similar_products:
                # Get the most common strain from similar products
                strains = []
                for product in similar_products:
                    strain = product.get('Product Strain', '') or product.get('Strain', '')
                    if strain and strain != 'nan':
                        strains.append(str(strain).strip())
                
                if strains:
                    # Return the most common strain
                    from collections import Counter
                    strain_counter = Counter(strains)
                    most_common_strain = strain_counter.most_common(1)[0][0]
                    logger.debug(f"Found {len(similar_products)} similar products, using most common strain: {most_common_strain}")
                    return most_common_strain
            
            # If no similar products found, try to infer from the name itself
            logger.debug(f"No similar products found for {product_name}, falling back to pattern matching")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent strain inference: {e}")
            return None

    def _find_similar_products(self, product_name, search_strategy='comprehensive'):
        """
        Enhanced method to find similar products using multiple strategies.
        
        Args:
            product_name (str): The product name to find matches for
            search_strategy (str): Strategy to use - 'comprehensive', 'aggressive', or 'conservative'
            
        Returns:
            list: List of similar product rows
        """
        if not self.df is not None or self.df.empty:
            logger.warning("No Excel data available for product matching")
            return []
        
        try:
            # Normalize the product name for comparison
            normalized_name = product_name.lower().strip()
            normalized_words = set(word for word in normalized_name.split() if len(word) > 2)  # Filter out short words
            
            # Look for exact or partial matches in existing product names
            product_name_col = 'Product Name*' if 'Product Name*' in self.df.columns else 'ProductName'
            if product_name_col not in self.df.columns:
                return []
            
            similar_products = []
            
            for _, row in self.df.iterrows():
                existing_name = str(row.get(product_name_col, '')).lower().strip()
                if existing_name and existing_name != 'nan':
                    existing_words = set(word for word in existing_name.split() if len(word) > 2)
                    
                    # Strategy 1: Exact matches
                    if normalized_name == existing_name:
                        similar_products.append(row)
                        continue
                    
                    # Strategy 2: High similarity matches (comprehensive strategy)
                    if search_strategy in ['comprehensive', 'aggressive']:
                        # Check for significant word overlap
                        word_overlap = len(normalized_words.intersection(existing_words))
                        total_unique_words = len(normalized_words.union(existing_words))
                        
                        if total_unique_words > 0:
                            similarity_score = word_overlap / total_unique_words
                            
                            # Comprehensive: 30% word overlap, Aggressive: 20% word overlap
                            threshold = 0.3 if search_strategy == 'comprehensive' else 0.2
                            if similarity_score >= threshold:
                                similar_products.append(row)
                                continue
                    
                    # Strategy 3: Brand/type matching
                    if search_strategy in ['comprehensive', 'aggressive']:
                        # Check if brand names match
                        brand_col = 'Product Brand' if 'Product Brand' in self.df.columns else 'Brand'
                        if brand_col in self.df.columns:
                            existing_brand = str(row.get(brand_col, '')).lower().strip()
                            if existing_brand and existing_brand != 'nan':
                                # Check if any brand word appears in the product name
                                brand_words = set(word for word in existing_brand.split() if len(word) > 2)
                                if brand_words.intersection(normalized_words):
                                    similar_products.append(row)
                                    continue
                    
                    # Strategy 4: Weight/size matching
                    if search_strategy in ['comprehensive', 'aggressive']:
                        import re
                        weight_pattern = r'(\d+\.?\d*)\s*(g|gram|grams|ml|oz|ounce|ounces)'
                        new_weight_match = re.search(weight_pattern, normalized_name)
                        existing_weight_match = re.search(weight_pattern, existing_name)
                        
                        if new_weight_match and existing_weight_match:
                            new_weight = float(new_weight_match.group(1))
                            existing_weight = float(existing_weight_match.group(1))
                            # More flexible weight matching
                            weight_tolerance = 0.5 if search_strategy == 'aggressive' else 0.1
                            if abs(new_weight - existing_weight) <= weight_tolerance:
                                similar_products.append(row)
                                continue
                    
                    # Strategy 5: Product type matching
                    if search_strategy in ['comprehensive', 'aggressive']:
                        # Check if product types are similar
                        type_col = 'Product Type*' if 'Product Type*' in self.df.columns else 'ProductType'
                        if type_col in self.df.columns:
                            existing_type = str(row.get(type_col, '')).lower().strip()
                            if existing_type and existing_type != 'nan':
                                # Check if product type words appear in the product name
                                type_words = set(word for word in existing_type.split() if len(word) > 2)
                                if type_words.intersection(normalized_words):
                                    similar_products.append(row)
                                    continue
                    
                    # Strategy 6: Strain name matching
                    if search_strategy in ['comprehensive', 'aggressive']:
                        strain_col = 'Product Strain' if 'Product Strain' in self.df.columns else 'Strain'
                        if strain_col in self.df.columns:
                            existing_strain = str(row.get(strain_col, '')).lower().strip()
                            if existing_strain and existing_strain != 'nan':
                                # Check if strain names match or are similar
                                strain_words = set(word for word in existing_strain.split() if len(word) > 2)
                                if strain_words.intersection(normalized_words):
                                    similar_products.append(row)
                                    continue
                    
                    # Strategy 7: Partial substring matching (aggressive only)
                    if search_strategy == 'aggressive':
                        # Check if any significant word from the new product appears in existing names
                        for word in normalized_words:
                            if len(word) > 3 and word in existing_name:  # Only longer words
                                similar_products.append(row)
                                break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_products = []
            for product in similar_products:
                product_id = str(product.get(product_name_col, ''))
                if product_id not in seen:
                    seen.add(product_id)
                    unique_products.append(product)
            
            logger.debug(f"Found {len(unique_products)} similar products for '{product_name}' using {search_strategy} strategy")
            return unique_products
            
        except Exception as e:
            logger.error(f"Error in enhanced product matching: {e}")
            return []

    def _infer_thc_from_existing_data(self, product_name):
        """
        Intelligently infer THC content by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their THC values
            if similar_products:
                # Get the most common THC value from similar products
                thc_values = []
                for product in similar_products:
                    thc = product.get('THC test result', '') or product.get('THC', '')
                    if thc and thc != 'nan' and thc != 0:
                        try:
                            thc_float = float(thc)
                            if thc_float > 0:
                                thc_values.append(thc_float)
                        except (ValueError, TypeError):
                            continue
                
                if thc_values:
                    # Return the average THC value from similar products
                    avg_thc = sum(thc_values) / len(thc_values)
                    logger.debug(f"Found {len(similar_products)} similar products, using average THC: {avg_thc:.1f}%")
                    return round(avg_thc, 1)
            
            # If no similar products found, fall back to type-based inference
            logger.debug(f"No similar products found for {product_name}, falling back to type-based inference")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent THC inference: {e}")
            return None

    def _infer_cbd_from_existing_data(self, product_name):
        """
        Intelligently infer CBD content by finding similar products in existing Excel data.
        """
        try:
            # Use the enhanced matching system with comprehensive strategy
            similar_products = self._find_similar_products(product_name, search_strategy='comprehensive')
            
            # If we found similar products, use their CBD values
            if similar_products:
                # Get the most common CBD value from similar products
                cbd_values = []
                for product in similar_products:
                    cbd = product.get('CBD test result', '') or product.get('CBD', '')
                    if cbd and cbd != 'nan' and cbd != 0:
                        try:
                            cbd_float = float(cbd)
                            if cbd_float > 0:
                                cbd_values.append(cbd_float)
                        except (ValueError, TypeError):
                            continue
                
                if cbd_values:
                    # Return the average CBD value from similar products
                    avg_cbd = sum(cbd_values) / len(cbd_values)
                    logger.debug(f"Found {len(similar_products)} similar products, using average CBD: {avg_cbd:.1f}%")
                    return round(avg_cbd, 1)
            
            # If no similar products found, fall back to type-based inference
            logger.debug(f"No similar products found for {product_name}, falling back to type-based inference")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent CBD inference: {e}")
            return None

    def add_product_with_educated_guess(self, product_name: str, vendor: str = None, brand: str = None) -> Dict[str, Any]:
        """
        Add a new product to the Excel DataFrame using educated guessing for missing information.
        
        Args:
            product_name: The product name to add
            vendor: Optional vendor name
            brand: Optional brand name
            
        Returns:
            Dictionary with the complete product information
        """
        try:
            # First try to find the product in existing data
            existing_product = self._find_exact_product(product_name)
            if existing_product:
                logger.info(f"Product '{product_name}' already exists in Excel data")
                return existing_product
            
            # Try educated guessing from product database
            educated_guess = None
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase(store_name=self._store_name)
                educated_guess = product_db.make_educated_guess(product_name, vendor, brand)
                if educated_guess:
                    logger.info(f"✅ Made educated guess for '{product_name}': {educated_guess}")
            except Exception as e:
                logger.warning(f"Could not use product database for educated guessing: {e}")
            
            # Create product data
            if educated_guess:
                # Use educated guess data
                product_data = {
                    'Product Name*': educated_guess.get("product_name", product_name),
                    'ProductName': educated_guess.get("product_name", product_name),
                    'Description': educated_guess.get("description", product_name),
                    'Product Type*': educated_guess.get("product_type", "Unknown"),
                    'Product Type': educated_guess.get("product_type", "Unknown"),
                    'Vendor': vendor or educated_guess.get("vendor", "Unknown"),
                    'Vendor/Supplier*': vendor or educated_guess.get("vendor", "Unknown"),
                    'Product Brand': brand or educated_guess.get("brand", "Unknown"),
                    'ProductBrand': brand or educated_guess.get("brand", "Unknown"),
                    'Product Strain': educated_guess.get("strain_name", "Unknown"),
                    'Strain Name': educated_guess.get("strain_name", "Unknown"),
                    'Lineage': educated_guess.get("lineage", "HYBRID"),
                    'Weight*': educated_guess.get("weight", "1"),
                    'Weight': educated_guess.get("weight", "1"),
                    'Quantity*': '1',
                    'Quantity': '1',
                    'Units': educated_guess.get("units", "g"),
                    'Price': educated_guess.get("price", "25"),
                    'Price* (Tier Name for Bulk)': educated_guess.get("price", "25"),
                    'Source': f'Educated Guess ({educated_guess.get("confidence", "medium")})',
                    'Quantity Received*': '1',
                    'Weight Unit* (grams/gm or ounces/oz)': educated_guess.get("units", "g"),
                    'CombinedWeight': educated_guess.get("weight", "1"),
                    'DescAndWeight': self._process_description_from_product_name(educated_guess.get('product_name', product_name)),  # Use Excel processor formula
                    'Description_Complexity': '1',
                    'Ratio_or_THC_CBD': '',
                    'THC test result': '',
                    'CBD test result': '',
                    'Test result unit (% or mg)': '%',
                    'Batch Number': '',
                    'Lot Number': '',
                    'Barcode*': '',
                    'Medical Only (Yes/No)': 'No',
                    'DOH': 'No',
                    'DOH Compliant (Yes/No)': 'No',
                    'State': 'active',
                    'Is Sample? (yes/no)': 'no',
                    'Is MJ product?(yes/no)': 'yes',
                    'Discountable? (yes/no)': 'yes',
                    'Room*': 'Default',
                    'Concentrate Type': '',
                    'Ratio': '',
                    'Joint Ratio': '',
                    'JointRatio': '',
                    'Med Price': '',
                    'Expiration Date(YYYY-MM-DD)': '',
                    'Is Archived? (yes/no)': 'no',
                    'THC Per Serving': '',
                    'Allergens': '',
                    'Solvent': '',
                    'Accepted Date': '',
                    'Internal Product Identifier': '',
                    'Product Tags (comma separated)': '',
                    'Image URL': '',
                    'Ingredients': '',
                }
            else:
                # Use basic inference from existing data
                product_data = {
                    'Product Name*': product_name,
                    'ProductName': product_name,
                    'Description': product_name,
                    'Product Type*': self._infer_product_type_from_name(product_name) or "Unknown",
                    'Product Type': self._infer_product_type_from_name(product_name) or "Unknown",
                    'Vendor': vendor or "Unknown",
                    'Vendor/Supplier*': vendor or "Unknown",
                    'Product Brand': brand or "Unknown",
                    'ProductBrand': brand or "Unknown",
                    'Product Strain': self._infer_strain_from_name(product_name) or "Unknown",
                    'Strain Name': self._infer_strain_from_name(product_name) or "Unknown",
                    'Lineage': self._infer_lineage_from_name(product_name, product_type) or "HYBRID",
                    'Weight*': self._infer_weight_from_name(product_name)['weight'],
                    'Weight': self._infer_weight_from_name(product_name)['weight'],
                    'Quantity*': '1',
                    'Quantity': '1',
                    'Units': self._infer_weight_from_name(product_name)['units'],
                    'Price': self._infer_price_from_type_and_weight(
                        self._infer_product_type_from_name(product_name) or "Unknown",
                        float(self._infer_weight_from_name(product_name)['weight'])
                    ),
                    'Price* (Tier Name for Bulk)': self._infer_price_from_type_and_weight(
                        self._infer_product_type_from_name(product_name) or "Unknown",
                        float(self._infer_weight_from_name(product_name)['weight'])
                    ),
                    'Source': 'Manual Entry with Inference',
                    'Quantity Received*': '1',
                    'Weight Unit* (grams/gm or ounces/oz)': self._infer_weight_from_name(product_name)['units'],
                    'CombinedWeight': self._infer_weight_from_name(product_name)['weight'],
                    'DescAndWeight': self._process_description_from_product_name(product_name),  # Use Excel processor formula
                    'Description_Complexity': '1',
                    'Ratio_or_THC_CBD': '',
                    'THC test result': '',
                    'CBD test result': '',
                    'Test result unit (% or mg)': '%',
                    'Batch Number': '',
                    'Lot Number': '',
                    'Barcode*': '',
                    'Medical Only (Yes/No)': 'No',
                    'DOH': 'No',
                    'DOH Compliant (Yes/No)': 'No',
                    'State': 'active',
                    'Is Sample? (yes/no)': 'no',
                    'Is MJ product?(yes/no)': 'yes',
                    'Discountable? (yes/no)': 'yes',
                    'Room*': 'Default',
                    'Concentrate Type': '',
                    'Ratio': '',
                    'Joint Ratio': '',
                    'JointRatio': '',
                    'Med Price': '',
                    'Expiration Date(YYYY-MM-DD)': '',
                    'Is Archived? (yes/no)': 'no',
                    'THC Per Serving': '',
                    'Allergens': '',
                    'Solvent': '',
                    'Accepted Date': '',
                    'Internal Product Identifier': '',
                    'Product Tags (comma separated)': '',
                    'Image URL': '',
                    'Ingredients': '',
                }
            
            # Add the product to the DataFrame
            if self.df is not None:
                # Ensure all columns exist
                for key in product_data.keys():
                    if key not in self.df.columns:
                        self.df[key] = ''
                
                # Add the new row
                self.df = pd.concat([self.df, pd.DataFrame([product_data])], ignore_index=True)
                logger.info(f"✅ Added product '{product_name}' to Excel DataFrame with educated guess")
            else:
                logger.warning("No Excel DataFrame available")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error adding product with educated guess: {e}")
            return {}
    
    def _find_exact_product(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Find an exact product match in the existing Excel data."""
        if self.df is None or self.df.empty:
            return None
        
        product_name_col = 'Product Name*' if 'Product Name*' in self.df.columns else 'ProductName'
        if product_name_col not in self.df.columns:
            return None
        
        # Look for exact match
        mask = self.df[product_name_col].astype(str).str.lower() == product_name.lower()
        if mask.any():
            row = self.df[mask].iloc[0]
            return row.to_dict()
        
        return None
    
    def _infer_price_from_type_and_weight(self, product_type: str, weight: float) -> str:
        """Infer price based on product type and weight."""
        product_type_lower = product_type.lower()
        
        if 'pre-roll' in product_type_lower:
            return '20'
        elif 'flower' in product_type_lower:
            if weight <= 1:
                return '35'
            elif weight <= 3.5:
                return '120'
            elif weight <= 7:
                return '220'
            else:
                return '400'
        elif 'concentrate' in product_type_lower:
            if weight <= 1:
                return '50'
            elif weight <= 2:
                return '90'
            else:
                return '150'
        elif 'vape' in product_type_lower:
            return '40'
        elif 'edible' in product_type_lower:
            return '25'
        else:
            return '25'

    def add_json_matched_products(self, products: List[Dict]) -> bool:
        """
        Add JSON-matched products to the existing Excel DataFrame.
        This ensures that JSON-matched products can be found during validation
        and label generation.
        
        Args:
            products: List of product dictionaries from JSON matching
            
        Returns:
            True if products were successfully added, False otherwise
        """
        try:
            if not products:
                logger.info("No products to add to Excel DataFrame")
                return True
                
            if self.df is None:
                logger.warning("No Excel DataFrame available for adding products")
                return False
                
            logger.info(f"Adding {len(products)} JSON-matched products to Excel DataFrame")
            
            # Create a list to store the new rows
            new_rows = []
            
            for product in products:
                # Create a row that matches the Excel DataFrame structure
                row_data = {}
                
                # Map all the fields to Excel columns
                for key, value in product.items():
                    # Handle both the original Excel column names and the JSON matcher field names
                    if key in self.df.columns:
                        row_data[key] = value
                    else:
                        # Try to find a matching column name
                        matching_col = None
                        for col in self.df.columns:
                            if col.lower() == key.lower() or col.lower().replace(' ', '').replace('*', '') == key.lower().replace(' ', '').replace('*', ''):
                                matching_col = col
                                break
                        
                        if matching_col:
                            row_data[matching_col] = value
                        else:
                            # If no matching column found, try to add it to the DataFrame
                            if key not in self.df.columns:
                                self.df[key] = ''
                            row_data[key] = value
                
                # Ensure all required Excel columns are present
                for col in self.df.columns:
                    if col not in row_data:
                        row_data[col] = ''
                
                new_rows.append(row_data)
            
            if new_rows:
                # Create DataFrame from new rows
                new_df = pd.DataFrame(new_rows)
                
                # Append to existing DataFrame
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                
                logger.info(f"Successfully added {len(new_rows)} JSON-matched products to Excel DataFrame")
                logger.info(f"Excel DataFrame now contains {len(self.df)} total records")
                
                # Rebuild caches to include new products
                self._rebuild_caches()
                
                return True
            else:
                logger.warning("No valid rows created for Excel DataFrame addition")
                return False
                
        except Exception as e:
            logger.error(f"Error adding JSON products to Excel DataFrame: {e}")
            return False

    def _rebuild_caches(self):
        """Rebuild internal caches after adding new products."""
        try:
            # Clear existing caches
            self._dropdown_cache = None
            self._strain_cache = None
            self._vendor_cache = None
            
            # Rebuild caches using the correct method names
            if hasattr(self, '_build_dropdown_cache'):
                self._build_dropdown_cache()
            elif hasattr(self, 'build_dropdown_cache'):
                self.build_dropdown_cache()
                
            if hasattr(self, '_build_strain_cache'):
                self._build_strain_cache()
            elif hasattr(self, 'build_strain_cache'):
                self.build_strain_cache()
                
            if hasattr(self, '_build_vendor_cache'):
                self._build_vendor_cache()
            elif hasattr(self, 'build_vendor_cache'):
                self.build_vendor_cache()
            
            logger.info("Successfully rebuilt Excel processor caches")
        except Exception as e:
            logger.warning(f"Error rebuilding caches: {e}")
            # Continue without cache rebuilding - this is not critical

    def _store_upload_in_database(self, df: pd.DataFrame, source_file: str = None) -> Dict[str, Any]:
        """
        Store Excel upload data in the database while excluding JSON matched tags.
        
        Args:
            df: DataFrame containing the Excel data to store
            source_file: Path to the source Excel file
            
        Returns:
            Dictionary with storage results including counts and status
        """
        try:
            # Use the same database instance as the main app to ensure consistency
            # This prevents writing to different database files in different environments
            try:
                # Try to get the global database instance first
                from app import get_product_database
                product_db = get_product_database()
                logger.info("Using global product database instance")
            except ImportError:
                # Fallback to creating a new instance if app module not available
                from src.core.data.product_database import ProductDatabase
                import os
                current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                db_path = os.path.join(current_dir, 'uploads', 'product_database.db')
                product_db = ProductDatabase(db_path)
                product_db.init_database()
                logger.info(f"Created new product database instance at: {db_path}")
            
            logger.info(f"Starting database storage for Excel upload: {len(df)} rows from {source_file}")
            
            if df is None or df.empty:
                logger.warning("No data to store - DataFrame is empty")
                return {'stored': 0, 'updated': 0, 'errors': 0, 'message': 'No data to store'}
            
            # Filter out JSON matched tags
            # JSON matched tags typically have 'Source': 'JSON Match' or similar indicators
            filtered_df = df.copy()
            
            # Remove rows that are JSON matched tags
            json_match_indicators = [
                'Source', 'ai_match_score', 'ai_confidence', 'ai_match_type',
                'json_match_score', 'json_confidence', 'json_match_type'
            ]
            
            # Check if any of these columns exist and contain JSON match data
            json_match_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            
            for col in json_match_indicators:
                if col in filtered_df.columns:
                    # Check for JSON match indicators in the column
                    if col == 'Source':
                        # Look for 'JSON Match' or similar in Source column
                        json_match_mask |= filtered_df[col].astype(str).str.contains('JSON Match|AI Match|JSON|AI', case=False, na=False)
                    else:
                        # Look for non-null values in other JSON match columns
                        json_match_mask |= filtered_df[col].notna()
            
            # Apply the filter to exclude JSON matched tags
            original_count = len(filtered_df)
            filtered_df = filtered_df[~json_match_mask]
            filtered_count = len(filtered_df)
            excluded_count = original_count - filtered_count
            
            logger.info(f"Filtered out {excluded_count} JSON matched tags, {filtered_count} rows remaining for database storage")
            
            if filtered_count == 0:
                logger.warning("All data was JSON matched tags - nothing to store in database")
                return {
                    'stored': 0, 
                    'updated': 0, 
                    'errors': 0, 
                    'excluded_json_matches': excluded_count,
                    'message': f'All {excluded_count} rows were JSON matched tags - excluded from database storage'
                }
            
            # Use the product database's store_excel_data method
            storage_result = product_db.store_excel_data(filtered_df, source_file)
            
            # Add JSON match exclusion information to the result
            storage_result['excluded_json_matches'] = excluded_count
            storage_result['original_count'] = original_count
            storage_result['filtered_count'] = filtered_count
            
            logger.info(f"Database storage completed: {storage_result['message']}")
            logger.info(f"Excluded {excluded_count} JSON matched tags from database storage")
            
            return storage_result
            
        except Exception as e:
            logger.error(f"Error storing Excel upload in database: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'stored': 0, 
                'updated': 0, 
                'errors': 1, 
                'excluded_json_matches': 0,
                'message': f'Database storage failed: {str(e)}'
            }

    def _process_database_records(self, db_records: List[Dict[str, Any]], template_type: str) -> List[Dict[str, Any]]:
        """Process database records into the format expected by template processor."""
        try:
            processed_records = []
            
            for record in db_records:
                try:
                    # Extract basic information
                    product_name = record.get('ProductName', '') or record.get('Product Name*', '')
                    
                    # Clean the product name to remove subtext and parenthetical information
                    original_product_name = product_name
                    cleaned_product_name = self.clean_product_name(product_name)
                    if cleaned_product_name != original_product_name:
                        logger.info(f"🧹 Cleaned database product name: '{original_product_name}' → '{cleaned_product_name}'")
                        product_name = cleaned_product_name
                    
                    description = record.get('Description', '') or product_name
                    
                    # Also clean the description if it contains uncleaned text
                    if description and description != product_name:
                        original_description = description
                        cleaned_description = self.clean_product_name(description)
                        if cleaned_description != original_description:
                            logger.info(f"🧹 Cleaned database description: '{original_description}' → '{cleaned_description}'")
                            description = cleaned_description
                    
                    # Create DescAndWeight with "Product Name - Weight" format
                    full_product_name = record.get('Product Name*', '') or record.get('ProductName', '')
                    weight_units = record.get('Units', '') or record.get('Weight*', '')
                    product_type = record.get('Product Type*', '').strip().lower()
                    desc_and_weight = self._create_desc_and_weight(full_product_name, weight_units, product_type) if full_product_name else description
                    
                    # Define classic types
                    classic_types = [
                        "flower", "pre-roll", "infused pre-roll", "concentrate", 
                        "solventless concentrate", "vape cartridge", "rso/co2 tankers"
                    ]
                    
                    # If product type is empty, treat as classic type (flower)
                    if not product_type:
                        product_type = "flower"
                    
                    # For classic types, use Ratio_or_THC_CBD (THC/CBD values)
                    if product_type in classic_types:
                        ratio_text = str(record.get('Ratio_or_THC_CBD', '')).strip()
                        # Check if we have a valid ratio, otherwise use default
                        if not ratio_text or ratio_text in ["", "CBD", "THC", "CBD:", "THC:", "CBD:\n", "THC:\n"]:
                            ratio_text = "THC: | BR | CBD:"
                        # If ratio contains THC/CBD values, use it directly
                        elif any(cannabinoid in ratio_text.upper() for cannabinoid in ['THC', 'CBD', 'CBC', 'CBG', 'CBN']):
                            ratio_text = ratio_text  # Keep as is
                        # If it's a valid ratio format, use it
                        elif is_real_ratio(ratio_text):
                            ratio_text = ratio_text  # Keep as is
                        # Otherwise, use default THC:CBD format
                        else:
                            ratio_text = "THC: | BR | CBD:"
                    
                    # For non-classic types, use Ratio column value
                    else:
                        ratio_text = str(record.get('Ratio', '')).strip()
                        # Keep the original ratio value from database for non-classic types
                        if not ratio_text or ratio_text in ["", "nan", "NaN"]:
                            ratio_text = ""  # Empty for non-classic types without ratio
                        # Otherwise, keep the ratio value as-is
                    
                    # Ensure we have a valid ratio text
                    if not ratio_text:
                        if product_type in classic_types:
                            ratio_text = "THC: | BR | CBD:"
                        else:
                            ratio_text = ""
                    
                    product_name = make_nonbreaking_hyphens(product_name)
                    description = make_nonbreaking_hyphens(description)
                    
                    # Get DOH value without normalization
                    doh_value = str(record.get('DOH', '')).strip().upper()
                    logger.debug(f"Processing DOH value: {doh_value}")
                    
                    # Get original values
                    product_brand = record.get('Product Brand', '').upper()
                    
                    # If no brand name, try to extract from product name or use vendor
                    if not product_brand or product_brand.strip() == '':
                        if product_name:
                            # Look for common brand patterns in product name
                            import re
                            # Pattern: product name followed by brand name (e.g., "White Widow CBG Platinum Distillate")
                            brand_patterns = [
                                r'(.+?)\s+(Platinum|Premium|Gold|Silver|Elite|Select|Reserve|Craft|Artisan|Boutique|Signature|Limited|Exclusive|Private|Custom|Special|Deluxe|Ultra|Super|Mega|Max|Pro|Plus|X)\s+(Distillate|Extract|Concentrate|Oil|Tincture|Gel|Capsule|Edible|Gummy|Chocolate|Beverage|Topical|Cream|Lotion|Salve|Balm|Spray|Drops|Syrup|Sauce|Dab|Wax|Shatter|Live|Rosin|Resin|Kief|Hash|Bubble|Ice|Water|Solventless|Full\s+Spectrum|Broad\s+Spectrum|Isolate|Terpene|Terpenes|Terp|Terps)',
                                r'(.+?)\s+(Distillate|Extract|Concentrate|Oil|Tincture|Gel|Capsule|Edible|Gummy|Chocolate|Beverage|Topical|Cream|Lotion|Salve|Balm|Spray|Drops|Syrup|Sauce|Dab|Wax|Shatter|Live|Rosin|Resin|Kief|Hash|Bubble|Ice|Water|Solventless|Full\s+Spectrum|Broad\s+Spectrum|Isolate|Terpene|Terpenes|Terp|Terps)',
                                r'(.+?)\s+(Platinum|Premium|Gold|Silver|Elite|Select|Reserve|Craft|Artisan|Boutique|Signature|Limited|Exclusive|Private|Custom|Special|Deluxe|Ultra|Super|Mega|Max|Pro|Plus|X)',
                            ]
                            
                            for pattern in brand_patterns:
                                match = re.search(pattern, product_name, re.IGNORECASE)
                                if match:
                                    # Extract the brand part (everything after the product name)
                                    full_match = match.group(0)
                                    product_part = match.group(1).strip()
                                    brand_part = full_match[len(product_part):].strip()
                                    if brand_part:
                                        product_brand = brand_part.upper()
                                        break
                        
                        # If still no brand, try vendor as fallback
                        if not product_brand or product_brand.strip() == '':
                            vendor = record.get('Vendor', '') or record.get('Vendor/Supplier*', '')
                            if vendor and vendor.strip() != '':
                                product_brand = vendor.strip().upper()
                    
                    original_lineage = str(record.get('Lineage', '')).upper()
                    original_product_strain = record.get('ProductStrain', '') or record.get('strain_name', '')
                    
                    # Extract strain from product name if Product Strain contains the full product name
                    extracted_strain = original_product_strain
                    if original_product_strain and 'Moonshot' in original_product_strain:
                        # Extract the strain name (everything before "Moonshot")
                        strain_name = original_product_strain.replace(' Moonshot', '').strip()
                        if strain_name:
                            extracted_strain = strain_name
                            logger.debug(f"Extracted strain '{extracted_strain}' from '{original_product_strain}'")
                    elif original_product_strain and product_name:
                        # Check if Product Strain contains the full product name (common with brand names)
                        if original_product_strain in product_name and len(original_product_strain) > len(product_name.split()[0]):
                            # Extract just the first word as the strain (e.g., "Grape" from "Grape Moonshot")
                            extracted_strain = product_name.split()[0]
                            logger.debug(f"Extracted strain '{extracted_strain}' from '{original_product_strain}' for product '{product_name}'")
                    
                    # For RSO/CO2 Tankers and Capsules, use Product Brand in place of Lineage
                    if product_type in ["rso/co2 tankers", "capsule"]:
                        final_lineage = product_brand if product_brand else original_lineage
                        final_product_strain = extracted_strain  # Use extracted strain
                    else:
                        # For other product types, use the actual Lineage value
                        final_lineage = original_lineage
                        final_product_strain = extracted_strain  # Use extracted strain
                    
                    # Extract THC/CBD values from database columns
                    total_thc_value = str(record.get('Total THC', '')).strip()
                    thc_content_value = str(record.get('THCA', '')).strip()
                    thc_test_result = str(record.get('THCA', '')).strip()  # Use THC Content
                    
                    # Clean up THC test result value
                    if thc_test_result in ['nan', 'NaN', '']:
                        thc_test_result = ''
                    
                    # Convert to float for comparison, handling empty/invalid values
                    def safe_float(value):
                        if not value or value in ['nan', 'NaN', '']:
                            return 0.0
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return 0.0
                    
                    # Compare Total THC vs THC test result, use highest
                    total_thc_float = safe_float(total_thc_value)
                    thc_test_float = safe_float(thc_test_result)
                    thc_content_float = safe_float(thc_content_value)
                    
                    # For THC: Use the highest value among Total THC, THC test result, and THCA
                    if total_thc_float > 0:
                        if thc_test_float > total_thc_float:
                            ai_value = thc_test_result
                            logger.debug(f"Using THC test result ({thc_test_result}) over Total THC ({total_thc_value}) for product: {product_name}")
                        else:
                            ai_value = total_thc_value
                    else:
                        # Total THC is 0 or empty, compare THCA vs THC test result
                        if thc_content_float > 0 and thc_content_float >= thc_test_float:
                            ai_value = thc_content_value
                        elif thc_test_float > 0:
                            ai_value = thc_test_result
                        else:
                            ai_value = ''
                    
                    # For CBD: merge Total CBD with CBD test result, use highest value
                    total_cbd_value = str(record.get('Total CBD', '')).strip()  # Use Total CBD
                    cbd_test_result_value = str(record.get('CBDA', '')).strip()  # Use CBDA as content
                    cbd_content_value = str(record.get('CBDA', '')).strip()  # Use CBDA as content
                    
                    # Clean up CBD values
                    if cbd_test_result_value in ['nan', 'NaN', '']:
                        cbd_test_result_value = ''
                    if cbd_content_value in ['nan', 'NaN', '']:
                        cbd_content_value = ''
                    
                    # Compare Total CBD vs CBD test result vs CBD Content, use highest
                    total_cbd_float = safe_float(total_cbd_value)
                    cbd_test_result_float = safe_float(cbd_test_result_value)
                    cbd_content_float = safe_float(cbd_content_value)
                    
                    # Use the highest CBD value from all sources
                    if cbd_test_result_float > 0 and cbd_test_result_float >= total_cbd_float and cbd_test_result_float >= cbd_content_float:
                        ak_value = cbd_test_result_value
                        logger.debug(f"Using CBD test result ({cbd_test_result_value}) for product: {product_name}")
                    elif cbd_content_float > total_cbd_float:
                        ak_value = cbd_content_value
                        logger.debug(f"Using CBD Content ({cbd_content_value}) over Total CBD ({total_cbd_value}) for product: {product_name}")
                    else:
                        ak_value = total_cbd_value
                    
                    # Clean up the values (remove 'nan', empty strings, etc.)
                    if ai_value in ['nan', 'NaN', '']:
                        ai_value = ''
                    if ak_value in ['nan', 'NaN', '']:
                        ak_value = ''
                    
                    # Get vendor information
                    vendor = record.get('Vendor', '') or record.get('Vendor/Supplier*', '')
                    if vendor and str(vendor).lower() == 'nan':
                        vendor = ''
                    
                    # Build the processed record with raw values (no markers)
                    processed = {
                        'ProductName': product_name,  # Keep this for compatibility
                        'Product Name*': product_name,  # Also store with original column name
                        'Description': description,
                        'DescAndWeight': desc_and_weight,  # Use extracted product name for DescAndWeight field
                        'WeightUnits': record.get('JointRatio', '') if product_type in {"pre-roll", "infused pre-roll"} else self._format_weight_units(record, excel_priority=True),
                        'ProductBrand': product_brand,
                        'Price': str(record.get('Price*', '')).strip() or str(record.get('Price', '')).strip(),  # Use correct price column
                        'Lineage': str(final_lineage) if str(final_lineage) else "",
                        'DOH': doh_value,  # Keep DOH as raw value
                        'Ratio_or_THC_CBD': ratio_text,  # Use the processed ratio_text for all product types
                        'ProductStrain': self.wrap_with_marker(final_product_strain, "PRODUCTSTRAIN") if final_product_strain else '',
                        'ProductType': record.get('Product Type*', ''),
                        'Ratio': str(record.get('Ratio_or_THC_CBD', '')).strip(),
                        'THC': wrap_with_marker(ai_value, "THC"),  # AI column for THC
                        'CBD': wrap_with_marker(ak_value, "CBD"),  # AK column for CBD
                        'THC_CBD': self._construct_thc_cbd_field(ai_value, ak_value, product_type),  # Construct combined THC_CBD field
                        'AI': ai_value,  # Total THC or THCA value for THC
                        'AJ': str(record.get('THCA', '')).strip(),  # THC Content value for alternative THC
                        'AK': ak_value,  # Total CBD value for CBD
                        'Vendor': vendor,  # Add vendor information
                    }
                    
                    # Ensure leading space before hyphen is a non-breaking space to prevent Word from stripping it
                    joint_ratio = record.get('JointRatio', '')
                    # Handle NaN values properly
                    if joint_ratio and str(joint_ratio).lower() in ['nan', 'nan']:
                        joint_ratio = ''
                    elif joint_ratio and str(joint_ratio).startswith(' -'):
                        joint_ratio = ' -\u00A0' + str(joint_ratio)[2:]
                    processed['JointRatio'] = joint_ratio
                    
                    logger.info(f"Rendered label for database record: {product_name if product_name else '[NO NAME]'}")
                    logger.debug(f"Processed database record DOH value: {processed['DOH']}")
                    logger.debug(f"Product Type: {product_type}, Classic: {product_type in classic_types}")
                    logger.debug(f"Original Lineage: {original_lineage}, Final Lineage: {final_lineage}")
                    logger.debug(f"Original Product Strain: {original_product_strain}, Final Product Strain: {final_product_strain}")
                    
                    processed_records.append(processed)
                except Exception as e:
                    logger.error(f"Error processing database record {product_name}: {str(e)}")
                    continue
            
            # Debug log the final processed records
            logger.debug(f"Processed {len(processed_records)} database records")
            for record in processed_records:
                logger.debug(f"Processed database record: {record.get('ProductName', 'NO NAME')}")
                logger.debug(f"Record DOH value: {record.get('DOH', 'NO DOH')}")
            
            return processed_records
            
        except Exception as e:
            logger.error(f"Error in _process_database_records: {str(e)}")
            return []

    def make_nonbreaking_hyphens(self, text: str) -> str:
        """Replace regular hyphens with non-breaking hyphens to prevent Word from stripping them."""
        if not text:
            return text
        return str(text).replace('-', '-\u00A0')
    
    def wrap_with_marker(self, text: str, marker: str) -> str:
        """Wrap text with marker tags for template processing."""
        if not text or str(text).strip() == '':
            return ''
        return f"{marker}_START{text}{marker}_END"

    def _extract_product_name_from_full_name(self, full_name):
        """Extract just the product name from 'Product Name by Vendor - Weight' format."""
        if not full_name or str(full_name).strip() == '':
            return ''
        
        name = str(full_name).strip()
        if not name:
            return ''
        
        # Handle "Product Name by Vendor - Weight" format
        if ' by ' in name and ' - ' in name:
            # Extract just the product name part before " by "
            return name.split(' by ')[0].strip()
        elif ' by ' in name:
            return name.split(' by ')[0].strip()
        elif ' - ' in name:
            # Only split on dashes followed by weight information (numbers, decimals, units)
            import re
            if re.search(r' - [\d.]', name):
                # Remove weight part but preserve the dash in product names
                return re.sub(r' - [\d.].*$', '', name).strip()
            else:
                # No weight information, return the name as-is
                return name.strip()
        return name.strip()

    def _create_desc_and_weight(self, full_name, weight_units, product_type=None):
        """Create DescAndWeight field with 'Product Name - Weight' format using soft hyphen."""
        # Extract just the product name from the full name
        product_name = self._extract_product_name_from_full_name(full_name)
        
        # Get weight units, clean them up
        weight = str(weight_units).strip() if weight_units else ''
        if weight and weight.lower() not in ['nan', 'none', 'null', '']:
            # Combine product name and weight with hyphen staying with weight (space after hyphen)
            return f"{product_name} -\u00A0{weight}"
        else:
            # Just return the product name if no weight
            return product_name

    def clean_product_name(self, name: str) -> str:
        """Remove subtext and parenthetical information from product names."""
        if not name:
            return name
        
        import re
        
        # Remove parentheses but preserve their content
        cleaned = re.sub(r'\(([^)]*)\)', r'\1', name)  # Replace (text) with text
        cleaned = re.sub(r'\[([^\]]*)\]', r'\1', cleaned)  # Replace [text] with text
        
        # Remove "by Dabstract JSON" specifically
        cleaned = re.sub(r'\s*by\s+Dabstract\s+JSON\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Remove other "by vendor" patterns
        cleaned = re.sub(r'\s*by\s+[^-]*\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Remove trailing dash patterns
        cleaned = re.sub(r'\s*-\s*[^-]*\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned

    def get_available_tag_names(self) -> List[str]:
        """Get available tag names as simple strings (for tag selection)."""
        try:
            available_tags = self.get_available_tags()
            # Extract just the product names from the tag dictionaries
            tag_names = []
            for tag in available_tags:
                if isinstance(tag, dict):
                    # Get the product name from the dictionary
                    product_name = tag.get('Product Name*') or tag.get('displayName') or tag.get('ProductName', '')
                    if product_name and product_name.strip():
                        tag_names.append(str(product_name).strip())
                elif isinstance(tag, str):
                    # If it's already a string, use it directly
                    tag_names.append(tag.strip())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_names = []
            for name in tag_names:
                if name not in seen:
                    seen.add(name)
                    unique_names.append(name)
            
            logger.info(f"get_available_tag_names: Returning {len(unique_names)} unique tag names")
            return unique_names
            
        except Exception as e:
            logger.error(f"Error in get_available_tag_names: {e}")
            return []

    def get_available_tags(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return a list of tag objects with all necessary data."""
        if self.df is None:
            logger.warning("DataFrame is None in get_available_tags, attempting to use database")
            try:
                from src.core.data.product_database import ProductDatabase
                # Use default store name if not available
                store_name = getattr(self, 'store_name', 'AGT_Bothell')
                db = ProductDatabase(store_name)
                products = db.get_all_products()
                
                logger.info(f"Retrieved {len(products)} products from database")
                
                # Convert database products to tag format
                tags = []
                for product in products:
                    # Create combined weight from Weight* and Units if available
                    weight_value = product.get('Weight*', '')
                    units_value = product.get('Units', '')
                    combined_weight = ''
                    
                    if weight_value and units_value and str(units_value) != 'None' and str(units_value) != '':
                        try:
                            if float(weight_value) == int(float(weight_value)):
                                combined_weight = f"{int(float(weight_value))}{units_value}"
                            else:
                                combined_weight = f"{weight_value}{units_value}"
                        except (ValueError, TypeError):
                            combined_weight = f"{weight_value}{units_value}"
                    elif weight_value:
                        combined_weight = str(weight_value)
                    
                    tag = {
                        'Product Name*': product.get('Product Name*', ''),
                        'Product Type*': product.get('Product Type*', ''),
                        'Vendor/Supplier*': product.get('Vendor/Supplier*', ''),
                        'Product Brand': product.get('Product Brand', ''),
                        'Weight*': product.get('Weight*', ''),
                        'Units': product.get('Units', ''),  # Add Units field
                        'CombinedWeight': combined_weight,  # Create combined weight
                        'Price*': product.get('Price*', '') or product.get('Price* (Tier Name for Bulk)', ''),
                        'Lineage': product.get('Lineage', ''),
                        'Product Strain': product.get('Product Strain', ''),
                        'DOH': product.get('DOH', ''),
                        'DOH Compliant (Yes/No)': product.get('DOH Compliant (Yes/No)', ''),
                        'Ratio': product.get('Ratio', ''),
                        'THC test result': product.get('THC test result', ''),
                        'CBD test result': product.get('CBD test result', ''),
                        'Source': 'Database'
                    }
                    tags.append(tag)
                
                logger.info(f"Converted {len(tags)} database products to tags")
                
                # Apply filters if provided
                if filters:
                    filtered_tags = []
                    for tag in tags:
                        # Apply same filtering logic as Excel processor
                        if filters.get('productType'):
                            tag_product_type = str(tag.get('Product Type*', '')).strip().lower()
                            filter_product_type = str(filters['productType']).strip().lower()
                            if tag_product_type != filter_product_type:
                                continue
                        
                        if filters.get('vendor'):
                            tag_vendor = str(tag.get('Vendor/Supplier*', '')).strip().lower()
                            filter_vendor = str(filters['vendor']).strip().lower()
                            if tag_vendor != filter_vendor:
                                continue
                        
                        if filters.get('brand'):
                            tag_brand = str(tag.get('Product Brand', '')).strip().lower()
                            filter_brand = str(filters['brand']).strip().lower()
                            if tag_brand != filter_brand:
                                continue
                        
                        filtered_tags.append(tag)
                    
                    logger.info(f"Applied filters, returning {len(filtered_tags)} tags")
                    return filtered_tags
                
                return tags
                
            except Exception as e:
                logger.error(f"Failed to get products from database: {e}")
                return []
        
        filtered_df = self.apply_filters(filters) if filters else self.df
        logger.info(f"get_available_tags: DataFrame shape {self.df.shape}, filtered shape {filtered_df.shape}")
        
        tags = []
        seen_product_names = set()  # Track seen product names to prevent duplicates
        
        for _, row in filtered_df.iterrows():
            # Get quantity from various possible column names
            quantity = row.get('Quantity*', '') or row.get('Quantity Received*', '') or row.get('Quantity', '') or row.get('qty', '') or ''
            
            # Get formatted weight with units
            weight_with_units = self._format_weight_units(row, excel_priority=True)
            raw_weight = row.get('Weight*', '')
            
            # Helper function to safely get values and handle NaN
            def safe_get_value(value, default=''):
                if value is None:
                    return default
                if isinstance(value, pd.Series):
                    if pd.isna(value).any():
                        return default
                    value = value.iloc[0] if len(value) > 0 else default
                elif pd.isna(value):
                    return default
                return str(value).strip()
            
            # Use the dynamically detected product name column
            product_name_col = 'Product Name*'
            if product_name_col not in self.df.columns:
                possible_cols = ['ProductName', 'Product Name', 'Description']
                product_name_col = next((col for col in possible_cols if col in self.df.columns), None)
                if not product_name_col:
                    product_name_col = 'Description'  # Fallback to Description
            
            # Get the product name
            product_name = safe_get_value(row.get(product_name_col, '')) or safe_get_value(row.get('Description', '')) or 'Unnamed Product'
            
            # CRITICAL FIX: Allow JSON matched products to have duplicates
            # Check if this is a JSON matched product
            is_json_matched = row.get('Source', '') == 'JSON Match'
            
            # Skip if we've already seen this product name (deduplication) - but allow JSON matched products
            if product_name in seen_product_names and not is_json_matched:
                logger.debug(f"Skipping duplicate product: {product_name}")
                continue
            
            # Add to seen set (only for non-JSON matched products to allow JSON duplicates)
            if not is_json_matched:
                seen_product_names.add(product_name)
            
            # Get vendor from multiple possible column names
            vendor_value = (
                safe_get_value(row.get('Vendor/Supplier*', '')) or  # Primary column name
                safe_get_value(row.get('Vendor', '')) or           # Alternative column name
                safe_get_value(row.get('Vendor/Supplier', ''))     # Fallback column name
            )
            
            # Debug logging for vendor field detection
            if not vendor_value and product_name:
                logger.debug(f"Vendor field is empty for product '{product_name}'. Available vendor columns: {[col for col in row.index if 'vendor' in col.lower() or 'supplier' in col.lower()]}")
                logger.debug(f"Row vendor values: Vendor/Supplier*='{row.get('Vendor/Supplier*', '')}', Vendor='{row.get('Vendor', '')}', Vendor/Supplier='{row.get('Vendor/Supplier', '')}'")
            
            # Get description for DescAndWeight field
            # DescAndWeight should contain just the description text (mapped to DESC marker in template)
            description = safe_get_value(row.get('Description', ''))
            product_name_for_desc = safe_get_value(row.get(product_name_col, ''))
            
            # Use Description if available, otherwise use Product Name
            desc_and_weight = description if description else product_name_for_desc
            
            # Extract THC/CBD values from the appropriate columns
            # Use the actual column names from the Excel file
            total_thc_value = safe_get_value(row.get('Total THC', ''))
            thc_content_value = safe_get_value(row.get('THC Content', ''))  # Use THC Content
            thc_test_result = safe_get_value(row.get('THC Content', ''))  # Use THC Content
            total_cbd_value = safe_get_value(row.get('Total CBD', ''))  # Use Total CBD
            cbd_content_value = safe_get_value(row.get('CBD Content', ''))  # Use CBD Content
            
            # Helper function to safely convert to float for comparison
            def safe_float(value):
                if not value or value in ['nan', 'NaN', '']:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # For THC: Use the highest value among Total THC, THC test result, and THCA
            total_thc_float = safe_float(total_thc_value)
            thc_test_float = safe_float(thc_test_result)
            thc_content_float = safe_float(thc_content_value)
            
            if total_thc_float > 0:
                if thc_test_float > total_thc_float:
                    ai_value = thc_test_result
                else:
                    ai_value = total_thc_value
            else:
                # Total THC is 0 or empty, compare THCA vs THC test result
                if thc_content_float > 0 and thc_content_float >= thc_test_float:
                    ai_value = thc_content_value
                elif thc_test_float > 0:
                    ai_value = thc_test_result
                else:
                    ai_value = ''
            
            # For CBD: merge CBDA with CBD test result, use highest value
            total_cbd_float = safe_float(total_cbd_value)
            cbd_content_float = safe_float(cbd_content_value)
            
            if cbd_content_float > total_cbd_float:
                ak_value = cbd_content_value
            else:
                ak_value = total_cbd_value
            
            # Clean up the values (remove 'nan', empty strings, etc.)
            if ai_value in ['nan', 'NaN', '']:
                ai_value = ''
            if ak_value in ['nan', 'NaN', '']:
                ak_value = ''
            
            # Get price value - use the actual column name from Excel file
            price_value = safe_get_value(row.get('Price*', '')) or safe_get_value(row.get('Price', '')) or safe_get_value(row.get('Price* (Tier Name for Bulk)', ''))
            
            tag = {
                'Product Name*': product_name,
                'Description': safe_get_value(row.get('Description', '')),  # Add Description field
                'DescAndWeight': desc_and_weight,  # Add DescAndWeight field
                'Vendor': vendor_value,
                'Vendor/Supplier*': vendor_value,
                'Product Brand': safe_get_value(row.get('Product Brand', '')),
                'ProductBrand': safe_get_value(row.get('Product Brand', '')),
                'Lineage': safe_get_value(row.get('Lineage', 'MIXED')),
                'Product Type*': safe_get_value(row.get('Product Type*', '')),
                'Product Type': safe_get_value(row.get('Product Type*', '')),
                'Weight*': safe_get_value(raw_weight),
                'Weight': safe_get_value(raw_weight),
                'WeightWithUnits': safe_get_value(weight_with_units),
                'WeightUnits': safe_get_value(weight_with_units),  # Add WeightUnits for frontend compatibility
                'CombinedWeight': safe_get_value(weight_with_units),  # Add CombinedWeight field for consistency with database products
                'weightWithUnits': safe_get_value(weight_with_units),  # Add lowercase version for frontend compatibility
                'Units': safe_get_value(row.get('Units', '')),  # Add Units field for consistency
                'Quantity*': safe_get_value(quantity),
                'Quantity Received*': safe_get_value(quantity),
                'quantity': safe_get_value(quantity),
                'DOH': safe_get_value(row.get('DOH', '')),  # Add DOH field for UI display
                'Price': price_value,  # Add Price field
                'THC': ai_value,  # Add THC value
                'CBD': ak_value,  # Add CBD value
                'AI': ai_value,  # Add AI field for THC
                'AJ': thc_content_value,  # Add AJ field for THC Content
                'AK': ak_value,  # Add AK field for CBD
                'Total THC': total_thc_value,  # Add Total THC field
                'THCA': thc_content_value,  # Add THC Content field
                'CBDA': total_cbd_value,  # Add Total CBD field
                'THC test result': thc_test_result,  # Add THC test result field
                'CBD test result': cbd_content_value,  # Add CBD Content field
                # Also include the lowercase versions for backward compatibility
                'vendor': vendor_value,
                'productBrand': safe_get_value(row.get('Product Brand', '')),
                'lineage': safe_get_value(row.get('Lineage', 'MIXED')),
                'productType': safe_get_value(row.get('Product Type*', '')),
                'weight': safe_get_value(raw_weight),
                'weightWithUnits': safe_get_value(weight_with_units),
                'displayName': product_name
            }
            # --- Filtering logic ---
            product_brand = str(tag['productBrand']).strip().lower()
            product_type = str(tag['productType']).strip().lower().replace('  ', ' ')
            weight = str(tag['weight']).strip().lower()

            # Sanitize lineage - prioritize existing lineage, fall back to inference from name  
            existing_lineage = str(row.get('Lineage', '') or '').strip().upper()
            if existing_lineage and existing_lineage in VALID_LINEAGES:
                lineage = existing_lineage
            else:
                # No valid lineage column - infer from product name and type
                product_type_for_inference = safe_get_value(row.get('Product Type*', ''))
                lineage = self._infer_lineage_from_name(product_name, product_type_for_inference)
            
            tag['Lineage'] = lineage
            tag['lineage'] = lineage

            # Filter out samples and invalid products
            product_name_lower = product_name.lower()
            product_type_lower = product_type.lower()
            if (
                weight == '-1g' or  # Invalid weight
                'trade sample' in product_type_lower or  # Filter any trade sample product types
                'sample' in product_name_lower or  # Filter products with "Sample" in name
                'trade sample' in product_name_lower or  # Filter products with "Trade Sample" in name
                any(pattern.lower() in product_name_lower for pattern in EXCLUDED_PRODUCT_PATTERNS) or  # Filter based on excluded patterns
                any(pattern.lower() in product_type_lower for pattern in EXCLUDED_PRODUCT_PATTERNS)  # Filter product types based on excluded patterns
            ):
                continue  # Skip this tag
            tags.append(tag)
        
        # Sort tags by vendor first, then by brand, then by weight
        def sort_key(tag):
            vendor = str(tag.get('vendor', '')).strip().lower()
            brand = str(tag.get('productBrand', '')).strip().lower()
            weight = ExcelProcessor.parse_weight_str(tag.get('weight', ''), tag.get('weightWithUnits', ''))
            return (vendor, brand, weight)
        
        sorted_tags = sorted(tags, key=sort_key)
        logger.info(f"get_available_tags: Returning {len(sorted_tags)} tags (removed {len(filtered_df) - len(sorted_tags)} duplicates)")
        return sorted_tags



    def ultra_fast_load(self, file_path: str) -> bool:
        """Ultra-fast loading with minimal processing for maximum speed"""
        try:
            self.logger.info(f"[ULTRA-FAST] Loading file: {file_path}")
            
            # Clear previous data efficiently
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                import gc
                gc.collect()
            
            # Read with minimal settings for maximum speed
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                nrows=50000,  # High row limit
                dtype=str,   # Read as strings for speed
                na_filter=False,  # Don't filter NA values
                keep_default_na=False  # Don't use default NA values
            )
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            self.logger.info(f"[ULTRA-FAST] Successfully read {len(df)} rows, {len(df.columns)} columns")
            
            # Handle duplicate columns efficiently
            df = self._handle_duplicate_columns_fast(df)
            
            # Remove duplicates efficiently
            initial_count = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            final_count = len(df)
            
            if initial_count != final_count:
                self.logger.info(f"[ULTRA-FAST] Removed {initial_count - final_count} duplicate rows")
            
            # Apply ultra-minimal processing
            df = self._ultra_minimal_processing(df)
            
            self.df = df
            self.logger.info(f"[ULTRA-FAST] Processing complete: {len(df)} rows")
            return True
            
        except Exception as e:
            self.logger.error(f"[ULTRA-FAST] Error loading file: {e}")
            return False

    def _handle_duplicate_columns_fast(self, df):
        """Handle duplicate columns efficiently"""
        if df.columns.duplicated().any():
            # Rename duplicate columns
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                cols[cols[cols == dup].index.values.tolist()] = [dup if i == 0 else f"{dup}_{i}" for i in range(sum(cols == dup))]
            df.columns = cols
        return df

    def _ultra_minimal_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ultra-minimal processing for maximum speed"""
        try:
            if len(df) == 0:
                return df
            
            # Only essential processing
            essential_columns = ['Product Name*', 'Product Type*', 'Lineage', 'Product Brand']
            
            # Ensure required columns exist
            for col in essential_columns:
                if col not in df.columns:
                    df[col] = "Unknown"
            
            # Basic string cleaning for key columns only
            for col in essential_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Remove excluded product types (minimal check)
            if 'Product Type*' in df.columns:
                excluded_types = ["Samples - Educational", "Sample - Vendor", "x-DEACTIVATED 1", "x-DEACTIVATED 2"]
                df = df[~df['Product Type*'].isin(excluded_types)]
                df.reset_index(drop=True, inplace=True)
            
            self.logger.info(f"[ULTRA-FAST] Ultra-minimal processing completed: {len(df)} rows remaining")
            return df
            
        except Exception as e:
            self.logger.error(f"[ULTRA-FAST] Error in ultra-minimal processing: {e}")
            return df

    def streaming_load(self, file_path: str, chunk_size: int = 10000) -> bool:
        """Load large files in streaming chunks for better memory usage"""
        try:
            self.logger.info(f"[STREAMING] Loading file in chunks: {file_path}")
            
            # Clear previous data
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                import gc
                gc.collect()
            
            # Read file in chunks
            chunks = []
            total_rows = 0
            
            # First, try to read the full file with high row limit
            df = pd.read_excel(
                file_path,
                engine='openpyxl',
                nrows=50000,  # High limit
                dtype=str,  # Read as strings for speed
                na_filter=False,
                keep_default_na=False
            )
            
            if df is None or df.empty:
                self.logger.error("No data found in Excel file")
                return False
            
            # Handle duplicate columns efficiently
            df = self._handle_duplicate_columns_fast(df)
            
            # Remove duplicates efficiently
            initial_count = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            final_count = len(df)
            
            if initial_count != final_count:
                self.logger.info(f"[STREAMING] Removed {initial_count - final_count} duplicate rows")
            
            # Apply minimal processing
            df = self._ultra_minimal_processing(df)
            
            self.df = df
            self.logger.info(f"[STREAMING] Streaming load completed: {len(df)} rows")
            return True
            
        except Exception as e:
            self.logger.error(f"[STREAMING] Error in streaming load: {e}")
            return False
    
    def _process_description_from_product_name(self, product_name: str) -> str:
        """Process description using the Excel processor formula."""
        if not product_name:
            return ''
        
        # Clean up the product name first
        description = str(product_name).strip()
        
        # Apply Excel processor formula: Remove " by " patterns
        if " by " in description:
            description = description.split(" by ")[0].strip()
        
        # Apply Excel processor formula: Remove weight information (patterns like " - 1g", " - .5g")
        import re
        description = re.sub(r' - [\d.].*$', '', description)
        
        return description

    def _process_descriptions_from_product_names(self):
        """Process Description values using our established formula from Product Name."""
        try:
            if self.df is None or self.df.empty:
                return
            
            # Find the product name column
            product_name_col = "ProductName"
            if product_name_col not in self.df.columns:
                possible_cols = ["Product Name*", "Product Name", "Description"]
                product_name_col = next((col for col in possible_cols if col in self.df.columns), None)
                if not product_name_col:
                    self.logger.warning("No product name column found for Description processing")
                    return
            
            # Ensure we have a Description column
            if "Description" not in self.df.columns:
                self.df["Description"] = ""
            
            # Replace ALL Description values with processed Product Name
            self.df["Description"] = self.df[product_name_col].astype(str).str.strip()
            self.logger.debug(f"Replaced all Description values with processed Product Name from {product_name_col}")
            
            # Handle " by " pattern for all Description values
            mask_by = self.df["Description"].str.contains(" by ", na=False)
            if mask_by.any():
                self.df.loc[mask_by, "Description"] = self.df.loc[mask_by, "Description"].str.split(" by ").str[0].str.strip()
                self.logger.debug(f"Processed ' by ' pattern in {mask_by.sum()} Description values")
            
            # Handle weight removal from Description - only remove weight parts, preserve product names with hyphens
            mask_weight_dash = self.df["Description"].str.contains(r" - [\d.]", na=False)
            if mask_weight_dash.any():
                # Remove weight part but preserve the dash in product names like "Pre-Roll"
                df_temp = self.df.loc[mask_weight_dash, "Description"].copy()
                # Use regex to find the weight part and remove it (handles both " - 1g" and " - .5g")
                df_temp = df_temp.str.replace(r" - [\d.].*$", "", regex=True)
                self.df.loc[mask_weight_dash, "Description"] = df_temp
                self.logger.debug(f"Removed weight information from {mask_weight_dash.sum()} Description values")
            
            self.logger.info(f"Successfully processed Description values using Product Name formula")
            
        except Exception as e:
            self.logger.error(f"Error processing descriptions from product names: {e}")

