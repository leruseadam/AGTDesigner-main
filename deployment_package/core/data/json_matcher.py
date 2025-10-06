import re
import json
import urllib.request
import logging
import time
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Dict, Set, Optional, Tuple, Any
from .field_mapping import get_canonical_field
import pandas as pd
from .product_database import ProductDatabase
from .ai_product_matcher import AIProductMatcher
from .advanced_matcher import AdvancedMatcher, MatchResult
from collections import defaultdict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Compile regex patterns once for performance
_DIGIT_UNIT_RE = re.compile(r"\b\d+(?:g|mg)\b")
_NON_WORD_RE = re.compile(r"[^\w\s-]")
_SPLIT_RE = re.compile(r"[-\s]+")

# Type override lookup
TYPE_OVERRIDES = {
    "all-in-one": "Vape Cartridge",
    "rosin": "Concentrate",
    "mini buds": "Flower",
    "bud": "Flower",
    "pre-roll": "Pre-roll",
    "alcohol/ethanol extract": "RSO/CO2 Tankers",
    "Alcohol/Ethanol Extract": "RSO/CO2 Tankers",
    "alcohol ethanol extract": "RSO/CO2 Tankers",
    "Alcohol Ethanol Extract": "RSO/CO2 Tankers",
    "c02/ethanol extract": "RSO/CO2 Tankers",
    "CO2 Concentrate": "RSO/CO2 Tankers",
    "co2 concentrate": "RSO/CO2 Tankers",
    # Vape cartridge indicators
    "jefe": "Vape Cartridge",
    "twisted": "Vape Cartridge",
    "fire": "Vape Cartridge",
    "cart": "Vape Cartridge",
    "cartridge": "Vape Cartridge",
    "vape": "Vape Cartridge",
    "disposable": "Vape Cartridge",
    "pod": "Vape Cartridge",
    "battery": "Vape Cartridge",
}


# Helper: Extract cannabinoid values from lab_result_data
CANNABINOID_TYPES = ["thc", "thca", "cbd", "cbda", "total-cannabinoids"]

def map_inventory_type_to_product_type(inventory_type, inventory_category=None, product_name=None):
    """
    Intelligently map JSON inventory types to proper product types.
    
    Args:
        inventory_type: The inventory_type from JSON (e.g., "Concentrate for Inhalation")
        inventory_category: The inventory_category from JSON (e.g., "IntermediateProduct")
        product_name: The product name for additional context (optional)
        
    Returns:
        Mapped product type string
    """
    if not inventory_type:
        return "Unknown"
    
    inventory_type_lower = str(inventory_type).lower().strip()
    inventory_category_lower = str(inventory_category).lower().strip() if inventory_category else ""
    product_name_lower = str(product_name).lower().strip() if product_name else ""
    
    # Enhanced mappings for common inventory types based on Cultivera data
    type_mappings = {
        # Concentrates and Vape Cartridges
        "concentrate for inhalation": "Vape Cartridge",
        "concentrate": "Vape Cartridge", 
        "extract": "Vape Cartridge",
        "oil": "Vape Cartridge",
        "distillate": "Vape Cartridge",
        "live resin": "Live Resin",
        "rosin": "Rosin",
        "wax": "Wax",
        "shatter": "Shatter",
        "vape cartridge": "Vape Cartridge",
        "vape pen": "Vape Cartridge",
        "disposable": "Disposable",
        
        # Flower and Pre-rolls
        "flower": "Flower",
        "bud": "Flower",
        "pre-roll": "Pre-Roll",
        "infused pre-roll": "Infused Pre-Roll",
        "preroll": "Pre-Roll",
        "joint": "Pre-Roll",
        
        # Edibles
        "edible": "Edible",
        "solid edible": "Edible",
        "gummy": "Gummy",
        "gummies": "Gummy",
        "chocolate": "Chocolate",
        "brownie": "Brownie",
        "cookie": "Cookie",
        "cookie": "Cookie",
        "candy": "Edible",
        "hard candy": "Edible",
        "soft candy": "Edible",
        
        # Topicals
        "topical": "Topical",
        "topical ointment": "Topical",
        "cream": "Topical",
        "balm": "Topical",
        "salve": "Topical",
        "lotion": "Topical",
        "ointment": "Topical",
        
        # Tinctures and Oils
        "tincture": "Tincture",
        "sublingual": "Tincture",
        "oral": "Tincture",
        "drops": "Tincture",
        
        # Capsules and Pills
        "capsule": "Capsule",
        "pill": "Capsule",
        "tablet": "Capsule",
        "softgel": "Capsule",
        
        # Beverages
        "beverage": "Beverage",
        "drink": "Beverage",
        "soda": "Beverage",
        "juice": "Beverage",
        "tea": "Beverage",
        "coffee": "Beverage",
        
        # Extracts and RSO
        "rso": "RSO",
        "co2": "CO2 Extract",
        "co2 extract": "CO2 Extract",
        "ethanol extract": "RSO",
        "alcohol extract": "RSO",
        "butane extract": "Concentrate",
        "hash": "Hash",
        "kief": "Kief",
        
        # Other categories
        "suppository": "Suppository",
        "transdermal": "Transdermal",
        "patch": "Transdermal",
        "inhaler": "Inhaler",
        "nasal spray": "Nasal Spray",
        "eye drops": "Eye Drops"
    }
    
    # Check direct mapping first
    if inventory_type_lower in type_mappings:
        return type_mappings[inventory_type_lower]
    
    # Check category-based mappings
    if "intermediate" in inventory_category_lower:
        if "concentrate" in inventory_type_lower or "extract" in inventory_type_lower:
            return "Vape Cartridge"
        elif "flower" in inventory_type_lower:
            return "Flower"
    
    # Enhanced product name analysis for "Medically Compliant" products
    if product_name_lower and "medically compliant" in product_name_lower:
        # Look for specific product type indicators in the name
        if any(keyword in product_name_lower for keyword in ["rosin", "wax", "shatter", "live resin", "distillate", "cartridge", "all-in-one", "liquid diamond", "caviar", "hash rosin", "sugar wax"]):
            return "Vape Cartridge"
        elif any(keyword in product_name_lower for keyword in ["flower", "bud", "pre-roll", "pre roll"]):
            return "Flower" if "flower" in product_name_lower else "Pre-Roll"
        elif any(keyword in product_name_lower for keyword in ["edible", "gummy", "chocolate", "cookie"]):
            return "Edible"
        elif any(keyword in product_name_lower for keyword in ["melt stix", "flavour stix", "rosin rolls", "infused blunt"]):
            return "Pre-Roll"
    
    # Check for specific keywords in the inventory type
    if any(keyword in inventory_type_lower for keyword in ["cartridge", "pen", "vape"]):
        return "Vape Cartridge"
    elif any(keyword in inventory_type_lower for keyword in ["flower", "bud", "nug"]):
        return "Flower"
    elif any(keyword in inventory_type_lower for keyword in ["edible", "gummy", "chocolate", "brownie", "cookie"]):
        return "Edible"
    elif any(keyword in inventory_type_lower for keyword in ["tincture", "oil", "drops"]):
        return "Tincture"
    elif any(keyword in inventory_type_lower for keyword in ["topical", "cream", "lotion", "salve"]):
        return "Topical"
    elif any(keyword in inventory_type_lower for keyword in ["pre-roll", "joint", "cigar"]):
        return "Pre-Roll"
    
    # Default fallback based on category
    if "concentrate" in inventory_type_lower or "extract" in inventory_type_lower:
        return "Vape Cartridge"
    elif "flower" in inventory_type_lower:
        return "Flower"
    else:
        # For any remaining unknown types, default to Vape Cartridge since most products are concentrates
        return "Vape Cartridge"

def extract_cannabinoids(lab_result_data):
    """Enhanced cannabinoid extraction with better parsing and validation."""
    result = {}
    if not lab_result_data:
        return result
    
    # Extract potency data
    potency = lab_result_data.get("potency", [])
    if not isinstance(potency, list):
        potency = []
    
    for c in potency:
        if not isinstance(c, dict):
            continue
            
        ctype = c.get("type", "").lower().strip()
        value = c.get("value")
        unit = c.get("unit", "").lower().strip()
        
        if ctype in CANNABINOID_TYPES and value is not None:
            # Convert value to float and validate
            try:
                float_value = float(value)
                # Handle percentage conversion (e.g., 100.000 -> 100.0)
                if unit == "pct" and float_value > 1:
                    # Some labs report percentages as 100.000 instead of 1.000
                    if float_value > 100:
                        float_value = float_value / 100
                elif unit == "mg" and float_value > 1000:
                    # Convert mg to g if needed
                    float_value = float_value / 1000
                
                result[ctype] = round(float_value, 1)  # Round to 1 decimal place
            except (ValueError, TypeError):
                logging.warning(f"Invalid cannabinoid value: {value} for type {ctype}")
                continue
    
    # Extract additional lab data
    if "coa" in lab_result_data:
        result["coa"] = lab_result_data["coa"]
    
    # Extract lab result status
    if "lab_result_status" in lab_result_data:
        result["lab_result_status"] = lab_result_data["lab_result_status"]
    
    # Extract lab result ID
    if "lab_result_id" in lab_result_data:
        result["lab_result_id"] = lab_result_data["lab_result_id"]
    
    # Extract COA dates
    if "coa_release_date" in lab_result_data:
        result["coa_release_date"] = lab_result_data["coa_release_date"]
    if "coa_expire_date" in lab_result_data:
        result["coa_expire_date"] = lab_result_data["coa_expire_date"]
    
    return result

def extract_vendor_info(json_data):
    """Extract vendor information from JSON data, trying multiple possible field names."""
    vendor = (str(json_data.get("vendor", "")).strip() or 
              str(json_data.get("supplier", "")).strip() or
              str(json_data.get("vendor_name", "")).strip() or
              str(json_data.get("supplier_name", "")).strip() or
              str(json_data.get("manufacturer", "")).strip() or
              str(json_data.get("distributor", "")).strip() or
              str(json_data.get("brand", "")).strip() or
              str(json_data.get("company", "")).strip() or
              str(json_data.get("producer", "")).strip() or
              str(json_data.get("grower", "")).strip() or
              str(json_data.get("farm", "")).strip() or
              str(json_data.get("lab", "")).strip() or
              str(json_data.get("laboratory", "")).strip() or "")
    
    # Enhanced vendor normalization with more comprehensive mappings
    if vendor:
        vendor_lower = vendor.lower()
        # Handle common vendor variations and abbreviations
        vendor_mappings = {
            'dcz': 'dcz holdings inc',
            'dank czar': 'dcz holdings inc',
            'jsm': 'jsm llc',
            'omega': 'omega labs',
            'airo': 'airo pro',
            'airopro': 'airo pro',
            'hustlers': 'hustler\'s ambition',
            'hustlers ambition': 'hustler\'s ambition',
            '1555': '1555 industrial llc',
            '1555 industrial': '1555 industrial llc',
            'dcz holdings': 'dcz holdings inc',
            'dcz holdings inc': 'dcz holdings inc',
            'dcz holdings inc.': 'dcz holdings inc',
            'jsm llc': 'jsm llc',
            'omega labs': 'omega labs',
            'omega cannabis': 'omega labs',
            'airo pro': 'airo pro',
            'hustler\'s ambition': 'hustler\'s ambition',
            '1555 industrial llc': '1555 industrial llc',
            'harmony farms': 'airo pro',
            'jsm': 'jsm llc'
        }
        
        for key, value in vendor_mappings.items():
            if key in vendor_lower:
                vendor = value
                break
    
    # If still no vendor, try to extract from product name patterns
    if not vendor:
        product_name = str(json_data.get("product_name", "")).strip()
        if product_name:
            import re
            # Look for "by [Brand]" pattern
            by_match = re.search(r'by\s+([A-Za-z0-9\s]+)(?:\s|$)', product_name, re.IGNORECASE)
            if by_match:
                vendor = by_match.group(1).strip()
            # Look for "from [Brand]" pattern
            elif "from" in product_name.lower():
                from_match = re.search(r'from\s+([A-Za-z0-9\s]+)(?:\s|$)', product_name, re.IGNORECASE)
                if from_match:
                    vendor = from_match.group(1).strip()
            # Look for "by [Brand] -" pattern
            elif "by" in product_name.lower() and "-" in product_name:
                by_dash_match = re.search(r'by\s+([A-Za-z0-9\s]+)\s*-', product_name, re.IGNORECASE)
                if by_dash_match:
                    vendor = by_dash_match.group(1).strip()
    
    # If still no vendor, try to extract from brand field
    if not vendor:
        brand = str(json_data.get("brand", "")).strip()
        if brand and brand.lower() not in ['unknown', 'n/a', '']:
            vendor = brand
    
    # Final fallback: extract from product name using common patterns
    if not vendor:
        product_name = str(json_data.get("product_name", "")).strip()
        if product_name:
            # Look for common vendor patterns in product names
            name_lower = product_name.lower()
            if any(x in name_lower for x in ['dank czar', 'dcz', 'jsm', 'omega', 'airo', 'hustler', 'super fog']):
                if 'dank czar' in name_lower or 'dcz' in name_lower:
                    vendor = 'dcz holdings inc'
                elif 'jsm' in name_lower:
                    vendor = 'jsm llc'
                elif 'omega' in name_lower:
                    vendor = 'omega labs'
                elif 'airo' in name_lower:
                    vendor = 'airo pro'
                elif 'hustler' in name_lower:
                    vendor = 'hustler\'s ambition'
                elif '1555' in name_lower:
                    vendor = '1555 industrial llc'
                elif 'super fog' in name_lower:
                    vendor = 'super fog'  # Add Super Fog as a recognized vendor
    
    return vendor

# Main function: Process manifest JSON and return list of product dicts
# Each dict contains all relevant DB fields, including cannabinoids/COA

def extract_products_from_manifest(manifest_json):
    """
    Given a manifest JSON (with inventory_transfer_items),
    return a list of dicts, each with all relevant DB fields.
    """
    items = manifest_json.get("inventory_transfer_items", [])
    products = []
    for item in items:
        product = {}
        # Map flat fields
        for k, v in item.items():
            db_field = JSON_TO_DB_FIELD_MAP.get(k, None)
            if db_field:
                product[db_field] = v
        # Nested lab_result_data
        lab_result_data = item.get("lab_result_data", {})
        cannabinoids = extract_cannabinoids(lab_result_data)
        product.update(cannabinoids)
        products.append(product)
    return products  # Fixed: was returning 'product' instead of 'products'

# Example usage:
# products = extract_products_from_manifest(manifest_json)
# for p in products:
#     print(p)

def map_json_to_db_fields(json_item):
    """Map incoming JSON keys to canonical DB columns using get_canonical_field."""
    mapped = {}
    for k, v in json_item.items():
        db_key = get_canonical_field(k)
        mapped[db_key] = v
    return mapped

MEDICALLY_COMPLIANT_PREFIXES = [
    'medically compliant -',
    'med compliant -',
    'med compliant-',
    'medically compliant-',
]

def infer_product_type_from_name(product_name: str) -> str:
    """
    Infer product type from product name using pattern matching and TYPE_OVERRIDES.
    """
    if not isinstance(product_name, str):
        return "Unknown Type"
    
    name_lower = product_name.lower()
    
    # Check TYPE_OVERRIDES first
    for key, value in TYPE_OVERRIDES.items():
        if key in name_lower:
            return value
    
    # Pattern-based inference - prioritize vape keywords over concentrate keywords
    if any(x in name_lower for x in ["flower", "bud", "nug", "herb", "marijuana", "cannabis"]):
        return "Flower"
    elif any(x in name_lower for x in ["vape", "cart", "cartridge", "disposable", "pod", "battery", "jefe", "twisted", "fire", "pen"]):
        return "Vape Cartridge"
    elif any(x in name_lower for x in ["concentrate", "rosin", "shatter", "wax", "live resin", "diamonds", "sauce", "extract", "oil", "distillate"]):
        return "Concentrate"
    elif any(x in name_lower for x in ["edible", "gummy", "chocolate", "cookie", "brownie", "candy"]):
        return "Edible (Solid)"
    elif any(x in name_lower for x in ["tincture", "oil", "drops", "liquid"]):
        return "Edible (Liquid)"
    elif any(x in name_lower for x in ["pre-roll", "joint", "cigar", "blunt"]):
        return "Pre-roll"
    elif any(x in name_lower for x in ["topical", "cream", "lotion", "salve", "balm"]):
        return "Topical"
    elif any(x in name_lower for x in ["tincture", "sublingual"]):
        return "Tincture"
    else:
        # Default to Vape Cartridge for any remaining unknown types since most products are concentrates
        return "Vape Cartridge"

def strip_medically_compliant_prefix(name):
    # Safety check: ensure name is a string
    if not isinstance(name, str):
        if isinstance(name, list):
            logging.warning(f"strip_medically_compliant_prefix received a list instead of string: {name}")
            # If it's a list, try to join it or take the first element
            if name:
                name = str(name[0]) if isinstance(name[0], str) else str(name[0])
            else:
                name = ""
        else:
            logging.warning(f"strip_medically_compliant_prefix received non-string type: {type(name)} - {name}")
            name = str(name) if name is not None else ""
    
    name = name.strip()
    for prefix in MEDICALLY_COMPLIANT_PREFIXES:
        if name.lower().startswith(prefix):
            return name[len(prefix):].strip()
    return name

def normalize_product_name(name):
    # Safety check: ensure name is a string
    if not isinstance(name, str):
        if isinstance(name, list):
            logging.warning(f"normalize_product_name received a list instead of string: {name}")
            # If it's a list, try to join it or take the first element
            if name:
                name = str(name[0]) if isinstance(name[0], str) else str(name[0])
            else:
                name = ""
        else:
            logging.warning(f"normalize_product_name received non-string type: {type(name)} - {name}")
            name = str(name) if name is not None else ""
    
    name = strip_medically_compliant_prefix(name)
    name = name.lower().strip()
    
    # Remove weight/measurement suffixes (e.g., " - 1g", " - 3.5g", " - 7g", etc.)
    weight_patterns = [
        r'\s*-\s*\d+(?:\.\d+)?\s*(?:g|gram|grams|mg|oz|ounce|ounces|pk|pack|packs|piece|pieces|roll|rolls|stix|stick|sticks)\b',
        r'\s*\d+(?:\.\d+)?\s*(?:g|gram|grams|mg|oz|ounce|ounces|pk|pack|packs|piece|pieces|roll|rolls|stix|stick|sticks)\b',
        r'\s*-\s*\d+(?:\.\d+)?\s*$',  # Just numbers at the end
        r'\s+\d+(?:\.\d+)?\s*$',  # Numbers at the end without dash
    ]
    
    for pattern in weight_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    name = re.sub(r'[^\w\s-]', '', name)  # remove non-alphanumeric except hyphen/space
    name = re.sub(r'[-\s]+', ' ', name)  # collapse hyphens and spaces
    return name.strip()

class JSONMatcher:
    """Handles JSON URL fetching and product matching functionality."""
    
    def __init__(self, excel_processor):
        self.excel_processor = excel_processor
        self._sheet_cache = None
        self._indexed_cache = None  # New indexed cache for O(1) lookups
        self.json_matched_names = None
        self._strain_cache = None
        self._lineage_cache = None
        self.advanced_matcher = AdvancedMatcher()  # Initialize advanced matching system
        
    def _build_sheet_cache(self):
        """Build a cache of sheet data for fast matching."""
        logging.info("Building sheet cache...")
        if self.excel_processor is None:
            logging.warning("Cannot build sheet cache: ExcelProcessor is None")
            self._sheet_cache = []
            self._indexed_cache = {}
            return
            
        df = self.excel_processor.df
        if df is None:
            logging.warning("Cannot build sheet cache: DataFrame is None, attempting to load default file")
            # Try to load a default file
            try:
                from .excel_processor import get_default_upload_file
                default_file = get_default_upload_file()
                if default_file:
                    logging.info(f"Loading default file for JSON matcher: {default_file}")
                    success = self.excel_processor.load_file(default_file)
                    if success:
                        df = self.excel_processor.df
                        logging.info(f"Successfully loaded default file, DataFrame now has {len(df) if df is not None else 0} rows")
                    else:
                        logging.error(f"Failed to load default file: {default_file}")
                else:
                    logging.warning("No default file available for JSON matcher")
            except Exception as e:
                logging.error(f"Error loading default file for JSON matcher: {e}")
            
            if df is None:
                logging.warning("Cannot build sheet cache: DataFrame is still None after attempting to load default file")
                self._sheet_cache = []
                self._indexed_cache = {}
                return
            
        if df.empty:
            logging.warning("Cannot build sheet cache: DataFrame is empty")
            self._sheet_cache = []
            self._indexed_cache = {}
            return
            
        logging.info(f"Building sheet cache from DataFrame with {len(df)} rows")
            
        # Determine the best description column to use
        description_col = None
        for col in ["Product Name*", "ProductName", "Description"]:
            if col in df.columns:
                description_col = col
                break
                
        if not description_col:
            logging.error("No suitable description column found")
            self._sheet_cache = []
            self._indexed_cache = {}
            return
            
        # Filter out samples and nulls
        if description_col == "Description":
            df = df[
                df[description_col].notna() &
                ~df[description_col].astype(str).str.lower().str.contains("sample", na=False)
            ]
        else:
            # For ProductName/Product Name*, filter out samples and nulls
            df = df[
                df[description_col].notna() &
                ~df[description_col].astype(str).str.lower().str.contains("sample", na=False) &
                ~df[description_col].astype(str).str.lower().str.contains("trade sample", na=False)
            ]
        
        cache = []
        indexed_cache = {
            'exact_names': {},  # O(1) exact name lookup
            'vendor_exact_names': {},  # O(1) vendor-specific exact name lookup
            'vendor_groups': defaultdict(list),  # O(1) vendor-based grouping
            'key_terms': defaultdict(list),  # O(1) key term lookup
            'normalized_names': defaultdict(list),  # O(1) normalized name lookup
        }
        
        for idx, row in df.iterrows():
            # Ensure idx is hashable by converting to string if needed
            hashable_idx = str(idx) if not isinstance(idx, (int, str, float)) else idx
            
            # Get description with proper type checking
            desc_raw = row[description_col] if description_col in row else ""
            desc = str(desc_raw) if desc_raw is not None else ""
            norm = self._normalize(desc)
            toks = set(norm.split())
            
            # Extract key terms for better matching
            key_terms = self._extract_key_terms(desc)
            
            # Get other fields with proper type checking
            brand_raw = row["Product Brand"] if "Product Brand" in row else ""
            brand = str(brand_raw) if brand_raw is not None else ""
            # Try multiple vendor column names
            vendor_raw = ""
            for vendor_col in ["Vendor", "Vendor/Supplier*", "Vendor/Supplier"]:
                if vendor_col in row and row[vendor_col] is not None:
                    vendor_raw = row[vendor_col]
                    break
            vendor = str(vendor_raw) if vendor_raw is not None else ""
            
            # DEBUG: Log vendor data for first few items
            if len(cache) < 5:
                print(f"🔍 DEBUG: Row {len(cache)}: vendor='{vendor}' (from column: {vendor_col if 'vendor_col' in locals() else 'none'})")
                print(f"🔍 DEBUG: Available columns: {list(row.index)}")
                print(f"🔍 DEBUG: Vendor column values: {[col for col in ['Vendor', 'Vendor/Supplier*', 'Vendor/Supplier'] if col in row]}")
            
            cache_item = {
                "idx": hashable_idx,
                "original_name": desc,
                "norm": norm,
                "tokens": toks,
                "key_terms": key_terms,
                "brand": brand,
                "vendor": vendor,
                "product_type": str(row["Product Type*"] if "Product Type*" in row else ""),
                "lineage": str(row["Lineage"] if "Lineage" in row else ""),
                "strain": str(row["Product Strain"] if "Product Strain" in row else "")
            }
            
            try:
                cache.append(cache_item)
                
                # Build indexed cache for O(1) lookups
                # 1. Exact name index
                exact_name = desc.lower().strip()
                if exact_name:
                    indexed_cache['exact_names'][exact_name] = cache_item
                
                # 2. Vendor-specific exact name index
                vendor_lower = vendor.lower().strip()
                if vendor_lower and exact_name:
                    vendor_key = f"{exact_name}|{vendor_lower}"
                    if vendor_key not in indexed_cache['vendor_exact_names']:
                        indexed_cache['vendor_exact_names'][vendor_key] = []
                    indexed_cache['vendor_exact_names'][vendor_key].append(cache_item)
                
                # 3. Vendor index
                if vendor_lower:
                    indexed_cache['vendor_groups'][vendor_lower].append(cache_item)
                
                # 3. Key terms index (for each key term)
                for term in key_terms:
                    indexed_cache['key_terms'][term].append(cache_item)
                
                # 4. Normalized name index
                if norm:
                    indexed_cache['normalized_names'][norm].append(cache_item)
                    
            except Exception as e:
                logging.warning(f"Error creating cache item for row {idx}: {e}")
                continue
                
        self._sheet_cache = cache
        self._indexed_cache = indexed_cache
        logging.info(f"Built sheet cache with {len(cache)} entries using column '{description_col}'")
        logging.info(f"Built indexed cache with {len(indexed_cache['exact_names'])} exact names, {len(indexed_cache['vendor_groups'])} vendors, {len(indexed_cache['key_terms'])} key terms")
        
        # DEBUG: Show actual vendors in the data
        if cache:
            vendors_in_data = set()
            for item in cache[:20]:  # Check first 20 items
                vendor = str(item.get("vendor", "")).strip()
                if vendor:
                    vendors_in_data.add(vendor)
            print(f"🔍 DEBUG: ACTUAL VENDORS IN EXCEL DATA: {sorted(list(vendors_in_data))[:10]}...")
            print(f"🔍 DEBUG: Total vendors found: {len(vendors_in_data)}")
        
    def _normalize(self, s: str) -> str:
        """Normalize text for matching by removing digits, units, and special characters."""
        # Ensure input is a string
        s = str(s or "")
        s = s.lower()
        s = _DIGIT_UNIT_RE.sub("", s)
        s = _NON_WORD_RE.sub(" ", s)
        return _SPLIT_RE.sub(" ", s).strip()
        
    def _extract_key_terms(self, name: str) -> Set[str]:
        """Extract meaningful product terms, excluding common prefixes/suffixes."""
        try:
            # Debug logging to see what type of input we're getting
            if not isinstance(name, str):
                logging.warning(f"_extract_key_terms received non-string input: {type(name)} - {name}")
                if isinstance(name, list):
                    logging.warning(f"_extract_key_terms received a list: {name}")
                    # If it's a list, try to join it or take the first element
                    if name:
                        name = str(name[0]) if isinstance(name[0], str) else str(name[0])
                    else:
                        name = ""
                else:
                    name = str(name) if name is not None else ""
            
            # Ensure input is a string
            name = str(name or "")
            name_lower = name.lower()
            
            # Split on both spaces and hyphens to break compound terms
            words = set()
            for part in name_lower.replace('_', ' ').split():
                # Split each part on hyphens as well
                sub_parts = part.split('-')
                for sub_part in sub_parts:
                    if sub_part.strip():  # Only add non-empty parts
                        words.add(sub_part.strip())
            
            # Common words to exclude
            common_words = {
                'medically', 'compliant', '1g', '2g', '3.5g', '7g', '14g', '28g', 'oz', 'gram', 'grams',
                'pk', 'pack', 'packs', 'piece', 'pieces', 'roll', 'rolls', 'stix', 'stick', 'sticks', 'brand', 'vendor', 'product',
                'the', 'and', 'or', 'with', 'for', 'of', 'by', 'from', 'to', 'in', 'on', 'at', 'a', 'an', 'mg', 'thc', 'cbd'
            }
            
            # Filter out common words and short words (less than 2 characters for words like "all", "in", "one")
            key_terms = {word for word in words if word not in common_words and len(word) >= 2}
            
            # Add product type indicators for better matching
            product_types = {
                'rosin', 'wax', 'shatter', 'live', 'resin', 'distillate', 'cartridge', 'pre-roll', 'pre-rolls',
                'blunt', 'blunts', 'edible', 'edibles', 'tincture', 'tinctures', 'topical', 'topicals',
                'concentrate', 'concentrates', 'flower', 'buds', 'infused', 'flavour', 'flavor'
            }
            
            # Add product type terms if found
            for word in words:
                if word in product_types:
                    key_terms.add(word)
            
            # Add strain names (common cannabis strain words)
            strain_indicators = {
                'gmo', 'runtz', 'cookies', 'cream', 'wedding', 'cake', 'blueberry', 'banana', 'strawberry',
                'grape', 'lemon', 'lime', 'orange', 'cherry', 'apple', 'mango', 'pineapple', 'passion',
                'dragon', 'fruit', 'guava', 'pink', 'lemonade', 'haze', 'kush', 'diesel', 'og', 'sherbet',
                'gelato', 'mintz', 'grinch', 'cosmic', 'combo', 'honey', 'bread', 'tricho', 'jordan',
                'super', 'boof', 'grandy', 'candy', 'afghani', 'hashplant', 'yoda', 'amnesia'
            }
            
            # Add strain terms if found
            for word in words:
                if word in strain_indicators:
                    key_terms.add(word)
            
            # Add vendor/brand terms (but exclude common prefixes)
            vendor_prefixes = {'medically', 'compliant', 'by'}
            name_parts = name_lower.split()
            for i, part in enumerate(name_parts):
                if part not in vendor_prefixes and len(part) >= 3:
                    # Add single vendor words only
                    key_terms.add(part)
                  
            return key_terms
        except Exception as e:
            logging.warning(f"Error in _extract_key_terms: {e}")
            return set()
    
    def _clean_product_name_for_display(self, product_name: str, strain: str = None, weight: str = None, units: str = None) -> str:
        """
        Clean up product name for better display when no database match is found.
        Creates a format like: "Strain Product Type - Weight"
        """
        try:
            # Use the existing normalization function that removes medically compliant prefix
            cleaned_name = strip_medically_compliant_prefix(product_name)
            
            # If we have strain information, try to create a cleaner name
            if strain and strain.strip():
                strain_name = strain.strip()
                
                # Try to build a better display name
                # Format: "Strain Product Type - Weight"
                display_parts = []
                
                # Start with the strain name
                display_parts.append(strain_name)
                
                # Extract product type from cleaned name
                cleaned_lower = cleaned_name.lower()
                if "flower" in cleaned_lower:
                    display_parts.append("Flower")
                elif "live resin" in cleaned_lower:
                    display_parts.append("Live Resin")
                elif "rosin" in cleaned_lower:
                    display_parts.append("Rosin")
                elif "concentrate" in cleaned_lower:
                    display_parts.append("Concentrate")
                elif "pre-roll" in cleaned_lower or "preroll" in cleaned_lower:
                    display_parts.append("Pre-roll")
                elif "cartridge" in cleaned_lower or "cart" in cleaned_lower:
                    display_parts.append("Cartridge")
                elif "edible" in cleaned_lower:
                    display_parts.append("Edible")
                
                # Add weight if available
                if weight and units:
                    display_parts.append(f"{weight}{units}")
                elif weight:
                    display_parts.append(weight)
                
                # Join the parts
                if len(display_parts) > 1:
                    return " ".join(display_parts)
            
            # Fallback to original cleaned name
            return cleaned_name
            
        except Exception as e:
            logging.warning(f"Error in _clean_product_name_for_display: {e}")
            return product_name
        
    def _extract_vendor(self, name: str) -> str:
        """Extract vendor/brand information from product name."""
        try:
            # Ensure input is a string
            name = str(name or "")
            name_lower = name.lower()
            
            # Handle "by" format (e.g., "Product Name by Vendor") - check this first
            if " by " in name_lower:
                parts = name_lower.split(" by ", 1)
                if len(parts) > 1:
                    vendor_part = parts[1].strip()
                    # Remove any trailing weight/size info (e.g., " - 1g", " - 7g")
                    if " - " in vendor_part:
                        vendor_part = vendor_part.split(" - ")[0].strip()
                    # Return the full vendor name, not just first word
                    return vendor_part.lower()
            
            # Handle "Medically Compliant -" prefix
            if name_lower.startswith("medically compliant -"):
                after_prefix = name.split("-", 1)[1].strip()
                # Remove any trailing weight/size info
                if " - " in after_prefix:
                    after_prefix = after_prefix.split(" - ")[0].strip()
                # Take just the brand name (first part before any additional dashes)
                # For "Dank Czar Rosin All-In-One", we want just "Dank Czar"
                brand_part = after_prefix.split(" - ")[0].strip() if " - " in after_prefix else after_prefix
                # If the brand part contains multiple words that look like a product type, take just the first two words
                words = brand_part.split()
                if len(words) >= 3:
                    # Check if the third word looks like a product type
                    product_types = ['rosin', 'wax', 'shatter', 'live', 'resin', 'distillate', 'cartridge', 'pre-roll', 'all-in-one']
                    if words[2].lower() in product_types:
                        brand_part = " ".join(words[:2])  # Take just first two words
                return brand_part.lower()
                
            # Handle parentheses format (e.g., "Product Name (Vendor)") - check this BEFORE dash-separated formats
            if "(" in name_lower and ")" in name_lower:
                start = name_lower.find("(") + 1
                end = name_lower.find(")")
                if start < end:
                    vendor_part = name_lower[start:end].strip()
                    # Remove any trailing weight/size info (e.g., "/14g", "/7g", etc.)
                    if "/" in vendor_part:
                        vendor_part = vendor_part.split("/")[0].strip()
                    # Remove any trailing weight/size info with dashes (e.g., " - Platinum Line")
                    if " - " in vendor_part:
                        vendor_part = vendor_part.split(" - ")[0].strip()
                    return vendor_part.lower()
                
            # Handle other dash-separated formats
            parts = name.split("-", 1)
            if len(parts) > 1:
                brand_part = parts[0].strip()
                # Remove any trailing weight/size info
                if " - " in brand_part:
                    brand_part = brand_part.split(" - ")[0].strip()
                return brand_part.lower()
                
            # Fallback: use first word
            words = name_lower.split()
            return words[0].lower() if words else ""
        except Exception as e:
            logging.warning(f"Error in _extract_vendor: {e}")
            return ""
        
    def _find_candidates_optimized(self, json_item: dict) -> List[dict]:
        """Find candidate matches using indexed lookups instead of O(n²) comparisons."""
        # Safety check: ensure json_item is a dictionary
        if not isinstance(json_item, dict):
            logging.warning(f"json_item is not a dictionary (type: {type(json_item)}), cannot find candidates")
            return []
            
        # Safety check: ensure indexed cache is not None (but allow fallback to database)
        if self._indexed_cache is None:
            logging.debug("Indexed cache is None, will use database fallback for vendor matching")
            # Don't return early - allow the function to continue with database fallback
            
        candidates = set()  # Use set for deduplication by index
        candidate_indices = set()  # Track indices to avoid duplicates
        
        # Safely extract product name with proper error handling
        json_name_raw = ""
        try:
            json_name_raw = str(json_item.get("product_name", ""))
        except (AttributeError, TypeError):
            logging.warning(f"Invalid product_name in JSON item: {json_item}")
            return []
            
        json_name = normalize_product_name(json_name_raw)
        json_strain = str(json_item.get("strain_name", "")).lower().strip()
        
        # Extract vendor from JSON item using enhanced vendor extraction
        json_vendor = None
        try:
            vendor_info = extract_vendor_info(json_item)
            if vendor_info:
                json_vendor = vendor_info.lower()
            elif json_item.get("brand"):
                json_vendor = str(json_item.get("brand", "")).strip().lower()
            else:
                # Extract vendor from product name
                json_vendor = self._extract_vendor(json_name_raw)
        except (AttributeError, TypeError) as e:
            logging.warning(f"Error extracting vendor from JSON item: {e}")
            json_vendor = None
        
        # Debug logging for specific items
        if "banana og" in json_name:
            logging.info(f"Finding candidates for: {json_name} (extracted vendor: {json_vendor})")
        
        if not json_name:
            return []
            
        # Strategy 1: Exact name match (highest priority) - only if indexed cache is available
        if self._indexed_cache and json_name in self._indexed_cache['exact_names']:
            exact_match = self._indexed_cache['exact_names'][json_name]
            return [exact_match]  # Return immediately for exact match
            
        # Strategy 2: Vendor-based filtering (STRICT - only match within same vendor)
        vendor_candidates = []
        if json_vendor:
            # First try exact vendor match (if indexed cache is available)
            if self._indexed_cache and json_vendor in self._indexed_cache['vendor_groups']:
                vendor_candidates = self._indexed_cache['vendor_groups'][json_vendor]
            elif self._indexed_cache:
                # Try fuzzy vendor matching for similar vendor names (but be more strict)
                vendor_candidates = self._find_strict_fuzzy_vendor_matches(json_vendor)
            
            # If we have vendor candidates, try to find better matches within the vendor
            if vendor_candidates:
                better_vendor_candidates = self._find_better_vendor_matches(json_item, vendor_candidates)
                if better_vendor_candidates:
                    vendor_candidates = better_vendor_candidates
                
            # Add vendor candidates to the result set
            for candidate in vendor_candidates:
                # Safety check: ensure candidate is a dictionary
                if not isinstance(candidate, dict):
                    logging.warning(f"Vendor candidate is not a dictionary (type: {type(candidate)}), skipping: {candidate}")
                    continue
                    
                if candidate["idx"] not in candidate_indices:
                    candidates.add(candidate["idx"])
                    candidate_indices.add(candidate["idx"])
                    
            # Debug logging for specific items
            if "banana og" in json_name:
                logging.info(f"Found {len(vendor_candidates)} vendor candidates for vendor '{json_vendor}'")
        
        # CRITICAL: If we have a vendor but no vendor candidates from indexed cache, 
        # try to find vendor candidates from database products
        if json_vendor and not vendor_candidates:
            logging.debug(f"No vendor candidates found in indexed cache for vendor '{json_vendor}' - checking database products")
            
            # Get all products including database products
            all_products = self._get_all_products()
            
            # Filter for vendor matches from all products
            vendor_candidates = []
            for product in all_products:
                if isinstance(product, dict):
                    candidate_vendor = str(product.get("Vendor/Supplier*", "") or product.get("vendor", "")).strip()
                    if candidate_vendor and self._is_vendor_match(json_vendor, candidate_vendor):
                        # Convert to indexed cache format
                        cache_item = {
                            "idx": len(vendor_candidates),
                            "original_name": product.get("Product Name*", ""),
                            "vendor": candidate_vendor,
                            "brand": product.get("Product Brand", ""),
                            "type": product.get("Product Type*", ""),
                            "description": product.get("Description", ""),
                            "_source": product.get("_source", "database"),
                            "_priority": product.get("_priority", 1)
                        }
                        vendor_candidates.append(cache_item)
            
            if vendor_candidates:
                logging.debug(f"Found {len(vendor_candidates)} vendor candidates from database for vendor '{json_vendor}'")
                # Add vendor candidates to the result set
                for candidate in vendor_candidates:
                    if candidate["idx"] not in candidate_indices:
                        candidates.add(candidate["idx"])
                        candidate_indices.add(candidate["idx"])
            else:
                logging.debug(f"No vendor candidates found in database for vendor '{json_vendor}' - returning empty list to prevent cross-vendor matches")
                return []
        
        # Strategy 3: Key term overlap (ONLY within vendor group to prevent cross-vendor matches)
        if json_vendor and vendor_candidates and self._indexed_cache:
            json_key_terms = self._extract_key_terms(json_name)
            for term in json_key_terms:
                if term in self._indexed_cache['key_terms']:
                    for candidate in self._indexed_cache['key_terms'][term]:
                        # Only include if candidate is from the same vendor group
                        candidate_vendor = str(candidate.get("vendor", "")).lower().strip()
                        if self._is_vendor_match(json_vendor, candidate_vendor):
                            if candidate["idx"] not in candidate_indices:
                                candidates.add(candidate["idx"])
                                candidate_indices.add(candidate["idx"])
                                
                                # Limit candidates to prevent performance issues
                                if len(candidates) >= 200:
                                    break
                    if len(candidates) >= 200:
                        break
        
        # Strategy 4: Normalized name similarity (ONLY within vendor group)
        if json_vendor and vendor_candidates and len(candidates) < 20 and json_name and self._indexed_cache:
            # Try to find similar normalized names within the same vendor
            for norm_name, norm_candidates in self._indexed_cache['normalized_names'].items():
                # Use simple similarity check
                similarity = SequenceMatcher(None, json_name, norm_name).ratio()
                if similarity >= 0.5:  # 50% similarity threshold
                    for candidate in norm_candidates:
                        # Only include if candidate is from the same vendor group
                        candidate_vendor = str(candidate.get("vendor", "")).lower().strip()
                        if self._is_vendor_match(json_vendor, candidate_vendor):
                            if candidate["idx"] not in candidate_indices:
                                candidates.add(candidate["idx"])
                                candidate_indices.add(candidate["idx"])
                                
                                # Limit candidates
                                if len(candidates) >= 100:
                                    break
                    if len(candidates) >= 100:
                        break
        
        # Convert back to list and limit total candidates for performance
        candidate_list = []
        
        # Get all products including database products for the final lookup
        all_products = self._get_all_products()
        
        # If we have candidates from the indexed cache, use those first
        if candidates:
            # Use sheet cache for indexed cache candidates
            if self._sheet_cache is not None:
                temp_index = {str(cache_item["idx"]): cache_item for cache_item in self._sheet_cache}
                candidate_indices_list = list(candidates)[:500]  # Limit to 500 candidates max
                
                for idx in candidate_indices_list:
                    cache_item = temp_index.get(str(idx))
                    if cache_item:
                        candidate_list.append(cache_item)
        
        # If we have vendor candidates from database, add those too
        if json_vendor and vendor_candidates:
            # Add database vendor candidates
            for candidate in vendor_candidates[:100]:  # Limit database candidates
                if candidate not in candidate_list:  # Avoid duplicates
                    candidate_list.append(candidate)
        
        return candidate_list
    
    def _is_vendor_match(self, vendor1: str, vendor2: str) -> bool:
        """Check if two vendors match using the same logic as the main matching function."""
        if not vendor1 or not vendor2:
            return False
            
        vendor1_clean = self._normalize_vendor_name(vendor1.lower().strip())
        vendor2_clean = self._normalize_vendor_name(vendor2.lower().strip())
        
        # Exact match
        if vendor1_clean == vendor2_clean:
            return True
            
        # Substring match (with length check)
        if (len(vendor1_clean) > len(vendor2_clean) * 2 and vendor2_clean in vendor1_clean) or \
           (len(vendor2_clean) > len(vendor1_clean) * 2 and vendor1_clean in vendor2_clean):
            return True
            
        # Use the flexible matching logic
        return self._is_vendor_match_flexible(vendor1_clean, vendor2_clean)
        
    def _find_fuzzy_vendor_matches(self, json_vendor: str) -> List[dict]:
        """Find vendor matches using fuzzy matching for similar vendor names."""
        if not json_vendor:
            return []
            
        matches = []
        available_vendors = list(self._indexed_cache['vendor_groups'].keys())
        
        # Common vendor name variations and abbreviations
        vendor_variations = {
            'dank czar': ['dcz holdings inc', 'dcz', 'dank czar holdings', 'dcz holdings', 'dcz holdings inc.'],
            'dcz holdings': ['dank czar', 'dcz', 'dcz holdings inc', 'dcz holdings inc.'],
            'dcz holdings inc': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc.'],
            'hustler\'s ambition': ['1555 industrial llc', 'hustler\'s ambition', 'hustlers ambition'],
            'hustlers ambition': ['1555 industrial llc', 'hustler\'s ambition', 'hustlers ambition'],
            'omega': ['jsm llc', 'omega labs', 'omega cannabis'],
            'airo pro': ['harmony farms', 'airo', 'airopro'],
            'jsm': ['omega', 'jsm llc', 'jsm labs'],
            'harmony': ['airo pro', 'harmony farms', 'harmony cannabis'],
        }
        
        # Check for known variations
        for variation_key, variations in vendor_variations.items():
            if json_vendor == variation_key or any(v in json_vendor for v in variations):
                for vendor in available_vendors:
                    if any(v in vendor for v in variations) or vendor in variations:
                        vendor_matches = self._indexed_cache['vendor_groups'][vendor]
                        # Safety check: ensure all matches are dictionaries
                        safe_matches = [match for match in vendor_matches if isinstance(match, dict)]
                        matches.extend(safe_matches)
        
        # If no matches found with known variations, try partial matching
        if not matches:
            for vendor in available_vendors:
                # Check if vendor contains key words from json_vendor
                json_words = set(json_vendor.split())
                vendor_words = set(vendor.split())
                
                # Check for word overlap
                overlap = json_words.intersection(vendor_words)
                if overlap and len(overlap) >= 1:  # At least one word in common
                    vendor_matches = self._indexed_cache['vendor_groups'][vendor]
                    # Safety check: ensure all matches are dictionaries
                    safe_matches = [match for match in vendor_matches if isinstance(match, dict)]
                    matches.extend(safe_matches)
        
        # If still no matches, try substring matching (more permissive)
        if not matches:
            json_vendor_lower = json_vendor.lower()
            for vendor in available_vendors:
                vendor_lower = vendor.lower()
                # Check if either vendor contains the other as a substring
                if json_vendor_lower in vendor_lower or vendor_lower in json_vendor_lower:
                    vendor_matches = self._indexed_cache['vendor_groups'][vendor]
                    # Safety check: ensure all matches are dictionaries
                    safe_matches = [match for match in vendor_matches if isinstance(match, dict)]
                    matches.extend(safe_matches)
        
        return matches
        
    def _find_better_vendor_matches(self, json_item: dict, vendor_candidates: List[dict]) -> List[dict]:
        """Find better matches within the same vendor by prioritizing similar product types and strain names."""
        if not vendor_candidates:
            return []
            
        json_name = str(json_item.get("product_name", "")).lower()
        json_key_terms = self._extract_key_terms(json_name)
        
        # Score each vendor candidate
        scored_candidates = []
        for candidate in vendor_candidates:
            # Safety check: ensure candidate is a dictionary
            if not isinstance(candidate, dict):
                logging.warning(f"Vendor candidate is not a dictionary (type: {type(candidate)}), skipping: {candidate}")
                continue
                
            candidate_name = str(candidate.get("original_name", "")).lower()
            candidate_key_terms = candidate.get("key_terms", set())
            
            # Calculate similarity score
            score = 0.0
            
            # Product type similarity
            product_types = {'rosin', 'wax', 'shatter', 'live', 'resin', 'distillate', 'cartridge', 'pre-roll', 'blunt', 'edible', 'tincture', 'topical', 'concentrate', 'flower', 'infused'}
            json_product_types = json_key_terms.intersection(product_types)
            candidate_product_types = candidate_key_terms.intersection(product_types)
            
            if json_product_types and candidate_product_types:
                if json_product_types == candidate_product_types:
                    score += 0.4  # Exact product type match
                elif json_product_types.intersection(candidate_product_types):
                    score += 0.2  # Partial product type match
            
            # Strain name similarity
            strain_indicators = {'gmo', 'runtz', 'cookies', 'cream', 'wedding', 'cake', 'blueberry', 'banana', 'strawberry', 'grape', 'lemon', 'cherry', 'apple', 'mango', 'pineapple', 'passion', 'dragon', 'fruit', 'guava', 'pink', 'lemonade', 'haze', 'kush', 'diesel', 'og', 'sherbet', 'gelato', 'mintz', 'grinch', 'cosmic', 'combo', 'honey', 'bread', 'tricho', 'jordan', 'super', 'boof', 'grandy', 'candy', 'afghani', 'hashplant', 'yoda', 'amnesia'}
            json_strains = json_key_terms.intersection(strain_indicators)
            candidate_strains = candidate_key_terms.intersection(strain_indicators)
            
            if json_strains and candidate_strains:
                if json_strains == candidate_strains:
                    score += 0.5  # Exact strain match
                elif json_strains.intersection(candidate_strains):
                    score += 0.3  # Partial strain match
            
            # General term overlap
            overlap = json_key_terms.intersection(candidate_key_terms)
            if overlap:
                overlap_ratio = len(overlap) / min(len(json_key_terms), len(candidate_key_terms)) if min(len(json_key_terms), len(candidate_key_terms)) > 0 else 0
                score += overlap_ratio * 0.3
            
            # Contains matching
            if json_name in candidate_name or candidate_name in json_name:
                score += 0.2
            
            scored_candidates.append((candidate, score))
        
        # Sort by score and return top candidates
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return [candidate for candidate, score in scored_candidates if score > 0.1]  # Reduced threshold from 0.2 to 0.1 for more candidates
        
    def _calculate_match_score(self, json_item: dict, cache_item: dict) -> float:
        """Calculate a match score between JSON item and cache item using enhanced field matching."""
        try:
            # Safety check: ensure both items are dictionaries
            if not isinstance(json_item, dict) or not isinstance(cache_item, dict):
                logging.warning(f"Invalid item types in _calculate_match_score: json_item={type(json_item)}, cache_item={type(cache_item)}")
                return 0.0
                
            # Extract core fields for matching
            json_name_raw = str(json_item.get("product_name", ""))
            cache_name_raw = str(cache_item.get("original_name", ""))
            json_name = normalize_product_name(json_name_raw)
            cache_name = normalize_product_name(cache_name_raw)
            json_strain = str(json_item.get("strain_name", "")).lower().strip()
            cache_strain = str(cache_item.get("strain", "")).lower().strip()
            
            # Extract vendors for strict vendor matching
            json_vendor = None
            if json_item.get("vendor"):
                json_vendor = str(json_item.get("vendor", "")).strip().lower()
            elif json_item.get("brand"):
                json_vendor = str(json_item.get("brand", "")).strip().lower()
            else:
                json_vendor = self._extract_vendor(json_name_raw)
            
            cache_vendor = str(cache_item.get("vendor", "")).strip().lower()
            
            # Extract additional fields for enhanced matching
            json_brand = str(json_item.get("brand", "")).lower().strip()
            cache_brand = str(cache_item.get("brand", "")).lower().strip()
            json_type = str(json_item.get("product_type", "")).lower().strip()
            cache_type = str(cache_item.get("product_type", "")).lower().strip()
            json_weight = str(json_item.get("weight", "")).lower().strip()
            cache_weight = str(cache_item.get("weight", "")).lower().strip()
            
            # Debug log
            logging.debug(f"[SCORE] JSON: '{json_name_raw}' (norm: '{json_name}') | Excel: '{cache_name_raw}' (norm: '{cache_name}') | Strain: '{json_strain}' vs '{cache_strain}' | Vendor: '{json_vendor}' vs '{cache_vendor}' | Brand: '{json_brand}' vs '{cache_brand}' | Type: '{json_type}' vs '{cache_type}' | Weight: '{json_weight}' vs '{cache_weight}'")
            
            # --- BEGIN: Enhanced vendor matching ---
            # If we have vendor information for both, they must match or be very similar
            if json_vendor and cache_vendor:
                # Check if vendors are the same or known variations
                vendor_variations = {
                    'dank czar': ['dcz holdings inc', 'dcz holdings inc.', 'dcz', 'dank czar holdings', 'dcz holdings', 'jsm llc'],
                    'dcz holdings': ['dank czar', 'dcz', 'dcz holdings inc', 'dcz holdings inc.', 'dcz holdings', 'jsm llc'],
                    'dcz holdings inc': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc.', 'jsm llc'],
                    'dcz holdings inc.': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc', 'jsm llc'],
                    'jsm llc': ['dank czar', 'dcz holdings', 'dcz holdings inc', 'dcz holdings inc.', 'dcz', 'omega'],
                    'hustler\'s ambition': ['1555 industrial llc', 'hustler\'s ambition', 'hustlers ambition'],
                    'hustlers ambition': ['1555 industrial llc', 'hustler\'s ambition', 'hustlers ambition'],
                    '1555 industrial llc': ['hustler\'s ambition', 'hustlers ambition'],
                    'omega': ['jsm llc', 'omega labs', 'omega cannabis'],
                    'airo pro': ['harmony farms', 'airo', 'airopro'],
                }
                
                vendors_match = False
                if json_vendor == cache_vendor:
                    vendors_match = True
                else:
                    # Check known variations
                    for main_vendor, variations in vendor_variations.items():
                        if (json_vendor in [main_vendor] + variations and 
                            cache_vendor in [main_vendor] + variations):
                            vendors_match = True
                            break
                    
                    # Also check for partial matches (more lenient)
                    if not vendors_match:
                        # Check if one vendor name contains the other
                        if json_vendor in cache_vendor or cache_vendor in json_vendor:
                            vendors_match = True
                
                # If vendors don't match, return very low score (but not 0 to allow for edge cases)
                if not vendors_match:
                    logging.debug(f"Vendor mismatch: '{json_vendor}' vs '{cache_vendor}' - returning low score")
                    return 0.05
            # --- END: Enhanced vendor matching ---
            
            # --- BEGIN: Enhanced brand matching ---
            # Brand matching provides additional confidence
            brand_bonus = 0.0
            if json_brand and cache_brand:
                if json_brand == cache_brand:
                    brand_bonus = 0.1
                elif json_brand in cache_brand or cache_brand in json_brand:
                    brand_bonus = 0.05
            # --- END: Enhanced brand matching ---
            
            # --- BEGIN: Enhanced product type matching ---
            # Product type matching provides additional confidence
            type_bonus = 0.0
            if json_type and cache_type:
                if json_type == cache_type:
                    type_bonus = 0.1
                elif json_type in cache_type or cache_type in json_type:
                    type_bonus = 0.05
            # --- END: Enhanced product type matching ---
            
            # --- BEGIN: Enhanced weight matching ---
            # Weight matching provides additional confidence
            weight_bonus = 0.0
            if json_weight and cache_weight:
                if json_weight == cache_weight:
                    weight_bonus = 0.1
                elif json_weight in cache_weight or cache_weight in json_weight:
                    weight_bonus = 0.05
            # --- END: Enhanced weight matching ---
            
            # --- BEGIN: Strict cannabis type filtering ---
            # Define recognized cannabis product types (update as needed)
            CANNABIS_TYPES = [
                "concentrate", "vape cartridge", "flower", "edible", "tincture", "capsule", "topical", "pre-roll"
            ]
            def is_cannabis_type(type_str):
                if not type_str:
                    return False
                type_str = str(type_str).lower()
                return any(t in type_str for t in CANNABIS_TYPES)

            # Get product type/category from both JSON and cache item
            json_type_check = json_item.get("product_type") or json_item.get("inventory_type") or json_item.get("inventory_category")
            cache_type_check = cache_item.get("product_type") or cache_item.get("product_category")

            # If either is not a cannabis type, do not match
            if not is_cannabis_type(json_type_check) or not is_cannabis_type(cache_type_check):
                return 0.0
            # --- END: Strict cannabis type filtering ---

            # Calculate base score with more stringent requirements
            base_score = 0.0

            # Exact match (highest score)
            if json_name == cache_name:
                base_score = 1.0
            # Contains match (high score)
            elif json_name in cache_name or cache_name in json_name:
                base_score = 0.9
            # Strain match bonus (good score)
            elif json_strain and cache_strain and json_strain == cache_strain:
                base_score = 0.8
            # Word overlap analysis (more stringent)
            else:
                json_words = set(json_name.split())
                cache_words = set(cache_name.split())
                
                # Remove common words that don't add value
                stop_words = {'and', 'or', 'the', 'a', 'an', 'with', 'for', 'live', 'resin', 'cart', 'cartridge'}
                json_words = json_words - stop_words
                cache_words = cache_words - stop_words
                
                if len(json_words) == 0 or len(cache_words) == 0:
                    base_score = 0.1
                else:
                    overlap = json_words & cache_words
                    if overlap:
                        # Require higher overlap for good matches
                        overlap_ratio = len(overlap) / min(len(json_words), len(cache_words))
                        if overlap_ratio >= 0.8:  # Raised from 0.5
                            base_score = 0.7
                        elif overlap_ratio >= 0.6:  # Raised from 0.3
                            base_score = 0.5
                        elif overlap_ratio >= 0.4:  # New middle tier
                            base_score = 0.3
                        else:
                            base_score = 0.1  # Lower score for weak overlap
                    else:
                        # No word overlap - very low score
                        base_score = 0.05
            
            # Apply bonuses for additional field matches (with diminishing returns)
            final_score = base_score + (brand_bonus * 0.8) + (type_bonus * 0.6) + (weight_bonus * 0.4)
            final_score = min(1.0, final_score)  # Cap at 1.0
            
            # Additional penalty for mismatched product types
            if json_type and cache_type and json_type != cache_type:
                # Check if they're in different categories
                concentrate_types = ['concentrate', 'vape', 'cartridge', 'oil', 'distillate']
                flower_types = ['flower', 'bud', 'pre-roll', 'joint']
                edible_types = ['edible', 'gummy', 'chocolate', 'candy']
                
                json_category = None
                cache_category = None
                
                for cat_name, types in [('concentrate', concentrate_types), ('flower', flower_types), ('edible', edible_types)]:
                    if any(t in json_type for t in types):
                        json_category = cat_name
                    if any(t in cache_type for t in types):
                        cache_category = cat_name
                
                if json_category and cache_category and json_category != cache_category:
                    final_score *= 0.3  # Heavy penalty for category mismatch
            
            return final_score
            
        except Exception as e:
            logging.error(f"Error in _calculate_match_score: {e}")
            logging.error(f"json_item: {json_item}")
            logging.error(f"cache_item: {cache_item}")
            return 0.05  # Return very low score instead of 0
        
    def fetch_and_match(self, url: str) -> List[Dict]:
        """
        Fetch JSON from URL and match products against the loaded Excel data.
        Simplified and more reliable implementation.
        
        Args:
            url: URL to fetch JSON data from (HTTP URL or data URL)
            
        Returns:
            List of matched product dictionaries
        """
        print(f"🔍 DEBUG: fetch_and_match called with URL: {url[:100]}...")
        # Special mode: return ALL DB products as matched tags (bypass JSON matching)
        if url.lower().startswith("db:all"):
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                db_products = product_db.get_all_products() or []
                print(f"🔍 DEBUG: DB_ALL mode - loading {len(db_products)} products from database")
                matched_products = []
                for row in db_products:
                    product = self._create_product_from_db_row(row)
                    matched_products.append(product)
                return matched_products
            except Exception as e:
                logging.error(f"DB_ALL mode failed: {e}")
                return []
        if not (url.lower().startswith("http") or url.lower().startswith("data:")):
            raise ValueError("Please provide a valid HTTP URL or data URL")
            
        # ALWAYS force rebuild to ensure vendor data is properly included
        print("🔍 DEBUG: FORCE REBUILDING sheet cache to include vendor data")
        self._sheet_cache = None
        self._indexed_cache = None
        self._build_sheet_cache()
            
        # DEBUG: Log the current state of Excel data
        print(f"🔍 DEBUG: Excel processor exists: {self.excel_processor is not None}")
        if self.excel_processor:
            print(f"🔍 DEBUG: Excel DataFrame exists: {self.excel_processor.df is not None}")
            if self.excel_processor.df is not None:
                print(f"🔍 DEBUG: Excel DataFrame rows: {len(self.excel_processor.df)}")
                print(f"🔍 DEBUG: Excel DataFrame columns: {list(self.excel_processor.df.columns)}")
                
                # Show unique vendors in Excel data
                vendor_cols = ['Vendor', 'Vendor/Supplier*', 'Vendor/Supplier']
                excel_vendors = set()
                for col in vendor_cols:
                    if col in self.excel_processor.df.columns:
                        vendors = self.excel_processor.df[col].dropna().unique()
                        excel_vendors.update([str(v).strip().lower() for v in vendors if str(v).strip()])
                
                print(f"🔍 DEBUG: Excel vendors ({len(excel_vendors)}): {sorted(list(excel_vendors))[:10]}...")
        print(f"🔍 DEBUG: Sheet cache length: {len(self._sheet_cache) if self._sheet_cache else 0}")
            
        # Note: We can still process JSON items even without Excel data
        # The sheet cache is only needed for Excel-based matching
        if not self._sheet_cache:
            print("⚠️ No Excel data available - will use Product Database for matching")

        try:
            # Handle data URLs differently from HTTP URLs
            if url.lower().startswith("data:"):
                try:
                    # Parse data URL
                    import base64
                    import json
                    
                    # Extract the data part after the comma
                    if ',' in url:
                        header, data_part = url.split(',', 1)
                        # Check if it's base64 encoded
                        if 'base64' in header:
                            # Decode base64 data
                            decoded_data = base64.b64decode(data_part).decode('utf-8')
                            payload = json.loads(decoded_data)
                        else:
                            # Direct JSON data
                            payload = json.loads(data_part)
                    else:
                        raise ValueError("Invalid data URL format")
                        
                    logging.info("Successfully parsed data URL")
                except Exception as data_error:
                    logging.error(f"Error parsing data URL: {data_error}")
                    raise ValueError(f"Failed to parse data URL: {data_error}")
            else:
                # Handle HTTP URLs
                import requests
                
                # Prepare headers for the request
                headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                }
                
                # Add authentication headers if available
                # These can be set via environment variables or configuration
                import os
                if os.environ.get('BAMBOO_API_KEY'):
                    headers['X-API-Key'] = os.environ.get('BAMBOO_API_KEY')
                if os.environ.get('BAMBOO_AUTH_TOKEN'):
                    headers['Authorization'] = f"Bearer {os.environ.get('BAMBOO_AUTH_TOKEN')}"
                if os.environ.get('BAMBOO_SESSION_TOKEN'):
                    headers['X-Session-Token'] = os.environ.get('BAMBOO_SESSION_TOKEN')
                
                # Try to make the request directly first
                try:
                    response = requests.get(url, headers=headers, timeout=60)
                    response.raise_for_status()
                    payload = response.json()
                except (requests.exceptions.RequestException, ValueError) as direct_error:
                    logging.info(f"Direct request failed, trying proxy: {direct_error}")
                    # Fallback to proxy endpoint if direct request fails
                    import os
                    base_url = os.environ.get('FLASK_BASE_URL', 'http://127.0.0.1:5001')
                    proxy_data = {'url': url, 'headers': headers}
                    response = requests.post(f'{base_url}/api/proxy-json', 
                                           json=proxy_data, 
                                           timeout=60)
                    response.raise_for_status()
                    payload = response.json()
                
            # Handle both list and dictionary payloads
            if isinstance(payload, list):
                items = payload
                global_vendor = ""
            elif isinstance(payload, dict):
                items = payload.get("inventory_transfer_items", [])
                global_vendor = payload.get("from_license_name", "")
                logging.info(f"Extracted global vendor from document: {global_vendor}")
            else:
                logging.warning(f"Unexpected payload type: {type(payload)}")
                return []
                
            if not items:
                logging.warning("No inventory transfer items found in JSON")
                return []

            # VENDOR PROPAGATION FIX: Find vendor from any item that has it and apply to all items
            if not global_vendor:
                # Look for vendor information in any of the items
                for item in items:
                    if isinstance(item, dict):
                        vendor = str(item.get('vendor', item.get('from_license_name', ''))).strip()
                        if vendor:
                            global_vendor = vendor
                            logging.info(f"🔧 VENDOR PROPAGATION: Found vendor '{global_vendor}' in item, applying to all items")
                            break
            
            # Apply the global vendor to ALL items that don't have one
            vendor_applied_count = 0
            for item in items:
                if isinstance(item, dict):
                    current_vendor = str(item.get('vendor', '')).strip()
                    if not current_vendor and global_vendor:
                        item['vendor'] = global_vendor
                        vendor_applied_count += 1
            
            if vendor_applied_count > 0:
                logging.info(f"🔧 VENDOR PROPAGATION: Applied vendor '{global_vendor}' to {vendor_applied_count} items that were missing vendor info")
                print(f"🔧 VENDOR PROPAGATION: Applied vendor '{global_vendor}' to {vendor_applied_count} items that were missing vendor info")
                
            # CRITICAL FIX: Preserve ALL items from JSON - no deduplication
            logging.info(f"Processing {len(items)} JSON items - preserving ALL items as requested")
            print(f"🔍 DEBUG: Processing {len(items)} JSON items - preserving ALL items as requested")
            
            # DEBUG: Show what vendor we're looking for in JSON
            if items:
                json_vendors = set()
                for item in items[:10]:  # Check first 10 items now that vendor is propagated
                    if isinstance(item, dict):
                        vendor = str(item.get('vendor', item.get('from_license_name', ''))).strip()
                        if vendor:
                            json_vendors.add(vendor)
                print(f"🔍 DEBUG: JSON VENDORS LOOKING FOR (after propagation): {sorted(list(json_vendors))}")
                
                # DEBUG: Show sample of all items to verify vendor propagation worked
                print(f"🔍 DEBUG: Sample of first 10 items (after vendor propagation):")
                for i, item in enumerate(items[:10]):
                    if isinstance(item, dict):
                        product_name = item.get('product_name', 'NO_NAME')
                        vendor = item.get('vendor', 'NO_VENDOR')
                        print(f"🔍 DEBUG:   Item {i}: '{product_name}' - vendor: '{vendor}'")
            
            unique_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                product_name = str(item.get("product_name", "")).strip()
                
                # CRITICAL FIX: Process ALL items, even those with missing product names
                # This ensures no products are lost due to missing product names in JSON
                if not product_name:
                    # Try to create a fallback product name from other available fields
                    vendor = str(item.get("vendor", "")).strip()
                    brand = str(item.get("brand", "")).strip()
                    weight = str(item.get("weight", "")).strip()
                    product_type = str(item.get("inventory_type", "")).strip()
                    
                    # Create a fallback product name
                    fallback_parts = []
                    if brand:
                        fallback_parts.append(brand)
                    if product_type:
                        fallback_parts.append(product_type)
                    if weight:
                        fallback_parts.append(weight)
                    
                    if fallback_parts:
                        product_name = " ".join(fallback_parts)
                    else:
                        product_name = f"JSON Product {len(unique_items) + 1}"
                    
                    logging.info(f"⚠️  Created fallback product name: '{product_name}' for JSON item with missing name")
                
                # Add ALL items without any deduplication - each item gets its own label
                unique_items.append(item)
            
            logging.info(f"CRITICAL FIX: Processed {len(items)} items -> {len(unique_items)} products (ALL preserved)")
            logging.info(f"CRITICAL FIX: Each JSON item will generate its own separate label")
            print(f"🔍 DEBUG: CRITICAL FIX: Processed {len(items)} items -> {len(unique_items)} products (ALL preserved)")
            print(f"🔍 DEBUG: CRITICAL FIX: Each JSON item will generate its own separate label")
            
            # DEBUG: Show vendors in JSON data
            json_vendors = set()
            for item in unique_items:
                item_vendor = str(item.get("vendor", "")).strip().lower()
                if item_vendor:
                    json_vendors.add(item_vendor)
                if global_vendor:
                    json_vendors.add(global_vendor.lower())
            
            print(f"🔍 DEBUG: JSON vendors ({len(json_vendors)}): {sorted(list(json_vendors))}")
                
            # Extract vendor information from root level if available
            vendor_meta = "Unknown Vendor"
            if isinstance(payload, dict) and "from_license_name" in payload:
                vendor_meta = payload.get('from_license_name', '')
                
            raw_date = datetime.now().strftime("%Y-%m-%d")
            if isinstance(payload, dict) and "est_arrival_at" in payload:
                raw_date = payload.get("est_arrival_at", "").split("T")[0]
                
            matched_products = []
            
            # For each JSON item, find the best match using Excel data
            processed_product_names = set()  # Track processed product names to prevent duplicates
            print(f"🔍 DEBUG: Starting to process {len(unique_items)} unique items from JSON")
            for i, item in enumerate(unique_items):
                # CRITICAL FIX: Don't skip items with missing product names - create fallback names
                if not item.get("product_name"):
                    # Try to create a fallback product name from other available fields
                    vendor = str(item.get("vendor", "")).strip()
                    brand = str(item.get("brand", "")).strip()
                    inventory_type = str(item.get("inventory_type", "")).strip()
                    
                    # Create a descriptive fallback name
                    fallback_parts = []
                    if brand:
                        fallback_parts.append(brand)
                    if inventory_type:
                        fallback_parts.append(inventory_type)
                    if vendor:
                        fallback_parts.append(f"by {vendor}")
                    
                    if fallback_parts:
                        item["product_name"] = " ".join(fallback_parts)
                        logging.info(f"⚠️  Created fallback product name: '{item['product_name']}' for item missing product_name")
                    else:
                        item["product_name"] = f"JSON Product {i+1}"
                        logging.info(f"⚠️  Created generic product name: '{item['product_name']}' for item missing product_name")
                    
                product_name = str(item.get("product_name", ""))
                
                # CRITICAL FIX: Process ALL items even with duplicate names to ensure maximum tag generation
                # Each JSON item should generate its own tag regardless of name duplication
                logging.info(f"🔄 Processing item {i+1}/{len(unique_items)}: '{product_name}'")
                print(f"🔍 DEBUG: Processing item {i+1}/{len(unique_items)}: '{product_name}'")
                
                vendor = global_vendor if global_vendor else str(item.get("vendor", ""))
                brand = str(item.get("brand", "")).strip()
                product_type = str(item.get("inventory_type", "")).strip()
                weight = str(item.get("unit_weight", item.get("weight", ""))).strip()
                strain = str(item.get("strain_name", item.get("strain", ""))).strip()
                
                # Use comprehensive matching logic (same as Excel) with AI tools
                try:
                    print(f"🔍 DEBUG: Trying comprehensive matching for '{product_name}' (type: {product_type})")
                    print(f"🔍 DEBUG: Item data: {item}")
                    print(f"🔍 DEBUG: Vendor: '{vendor}', Product Type: {product_type}, Strain: {strain}")
                    print(f"🔍 DEBUG: Global Vendor: '{global_vendor}'")
                    
                    comprehensive_products = self._process_item_with_main_matching(item, product_name, vendor, product_type, strain, global_vendor)
                    print(f"🔍 DEBUG: Comprehensive matching returned {len(comprehensive_products)} products")
                    
                    if comprehensive_products:
                        for product in comprehensive_products:
                            matched_products.append(product)
                        print(f"🔍 DEBUG: Added {len(comprehensive_products)} products from comprehensive matching")
                        continue  # Skip the old matching logic below
                    else:
                        print(f"🔍 DEBUG: No products found by comprehensive matching, trying DIRECT advanced matching")
                        
                        # DIRECT Advanced Matching - bypass all other logic
                        try:
                            # Ensure sheet cache is built
                            if self._sheet_cache is None:
                                print(f"🔍 DEBUG: Building sheet cache for DIRECT advanced matching")
                                self._build_sheet_cache()
                            
                            if self._sheet_cache:
                                print(f"🔍 DEBUG: DIRECT Advanced matching with {len(self._sheet_cache)} candidates")
                                
                                # Prepare JSON item for advanced matching
                                json_item = {
                                    "product_name": product_name,
                                    "vendor": vendor,
                                    "brand": brand,
                                    "product_type": product_type,
                                    "weight": weight,
                                    "strain_name": strain
                                }
                                
                                # Use advanced matching directly (with vendor isolation)
                                advanced_matches = self._find_advanced_matches(json_item)
                                if advanced_matches:
                                    best_advanced = advanced_matches[0]
                                    print(f"🔍 DEBUG: DIRECT Advanced matching found {len(advanced_matches)} matches, best score {best_advanced.overall_score:.1f}")
                                    
                                    # Create product from advanced match
                                    advanced_product = self._create_product_from_advanced_match(best_advanced.item, item, global_vendor)
                                    if advanced_product:
                                        matched_products.append(advanced_product)
                                        print(f"🔍 DEBUG: Added product from DIRECT advanced matching")
                                        continue
                                else:
                                    print(f"🔍 DEBUG: DIRECT Advanced matching found no matches")
                            else:
                                print(f"🔍 DEBUG: No sheet cache for DIRECT advanced matching")
                        except Exception as direct_advanced_error:
                            print(f"🔍 DEBUG: DIRECT Advanced matching error: {direct_advanced_error}")
                        
                        print(f"🔍 DEBUG: No products found by any matching method - SKIPPING PRODUCT (no fallback to JSON names)")
                        continue
                except Exception as main_match_error:
                    logging.warning(f"Error in comprehensive matching logic: {main_match_error}")
                    print(f"🔍 DEBUG: Comprehensive matching error: {main_match_error}")
                    import traceback
                    print(f"🔍 DEBUG: Comprehensive matching traceback: {traceback.format_exc()}")
                
                # FALLBACK: Old matching logic if comprehensive matching fails
                best_score = 0.0
                best_match = None
                match_source = None
                db_match = None
                excel_match = None
                excel_score = 0.0
                db_score = 0.0
                
                # PRIORITY 1: Try Product Database (always try this)
                try:
                    import os
                    from .product_database import ProductDatabase
                    product_db = ProductDatabase()
                    
                    # DEBUG: Check database status
                    print(f"🔍 DEBUG: Database path: {product_db.db_path}")
                    print(f"🔍 DEBUG: Database exists: {os.path.exists(product_db.db_path) if hasattr(product_db, 'db_path') else 'Unknown'}")
                    
                    # Initialize database if needed
                    product_db.init_database()
                    
                    # DEBUG: Check if database has data
                    try:
                        conn = product_db._get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM products")
                        count = cursor.fetchone()[0]
                        print(f"🔍 DEBUG: Database has {count} products")
                    except Exception as db_check_error:
                        print(f"🔍 DEBUG: Database check failed: {db_check_error}")
                    
                    # DEBUG: Log database search parameters
                    print(f"🔍 DEBUG: Searching database for product_name='{product_name}', vendor='{vendor}', product_type='{product_type}', strain='{strain}'")
                    
                    # Try to find a matching product in the database
                    db_match = product_db.find_best_product_match(
                        product_name=product_name,
                        vendor=vendor,
                        product_type=product_type,
                        strain=strain
                    )
                    
                    if db_match:
                        # Calculate score for database match
                        db_score = 70.0  # Base score for database match
                        
                        # Add bonuses for better matches
                        db_name = db_match.get('product_name', '').lower()
                        if product_name.lower() == db_name:
                            db_score += 20.0  # Exact name match
                        elif product_name.lower() in db_name or db_name in product_name.lower():
                            db_score += 15.0  # Contains match
                        
                        # Vendor match bonus
                        if vendor and db_match.get('vendor'):
                            if vendor.lower() == db_match.get('vendor', '').lower():
                                db_score += 10.0
                        
                        # Strain match bonus
                        if strain and db_match.get('product_strain'):
                            if strain.lower() == db_match.get('product_strain', '').lower():
                                db_score += 10.0
                        
                        db_score = min(100.0, db_score)  # Cap at 100
                        logging.info(f"✅ Found Product Database match for '{product_name}': {db_match.get('product_name', 'Unknown')} (score: {db_score:.1f})")
                    else:
                        logging.info(f"📝 No Product Database match found for '{product_name}'")
                        
                except Exception as db_error:
                    logging.warning(f"Error accessing Product Database: {db_error}")
                
                # PRIORITY 2: Try Excel data (always try this if available)
                if self.excel_processor and self.excel_processor.df is not None and self._sheet_cache:
                    df = self.excel_processor.df
                    
                    # CRITICAL FIX: Track Excel matches by product name to prevent duplicates
                    excel_matches_by_name = {}
                    
                    for idx, row in df.iterrows():
                        try:
                            # Get product name from Excel row
                            excel_product_name = str(row.get('Product Name*', '') or row.get('ProductName', '') or row.get('Description', '')).strip().lower()
                            excel_vendor = str(row.get('Vendor', '') or row.get('Vendor/Supplier*', '')).strip().lower()
                            
                            if not excel_product_name:
                                continue
                            
                            # Calculate match score with intelligent product type and naming pattern matching
                            score = 0.0
                            
                            # Get Excel product type for intelligent matching
                            excel_product_type = str(row.get('Product Type*', '') or row.get('ProductType', '')).strip().lower()
                            
                            # Exact name match (highest priority)
                            if product_name.lower() == excel_product_name:
                                score += 100.0
                            
                            # Product type match (very important for accuracy)
                            if product_type and excel_product_type:
                                print(f"🔍 DEBUG: Comparing product types: '{product_type}' vs '{excel_product_type}'")
                                if product_type.lower() == excel_product_type:
                                    score += 80.0  # High bonus for exact product type match
                                    print(f"🔍 DEBUG: Exact product type match: +80.0")
                                elif self._are_product_types_compatible(product_type, excel_product_type):
                                    score += 60.0  # Good bonus for compatible product types
                                    print(f"🔍 DEBUG: Compatible product types: +60.0")
                                else:
                                    score -= 30.0  # Penalty for incompatible product types
                                    print(f"🔍 DEBUG: Incompatible product types: -30.0")
                            
                            # Intelligent naming pattern matching
                            pattern_score = self._calculate_naming_pattern_score(product_name, excel_product_name, product_type)
                            score += pattern_score
                            print(f"🔍 DEBUG: Naming pattern score: {pattern_score}")
                            
                            # Vendor match
                            if vendor and excel_vendor and vendor.lower() == excel_vendor.lower():
                                score += 50.0
                            
                            # Partial name match (only if product types are compatible)
                            if product_type and excel_product_type and self._are_product_types_compatible(product_type, excel_product_type):
                                if product_name.lower() in excel_product_name or excel_product_name in product_name.lower():
                                    score += 40.0
                            
                            # Fuzzy string similarity (only if product types are compatible)
                            if not product_type or not excel_product_type or self._are_product_types_compatible(product_type, excel_product_type):
                                try:
                                    from fuzzywuzzy import fuzz
                                    similarity = fuzz.ratio(product_name.lower(), excel_product_name)
                                    if similarity >= 70:  # Lowered from 80
                                        score += 35.0
                                    elif similarity >= 50:  # Lowered from 60
                                        score += 25.0
                                    elif similarity >= 30:  # Lowered from 40
                                        score += 15.0
                                except ImportError:
                                    # Fallback if fuzzywuzzy is not available
                                    common_chars = sum(1 for c in product_name.lower() if c in excel_product_name.lower())
                                    total_chars = max(len(product_name), len(excel_product_name))
                                    if total_chars > 0:
                                        char_similarity = common_chars / total_chars
                                        if char_similarity >= 0.2:  # Lowered from 0.3
                                            score += 10.0
                            
                            # Store match by product name to prevent duplicates
                            if excel_product_name not in excel_matches_by_name or score > excel_matches_by_name[excel_product_name]['score']:
                                excel_matches_by_name[excel_product_name] = {
                                    'row': row,
                                    'score': score
                                }
                                
                        except Exception as e:
                            logging.debug(f"Error processing Excel row {idx}: {e}")
                            continue
                    
                    # Find the best match from deduplicated Excel matches
                    if excel_matches_by_name:
                        best_excel_match = max(excel_matches_by_name.values(), key=lambda x: x['score'])
                        excel_score = best_excel_match['score']
                        excel_match = best_excel_match['row']
                        logging.info(f"✅ Found Excel match for '{product_name}': {excel_score:.1f}")
                    else:
                        logging.info(f"📝 No Excel match found for '{product_name}'")
                
                # DEBUG: Log matching results
                print(f"🔍 DEBUG: Product '{product_name}' - DB match: {db_match is not None}, Excel match: {excel_match is not None}")
                if db_match:
                    print(f"🔍 DEBUG: DB score: {db_score:.1f}")
                if excel_match is not None and not (hasattr(excel_match, 'empty') and excel_match.empty):
                    print(f"🔍 DEBUG: Excel score: {excel_score:.1f}")
                
                # IMPROVED: Choose the best match between database and Excel
                if db_match and excel_match is not None and not (hasattr(excel_match, 'empty') and excel_match.empty):
                    # Both found - choose the better one
                    # Ensure scores are numbers to avoid Series comparison issues
                    db_score_num = float(db_score) if db_score is not None else 0.0
                    excel_score_num = float(excel_score) if excel_score is not None else 0.0
                    if db_score_num >= excel_score_num:
                        best_match = self._convert_database_match_to_excel_format(db_match)
                        best_score = db_score
                        match_source = 'Product Database Match'
                        logging.info(f"🏆 Using Database match (score: {db_score:.1f} vs Excel: {excel_score:.1f})")
                    else:
                        best_match = excel_match
                        best_score = excel_score_num
                        match_source = 'Excel Match'
                        logging.info(f"🏆 Using Excel match (score: {excel_score_num:.1f} vs Database: {db_score_num:.1f})")
                elif db_match:
                    # Only database match found
                    best_match = self._convert_database_match_to_excel_format(db_match)
                    best_score = db_score
                    match_source = 'Product Database Match'
                    logging.info(f"🏆 Using Database match (score: {db_score:.1f})")
                elif excel_match is not None and not (hasattr(excel_match, 'empty') and excel_match.empty):
                    # Only Excel match found
                    best_match = excel_match
                    best_score = float(excel_score) if excel_score is not None else 0.0
                    match_source = 'Excel Match'
                    logging.info(f"🏆 Using Excel match (score: {best_score:.1f})")
                
                # IMPROVED: Process items with more lenient matching - always create a product
                # Lower thresholds to retain more matches
                best_score_num = float(best_score) if best_score is not None else 0.0
                if best_match is not None and not (hasattr(best_match, 'empty') and best_match.empty) and best_score_num >= 2.0:  # Much more lenient threshold - lowered from 5.0
                    try:
                        # Check if this is a database match
                        if match_source == 'Product Database Match':
                            # Use the database match directly (already converted to Excel format)
                            # This preserves all the proper database values (pricing, etc.)
                            product = best_match.copy()
                            
                            # Only add minimal JSON data that doesn't override database values
                            # Store original JSON product name for reference
                            product['Original JSON Product Name'] = str(item.get("product_name", ""))
                            
                            # Add JSON quantity if available and database doesn't have it
                            current_qty = product.get('Quantity*') if hasattr(product, 'get') else (product['Quantity*'] if hasattr(product, 'index') and 'Quantity*' in product.index else '') if hasattr(product, 'index') else ''
                            if not current_qty and item.get('qty'):
                                product['Quantity*'] = str(item.get('qty'))
                            
                            # Try to extract THC/CBD values from JSON data if database doesn't have them
                            thc_value = product.get('THC test result') if hasattr(product, 'get') else (product['THC test result'] if hasattr(product, 'index') and 'THC test result' in product.index else '') if hasattr(product, 'index') else ''
                            if not thc_value or thc_value == '':
                                # Try multiple sources for THC values
                                thc_value = (item.get('THC test result') or 
                                            item.get('thc') or 
                                            item.get('thc_percent') or 
                                            item.get('thc_percentage') or 
                                            item.get('total_thc') or 
                                            item.get('total_thc_percent'))
                                if thc_value:
                                    product['THC test result'] = str(thc_value)
                                    logging.info(f"🧪 Added THC value from JSON: {thc_value}")
                            
                            cbd_value = product.get('CBD test result') if hasattr(product, 'get') else (product['CBD test result'] if hasattr(product, 'index') and 'CBD test result' in product.index else '') if hasattr(product, 'index') else ''
                            if not cbd_value or cbd_value == '':
                                # Try multiple sources for CBD values
                                cbd_value = (item.get('CBD test result') or 
                                            item.get('cbd') or 
                                            item.get('cbd_percent') or 
                                            item.get('cbd_percentage') or 
                                            item.get('total_cbd') or 
                                            item.get('total_cbd_percent'))
                                if cbd_value:
                                    product['CBD test result'] = str(cbd_value)
                                    logging.info(f"🧪 Added CBD value from JSON: {cbd_value}")
                            
                            # Try to extract from lab_result_data as well
                            lab_result_data = item.get("lab_result_data", {})
                            if lab_result_data:
                                cannabinoids = extract_cannabinoids(lab_result_data)
                                current_thc = product.get('THC test result') if hasattr(product, 'get') else (product['THC test result'] if hasattr(product, 'index') and 'THC test result' in product.index else '') if hasattr(product, 'index') else ''
                                if 'thc' in cannabinoids and (not current_thc or current_thc == ''):
                                    product['THC test result'] = str(cannabinoids['thc'])
                                    logging.info(f"🧪 Added THC value from lab_result_data: {cannabinoids['thc']}")
                                current_cbd = product.get('CBD test result') if hasattr(product, 'get') else (product['CBD test result'] if hasattr(product, 'index') and 'CBD test result' in product.index else '') if hasattr(product, 'index') else ''
                                if 'cbd' in cannabinoids and (not current_cbd or current_cbd == ''):
                                    product['CBD test result'] = str(cannabinoids['cbd'])
                                    logging.info(f"🧪 Added CBD value from lab_result_data: {cannabinoids['cbd']}")
                            
                            # Store original JSON product name for reference
                            original_json_name = str(item.get("product_name", ""))
                            if original_json_name and original_json_name.strip():
                                product['Original JSON Product Name'] = original_json_name
                                # Use the original JSON name as the product name
                                product['Product Name*'] = original_json_name
                                product['displayName'] = original_json_name
                            
                            matched_products.append(product)
                            logging.info(f"✅ Using Product Database match for '{product_name}' with complete database values")
                        else:
                            # Create product object from Excel match
                            product = self._create_product_from_excel_match(best_match, item, global_vendor)
                            # Store original JSON product name for deduplication
                            product['Original JSON Product Name'] = str(item.get("product_name", ""))
                            
                            # Store original JSON product name for reference
                            original_json_name = str(item.get("product_name", ""))
                            if original_json_name and original_json_name.strip():
                                product['Original JSON Product Name'] = original_json_name
                                # Use the original JSON name as the product name
                                product['Product Name*'] = original_json_name
                                product['displayName'] = original_json_name
                            
                            matched_products.append(product)
                            logging.info(f"✅ Found Excel match for '{product_name}' with score {best_score:.1f}")
                    except Exception as e:
                        logging.warning(f"Error creating product from Excel match: {e}")
                        # Create basic product from JSON data
                        product = self._create_product_from_json(item, global_vendor)
                        # Store original JSON product name for deduplication
                        product['Original JSON Product Name'] = str(item.get("product_name", ""))
                        matched_products.append(product)
                        logging.info(f"📝 Created product from JSON data for '{product_name}' (Excel match failed)")
                        
                        # Create new database entry for unmatched JSON tag
                        try:
                            from .product_database import ProductDatabase
                            product_db = ProductDatabase()
                            self._create_database_entry_for_unmatched_json(product, product_db)
                            logging.info(f"🗄️ Created database entry for unmatched JSON product: '{product_name}'")
                        except Exception as db_entry_error:
                            logging.warning(f"Failed to create database entry for '{product_name}': {db_entry_error}")
                else:
                    # IMPROVED: Always create product from JSON data if no match or low score
                    # This ensures all JSON items are included in the results
                    logging.info(f"📝 No good match found for '{product_name}' (best score: {best_score:.1f}) - creating from JSON data")
                    
                    # Try to use partial match data if available
                    if best_match is not None and not (hasattr(best_match, 'empty') and best_match.empty) and best_score_num < 5.0:
                        # Use the partial match but enhance it with JSON data
                        try:
                            if match_source == 'Product Database Match':
                                product = self._convert_database_match_to_excel_format(best_match)
                            else:
                                product = self._create_product_from_excel_match(best_match, item, global_vendor)
                            
                            # Enhance with JSON data
                            self._enhance_product_with_json_data(product, item)
                            logging.info(f"📝 Enhanced partial match with JSON data for '{product_name}' (score: {best_score:.1f})")
                        except Exception as enhance_error:
                            logging.warning(f"Error enhancing partial match: {enhance_error}")
                            product = self._create_product_from_json(item, global_vendor)
                    else:
                        # Create completely new product from JSON data
                        product = self._create_product_from_json(item, global_vendor)
                        logging.info(f"📝 Created new product from JSON data for '{product_name}'")
                    
                    # Store original JSON product name for deduplication
                    original_json_name = str(item.get("product_name", ""))
                    product['Original JSON Product Name'] = original_json_name
                    
                    # Make each JSON item unique by adding a unique identifier
                    if original_json_name and original_json_name.strip():
                        unique_id = f"{original_json_name}_{i+1:03d}"  # Add item index for uniqueness
                        product['Product Name*'] = unique_id
                        product['displayName'] = unique_id
                    
                    matched_products.append(product)
                    
                    # Create new database entry for unmatched JSON tag
                    try:
                        from .product_database import ProductDatabase
                        product_db = ProductDatabase()
                        self._create_database_entry_for_unmatched_json(product, product_db)
                        logging.info(f"🗄️ Created database entry for unmatched JSON product: '{product_name}'")
                    except Exception as db_entry_error:
                        logging.warning(f"Failed to create database entry for '{product_name}': {db_entry_error}")
            
            # CRITICAL FIX: Deduplicate by product name - keep only the best match for each unique product
            def _score_of(p: dict) -> float:
                for k in ['overall_score', 'fuzzy_score', 'comprehensive_score', 'partial_score', 'score']:
                    v = p.get(k)
                    if isinstance(v, (int, float)):
                        return float(v)
                return 0.0

            # Group products by their final product name and keep only the best match
            product_groups = {}
            for p in matched_products:
                product_name = str(p.get('Product Name*', '') or '').strip()
                if product_name:
                    if product_name not in product_groups or _score_of(p) > _score_of(product_groups[product_name]):
                        product_groups[product_name] = p
                        logging.info(f"✅ Kept best match for '{product_name}' (score: {_score_of(p):.1f})")
                    else:
                        existing_score = _score_of(product_groups[product_name])
                        logging.info(f"⚠️  Skipped duplicate '{product_name}' (score: {_score_of(p):.1f} <= {existing_score:.1f})")
            
            matched_products = list(product_groups.values())
            logging.info(f"CRITICAL FIX: Deduplicated to {len(matched_products)} unique products from {len(matched_products) + sum(1 for _ in product_groups if len(product_groups) > 1)} total matches")
                
            logging.info(f"CRITICAL FIX: After deduplication: {len(matched_products)} unique products")
            logging.info(f"CRITICAL FIX: Input items: {len(items)}, Processed items: {len(unique_items)}, Final products: {len(matched_products)}")
            
            # Verify that we have reasonable number of products
            if len(matched_products) > len(unique_items):
                logging.warning(f"⚠️  WARNING: More products ({len(matched_products)}) than input items ({len(unique_items)}) - duplicates may still exist")
            else:
                logging.info(f"✅ SUCCESS: {len(matched_products)} unique products created from {len(unique_items)} input items")
            
            # CRITICAL FIX: Removed auto-fallback that loads all DB products
            # This was causing the system to return 24,831 products instead of vendor-filtered matches
            # Now we only return the actual matched products, even if there are few matches
            logging.info(f"✅ FINAL RESULT: {len(matched_products)} products matched from JSON data (no auto-fallback to all DB products)")
            
            # Log vendor distribution for debugging
            if matched_products:
                vendor_counts = {}
                for product in matched_products:
                    vendor = product.get('Vendor/Supplier*', product.get('Vendor', 'Unknown'))
                    vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                
                logging.info(f"📊 Vendor distribution: {dict(list(vendor_counts.items())[:5])}")  # Show first 5 vendors

            # Store matched products for later use
            self.json_matched_names = [p.get('Product Name*', '') for p in matched_products if p.get('Product Name*')]
            
            return matched_products

        except Exception as e:
            logging.error(f"Error in fetch_and_match: {e}")
            return []
    
    def _create_product_from_excel_match(self, excel_row, json_item, global_vendor):
        """Create a product object from Excel row data, enhanced with JSON data."""
        try:
            # Get quantity from various possible column names
            def safe_row_get(row, key, default=''):
                try:
                    if hasattr(row, 'get') and callable(getattr(row, 'get')):
                        return row.get(key, default)
                    else:
                        return row[key] if key in row.index else default
                except (KeyError, AttributeError, TypeError):
                    return default
            
            quantity = safe_row_get(excel_row, 'Quantity*', '') or safe_row_get(excel_row, 'Quantity Received*', '') or safe_row_get(excel_row, 'Quantity', '') or ''
            
            # Get formatted weight with units
            weight_raw = safe_row_get(excel_row, 'Weight*', '')
            weight_with_units = weight_raw
            if weight_raw and safe_row_get(excel_row, 'Units'):
                weight_with_units = f"{weight_raw} {safe_row_get(excel_row, 'Units')}"
            
            # Use the dynamically detected product name column
            product_name_col = 'Product Name*'
            if product_name_col not in excel_row.index:
                possible_cols = ['ProductName', 'Product Name', 'Description']
                product_name_col = next((col for col in possible_cols if col in excel_row.index), 'Description')
            
            # Safely extract product name
            try:
                if hasattr(excel_row, 'get') and callable(getattr(excel_row, 'get')):
                    product_name = excel_row.get(product_name_col, '') or excel_row.get('Description', '') or 'Unnamed Product'
                else:
                    product_name = excel_row[product_name_col] if product_name_col in excel_row.index else ''
                    # Convert to string to avoid Series ambiguity
                    product_name = str(product_name) if product_name is not None else ''
                    if not product_name and 'Description' in excel_row.index:
                        product_name = str(excel_row['Description']) if excel_row['Description'] is not None else ''
                # Convert to string to avoid Series ambiguity
                product_name = str(product_name) if product_name is not None else ''
                if not product_name:
                    product_name = 'Unnamed Product'
            except Exception as e:
                logging.warning(f"Error extracting product name: {e}")
                product_name = 'Unnamed Product'
            
            # Helper function to safely get values
            def safe_get_value(value, default=''):
                if value is None:
                    return default
                if isinstance(value, pd.Series):
                    if pd.isna(value).any():
                        return default
                    value = value.iloc[0] if len(value) > 0 else default
                elif pd.isna(value):
                    return default
                str_value = str(value).strip()
                if str_value.lower() in ['nan', 'inf', '-inf']:
                    return default
                return str_value
            
            # Sanitize lineage - use intelligent defaults based on product type
            lineage = str(safe_row_get(excel_row, 'Lineage', '') or '').strip().upper()
            if not lineage or lineage not in ['SATIVA', 'INDICA', 'HYBRID', 'HYBRID/SATIVA', 'HYBRID/INDICA', 'CBD', 'MIXED', 'PARAPHERNALIA']:
                # Use intelligent lineage assignment based on product type
                product_type = str(safe_row_get(excel_row, 'Product Type*', '') or '').strip()
                lineage = self._get_default_lineage_for_product_type(product_type)
            
            # Use global vendor from JSON if available, otherwise use Excel vendor
            vendor_value = global_vendor if global_vendor else safe_get_value(safe_row_get(excel_row, 'Vendor', ''))
            
            # Clean product name - preserve the actual product name
            def clean_product_name(name):
                if not name:
                    return name
                import re
                # Only remove obvious suffixes that are clearly not part of the product name
                cleaned = re.sub(r'\s*by\s+Dabstract\s+JSON\s*$', '', name, flags=re.IGNORECASE)
                # Remove extra whitespace but preserve the actual product name
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip()
            
            original_name = safe_get_value(product_name)
            cleaned_product_name = clean_product_name(original_name)
            
            # Use simple display name to avoid deduplication issues
            comprehensive_display_name = cleaned_product_name
            
            # Create the product object
            product = {
                'Product Name*': cleaned_product_name,
                'Vendor': vendor_value,
                'Vendor/Supplier*': vendor_value,
                'Product Brand': safe_get_value(safe_row_get(excel_row, 'Product Brand', '')),
                'Lineage': lineage,
                'Product Type*': safe_get_value(safe_row_get(excel_row, 'Product Type*', '')),
                'Weight*': safe_get_value(weight_with_units),
                'Weight': safe_get_value(weight_with_units),
                'WeightWithUnits': safe_get_value(weight_with_units),
                'Quantity*': safe_get_value(quantity),
                'Quantity': safe_get_value(quantity),
                'displayName': comprehensive_display_name,
                'Price': safe_get_value(safe_row_get(excel_row, 'Price', '')),
                'Product Strain': safe_get_value(safe_row_get(excel_row, 'Product Strain', '')),
                'Units': safe_get_value(safe_row_get(excel_row, 'Units', '')),
                'Description': safe_get_value(safe_row_get(excel_row, 'Description', product_name)),
                'Ratio': safe_get_value(safe_row_get(excel_row, 'Ratio', '')),
                'Ratio_or_THC_CBD': safe_get_value(safe_row_get(excel_row, 'Ratio_or_THC_CBD', '')),
                'CombinedWeight': safe_get_value(safe_row_get(excel_row, 'CombinedWeight', weight_raw)),
                'Description_Complexity': safe_get_value(safe_row_get(excel_row, 'Description_Complexity', '1')),
                'JointRatio': safe_get_value(safe_row_get(excel_row, 'JointRatio', weight_with_units)),
                'Test result unit (% or mg)': safe_get_value(safe_row_get(excel_row, 'Test result unit (% or mg)', '')),
                'THC test result': safe_get_value(safe_row_get(excel_row, 'THC test result', '')),
                'CBD test result': safe_get_value(safe_row_get(excel_row, 'CBD test result', '')),
                'Source': "JSON Match"  # Mark as JSON matched item
            }
            
            # Add any additional fields from JSON that might be useful
            if json_item.get('strain'):
                product['Product Strain'] = json_item.get('strain')
            if json_item.get('brand'):
                product['Product Brand'] = json_item.get('brand')
            if json_item.get('inventory_type'):
                raw_type = map_inventory_type_to_product_type(
                    json_item.get('inventory_type'),
                    json_item.get('inventory_category'),
                    product_name
                )
                # Apply product name-based overrides
                product['Product Type*'] = self._apply_product_name_overrides(
                    raw_type, 
                    product_name, 
                    json_item
                )
            
            return product
            
        except Exception as e:
            logging.error(f"Error creating product from Excel match: {e}")
            # Fallback to JSON-only product
            return self._create_product_from_json(json_item, global_vendor)
    
    def _convert_database_match_to_excel_format(self, db_match):
        """Convert a database match to Excel format for consistent processing."""
        try:
            # Handle both dictionary and pandas Series inputs
            if hasattr(db_match, 'get') and callable(getattr(db_match, 'get')):
                # It's a dictionary-like object
                get_func = db_match.get
            else:
                # It's a pandas Series or other object - use safe access
                def get_func(key, default=''):
                    try:
                        if hasattr(db_match, 'index') and key in db_match.index:
                            return db_match[key]
                        return default
                    except (KeyError, AttributeError, TypeError):
                        return default
            
            # Convert database match to Excel row format
            excel_row = {
                'Product Name*': get_func('Product Name*', ''),
                'ProductName': get_func('ProductName', ''),
                'Description': get_func('Description', get_func('Product Name*', '')),
                'Product Type*': get_func('Product Type*', ''),
                'Product Brand': get_func('Product Brand', ''),
                'Vendor/Supplier*': get_func('Vendor/Supplier*', ''),
                'Product Strain': get_func('Product Strain', ''),
                'Lineage': get_func('Lineage', ''),
                'Weight*': get_func('Weight*', ''),
                'Units': get_func('Units', ''),
                'Price': get_func('Price', ''),
                'Quantity*': get_func('Quantity*', ''),
                'DOH': get_func('DOH', ''),
                'State': get_func('State', 'active'),
                'Is Sample? (yes/no)': get_func('Is Sample?', 'no'),
                'Is MJ product?(yes/no)': get_func('Is MJ product?', 'yes'),
                'Discountable? (yes/no)': get_func('Discountable?', 'yes'),
                'Room*': get_func('Room*', 'Default'),
                'Medical Only (Yes/No)': get_func('Medical Only', 'No'),
                'THC test result': get_func('Total THC', ''),
                'CBD test result': get_func('CBDA', ''),
                'Test result unit (% or mg)': get_func('Test result unit (% or mg)', '%'),
                'Source': 'Product Database Match'
            }
            
            # Add any additional fields from the database match
            try:
                if hasattr(db_match, 'items') and callable(getattr(db_match, 'items')):
                    for key, value in db_match.items():
                        if key not in excel_row and value is not None:
                            excel_row[key] = value
                elif hasattr(db_match, 'index'):
                    # It's a pandas Series - iterate over index
                    for key in db_match.index:
                        if key not in excel_row:
                            value = db_match[key]
                            if value is not None:
                                excel_row[key] = value
            except Exception as items_error:
                logging.debug(f"Could not iterate over db_match items: {items_error}")
            
            logging.info(f"✅ Converted database match to Excel format: '{excel_row.get('Product Name*', '')}'")
            return excel_row
            
        except Exception as e:
            logging.error(f"Error converting database match to Excel format: {e}")
            # Return a basic fallback with safe access
            try:
                if hasattr(db_match, 'get') and callable(getattr(db_match, 'get')):
                    product_name = db_match.get('product_name', '')
                else:
                    product_name = db_match.get('product_name', '') if hasattr(db_match, 'get') else str(db_match.get('product_name', '')) if hasattr(db_match, 'get') else 'Unknown Product'
            except:
                product_name = 'Unknown Product'
                
            return {
                'Product Name*': product_name,
                'ProductName': product_name,
                'Description': product_name,
                'Source': 'Product Database Match'
            }

    def _create_product_from_json(self, json_item, global_vendor):
        """Create a product object from JSON data only."""
        try:
            product_name = str(json_item.get("product_name", "")).strip()
            vendor = global_vendor if global_vendor else str(json_item.get("vendor", "")).strip()
            brand = str(json_item.get("brand", "")).strip()
            # Try multiple possible product type columns in order of preference
            # Including Column C:C as requested
            raw_product_type = (
                json_item.get("C") or  # Column C:C as requested
                json_item.get("product_type") or 
                json_item.get("Product Type*") or 
                json_item.get("ProductType") or 
                json_item.get("inventory_type") or 
                json_item.get("inventory_category") or 
                ""
            )
            raw_product_type = str(raw_product_type).strip()
            
            # Apply product name-based overrides to Column C value
            product_type = self._apply_product_name_overrides(raw_product_type, product_name, json_item)
            
            # Log product type source for debugging
            if product_type:
                logging.info(f"🏷️ Found product type '{product_type}' for '{product_name}' from JSON data")
            else:
                logging.warning(f"⚠️ No product type found in JSON data for '{product_name}' - will use inference/mapping")
            weight = str(json_item.get("unit_weight", json_item.get("weight", ""))).strip()
            units = str(json_item.get("unit_weight_uom", json_item.get("unit_of_measure", "g"))).strip()
            strain = str(json_item.get("strain_name", json_item.get("strain", ""))).strip()
            
            # Enhanced inference from similar database matches
            inferred_data = self._infer_from_similar_database_matches(
                product_name, vendor, brand, product_type, strain, weight
            )
            
            # ENHANCED STRAIN EXTRACTION: If no strain in JSON, try to find in database
            if not strain and product_name:
                # First try to extract strain from product name
                extracted_strain = self._extract_strain_from_product_name(product_name)
                if extracted_strain:
                    strain = extracted_strain
                    logging.info(f"🧬 Extracted strain '{strain}' from product name '{product_name}' for unmatched JSON entry")
                else:
                    # Try to find strain in database by searching for similar product names
                    try:
                        from .product_database import ProductDatabase
                        product_db = ProductDatabase()
                        db_strain = self._find_strain_in_database(product_name, product_db)
                        if db_strain:
                            strain = db_strain
                            logging.info(f"🗄️ Found strain '{strain}' in database for product '{product_name}'")
                    except Exception as db_error:
                        logging.warning(f"Failed to search database for strain: {db_error}")
            
            # Clean product name - preserve the actual product name from JSON
            def clean_product_name(name):
                if not name:
                    return name
                import re
                # Replace "Vaporizer" with "Disposable Vape"
                cleaned = re.sub(r'\bVaporizer\b', 'Disposable Vape', name, flags=re.IGNORECASE)
                # Only remove obvious suffixes that are clearly not part of the product name
                cleaned = re.sub(r'\s*by\s+Dabstract\s+JSON\s*$', '', cleaned, flags=re.IGNORECASE)
                # Remove extra whitespace but preserve the actual product name
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip()
            
            # Use the actual product name from JSON, with minimal cleaning
            cleaned_product_name = clean_product_name(product_name)
            
            # Log the cleaning process for debugging
            if product_name and product_name != cleaned_product_name:
                logging.info(f"🧹 Cleaned product name: '{product_name}' → '{cleaned_product_name}'")
            
            # If cleaning removed too much, use the original name
            if not cleaned_product_name or len(cleaned_product_name) < 3:
                cleaned_product_name = product_name
                logging.info(f"⚠️ Using original product name due to insufficient cleaning: '{product_name}'")
            
            # Use simple display name to avoid deduplication issues
            comprehensive_display_name = cleaned_product_name
            
            # Use inferred data from similar database matches, with fallbacks
            final_brand = inferred_data.get('brand') or brand or self._infer_brand_from_name(cleaned_product_name)
            final_product_type = inferred_data.get('product_type') or self._infer_product_type_from_name(cleaned_product_name)
            final_lineage = inferred_data.get('lineage') or self._get_default_lineage_for_product_type(product_type)
            
            # Determine the final product type to use
            raw_final_type = product_type or final_product_type or map_inventory_type_to_product_type(
                json_item.get('inventory_type', ''), 
                json_item.get('inventory_category'),
                product_name
            )
            
            # Apply product name-based overrides to the final product type
            final_assigned_type = self._apply_product_name_overrides(
                raw_final_type, 
                product_name, 
                json_item
            )
            
            # Log the final product type assignment
            if product_type:
                logging.info(f"✅ Using JSON product type '{final_assigned_type}' for '{cleaned_product_name}'")
            elif final_product_type:
                logging.info(f"🔍 Using inferred product type '{final_assigned_type}' for '{cleaned_product_name}'")
            else:
                logging.info(f"🗺️ Using mapped product type '{final_assigned_type}' for '{cleaned_product_name}'")
            
            # ENHANCED: Intelligent price matching with multiple strategies
            final_price = self._intelligently_match_price(
                json_item, 
                inferred_data, 
                cleaned_product_name, 
                final_assigned_type, 
                weight, 
                strain
            )
            final_cost = self._intelligently_match_cost(
                json_item, 
                inferred_data, 
                final_price, 
                cleaned_product_name
            )
            
            # Log inference results for debugging
            if inferred_data.get('brand'):
                logging.info(f"🏷️ Inferred Brand '{final_brand}' from similar database matches for '{cleaned_product_name}'")
            elif final_brand:
                logging.info(f"🔍 Inferred Brand '{final_brand}' from product name '{cleaned_product_name}'")
            else:
                logging.info(f"🏷️ No brand inferred for product name '{cleaned_product_name}' (correctly avoiding strain names)")
                
            if inferred_data.get('product_type'):
                logging.info(f"🔍 Inferred Product Type '{final_product_type}' from similar database matches for '{cleaned_product_name}'")
            elif final_product_type:
                logging.info(f"🔍 Inferred Product Type '{final_product_type}' from product name '{cleaned_product_name}'")
                
            if inferred_data.get('lineage'):
                logging.info(f"🧬 Inferred Lineage '{final_lineage}' from similar database matches for '{cleaned_product_name}'")
            
            # Create weight with units for CombinedWeight
            try:
                weight_value = str(round(float(weight or '1')))
            except (ValueError, TypeError):
                weight_value = '1'
            weight_with_units = f"{weight_value}{units or 'g'}"
            
            # Create the product object
            product = {
                'Product Name*': cleaned_product_name,
                'ProductName': cleaned_product_name,
                'Description': cleaned_product_name,
                'displayName': comprehensive_display_name,
                'Product Type*': final_assigned_type,
                'Product Brand': final_brand or '',
                'Product Strain': strain or 'Unknown Strain',
                'Lineage': final_lineage,
                'Vendor': vendor or 'Unknown Vendor',
                'Price': final_price,
                'Weight*': weight_value,
                'Weight': weight_value,
                'CombinedWeight': weight_with_units,  # CombinedWeight includes units
                'Quantity*': json_item.get('qty', json_item.get('Quantity*', json_item.get('quantity', '1'))),
                'Quantity': json_item.get('qty', json_item.get('Quantity*', json_item.get('quantity', '1'))),
                'Units': units or 'g',
                'THC test result': (json_item.get('THC test result') or 
                                   json_item.get('thc') or 
                                   json_item.get('thc_percent') or 
                                   json_item.get('thc_percentage') or 
                                   json_item.get('total_thc') or 
                                   json_item.get('total_thc_percent') or 
                                   0.0),
                'CBD test result': (json_item.get('CBD test result') or 
                                   json_item.get('cbd') or 
                                   json_item.get('cbd_percent') or 
                                   json_item.get('cbd_percentage') or 
                                   json_item.get('total_cbd') or 
                                   json_item.get('total_cbd_percent') or 
                                   0.0),
                'Test result unit (% or mg)': json_item.get('Test result unit (% or mg)', '%'),
                'State': 'active',
                'Is Sample? (yes/no)': 'no',
                'Is MJ product?(yes/no)': 'yes',
                'Discountable? (yes/no)': 'yes',
                'Room*': 'Default',
                'Medical Only (Yes/No)': 'No',
                'DOH': 'No',
                'Source': 'JSON Match'  # Mark as JSON matched item
            }
            
            # Extract cannabinoid data from lab_result_data if available
            lab_result_data = json_item.get("lab_result_data", {})
            if lab_result_data:
                cannabinoids = extract_cannabinoids(lab_result_data)
                # Update THC and CBD test results with extracted data
                if 'thc' in cannabinoids:
                    product['THC test result'] = cannabinoids['thc']
                if 'cbd' in cannabinoids:
                    product['CBD test result'] = cannabinoids['cbd']
                if 'coa' in cannabinoids:
                    product['COA Link'] = cannabinoids['coa']
            
            # Add any additional fields from the JSON item
            for key, value in json_item.items():
                if key not in product:
                    product[key] = value
            
            # Log the final product for debugging
            logging.info(f"✅ Created JSON product: '{product['Product Name*']}' (Type: {product['Product Type*']}, Brand: {product['Product Brand']})")
            
            return product
            
        except Exception as e:
            logging.error(f"❌ Error creating product from JSON: {e}")
            logging.error(f"❌ JSON item that caused error: {json_item}")
            # Return a basic fallback product
            return {
                'Product Name*': f"JSON Product {hash(str(json_item)) % 1000}",
                'Source': 'JSON Match - Error',
                'Error': str(e)
            }
    
    def _infer_from_similar_database_matches(self, product_name, vendor, brand, product_type, strain, weight):
        """
        Infer brand, lineage, and product type from similar products in the database.
        
        Args:
            product_name: The product name to find similar matches for
            vendor: The vendor name
            brand: The brand name (if any)
            product_type: The product type (if any)
            strain: The strain name (if any)
            weight: The weight (if any)
            
        Returns:
            dict: Dictionary containing inferred brand, lineage, and product_type
        """
        try:
            # Initialize Product Database
            from .product_database import ProductDatabase
            product_db = ProductDatabase()
            
            # Search for similar products using multiple strategies
            similar_products = self._find_similar_products_in_database(
                product_name, vendor, brand, product_type, strain, weight, product_db
            )
            
            if not similar_products:
                logging.debug(f"No similar products found for '{product_name}' in database")
                
                # Fallback: If we have vendor information but no database matches, 
                # use vendor as brand for known cannabis vendors
                if vendor and vendor.lower() not in ['unknown', 'nan', '']:
                    # Known cannabis vendors and their associated brands
                    vendor_brand_mapping = {
                        'trigonal': 'Oleum',  # Trigonal vendor typically uses Oleum brand
                        'oleum': 'Oleum',
                        'dabstract': 'Dabstract',
                        'constellation': 'Constellation Cannabis',
                        'mary jones': 'Mary Jones Cannabis Co',
                        'collections': 'Collections Cannabis',
                        'blue roots': 'Blue Roots Cannabis',
                        'grow op': 'Grow Op Farms',
                        'cloud 9': 'Cloud 9 Farms',
                        'collective': 'The Collective',
                        'fifty fold': 'Fifty Fold',
                        'seattle sluggerz': 'Seattle Sluggerz',
                        'hibro': 'Hibro Wholesale',
                        'core reactor': 'Core Reactor',
                        'diamond knot': 'Diamond Knot',
                        'terp slurper': 'Terp Slurper'
                    }
                    
                    vendor_lower = vendor.lower()
                    if vendor_lower in vendor_brand_mapping:
                        brand = vendor_brand_mapping[vendor_lower]
                        logging.info(f"🎯 Using vendor '{vendor}' → brand '{brand}' (no database matches found)")
                        return {'brand': brand}
                
                return {}
            
            # Analyze similar products to infer missing data
            inferred_data = self._analyze_similar_products_for_inference(similar_products, product_name, vendor)
            
            # ENHANCED: Add price and cost inference with vendor context
            price_cost_data = self._infer_price_and_cost_from_similar_products(
                similar_products, product_name, product_type, weight, vendor
            )
            inferred_data.update(price_cost_data)
            
            if inferred_data:
                logging.info(f"🎯 Inferred data from {len(similar_products)} similar products for '{product_name}': {inferred_data}")
            
            return inferred_data
            
        except Exception as e:
            logging.warning(f"Failed to infer from similar database matches: {e}")
            return {}
    
    def _find_similar_products_in_database(self, product_name, vendor, brand, product_type, strain, weight, product_db):
        """
        Find similar products in the database using multiple search strategies.
        
        Returns:
            list: List of similar product dictionaries
        """
        similar_products = []
        
        try:
            # Strategy 1: Search by product name similarity
            name_similar_products = self._search_by_name_similarity(product_name, product_db)
            similar_products.extend(name_similar_products)
            
            # Strategy 2: Search by vendor + product type
            if vendor and product_type:
                vendor_type_products = self._search_by_vendor_and_type(vendor, product_type, product_db)
                similar_products.extend(vendor_type_products)
            
            # Strategy 2.5: Search by vendor only (to find brand patterns for this vendor)
            if vendor:
                vendor_products = self._search_by_vendor_only(vendor, product_db)
                similar_products.extend(vendor_products)
            
            # Strategy 3: Search by strain name
            if strain:
                strain_products = self._search_by_strain(strain, product_db)
                similar_products.extend(strain_products)
            
            # Strategy 4: Search by brand name
            if brand:
                brand_products = self._search_by_brand(brand, product_db)
                similar_products.extend(brand_products)
            
            # Strategy 5: Search by weight and product type
            if weight and product_type:
                weight_type_products = self._search_by_weight_and_type(weight, product_type, product_db)
                similar_products.extend(weight_type_products)
            
            # Remove duplicates and limit results
            unique_products = []
            seen_ids = set()
            for product in similar_products:
                product_id = product.get('id') or product.get('product_name', '')
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    unique_products.append(product)
            
            # Limit to top 20 most relevant results
            return unique_products[:20]
            
        except Exception as e:
            logging.warning(f"Error finding similar products in database: {e}")
            return []
    
    def _search_by_name_similarity(self, product_name, product_db):
        """Search for products with similar names using fuzzy matching."""
        try:
            import sqlite3
            conn = sqlite3.connect(product_db.db_path)
            
            # Get all products for fuzzy matching
            query = 'SELECT * FROM products WHERE "Product Name*" IS NOT NULL AND "Product Name*" != \'\''
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return []
            
            # Use fuzzy matching to find similar names
            from fuzzywuzzy import process
            matches = process.extract(
                product_name, 
                df['Product Name*'].tolist(), 
                limit=10, 
                scorer=fuzz.token_sort_ratio
            )
            
            # Filter matches with at least 60% similarity
            similar_products = []
            for match_name, score in matches:
                if score >= 60:
                    product_row = df[df['Product Name*'] == match_name].iloc[0]
                    similar_products.append(product_row.to_dict())
            
            return similar_products
            
        except Exception as e:
            logging.warning(f"Error in name similarity search: {e}")
            return []
    
    def _search_by_vendor_and_type(self, vendor, product_type, product_db):
        """Search for products with matching vendor and product type."""
        try:
            import sqlite3
            conn = sqlite3.connect(product_db.db_path)
            
            query = """
                SELECT * FROM products 
                WHERE "Vendor/Supplier*" = ? AND "Product Type*" = ?
                LIMIT 10
            """
            df = pd.read_sql_query(query, conn, params=[vendor, product_type])
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logging.warning(f"Error in vendor+type search: {e}")
            return []
    
    def _search_by_vendor_only(self, vendor, product_db):
        """Search for products with matching vendor to find brand patterns."""
        try:
            import sqlite3
            conn = sqlite3.connect(product_db.db_path)
            
            query = """
                SELECT * FROM products 
                WHERE "Vendor/Supplier*" = ? AND "Product Brand" IS NOT NULL AND "Product Brand" != ''
                LIMIT 15
            """
            df = pd.read_sql_query(query, conn, params=[vendor])
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logging.warning(f"Error in vendor-only search: {e}")
            return []
    
    def _search_by_strain(self, strain, product_db):
        """Search for products with matching strain."""
        try:
            import sqlite3
            conn = sqlite3.connect(product_db.db_path)
            
            # Search in both products and strains tables using correct column names
            query = """
                SELECT p.*, s.canonical_lineage 
                FROM products p
                LEFT JOIN strains s ON p.strain_id = s.id
                WHERE p.product_strain = ? OR s.strain_name = ?
                LIMIT 10
            """
            df = pd.read_sql_query(query, conn, params=[strain, strain])
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logging.warning(f"Error in strain search: {e}")
            return []
    
    def _search_by_brand(self, brand, product_db):
        """Search for products with matching brand."""
        try:
            import sqlite3
            conn = sqlite3.connect(product_db.db_path)
            
            query = """
                SELECT * FROM products 
                WHERE "Product Brand" = ?
                LIMIT 10
            """
            df = pd.read_sql_query(query, conn, params=[brand])
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logging.warning(f"Error in brand search: {e}")
            return []
    
    def _search_by_weight_and_type(self, weight, product_type, product_db):
        """Search for products with similar weight and product type."""
        try:
            import sqlite3
            import re
            
            # Extract numeric weight value
            weight_match = re.search(r'(\d+\.?\d*)', str(weight))
            if not weight_match:
                return []
            
            weight_value = float(weight_match.group(1))
            
            conn = sqlite3.connect(product_db.db_path)
            
            # Search for products with similar weight (within 20% tolerance)
            query = """
                SELECT * FROM products 
                WHERE "Product Type*" = ? AND "Weight*" IS NOT NULL
                LIMIT 20
            """
            df = pd.read_sql_query(query, conn, params=[product_type])
            conn.close()
            
            # Filter by weight similarity
            similar_products = []
            for _, row in df.iterrows():
                row_weight = str(row.get('weight', ''))
                row_weight_match = re.search(r'(\d+\.?\d*)', row_weight)
                if row_weight_match:
                    row_weight_value = float(row_weight_match.group(1))
                    # Check if weights are within 20% of each other
                    if abs(weight_value - row_weight_value) / max(weight_value, row_weight_value) <= 0.2:
                        similar_products.append(row.to_dict())
            
            return similar_products[:10]
            
        except Exception as e:
            logging.warning(f"Error in weight+type search: {e}")
            return []
    
    def _analyze_similar_products_for_inference(self, similar_products, target_product_name, target_vendor=None):
        """
        Analyze similar products to infer missing brand, lineage, and product type.
        
        Args:
            similar_products: List of similar product dictionaries
            target_product_name: The target product name for context
            target_vendor: The target vendor for vendor-based inference
            
        Returns:
            dict: Dictionary with inferred brand, lineage, and product_type
        """
        try:
            inferred_data = {}
            
            # Analyze brands - be smart about vendor-based inference
            brands = []
            vendor_brands = {}  # Track brands by vendor for vendor-based inference
            
            for product in similar_products:
                brand = product.get('brand', '').strip()
                product_vendor = product.get('vendor', '').strip()
                
                if brand and brand.lower() not in ['unknown', 'nan', '']:
                    # Additional validation: don't use strain names as brands
                    brand_lower = brand.lower()
                    strain_indicators = [
                        'gsc', 'wedding', 'blue', 'strawberry', 'jet', 'fuel', 'gelato', 'purple', 'punch',
                        'glazed', 'apricot', 'candy', 'passion', 'fruit', 'rainbow', 'sherbet', 'dream',
                        'honey', 'crystal', 'guava', 'gmo', 'liquid', 'diamond', 'disposable', 'vape',
                        'live', 'resin', 'cartridge', 'og', 'kush', 'haze', 'diesel', 'cookies', 'runtz',
                        'sherbert', 'banana', 'mango', 'pineapple', 'cherry', 'grape', 'lemon', 'lime',
                        'orange', 'apple', 'berry', 'peach', 'plum', 'watermelon', 'mint', 'vanilla',
                        'chocolate', 'coffee', 'caramel', 'sugar', 'sweet', 'cake', 'pie', 'cream'
                    ]
                    
                    # Skip if brand looks like a strain name
                    if not any(strain in brand_lower for strain in strain_indicators):
                        brands.append(brand)
                        
                        # Track brands by vendor for vendor-based inference
                        if product_vendor:
                            if product_vendor not in vendor_brands:
                                vendor_brands[product_vendor] = []
                            vendor_brands[product_vendor].append(brand)
            
            # Smart brand inference logic
            if brands:
                from collections import Counter
                brand_counter = Counter(brands)
                most_common_brand, count = brand_counter.most_common(1)[0]
                
                # Strategy 1: If we have multiple confirmations of the same brand, use it
                if count >= 2:
                    inferred_data['brand'] = most_common_brand
                    logging.info(f"🎯 Inferred brand '{most_common_brand}' from {count} similar products")
                
                # Strategy 2: If we have vendor information and vendor-specific brand patterns
                elif target_vendor and target_vendor in vendor_brands:
                    # Check if the target vendor has a consistent brand pattern
                    vendor_brand_list = vendor_brands[target_vendor]
                    if len(vendor_brand_list) >= 2:  # Need at least 2 products from this vendor
                        vendor_brand_counter = Counter(vendor_brand_list)
                        vendor_most_common, vendor_count = vendor_brand_counter.most_common(1)[0]
                        
                        # If this vendor consistently uses the same brand, infer it
                        if vendor_count >= 2:
                            inferred_data['brand'] = vendor_most_common
                            logging.info(f"🎯 Inferred brand '{vendor_most_common}' from vendor '{target_vendor}' pattern ({vendor_count} products)")
                
                # Strategy 3: If no specific vendor match, try any vendor with consistent brand pattern
                elif not inferred_data.get('brand'):
                    for vendor, vendor_brand_list in vendor_brands.items():
                        if len(vendor_brand_list) >= 3:  # Need at least 3 products for general inference
                            vendor_brand_counter = Counter(vendor_brand_list)
                            vendor_most_common, vendor_count = vendor_brand_counter.most_common(1)[0]
                            
                            # If this vendor consistently uses the same brand, infer it
                            if vendor_count >= 3:
                                inferred_data['brand'] = vendor_most_common
                                logging.info(f"🎯 Inferred brand '{vendor_most_common}' from vendor '{vendor}' pattern ({vendor_count} products)")
                                break
            
            # Analyze product types
            product_types = []
            for product in similar_products:
                ptype = product.get('product_type', '').strip()
                if ptype and ptype.lower() not in ['unknown', 'nan', '']:
                    product_types.append(ptype)
            
            if product_types:
                # Use the most common product type
                from collections import Counter
                type_counter = Counter(product_types)
                most_common_type = type_counter.most_common(1)[0][0]
                inferred_data['product_type'] = most_common_type
            
            # Analyze lineages
            lineages = []
            for product in similar_products:
                lineage = product.get('canonical_lineage', '').strip()
                if lineage and lineage.lower() not in ['unknown', 'nan', '']:
                    lineages.append(lineage)
            
            if lineages:
                # Use the most common lineage
                from collections import Counter
                lineage_counter = Counter(lineages)
                most_common_lineage = lineage_counter.most_common(1)[0][0]
                inferred_data['lineage'] = most_common_lineage
            
            return inferred_data
            
        except Exception as e:
            logging.warning(f"Error analyzing similar products for inference: {e}")
            return {}
    
    def _infer_price_and_cost_from_similar_products(self, similar_products, product_name, product_type, weight, vendor=None):
        """
        Infer price and cost from similar products in the database, prioritizing vendor context.
        
        Args:
            similar_products: List of similar product dictionaries
            product_name: The product name
            product_type: The product type
            weight: The weight
            vendor: The vendor name for context-specific pricing
            
        Returns:
            Dictionary with inferred price and cost
        """
        import re  # Move import to top of function
        
        try:
            inferred_data = {}
            
            # Extract prices and costs from similar products, prioritizing vendor context
            prices = []
            costs = []
            vendor_prices = []
            vendor_costs = []
            
            for product in similar_products:
                # Check if this product is from the same vendor
                product_vendor = product.get('vendor', '').strip().lower()
                is_same_vendor = vendor and product_vendor == vendor.lower()
                
                # Extract price
                price = product.get('price', '').strip()
                if price and price.lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                    # Clean price string (remove $, commas, etc.)
                    price_clean = re.sub(r'[^\d.]', '', price)
                    try:
                        price_float = float(price_clean)
                        if price_float > 0:
                            prices.append(price_float)
                            if is_same_vendor:
                                vendor_prices.append(price_float)
                    except (ValueError, TypeError):
                        pass
                
                # Extract cost
                cost = product.get('cost', '').strip()
                if cost and cost.lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                    # Clean cost string (remove $, commas, etc.)
                    cost_clean = re.sub(r'[^\d.]', '', cost)
                    try:
                        cost_float = float(cost_clean)
                        if cost_float > 0:
                            costs.append(cost_float)
                            if is_same_vendor:
                                vendor_costs.append(cost_float)
                    except (ValueError, TypeError):
                        pass
            
            # Calculate inferred price - prioritize vendor-specific pricing
            if vendor_prices:
                # Use vendor-specific pricing if available
                vendor_prices.sort()
                median_price = vendor_prices[len(vendor_prices) // 2]
                if median_price.is_integer():
                    inferred_data['price'] = f"${int(median_price)}"
                else:
                    inferred_data['price'] = f"${median_price:.2f}"
                logging.info(f"💰 Inferred price ${median_price:.2f} from {len(vendor_prices)} vendor-specific products for '{product_name}' (vendor: {vendor})")
            elif prices:
                # Use all similar products if no vendor-specific data
                prices.sort()
                median_price = prices[len(prices) // 2]
                if median_price.is_integer():
                    inferred_data['price'] = f"${int(median_price)}"
                else:
                    inferred_data['price'] = f"${median_price:.2f}"
                logging.info(f"💰 Inferred price ${median_price:.2f} from {len(prices)} similar products for '{product_name}'")
            else:
                # Fallback to intelligent price estimation based on product type and weight
                estimated_price = self._estimate_price_by_type_and_weight(product_type, weight)
                if estimated_price.is_integer():
                    inferred_data['price'] = f"${int(estimated_price)}"
                else:
                    inferred_data['price'] = f"${estimated_price:.2f}"
                logging.info(f"💰 Estimated price ${estimated_price:.2f} based on type '{product_type}' and weight '{weight}' for '{product_name}'")
            
            # Calculate inferred cost - prioritize vendor-specific pricing
            if vendor_costs:
                # Use vendor-specific cost if available
                vendor_costs.sort()
                median_cost = vendor_costs[len(vendor_costs) // 2]
                if median_cost.is_integer():
                    inferred_data['cost'] = f"${int(median_cost)}"
                else:
                    inferred_data['cost'] = f"${median_cost:.2f}"
                logging.info(f"💵 Inferred cost ${median_cost:.2f} from {len(vendor_costs)} vendor-specific products for '{product_name}' (vendor: {vendor})")
            elif costs:
                # Use all similar products if no vendor-specific data
                costs.sort()
                median_cost = costs[len(costs) // 2]
                if median_cost.is_integer():
                    inferred_data['cost'] = f"${int(median_cost)}"
                else:
                    inferred_data['cost'] = f"${median_cost:.2f}"
                logging.info(f"💵 Inferred cost ${median_cost:.2f} from {len(costs)} similar products for '{product_name}'")
            else:
                # Estimate cost as 60-70% of price (typical wholesale markup)
                price_str = inferred_data.get('price', '$25.00')
                price_clean = re.sub(r'[^\d.]', '', price_str)
                try:
                    price_float = float(price_clean)
                    estimated_cost = price_float * 0.65  # 65% of retail price
                    inferred_data['cost'] = f"${estimated_cost:.2f}"
                    logging.info(f"💵 Estimated cost ${estimated_cost:.2f} as 65% of price for '{product_name}'")
                except (ValueError, TypeError):
                    inferred_data['cost'] = "$16.25"  # Default cost
                    logging.info(f"💵 Using default cost $16.25 for '{product_name}'")
            
            return inferred_data
            
        except Exception as e:
            logging.warning(f"Error inferring price and cost from similar products: {e}")
            return {}
    
    def _intelligently_match_price(self, json_item, inferred_data, product_name, product_type, weight, strain):
        """
        Intelligently match price using multiple strategies in order of preference.
        
        Args:
            json_item: Original JSON data
            inferred_data: Data inferred from similar products
            product_name: Product name
            product_type: Product type
            weight: Product weight
            strain: Product strain
            
        Returns:
            Best matched price as string
        """
        try:
            # Debug: Log all available price sources
            self._debug_price_sources(json_item, inferred_data, product_name)
            
            # Strategy 1: Use price from similar database products (highest confidence)
            if inferred_data.get('price'):
                price = inferred_data['price']
                logging.info(f"💰 Using database-inferred price '{price}' for '{product_name}'")
                return price
            
            # Strategy 2: Use price from JSON data (multiple possible columns)
            json_price = (
                json_item.get('price') or 
                json_item.get('Price') or 
                json_item.get('line_price') or 
                json_item.get('retail_price') or 
                json_item.get('unit_price') or 
                json_item.get('sale_price') or 
                json_item.get('unit_cost') or 
                json_item.get('cost') or 
                json_item.get('Cost') or 
                json_item.get('wholesale_price') or 
                json_item.get('msrp') or 
                json_item.get('list_price') or 
                json_item.get('suggested_price') or 
                json_item.get('market_price') or 
                ''
            )
            
            if json_price and str(json_price).strip().lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                # Clean and validate the price
                import re
                price_clean = re.sub(r'[^\d.]', '', str(json_price))
                try:
                    price_float = float(price_clean)
                    if price_float > 0:
                        if price_float.is_integer():
                            price = f"${int(price_float)}"
                        else:
                            price = f"${price_float:.2f}"
                        logging.info(f"💰 Using JSON price '{price}' for '{product_name}'")
                        return price
                except (ValueError, TypeError):
                    pass
            
            # Strategy 3: Search for similar product names and use average prices
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                similar_products = self._search_similar_product_names(product_name, product_db)
                
                if similar_products:
                    # Calculate average price from similar products
                    prices = []
                    for product in similar_products:
                        price = product.get('price', '').strip()
                        if price and price.lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                            price_clean = re.sub(r'[^\d.]', '', price)
                            try:
                                price_float = float(price_clean)
                                if price_float > 0:
                                    prices.append(price_float)
                            except (ValueError, TypeError):
                                pass
                    
                    if prices:
                        # Use average price from similar products
                        avg_price = sum(prices) / len(prices)
                        if avg_price.is_integer():
                            price = f"${int(avg_price)}"
                        else:
                            price = f"${avg_price:.2f}"
                        logging.info(f"💰 Using average price '{price}' from {len(prices)} similar products for '{product_name}'")
                        return price
            except Exception as e:
                logging.warning(f"Error searching for similar product names: {e}")
            
            # Strategy 4: Use intelligent estimation based on product characteristics
            try:
                estimated_price = self._estimate_price_by_type_and_weight(product_type, weight)
                if estimated_price.is_integer():
                    price = f"${int(estimated_price)}"
                else:
                    price = f"${estimated_price:.2f}"
                logging.info(f"💰 Using estimated price '{price}' for '{product_name}'")
                return price
            except Exception as e:
                logging.warning(f"Error in price estimation: {e}")
            
            # Strategy 5: Simple fallback based on product type only
            fallback_prices = {
                'flower': '$12.00',
                'concentrate': '$30.00', 
                'live resin': '$35.00',
                'cartridge': '$40.00',
                'disposable vape': '$45.00',
                'edible': '$15.00',
                'tincture': '$25.00',
                'topical': '$20.00',
                'pre-roll': '$15.00',
                'vape cartridge': '$40.00'
            }
            
            product_type_lower = str(product_type).lower()
            for type_key, fallback_price in fallback_prices.items():
                if type_key in product_type_lower:
                    logging.info(f"💰 Using fallback price '{fallback_price}' for '{product_name}'")
                    return fallback_price
            
            # Ultimate fallback
            price = '$25.00'
            logging.info(f"💰 Using ultimate fallback price '{price}' for '{product_name}'")
            return price
            
        except Exception as e:
            logging.warning(f"Error in intelligent price matching: {e}")
            return "$25.00"  # Safe fallback
    
    def _intelligently_match_cost(self, json_item, inferred_data, final_price, product_name):
        """
        Intelligently match cost using multiple strategies.
        
        Args:
            json_item: Original JSON data
            inferred_data: Data inferred from similar products
            final_price: The final price that was determined
            product_name: Product name
            
        Returns:
            Best matched cost as string
        """
        try:
            # Strategy 1: Use cost from similar database products (highest confidence)
            if inferred_data.get('cost'):
                cost = inferred_data['cost']
                logging.info(f"💵 Using database-inferred cost '{cost}' for '{product_name}'")
                return cost
            
            # Strategy 2: Use cost from JSON data
            json_cost = (
                json_item.get('cost') or 
                json_item.get('Cost') or 
                json_item.get('wholesale_cost') or 
                json_item.get('unit_cost') or 
                json_item.get('purchase_price') or 
                ''
            )
            
            if json_cost and str(json_cost).strip().lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                # Clean and validate the cost
                import re
                cost_clean = re.sub(r'[^\d.]', '', str(json_cost))
                try:
                    cost_float = float(cost_clean)
                    if cost_float > 0:
                        if cost_float.is_integer():
                            cost = f"${int(cost_float)}"
                        else:
                            cost = f"${cost_float:.2f}"
                        logging.info(f"💵 Using JSON cost '{cost}' for '{product_name}'")
                        return cost
                except (ValueError, TypeError):
                    pass
            
            # Strategy 3: Search for similar product names and use average costs
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                similar_products = self._search_similar_product_names(product_name, product_db)
                
                if similar_products:
                    # Calculate average cost from similar products
                    costs = []
                    for product in similar_products:
                        cost = product.get('cost', '').strip()
                        if cost and cost.lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                            cost_clean = re.sub(r'[^\d.]', '', cost)
                            try:
                                cost_float = float(cost_clean)
                                if cost_float > 0:
                                    costs.append(cost_float)
                            except (ValueError, TypeError):
                                pass
                    
                    if costs:
                        # Use average cost from similar products
                        avg_cost = sum(costs) / len(costs)
                        if avg_cost.is_integer():
                            cost = f"${int(avg_cost)}"
                        else:
                            cost = f"${avg_cost:.2f}"
                        logging.info(f"💵 Using average cost '{cost}' from {len(costs)} similar products for '{product_name}'")
                        return cost
            except Exception as e:
                logging.warning(f"Error searching for similar product costs: {e}")
            
            # Strategy 4: Default cost
            cost = "$16.25"
            logging.info(f"💵 Using default cost '{cost}' for '{product_name}'")
            return cost
            
        except Exception as e:
            logging.warning(f"Error in intelligent cost matching: {e}")
            return "$16.25"  # Safe fallback
    
    def _debug_price_sources(self, json_item, inferred_data, product_name):
        """Debug method to log all available price sources."""
        try:
            logging.info(f"🔍 DEBUG: Price sources for '{product_name}':")
            
            # Check JSON price columns
            price_columns = [
                'price', 'Price', 'line_price', 'retail_price', 'unit_price', 
                'sale_price', 'unit_cost', 'cost', 'Cost', 'wholesale_price',
                'msrp', 'list_price', 'suggested_price', 'market_price'
            ]
            
            json_prices = {}
            for col in price_columns:
                value = json_item.get(col)
                if value and str(value).strip().lower() not in ['unknown', 'nan', '', '0', '$0', '0.00']:
                    json_prices[col] = value
            
            if json_prices:
                logging.info(f"🔍 DEBUG: JSON price columns found: {json_prices}")
            else:
                logging.info(f"🔍 DEBUG: No valid JSON price columns found")
            
            # Check inferred data
            if inferred_data.get('price'):
                logging.info(f"🔍 DEBUG: Inferred price: {inferred_data['price']}")
            else:
                logging.info(f"🔍 DEBUG: No inferred price found")
            
            # Log all JSON keys for debugging
            all_keys = list(json_item.keys())
            logging.info(f"🔍 DEBUG: All JSON keys available: {all_keys}")
            
        except Exception as e:
            logging.warning(f"Error in price source debugging: {e}")
    
    def _apply_product_name_overrides(self, raw_product_type, product_name, json_item):
        """
        Apply product name-based overrides to Column C values.
        
        Args:
            raw_product_type: The original product type from Column C
            product_name: The product name to analyze
            json_item: The full JSON item for context
            
        Returns:
            Modified product type based on product name analysis
        """
        try:
            if not product_name:
                return raw_product_type
            
            product_name_lower = product_name.lower()
            
            # Rule 1: If product name contains vape keywords, prioritize "Vape Cartridge"
            vape_keywords = ['vape', 'cart', 'cartridge', 'disposable', 'pod', 'battery', 'jefe', 'twisted', 'fire', 'pen']
            if any(keyword in product_name_lower for keyword in vape_keywords):
                logging.info(f"🔄 Product name contains vape keywords, overriding '{raw_product_type}' to 'Vape Cartridge' for '{product_name}'")
                return "Vape Cartridge"
            
            # Rule 2: If product name contains concentrate keywords (and no vape keywords)
            # Change Column C value to "Concentrate"
            concentrate_keywords = ['concentrate', 'rosin', 'shatter', 'wax', 'live resin', 'diamonds', 'sauce', 'extract', 'oil', 'distillate']
            if any(keyword in product_name_lower for keyword in concentrate_keywords):
                logging.info(f"🔄 Product name contains concentrate keywords, overriding '{raw_product_type}' to 'Concentrate' for '{product_name}'")
                return "Concentrate"
            
            # Rule 3: If it says "Concentrate for Inhalation" but lacks vape keywords
            # Change to simply "Concentrate"
            if raw_product_type and "concentrate for inhalation" in raw_product_type.lower():
                if not any(keyword in product_name_lower for keyword in vape_keywords):
                    logging.info(f"🔄 'Concentrate for Inhalation' without vape keywords, overriding to 'Concentrate' for '{product_name}'")
                    return "Concentrate"
            
            # No overrides needed, return original
            return raw_product_type
            
        except Exception as e:
            logging.warning(f"Error applying product name overrides: {e}")
            return raw_product_type
    
    def _search_similar_product_names(self, product_name, product_db):
        """
        Search for products with similar names and return their average prices.
        
        Args:
            product_name: Product name to search for
            product_db: ProductDatabase instance
            
        Returns:
            List of similar products with prices
        """
        try:
            from fuzzywuzzy import fuzz
            
            # Get all products from database
            conn = product_db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.*, s.canonical_lineage, s.sovereign_lineage
                FROM products p
                LEFT JOIN strains s ON p.strain_id = s.id
                WHERE p.price IS NOT NULL AND p.price != '' AND p.price != '0' AND p.price != '$0'
                ORDER BY p.last_seen_date DESC
            ''')
            
            all_products = []
            for row in cursor.fetchall():
                product = dict(zip([col[0] for col in cursor.description], row))
                all_products.append(product)
            
            # Find similar products using fuzzy matching
            similar_products = []
            product_name_lower = product_name.lower()
            
            for product in all_products:
                db_name = product.get('product_name', '').lower()
                if db_name:
                    # Calculate similarity score
                    similarity = fuzz.ratio(product_name_lower, db_name)
                    
                    # Also check for partial matches (substring similarity)
                    partial_similarity = fuzz.partial_ratio(product_name_lower, db_name)
                    
                    # Use the higher of the two similarity scores
                    max_similarity = max(similarity, partial_similarity)
                    
                    # Include products with 40% or higher similarity - lowered for better matching
                    if max_similarity >= 40:
                        product['similarity_score'] = max_similarity
                        similar_products.append(product)
            
            # Sort by similarity score (highest first) and limit results
            similar_products.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            # Return top 10 most similar products
            return similar_products[:10]
            
        except Exception as e:
            logging.warning(f"Error searching for similar product names: {e}")
            return []
    
    def _search_exact_product_matches(self, product_name, product_type, strain, product_db):
        """
        Search for exact product matches in the database.
        
        Args:
            product_name: Product name to search for
            product_type: Product type
            strain: Product strain
            product_db: ProductDatabase instance
            
        Returns:
            List of matching products
        """
        try:
            matches = []
            
            # Search by exact product name
            name_matches = product_db.search_products_by_name(product_name)
            matches.extend(name_matches)
            
            # Search by product type and strain combination
            if product_type and strain:
                type_strain_matches = product_db.search_products_by_type_and_strain(product_type, strain)
                matches.extend(type_strain_matches)
            
            # Remove duplicates based on product name
            seen_names = set()
            unique_matches = []
            for match in matches:
                name = match.get('product_name', '')
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_matches.append(match)
            
            return unique_matches
            
        except Exception as e:
            logging.warning(f"Error searching for exact product matches: {e}")
            return []

    def _estimate_price_by_type_and_weight(self, product_type, weight):
        """
        Estimate price based on product type and weight.
        
        Args:
            product_type: The product type
            weight: The weight
            
        Returns:
            Estimated price as float
        """
        try:
            # Extract weight value
            import re
            weight_clean = re.sub(r'[^\d.]', '', str(weight))
            weight_float = float(weight_clean) if weight_clean else 1.0
            
            # Base prices per unit by product type (more realistic)
            base_prices = {
                'flower': 12.0,          # $12 for flower (typical 1g)
                'concentrate': 30.0,     # $30 for concentrates (typical 1g)
                'live resin': 35.0,      # $35 for live resin (typical 1g)
                'cartridge': 40.0,       # $40 for cartridges (typical 1g)
                'disposable vape': 45.0, # $45 for disposables (typical 1g)
                'edible': 15.0,          # $15 for edibles (typical 10mg)
                'tincture': 25.0,        # $25 for tinctures (typical 1oz)
                'topical': 20.0,         # $20 for topicals (typical 1oz)
                'pre-roll': 15.0,        # $15 for pre-rolls (typical 1g)
                'vape cartridge': 40.0,  # $40 for vape cartridges (typical 1g)
            }
            
            # Find matching product type
            product_type_lower = str(product_type).lower()
            base_price = 25.0  # Default price
            
            for type_key, price in base_prices.items():
                if type_key in product_type_lower:
                    base_price = price
                    break
            
            # Calculate total price based on weight and product type
            weight_str = str(weight).lower()
            
            # Special handling for different product types and units
            if 'edible' in product_type_lower:
                if 'mg' in weight_str:
                    # For edibles in mg, use base price (already per 10mg)
                    total_price = base_price
                elif 'g' in weight_str:
                    # For edibles in grams, convert to mg (1g = 1000mg, so 100x 10mg servings)
                    total_price = base_price * (weight_float * 100)
                else:
                    total_price = base_price
            elif 'tincture' in product_type_lower or 'topical' in product_type_lower:
                # For tinctures/topicals, weight doesn't significantly affect price
                total_price = base_price
            elif 'flower' in product_type_lower:
                # For flower, use a more reasonable weight calculation
                if weight_float <= 1.0:
                    total_price = base_price  # $12 for 1g
                elif weight_float <= 3.5:
                    total_price = base_price * 2.5  # $30 for 3.5g (eighth)
                else:
                    total_price = base_price * min(weight_float, 4.0)  # Cap at 4g
            else:
                # For other products, multiply by weight but cap the multiplier
                weight_multiplier = min(weight_float, 3.0)  # Cap at 3x for very large weights
                total_price = base_price * weight_multiplier
            
            # Apply reasonable bounds
            total_price = max(8.0, min(80.0, total_price))  # Between $8 and $80
            
            return total_price
            
        except Exception as e:
            logging.warning(f"Error estimating price by type and weight: {e}")
            return 25.0  # Default fallback price
            
    def fetch_and_match_with_product_db(self, url: str) -> List[Dict]:
        """
        Fetch JSON from URL and create product tags, prioritizing Product Database lookups
        over exact JSON wording. This method first tries to find existing products in the
        database before creating new ones from JSON data.
        
        Args:
            url: URL to fetch JSON data from
            
        Returns:
            List of product dictionaries
        """
        logging.debug(f"fetch_and_match_with_product_db called with URL: {url}")
        if not url.lower().startswith("http"):
            raise ValueError("Please provide a valid HTTP URL")
            
        try:
            # Initialize Product Database for priority lookups
            logging.info("Initializing Product Database for priority lookups...")
            try:
                product_db = ProductDatabase()
                logging.info("Product Database initialized successfully")
            except Exception as e:
                logging.warning(f"Could not initialize Product Database: {e}")
                product_db = None
            
            # Use the proxy endpoint to handle authentication and CORS
            import requests
            
            # Prepare headers for the request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add authentication headers if available
            import os
            if os.environ.get('BAMBOO_API_KEY'):
                headers['X-API-Key'] = os.environ.get('BAMBOO_API_KEY')
            if os.environ.get('BAMBOO_AUTH_TOKEN'):
                headers['Authorization'] = f"Bearer {os.environ.get('BAMBOO_AUTH_TOKEN')}"
            if os.environ.get('BAMBOO_SESSION_TOKEN'):
                headers['X-Session-Token'] = os.environ.get('BAMBOO_SESSION_TOKEN')
            
            proxy_data = {
                'url': url,
                'headers': headers
            }
            
            # Try to make the request directly first (for external URLs)
            try:
                response = requests.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                payload = response.json()
            except (requests.exceptions.RequestException, ValueError) as direct_error:
                logging.info(f"Direct request failed, trying proxy: {direct_error}")
                # Fallback to proxy endpoint if direct request fails
                import os
                base_url = os.environ.get('FLASK_BASE_URL', 'http://127.0.0.1:5001')
                response = requests.post(f'{base_url}/api/proxy-json', 
                                       json=proxy_data, 
                                       timeout=60)
                response.raise_for_status()
                payload = response.json()
                
            # Handle both list and dictionary payloads
            if isinstance(payload, list):
                items = payload
            elif isinstance(payload, dict):
                items = payload.get("inventory_transfer_items", [])
                # Extract global vendor from document metadata
                global_vendor = payload.get("from_license_name", "")
                logging.info(f"Extracted global vendor from document: {global_vendor}")
            else:
                logging.warning(f"Unexpected payload type: {type(payload)}")
                return []
                
            if not items:
                logging.warning("No inventory transfer items found in JSON")
                return []
                
            # CRITICAL FIX: Preserve ALL items from JSON - no deduplication
            logging.info(f"Processing {len(items)} JSON items with Product Database priority - preserving ALL items as requested")
            
            unique_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                product_name = str(item.get("product_name", "")).strip()
                
                # CRITICAL FIX: Process ALL items, even those with missing product names
                if not product_name:
                    # Try to create a fallback product name from other available fields
                    vendor = str(item.get("vendor", "")).strip()
                    brand = str(item.get("brand", "")).strip()
                    weight = str(item.get("weight", "")).strip()
                    product_type = str(item.get("inventory_type", "")).strip()
                    
                    # Create a fallback product name
                    fallback_parts = []
                    if brand:
                        fallback_parts.append(brand)
                    if product_type:
                        fallback_parts.append(product_type)
                    if weight:
                        fallback_parts.append(weight)
                    
                    if fallback_parts:
                        product_name = " ".join(fallback_parts)
                    else:
                        product_name = f"JSON Product {len(unique_items) + 1}"
                    
                    logging.info(f"⚠️  Created fallback product name: '{product_name}' for JSON item with missing name")
                
                # Add ALL items without any deduplication - each item gets its own label
                unique_items.append(item)
            
            logging.info(f"CRITICAL FIX: Processed {len(items)} items -> {len(unique_items)} products (ALL preserved)")
            
            # Use all items for processing (no deduplication)
            items = unique_items
            
            # Initialize tracking variables
            matched_idxs = set()
            match_scores = {}
            all_tags = []
            processed_count = 0
            matched_count = 0
            db_lookup_count = 0
            educated_guess_count = 0
            new_product_count = 0
            new_database_entries_count = 0
            
            # Helper function to clean product names
            def clean_product_name(name):
                if not name:
                    return name
                import re
                # Only remove obvious suffixes that are clearly not part of the product name
                cleaned = re.sub(r'\s*by\s+Dabstract\s+JSON\s*$', '', name, flags=re.IGNORECASE)
                # Remove extra whitespace but preserve the actual product name
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip()
            
            # Performance monitoring
            start_time = time.time()
            
            for i, item in enumerate(items):
                try:
                    # Safety check: ensure item is a dictionary
                    if not isinstance(item, dict):
                        logging.warning(f"Item {i+1} is not a dictionary (type: {type(item)}), skipping: {item}")
                        continue
                    
                    # Enhanced product information extraction using new database columns
                    original_product_name = str(item.get("product_name", "")).strip()
                    product_name = original_product_name  # Will be replaced with matched database name if found
                    logging.debug(f"Processing product: {product_name}")
                    # CRITICAL FIX: Don't skip items with missing product names - create fallback names
                    if not product_name:
                        # Try to create a fallback product name from other available fields
                        vendor = str(item.get("vendor", "")).strip()
                        brand = str(item.get("brand", "")).strip()
                        inventory_type = str(item.get("inventory_type", "")).strip()
                        
                        # Create a descriptive fallback name
                        fallback_parts = []
                        if brand:
                            fallback_parts.append(brand)
                        if inventory_type:
                            fallback_parts.append(inventory_type)
                        if vendor:
                            fallback_parts.append(f"by {vendor}")
                        
                        if fallback_parts:
                            product_name = " ".join(fallback_parts)
                            logging.info(f"⚠️  Created fallback product name: '{product_name}' for item missing product_name")
                        else:
                            product_name = f"JSON Product {len(all_tags)+1}"
                            logging.info(f"⚠️  Created generic product name: '{product_name}' for item missing product_name")
                        
                    # Use global vendor from document metadata (already set above)
                    vendor = global_vendor if global_vendor else str(item.get("vendor", "")).strip()
                    
                    # PRIORITY 1: Use comprehensive matching logic (same as Excel) with AI tools
                    try:
                        # Use the same comprehensive matching logic that was working in the debug output
                        print(f"🔍 DEBUG: Trying comprehensive matching for '{product_name}' (type: {product_type})")
                        matched_products = self._process_item_with_main_matching(item, product_name, vendor, product_type, strain, global_vendor)
                        print(f"🔍 DEBUG: Comprehensive matching returned {len(matched_products)} products")
                        if matched_products:
                            for product in matched_products:
                                tag = self._create_tag_from_product(product, item, global_vendor)
                                all_tags.append(tag)
                                matched_count += 1
                            print(f"🔍 DEBUG: Added {len(matched_products)} tags from comprehensive matching")
                            continue  # Skip the educated guess and JSON processing below
                        else:
                            print(f"🔍 DEBUG: No products found by comprehensive matching, falling back to AI-powered database lookup")
                    except Exception as main_match_error:
                        logging.warning(f"Error in comprehensive matching logic: {main_match_error}")
                        print(f"🔍 DEBUG: Comprehensive matching error: {main_match_error}")
                    
                    # PRIORITY 2: Fallback to AI-Powered Product Database lookup if comprehensive matching fails
                    db_info = None
                    if product_db:
                        try:
                            logging.debug(f"Attempting AI-Powered Product Database lookup for: {product_name}")
                            
                            # Initialize AI matcher if not already done
                            if not hasattr(self, 'ai_matcher'):
                                self.ai_matcher = AIProductMatcher(product_db)
                                logging.info("✅ AI Product Matcher initialized")
                            
                            # First try to find the product directly
                            db_info = product_db.get_product_info(product_name, vendor)
                            
                            if not db_info:
                                # Use AI-powered matching to find the best strain match
                                logging.debug(f"Using AI matcher to find best strain match for: {product_name}")
                                
                                # Extract product features for AI matching
                                product_features = self.ai_matcher.extract_product_features(item)
                                
                                # Find best matches using AI scoring
                                matches = self.ai_matcher.find_best_matches(product_features, max_matches=3)
                                
                                if matches:
                                    best_match = matches[0]
                                    logging.info(f"🤖 AI Matcher found {len(matches)} potential matches")
                                    logging.info(f"   Best match: {best_match.strain_name} (confidence: {best_match.confidence}, score: {best_match.total_score:.3f})")
                                    
                                    # Get strain info for the best match
                                    strain_info = product_db.get_strain_info(best_match.strain_name)
                                    if strain_info:
                                        # Extract weight from product name if available
                                        weight_match = re.search(r'/(\d+)g', product_name)
                                        extracted_weight = weight_match.group(1) if weight_match else "1"
                                        
                                        # Create description in the format: "Strain Name Core Flower - Weight"
                                        # This follows the user's requirement for "Golden Pineapple Core Flower - 14g"
                                        formatted_description = f"{best_match.strain_name} Core Flower - {extracted_weight}g"
                                        
                                        db_info = {
                                            'product_name': product_name,
                                            'vendor': vendor,
                                            'strain_name': best_match.strain_name,
                                            'lineage': strain_info.get('canonical_lineage', 'HYBRID'),
                                            'product_type': product_features.get('product_type', 'Core Flower'),
                                            'price': '25',  # Default price
                                            'weight': extracted_weight,
                                            'units': 'g',
                                            'description': formatted_description,  # Use proper tag format
                                            'ai_match_score': best_match.total_score,
                                            'ai_confidence': best_match.confidence,
                                            'ai_match_type': best_match.match_type,
                                        }
                                        
                                        # Log AI matching details
                                        match_summary = self.ai_matcher.get_match_summary(matches)
                                        logging.info(f"🤖 AI Match Summary for '{product_name}':")
                                        logging.info(f"   Strain: {best_match.strain_name}")
                                        logging.info(f"   Confidence: {best_match.confidence}")
                                        logging.info(f"   Score: {best_match.total_score:.3f}")
                                        logging.info(f"   Match Type: {best_match.match_type}")
                                        logging.info(f"   Score Breakdown: {match_summary['score_breakdown']}")
                                        
                                        logging.info(f"✅ AI-Powered Strain Database match found for: {best_match.strain_name} -> {strain_info.get('canonical_lineage', 'HYBRID')}")
                            
                            if db_info:
                                db_lookup_count += 1
                                logging.info(f"✅ Product/Strain Database match found for: {product_name}")
                                # Use database info to override JSON data
                                product_name = db_info.get("product_name", product_name)
                                vendor = db_info.get("vendor", vendor)
                                brand = db_info.get("brand", "")
                                product_type = db_info.get("product_type", "")
                                strain = db_info.get("strain_name", "")
                                lineage = db_info.get("lineage", "")
                                price = str(db_info.get("price", ""))
                                weight = str(db_info.get("weight", ""))
                                units = str(db_info.get("units", ""))
                                description = db_info.get("description", "")
                                
                                # Create tag using database information - prioritize description over product name
                                tag = self._create_tag_from_database_info(db_info, vendor)
                                all_tags.append(tag)
                                matched_count += 1
                                continue  # Skip JSON processing since we have database info
                            else:
                                logging.debug(f"No Product/Strain Database match found for: {product_name}, proceeding with JSON processing")
                        except Exception as db_error:
                            logging.warning(f"Product Database lookup error for '{product_name}': {db_error}")
                    
                    # PRIORITY 3: Try educated guessing if no database match
                    educated_guess = None
                    if product_db:
                        try:
                            logging.info(f"🔍 Attempting educated guess for: {product_name}")
                            logging.info(f"   Vendor: {vendor}")
                            logging.info(f"   Brand: {brand}")
                            educated_guess = product_db.make_educated_guess(product_name, vendor, brand)
                            if educated_guess:
                                logging.info(f"✅ Made educated guess for '{product_name}': {educated_guess}")
                                # Use educated guess data
                                product_name = educated_guess.get("product_name", product_name)
                                vendor = educated_guess.get("vendor", vendor)
                                brand = educated_guess.get("brand", brand or "")
                                product_type = educated_guess.get("product_type", "")
                                strain = educated_guess.get("strain_name", "")
                                lineage = educated_guess.get("lineage", "")
                                price = str(educated_guess.get("price", ""))
                                weight = str(educated_guess.get("weight", ""))
                                units = str(educated_guess.get("units", ""))
                                description = educated_guess.get("description", "")
                                
                                # Create tag using educated guess information
                                tag = self._create_tag_from_educated_guess(educated_guess, vendor)
                                all_tags.append(tag)
                                
                                # Add educated guess to database so it shows up in UI
                                self._add_educated_guess_to_database(educated_guess, vendor)
                                
                                educated_guess_count += 1
                                matched_count += 1
                                continue  # Skip JSON processing since we have educated guess
                            else:
                                logging.info(f"❌ No educated guess available for '{product_name}'")
                        except Exception as guess_error:
                            logging.warning(f"Educated guess error for '{product_name}': {guess_error}")
                    
                    # PRIORITY 4: Try main matching logic (database + Excel) if no educated guess
                    if not educated_guess:
                        # Try the main matching logic that was working in the debug output
                        try:
                            # Call the main matching function that was working
                            matched_products = self._process_item_with_main_matching(item, product_name, vendor, product_type, strain, global_vendor)
                            if matched_products:
                                for product in matched_products:
                                    tag = self._create_tag_from_product(product, item, global_vendor)
                                    all_tags.append(tag)
                                    matched_count += 1
                                continue  # Skip the JSON processing below
                        except Exception as main_match_error:
                            logging.warning(f"Error in main matching logic: {main_match_error}")
                    
                    # PRIORITY 5: If no match found, proceed with JSON processing
                    new_product_count += 1
                    logging.debug(f"Creating new product from JSON data: {product_name}")
                    
                    # Enhanced brand extraction with fallbacks
                    brand = str(item.get("brand", "")).strip()
                    logging.debug(f"Extracting brand for: {product_name}")
                    if not brand:
                        # Try to extract brand from product name patterns
                        name_lower = product_name.lower()
                        
                        # Look for common brand patterns - prioritize these for the Cultivera data
                        if "dank czar" in name_lower:
                            brand = "Dank Czar"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "omega" in name_lower:
                            brand = "Omega Labs"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "airo" in name_lower:
                            brand = "Airo Pro"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "jsm" in name_lower:
                            brand = "JSM"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "hustler" in name_lower:
                            brand = "Hustler's Ambition"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "1555" in name_lower:
                            brand = "1555 Industrial"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "harmony" in name_lower:
                            brand = "Harmony Farms"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        # Additional Cultivera brand patterns
                        elif "farmer's daughter" in name_lower:
                            brand = "Farmer's Daughter"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "greasy runtz" in name_lower:
                            brand = "Greasy Runtz"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "kelloggz koffee" in name_lower:
                            brand = "Kelloggz Koffee"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "trop banana" in name_lower:
                            brand = "Trop Banana"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        elif "velvet koffee" in name_lower:
                            brand = "Velvet Koffee"
                            logging.debug(f"  -> Detected brand from pattern: {brand}")
                        
                        # Look for "by [Brand]" pattern
                        if not brand:
                            import re
                            by_match = re.search(r'by\s+([A-Za-z0-9\s]+)(?:\s|$)', product_name, re.IGNORECASE)
                            if by_match:
                                brand = by_match.group(1).strip().title()
                                logging.debug(f"  -> Detected brand from 'by' pattern: {brand}")
                        
                        # Look for "from [Brand]" pattern
                        if not brand:
                            from_match = re.search(r'from\s+([A-Za-z0-9\s]+)(?:\s|$)', product_name, re.IGNORECASE)
                            if from_match:
                                brand = from_match.group(1).strip().title()
                                logging.debug(f"  -> Detected brand from 'from' pattern: {brand}")
                        
                        # Look for "Brand -" pattern (Cultivera format)
                        if not brand:
                            if " - " in product_name:
                                parts = product_name.split(" - ")
                                if len(parts) > 0:
                                    potential_brand = parts[0].strip()
                                    if len(potential_brand) > 2 and not any(x in potential_brand.lower() for x in ["live", "resin", "rosin", "wax", "shatter", "hash", "flower", "bud", "pre", "roll", "joint", "cartridge", "vape", "pen", "edible", "gummy", "chocolate", "cookie", "brownie", "candy", "sweet", "food", "drink", "beverage", "tincture", "drops", "capsule", "pill", "tablet", "lozenge", "mint", "chew", "chewing", "cream", "lotion", "salve", "balm", "ointment", "gel", "spray", "patch", "transdermal", "skin", "external", "apply", "rub", "grinder", "pipe", "bong", "rig", "torch", "lighter", "tray", "scale", "storage", "container", "jar", "bag", "accessory", "tool"]):
                                        brand = potential_brand.title()
                                        logging.debug(f"  -> Detected brand from dash pattern: {brand}")
                        
                        # Special handling for Cultivera data - look for brand indicators in product names
                        if not brand:
                            # Look for "Dank Czar" in product names
                            if "dank czar" in name_lower:
                                brand = "Dank Czar"
                                logging.debug(f"  -> Detected Dank Czar brand from product name: {brand}")
                            # Look for "Omega" in product names
                            elif "omega" in name_lower:
                                brand = "Omega Labs"
                                logging.debug(f"  -> Detected Omega Labs brand from product name: {brand}")
                            # Look for "Medically Compliant" as a brand indicator
                            elif "medically compliant" in name_lower:
                                # Extract the brand after "Medically Compliant -"
                                if "medically compliant -" in name_lower:
                                    parts = name_lower.split("medically compliant -")
                                    if len(parts) > 1:
                                        potential_brand = parts[1].split(" - ")[0].strip()
                                        if potential_brand and len(potential_brand) > 2:
                                            brand = potential_brand.title()
                                            logging.debug(f"  -> Detected brand from Medically Compliant pattern: {brand}")
                    
                    # If still no brand, use vendor as brand
                    if not brand and vendor:
                        brand = vendor.title()
                        logging.debug(f"  -> Using vendor as brand: {brand}")
                    
                    # If still no brand, try to extract from product name using capitalization patterns
                    if not brand:
                        words = product_name.split()
                        for word in words:
                            if len(word) > 2 and word[0].isupper() and word[1:].islower():
                                # Check if it's not a common product word
                                common_words = ["live", "resin", "rosin", "wax", "shatter", "hash", "flower", "bud", "pre", "roll", "joint", "cartridge", "vape", "pen", "edible", "gummy", "chocolate", "cookie", "brownie", "candy", "sweet", "food", "drink", "beverage", "tincture", "drops", "capsule", "pill", "tablet", "lozenge", "mint", "chew", "chewing", "cream", "lotion", "salve", "balm", "ointment", "gel", "spray", "patch", "transdermal", "skin", "external", "apply", "rub", "grinder", "pipe", "bong", "rig", "torch", "lighter", "tray", "scale", "storage", "container", "jar", "bag", "accessory", "tool"]
                                if word.lower() not in common_words:
                                    brand = word
                                    logging.debug(f"  -> Detected brand from capitalization: {brand}")
                                    break
                    
                    logging.debug(f"Final brand for '{product_name}': {brand}")
                    
                    # Extract product type with intelligent mapping from inventory_type
                    inventory_type = str(item.get("inventory_type", "")).strip()
                    inventory_category = str(item.get("inventory_category", "")).strip()
                    
                    # Use the mapping function to get proper product type
                    product_type = map_inventory_type_to_product_type(inventory_type, inventory_category, product_name)
                    
                    if not product_type or product_type == "Unknown":
                        # Fallback to inference if mapping didn't work
                        name_lower = product_name.lower()
                        logging.debug(f"Inferring product type for: {product_name}")
                        
                        # Concentrate types
                        if any(x in name_lower for x in ["rosin", "wax", "shatter", "live resin", "distillate", "hash", "live hash", "bubble hash", "kief", "keef", "crystal", "diamond", "sauce", "terp sauce", "terpene", "terps", "extract", "extraction", "solventless", "solvent-less"]):
                            product_type = "concentrate"
                            logging.debug(f"  -> Detected concentrate type: {product_type}")
                        # Pre-roll types
                        elif any(x in name_lower for x in ["pre-roll", "pre roll", "preroll", "joint", "blunt", "cigar", "cone", "paper", "rolling", "rolled"]):
                            product_type = "pre-roll"
                            logging.debug(f"  -> Detected pre-roll type: {product_type}")
                        # Vape types
                        elif any(x in name_lower for x in ["cartridge", "vape", "pen", "disposable", "pod", "battery", "510", "thc", "cbd", "oil", "distillate", "live resin", "rosin", "sauce"]):
                            product_type = "vape cartridge"
                            logging.debug(f"  -> Detected vape type: {product_type}")
                        # Flower types
                        elif any(x in name_lower for x in ["flower", "bud", "nug", "buds", "nugs", "marijuana", "cannabis", "weed", "herb", "green", "natural", "raw", "loose", "loose leaf"]):
                            product_type = "flower"
                            logging.debug(f"  -> Detected flower type: {product_type}")
                        # Edible types
                        elif any(x in name_lower for x in ["edible", "gummy", "chocolate", "cookie", "brownie", "candy", "sweet", "food", "drink", "beverage", "tincture", "drops", "capsule", "pill", "tablet", "lozenge", "mint", "chew", "chewing"]):
                            product_type = "edible"
                            logging.debug(f"  -> Detected edible type: {product_type}")
                        # Topical types
                        elif any(x in name_lower for x in ["topical", "cream", "lotion", "salve", "balm", "ointment", "gel", "spray", "patch", "transdermal", "skin", "external", "apply", "rub"]):
                            product_type = "topical"
                            logging.debug(f"  -> Detected topical type: {product_type}")
                        # Paraphernalia types
                        elif any(x in name_lower for x in ["paraphernalia", "grinder", "pipe", "bong", "dab rig", "rig", "torch", "lighter", "rolling tray", "tray", "scale", "scale", "storage", "container", "jar", "bag", "accessory", "tool"]):
                            product_type = "paraphernalia"
                            logging.debug(f"  -> Detected paraphernalia type: {product_type}")
                        # CBD specific types
                        elif any(x in name_lower for x in ["cbd", "hemp", "cannabidiol", "non-psychoactive", "non psychoactive", "medicinal", "therapeutic", "wellness", "health"]):
                            if any(x in name_lower for x in ["gummy", "oil", "tincture", "cream"]):
                                product_type = "edible" if "gummy" in name_lower or "oil" in name_lower else "topical"
                            else:
                                product_type = "cbd product"
                            logging.debug(f"  -> Detected CBD type: {product_type}")
                        # Default based on common patterns
                        else:
                            # Look for weight indicators to make educated guesses
                            if any(x in name_lower for x in ["1g", "2g", "3.5g", "7g", "14g", "28g", "gram", "grams", "oz", "ounce"]):
                                product_type = "flower"  # Most likely flower if weight is specified
                                logging.debug(f"  -> Defaulted to flower based on weight: {product_type}")
                            elif any(x in name_lower for x in ["mg", "milligram", "milligrams"]):
                                product_type = "edible"  # Most likely edible if mg is specified
                                logging.debug(f"  -> Defaulted to edible based on mg: {product_type}")
                            else:
                                product_type = "concentrate"  # Conservative default
                                logging.debug(f"  -> Defaulted to concentrate: {product_type}")
                    
                    logging.debug(f"Final product type for '{product_name}': {product_type} (mapped from inventory_type: {inventory_type})")
                    logging.debug(f"Product type for '{product_name}': '{product_type}'")
                    
                    # Enhanced weight and quantity extraction
                    weight = str(item.get("unit_weight", "")).strip()  # Fix: use unit_weight for Cultivera JSON
                    quantity = str(item.get("qty", "1")).strip()  # Fix: use qty for Cultivera JSON
                    units = str(item.get("unit_weight_uom", "g")).strip()  # Fix: use unit_weight_uom for Cultivera JSON
                    
                    # Extract description from JSON data
                    description = str(item.get("description", "")).strip()
                    if not description:
                        # Try alternative description fields
                        description = str(item.get("product_description", "")).strip()
                    if not description:
                        # Use product name as fallback description
                        description = product_name
                    
                    # If weight is still empty, try to extract from product name
                    if not weight:
                        import re
                        # Look for weight patterns in product name
                        weight_patterns = [
                            r'(\d+\.?\d*)\s*(g|gram|grams|gm)',  # 3.5g, 3.5 gram, etc.
                            r'(\d+\.?\d*)\s*(mg|milligram|milligrams)',  # 100mg, etc.
                            r'(\d+\.?\d*)\s*(oz|ounce|ounces)',  # 1oz, etc.
                            r'(\d+\.?\d*)\s*(lb|pound|pounds)',  # 1lb, etc.
                        ]
                        
                        for pattern in weight_patterns:
                            match = re.search(pattern, product_name, re.IGNORECASE)
                            if match:
                                weight = match.group(1)
                                units = match.group(2).lower()
                                if units in ['gram', 'grams', 'gm']:
                                    units = 'g'
                                elif units in ['milligram', 'milligrams']:
                                    units = 'mg'
                                elif units in ['ounce', 'ounces']:
                                    units = 'oz'
                                elif units in ['pound', 'pounds']:
                                    units = 'lb'
                                logging.debug(f"  -> Extracted weight from product name: {weight} {units}")
                                break
                    
                    # Ensure weight has a value
                    if not weight:
                        weight = "1"  # Default weight
                        logging.debug(f"  -> Using default weight: {weight}")
                    
                    # Ensure units have a value
                    if not units:
                        units = "g"  # Default to grams
                        logging.debug(f"  -> Using default units: {units}")
                    
                    logging.debug(f"Final weight for '{product_name}': {weight} {units}")
                    
                    # Enhanced price extraction with better estimation
                    price = str(item.get("line_price", item.get("price", ""))).strip()
                    if not price:
                        # Estimate price based on product type and weight
                        if "pre-roll" in product_type.lower():
                            price = "20"
                        elif "flower" in product_type.lower():
                            if weight and weight.isdigit():
                                weight_val = float(weight)
                                if weight_val <= 1:
                                    price = "35"
                                elif weight_val <= 3.5:
                                    price = "120"
                                elif weight_val <= 7:
                                    price = "220"
                                else:
                                    price = "400"
                            else:
                                price = "35"
                        elif "concentrate" in product_type.lower():
                            if weight and weight.isdigit():
                                weight_val = float(weight)
                                if weight_val <= 1:
                                    price = "50"
                                elif weight_val <= 2:
                                    price = "90"
                                else:
                                    price = "150"
                            else:
                                price = "50"
                        else:
                            price = "25"
                    
                    # Enhanced strain information extraction
                    strain = str(item.get("strain_name", "")).strip()
                    if not strain:
                        # First try to extract strain from product name
                        extracted_strain = self._extract_strain_from_product_name(product_name)
                        if extracted_strain:
                            strain = extracted_strain
                            logging.info(f"🧬 Extracted strain '{strain}' from product name '{product_name}' in fetch_and_match_with_product_db")
                        else:
                            # Try to find strain in database
                            try:
                                db_strain = self._find_strain_in_database(product_name, product_db)
                                if db_strain:
                                    strain = db_strain
                                    logging.info(f"🗄️ Found strain '{strain}' in database for product '{product_name}' in fetch_and_match_with_product_db")
                            except Exception as db_error:
                                logging.warning(f"Failed to search database for strain in fetch_and_match_with_product_db: {db_error}")
                    
                    # Enhanced lineage determination
                    lineage = "HYBRID"  # Default
                    if strain:
                        # Enhanced lineage logic based on strain characteristics
                        strain_lower = strain.lower()
                        
                        # Sativa-dominant strains
                        if any(x in strain_lower for x in ["haze", "sativa", "durban", "jack", "herer", "trainwreck", "green crack", "maui", "wowie", "amnesia", "lemon", "lime", "tropical", "tangie", "clementine", "mandarin", "orange", "citrus", "energetic", "uplifting", "creative", "focus", "daytime"]):
                            lineage = "SATIVA"
                        # Indica-dominant strains
                        elif any(x in strain_lower for x in ["kush", "indica", "afghan", "afghani", "bubba", "master", "purple", "granddaddy", "grand daddy", "northern lights", "skunk", "hashplant", "relaxing", "sedating", "sleep", "nighttime", "body", "couch", "lock"]):
                            lineage = "INDICA"
                        # Hybrid strains (including balanced)
                        elif any(x in strain_lower for x in ["og", "diesel", "cookies", "runtz", "gelato", "wedding", "cake", "sherbet", "sherbert", "blueberry", "strawberry", "banana", "mango", "pineapple", "cherry", "grape", "apple", "guava", "dragon", "fruit", "passion", "peach", "apricot", "watermelon", "cantaloupe", "honeydew", "kiwi", "plum", "raspberry", "blackberry", "yoda", "cosmic", "combo", "honey", "bread", "mintz", "grinch", "ak-47", "white widow", "chemdawg", "sour", "cheese", "blue dream", "balanced", "hybrid"]):
                            lineage = "HYBRID"
                        # CBD strains
                        elif any(x in strain_lower for x in ["cbd", "hemp", "cannabidiol", "non-psychoactive", "non psychoactive", "medicinal", "therapeutic", "wellness", "health", "paraphernalia"]):
                            lineage = "CBD"
                        # Special cases
                        elif "haze" in strain_lower and ("purple" in strain_lower or "amnesia" in strain_lower):
                            lineage = "HYBRID/SATIVA"  # Purple Haze, Amnesia Haze are often hybrid-sativa
                        elif "kush" in strain_lower and ("purple" in strain_lower or "bubba" in strain_lower):
                            lineage = "HYBRID/INDICA"  # Purple Kush, Bubba Kush are often hybrid-indica
                        else:
                            lineage = "HYBRID"  # Conservative default
                    else:
                        # If no strain info, try to infer from product type
                        # Use intelligent lineage assignment based on product type
                        lineage = self._get_default_lineage_for_product_type(product_type)
                    
                    # Extract additional fields for new database columns
                    thc_result = str(item.get("thc", "")).strip()
                    cbd_result = str(item.get("cbd", "")).strip()
                    test_unit = str(item.get("test_unit", "%")).strip()
                    batch_num = str(item.get("batch_number", "")).strip()
                    lot_num = str(item.get("lot_number", "")).strip()
                    barcode = str(item.get("barcode", "")).strip()
                    cost = str(item.get("cost", "")).strip()
                    medical_only = str(item.get("medical_only", "No")).strip()
                    med_price = str(item.get("med_price", "")).strip()
                    expiration = str(item.get("expiration_date", "")).strip()
                    is_archived = str(item.get("is_archived", "no")).strip()
                    thc_per_serving = str(item.get("thc_per_serving", "")).strip()
                    allergens = str(item.get("allergens", "")).strip()
                    solvent = str(item.get("solvent", "")).strip()
                    accepted_date = str(item.get("accepted_date", "")).strip()
                    internal_id = str(item.get("internal_id", "")).strip()
                    product_tags = str(item.get("product_tags", "")).strip()
                    image_url = str(item.get("image_url", "")).strip()
                    ingredients = str(item.get("ingredients", "")).strip()
                    
                    # Enhanced product tag creation using new database columns
                    tag = {
                        # Core product information
                        'Product Name*': product_name,
                        'ProductName': product_name,
                        'Description': description,
                        'Product Type*': product_type or infer_product_type_from_name(product_name),
                        'Product Type': product_type or infer_product_type_from_name(product_name),
                        'Vendor': vendor,
                        'Vendor/Supplier*': vendor,
                        'Product Brand': brand,
                        'ProductBrand': brand,
                        'Product Strain': strain,
                        'Strain Name': strain,
                        'Lineage': lineage,
                        'Weight*': f"{weight} {units}" if weight and units else weight,
                        'Weight': f"{weight} {units}" if weight and units else weight,
                        'Quantity*': quantity,
                        'Quantity': quantity,
                        'Units': units,
                        'Price': price,
                        'Price* (Tier Name for Bulk)': price,
                        
                        # Enhanced fields using new database columns
                        'State': 'active',
                        'Is Sample? (yes/no)': 'no',
                        'Is MJ product?(yes/no)': 'yes',
                        'Discountable? (yes/no)': 'yes',
                        'Room*': 'Default',
                        'Medical Only (Yes/No)': 'No',
                        'DOH': 'No',
                        'DOH Compliant (Yes/No)': 'No',
                        
                        # New database column mappings
                        'Concentrate Type': product_type if "concentrate" in product_type.lower() else '',
                        'Ratio': '',
                        'Joint Ratio': '',
                        'JointRatio': '',
                        'THC test result': thc_result,
                        'CBD test result': cbd_result,
                        'Test result unit (% or mg)': test_unit,
                        'Batch Number': batch_num,
                        'Lot Number': lot_num,
                        'Barcode*': barcode,
                        'Med Price': med_price,
                        'Expiration Date(YYYY-MM-DD)': expiration,
                        'Is Archived? (yes/no)': is_archived,
                        'THC Per Serving': thc_per_serving,
                        'Allergens': allergens,
                        'Solvent': solvent,
                        'Accepted Date': accepted_date,
                        'Internal Product Identifier': internal_id,
                        'Product Tags (comma separated)': product_tags,
                        'Image URL': image_url,
                        'Ingredients': ingredients,
                        
                        # Legacy fields for compatibility - CRITICAL FIX: Use Excel-compatible source
                        'Source': 'Excel Import',  # Changed from 'JSON Match - New Product' to 'Excel Import'
                        'Quantity Received*': quantity,
                        'Weight Unit* (grams/gm or ounces/oz)': units,
                        'CombinedWeight': weight,
                        'DescAndWeight': self._process_description_from_product_name(primary_product_name, weight, units),  # Use Excel processor formula with weight
                        'Description_Complexity': '1',
                        'Ratio_or_THC_CBD': '',
                        'displayName': clean_product_name(product_name),  # Use cleaned product name for consistency
                        'weightWithUnits': f"{str(round(float(weight or '1')))}{units or 'g'}",
                        'WeightWithUnits': f"{str(round(float(weight or '1')))}{units or 'g'}",
                        'WeightUnits': f"{str(round(float(weight or '1')))}{units or 'g'}",
                        'vendor': vendor,
                        'productBrand': brand,
                        'lineage': lineage,
                        'productType': product_type,
                        'weight': weight,
                        'units': units,
                        'price': price,
                        'description': description,
                        'strain': strain,
                        'quantity': quantity,
                        'thc': thc_result,
                        'cbd': cbd_result,
                        'test_unit': test_unit,
                        'batch_number': batch_num,
                        'lot_number': lot_num,
                        'barcode': barcode,
                        'cost': cost,
                        'medical_only': medical_only,
                        'med_price': med_price,
                        'expiration_date': expiration,
                        'is_archived': is_archived,
                        'thc_per_serving': thc_per_serving,
                        'allergens': allergens,
                        'solvent': solvent,
                        'accepted_date': accepted_date,
                        'internal_id': internal_id,
                        'product_tags': product_tags,
                        'image_url': image_url,
                        'ingredients': ingredients,
                    }
                    
                    all_tags.append(tag)
                    processed_count += 1
                    
                    # Create new database entry for unmatched JSON tag
                    if product_db:
                        try:
                            self._create_database_entry_for_unmatched_json(tag, product_db)
                            new_database_entries_count += 1
                        except Exception as db_entry_error:
                            logging.warning(f"Failed to create database entry for '{product_name}': {db_entry_error}")
                    
                    # Add debug logging after each item is processed
                    print(f"🔍 DEBUG: === COMPLETED PROCESSING ITEM {i+1}/{len(unique_items)} ===")
                    print(f"🔍 DEBUG: Current matched_products count: {len(matched_products)}")
                    print(f"🔍 DEBUG: Continuing to next item...")
                    
                    # Add a small delay to ensure logs are flushed
                    import time
                    time.sleep(0.1)
                
                except Exception as item_error:
                    logging.error(f"Error processing item {i+1}: {item_error}")
                    continue
            
            # Log summary of Product Database vs JSON processing
            logging.info(f"Product Database priority processing completed:")
            logging.info(f"  - Total items processed: {processed_count}")
            logging.info(f"  - Product Database matches: {db_lookup_count}")
            logging.info(f"  - Educated guesses: {educated_guess_count}")
            logging.info(f"  - New products from JSON: {new_product_count}")
            logging.info(f"  - New database entries created: {new_database_entries_count}")
            logging.info(f"  - Total tags created: {len(all_tags)}")
            
            # CRITICAL FIX: Integrate JSON-matched products with Excel system
            try:
                # Get the current Excel processor from the session
                from flask import g
                if hasattr(g, 'excel_processor') and g.excel_processor:
                    logging.info("Integrating JSON-matched products with Excel system...")
                    integration_success = self.integrate_with_excel_system(g.excel_processor, all_tags)
                    if integration_success:
                        logging.info("✅ Successfully integrated JSON products with Excel system")
                    else:
                        logging.warning("⚠️ Failed to integrate JSON products with Excel system")
                else:
                    logging.warning("No Excel processor available in session for integration")
            except Exception as integration_error:
                logging.error(f"Error during Excel integration: {integration_error}")
            
            # Performance summary
            total_time = time.time() - start_time
            logging.info(f"🚀 JSON MATCHING PERFORMANCE SUMMARY:")
            logging.info(f"   Total time: {total_time:.2f}s")
            logging.info(f"   Items processed: {processed_count}")
            logging.info(f"   Items matched: {matched_count}")
            logging.info(f"   Match rate: {(matched_count/processed_count*100):.1f}%" if processed_count > 0 else "   Match rate: 0%")
            logging.info(f"   Processing speed: {processed_count/total_time:.1f} items/sec" if total_time > 0 else "   Processing speed: N/A")
            
            return all_tags
            
        except Exception as e:
            logging.error(f"Error in fetch_and_match_with_product_db: {e}")
            raise
            
    def _get_cache_item_name(self, idx_str: str) -> str:
        """Get the original name of a cache item by index."""
        for item in self._sheet_cache:
            if isinstance(item, dict) and item.get("idx") == idx_str:
                return item.get("original_name", "Unknown")
        return "Unknown"
        
    def get_matched_names(self) -> Optional[List[str]]:
        """Get the currently matched product names from JSON."""
        return getattr(self, 'json_matched_names', None)
        
    def get_matched_tags(self) -> Optional[List[Dict]]:
        """Get the currently matched full tag objects from JSON."""
        return getattr(self, 'json_matched_tags', None)
        
    def clear_matches(self):
        """Clear the current JSON matches."""
        self.json_matched_names = None
        self.json_matched_tags = None
        
    def rebuild_sheet_cache(self):
        """Force rebuild the sheet cache."""
        self._sheet_cache = None
        self._indexed_cache = None
        self._build_sheet_cache()
        
    def rebuild_strain_cache(self):
        """Force rebuild the strain cache."""
        self._strain_cache = None
        self._lineage_cache = None
        self._build_strain_cache()
        
    def rebuild_all_caches(self):
        """Force rebuild all caches."""
        self.rebuild_sheet_cache()
        self.rebuild_strain_cache()
        
    def get_sheet_cache_status(self):
        """Get the status of the sheet cache."""
        if self._sheet_cache is None:
            return "Not built"
        elif not self._sheet_cache:
            return "Empty"
        else:
            cache_info = f"Built with {len(self._sheet_cache)} entries"
            if self._indexed_cache:
                cache_info += f" (indexed: {len(self._indexed_cache['exact_names'])} exact, {len(self._indexed_cache['vendor_groups'])} vendors, {len(self._indexed_cache['key_terms'])} terms)"
            return cache_info
            
    def get_strain_cache_status(self):
        """Get the status of the strain cache."""
        if self._strain_cache is None:
            return "Not built"
        elif not self._strain_cache:
            return "Empty"
        else:
            return f"Built with {len(self._strain_cache)} strains and {len(self._lineage_cache)} lineages"
        
    def process_json_inventory(self, url: str) -> pd.DataFrame:
        """
        Process JSON inventory data and return as DataFrame for inventory slips.
        
        Args:
            url: URL to fetch JSON data from
            
        Returns:
            DataFrame with processed inventory data
        """
        try:
            # Use the proxy endpoint to handle authentication and CORS
            import requests
            
            # Prepare headers for the request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add authentication headers if available
            import os
            if os.environ.get('BAMBOO_API_KEY'):
                headers['X-API-Key'] = os.environ.get('BAMBOO_API_KEY')
            if os.environ.get('BAMBOO_AUTH_TOKEN'):
                headers['Authorization'] = f"Bearer {os.environ.get('BAMBOO_AUTH_TOKEN')}"
            if os.environ.get('BAMBOO_SESSION_TOKEN'):
                headers['X-Session-Token'] = os.environ.get('BAMBOO_SESSION_TOKEN')
            
            proxy_data = {
                'url': url,
                'headers': headers
            }
            
            # Try to make the request directly first (for external URLs)
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                payload = response.json()
            except (requests.exceptions.RequestException, ValueError) as direct_error:
                logging.info(f"Direct request failed, trying proxy: {direct_error}")
                # Fallback to proxy endpoint if direct request fails
                import os
                base_url = os.environ.get('FLASK_BASE_URL', 'http://127.0.0.1:5001')
                response = requests.post(f'{base_url}/api/proxy-json', 
                                       json=proxy_data, 
                                       timeout=30)
                response.raise_for_status()
                payload = response.json()
                
            # Handle both list and dictionary payloads
            if isinstance(payload, list):
                items = payload
                vendor_meta = "Unknown Vendor"
                raw_date = datetime.now().strftime("%Y-%m-%d")
            elif isinstance(payload, dict):
                items = payload.get("inventory_transfer_items", [])
                vendor_meta = f"{payload.get('from_license_number', '')} – {payload.get('from_license_name', '')}"
                raw_date = payload.get("est_arrival_at", "").split("T")[0]
            else:
                logging.warning(f"Unexpected payload type: {type(payload)}")
                return pd.DataFrame()
            
            records = []
            for itm in items:
                # Ensure all values are strings to prevent type issues
                product_name = str(itm.get("product_name", "")) if itm.get("product_name") is not None else ""
                inventory_id = str(itm.get("inventory_id", "")) if itm.get("inventory_id") is not None else ""
                qty = str(itm.get("qty", "")) if itm.get("qty") is not None else ""
                
                records.append({
                    "Product Name*": product_name,
                    "Barcode*": inventory_id,
                    "Quantity Received*": qty,
                    "Accepted Date": raw_date,
                    "Vendor/Supplier*": vendor_meta,
                })
                
            df = pd.DataFrame(records)
            logging.info(f"Processed {len(records)} inventory items from JSON")
            return df
            
        except Exception as e:
            logging.error(f"Error processing JSON inventory: {str(e)}")
            raise 

    def _build_strain_cache(self):
        """Build a cache of strain data from the product database for fast matching."""
        try:
            product_db = ProductDatabase()
            self._strain_cache = product_db.get_all_strains()
            self._lineage_cache = product_db.get_strain_lineage_map()
            
            # Debug: Check what's in the strain cache
            if self._strain_cache:
                sample_strains = list(self._strain_cache)[:5]
                logging.info(f"Sample strains in cache: {sample_strains}")
                for strain in sample_strains:
                    if not isinstance(strain, str):
                        logging.warning(f"Non-string strain found: {type(strain)} - {strain}")
            
            logging.info(f"Built strain cache with {len(self._strain_cache)} strains and {len(self._lineage_cache)} lineages")
        except Exception as e:
            logging.warning(f"Could not build strain cache: {e}")
            self._strain_cache = set()
            self._lineage_cache = {}
        
    def _find_strains_in_text(self, text: str) -> List[Tuple[str, str]]:
        """Find known strains in text and return (strain_name, lineage) pairs."""
        if not self._strain_cache:
            self._build_strain_cache()
            
        # Ensure input is a string
        text = str(text or "")
        if not text:
            return []
            
        text_lower = text.lower()
        found_strains = []
        
        # Check for exact strain matches
        for strain in self._strain_cache:
            # Ensure strain is a string before calling .lower()
            if isinstance(strain, str):
                if strain.lower() in text_lower:
                    lineage = self._lineage_cache.get(strain, "HYBRID")
                    found_strains.append((strain, lineage))
            else:
                # Skip non-string strains and log for debugging
                logging.warning(f"Skipping non-string strain in cache: {type(strain)} - {strain}")
                
        # Sort by length (longer strains first) to prioritize more specific matches
        found_strains.sort(key=lambda x: len(x[0]), reverse=True)
        
        return found_strains 

    def _find_strict_fuzzy_vendor_matches(self, json_vendor: str) -> List[dict]:
        """Find vendor matches using strict fuzzy matching - only very similar vendor names."""
        if not json_vendor:
            return []
            
        matches = []
        available_vendors = list(self._indexed_cache['vendor_groups'].keys())
        
        # Only known vendor name variations that are definitely the same company
        vendor_variations = {
            # Dank Czar variations only
            'dank czar': ['dcz holdings inc', 'dcz holdings inc.', 'dcz holdings', 'dcz'],
            'dcz holdings': ['dank czar', 'dcz', 'dcz holdings inc', 'dcz holdings inc.'],
            'dcz holdings inc': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc.'],
            'dcz holdings inc.': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc'],
            'dcz': ['dank czar', 'dcz holdings', 'dcz holdings inc', 'dcz holdings inc.'],
            
            # Hustler's Ambition variations only
            'hustler\'s ambition': ['hustlers ambition', '1555 industrial llc'],
            'hustlers ambition': ['hustler\'s ambition', '1555 industrial llc'],
            '1555 industrial llc': ['hustler\'s ambition', 'hustlers ambition'],
            
            # Omega Labs variations only
            'omega labs': ['omega', 'omega cannabis'],
            'omega': ['omega labs', 'omega cannabis'],
            'omega cannabis': ['omega labs', 'omega'],
            
            # Airo Pro variations only
            'airo pro': ['airo', 'airopro', 'harmony farms'],
            'airo': ['airo pro', 'airopro', 'harmony farms'],
            'airopro': ['airo pro', 'airo', 'harmony farms'],
            'harmony farms': ['airo pro', 'airo', 'airopro'],
            
            # Collections Cannabis variations only
            'collections cannabis': ['collections', 'collections llc'],
            'collections': ['collections cannabis', 'collections llc'],
            'collections llc': ['collections cannabis', 'collections'],
            
            # Blue Roots variations only
            'blue roots cannabis': ['blue roots', 'blue roots llc'],
            'blue roots': ['blue roots cannabis', 'blue roots llc'],
            'blue roots llc': ['blue roots cannabis', 'blue roots'],
            
            # Grow Op Farms variations only
            'grow op farms': ['grow op', 'grow op llc'],
            'grow op': ['grow op farms', 'grow op llc'],
            'grow op llc': ['grow op farms', 'grow op'],
            
            # Cloud 9 Farms variations only
            'cloud 9 farms': ['cloud 9', 'cloud 9 llc'],
            'cloud 9': ['cloud 9 farms', 'cloud 9 llc'],
            'cloud 9 llc': ['cloud 9 farms', 'cloud 9'],
            
            # The Collective variations only
            'the collective': ['collective', 'collective llc'],
            'collective': ['the collective', 'collective llc'],
            'collective llc': ['the collective', 'collective'],
            
            # 1555 Industrial variations only
            '1555 industrial': ['1555 industrial llc', '1555 llc'],
            '1555 llc': ['1555 industrial', '1555 industrial llc'],
            
            # Georgetown Bottling variations only
            'georgetown bottling spc': ['georgetown bottling', 'cormorant edibles', 'cormorant'],
            'georgetown bottling': ['georgetown bottling spc', 'cormorant edibles', 'cormorant'],
            'cormorant edibles': ['georgetown bottling spc', 'georgetown bottling', 'cormorant'],
            'cormorant': ['georgetown bottling spc', 'georgetown bottling', 'cormorant edibles'],
        }
        
        # Check for known variations only
        for variation_key, variations in vendor_variations.items():
            # Check if json_vendor matches the main key or any of its variations
            if json_vendor == variation_key or json_vendor in variations:
                for vendor in available_vendors:
                    # Check if the available vendor matches the main key or any of its variations
                    if vendor == variation_key or vendor in variations:
                        matches.extend(self._indexed_cache['vendor_groups'][vendor])
        
        # If no matches found with known variations, try very strict word matching
        if not matches:
            json_words = set(json_vendor.split())
            for vendor in available_vendors:
                vendor_words = set(vendor.split())
                
                # Only match if there's significant word overlap (at least 2 words or 75% overlap)
                overlap = json_words.intersection(vendor_words)
                if len(overlap) >= 2 or (len(overlap) >= 1 and len(overlap) / min(len(json_words), len(vendor_words)) >= 0.75):
                    matches.extend(self._indexed_cache['vendor_groups'][vendor])
        
        return matches 
    
    def _get_cache_item_name(self, idx):
        """Get the name of a cache item by index."""
        for item in self._sheet_cache:
            if str(item.get("idx", "")) == str(idx):
                return item.get("original_name", "Unknown")
        return "Unknown"

    def intelligent_match_product(self, json_item: dict) -> Tuple[Optional[dict], float, str]:
        """
        Intelligently match a JSON product to existing products using sophisticated fuzzy matching.
        
        Returns:
            Tuple of (matched_product, confidence_score, match_reason)
        """
        try:
            json_name = str(json_item.get("product_name", "")).strip()
            json_vendor = str(json_item.get("vendor", "")).strip().lower()
            json_brand = str(json_item.get("brand", "")).strip().lower()
            json_type = str(json_item.get("product_type", "")).strip().lower()
            json_weight = str(json_item.get("weight", "")).strip()
            json_strain = str(json_item.get("strain_name", "")).strip().lower()
            
            # Reduced logging for performance
            logging.debug(f"🔍 INTELLIGENT MATCHING: '{json_name}' (vendor: {json_vendor}, brand: {json_brand}, type: {json_type}, weight: {json_weight}, strain: {json_strain})")
            
            if not json_name:
                return None, 0.0, "No product name provided"
            
            # Step 1: Try exact name matching first (highest confidence) - PRIORITIZE DATABASE
            exact_matches = self._find_exact_name_matches(json_name)
            if exact_matches:
                # Sort by priority: database matches first, then Excel
                exact_matches.sort(key=lambda x: x.get('_priority', 999))
                db_matches = [m for m in exact_matches if m.get('_source') == 'database']
                excel_matches = [m for m in exact_matches if m.get('_source') == 'excel']
                
                best_match = exact_matches[0]  # Now guaranteed to be database if available
                source = best_match.get('_source', 'unknown')
                logging.debug(f"✅ EXACT MATCH ({source.upper()}): '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (Total: {len(exact_matches)}, DB: {len(db_matches)}, Excel: {len(excel_matches)})")
                return best_match, 1.0, f"Exact name match ({source})"
            else:
                logging.debug(f"❌ No exact match for '{json_name}'")
            
            # Step 2: Try vendor-based exact name matching - PRIORITIZE DATABASE
            if json_vendor:
                vendor_exact_matches = self._find_vendor_exact_name_matches(json_name, json_vendor)
                if vendor_exact_matches:
                    # Sort by priority: database matches first, then Excel
                    vendor_exact_matches.sort(key=lambda x: x.get('_priority', 999))
                    best_match = vendor_exact_matches[0]  # Now guaranteed to be database if available
                    source = best_match.get('_source', 'unknown')
                    logging.debug(f"✅ VENDOR EXACT MATCH ({source.upper()}): '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                    return best_match, 0.95, f"Vendor-based exact name match ({source})"
                else:
                    logging.debug(f"❌ No vendor exact match for '{json_name}' with vendor '{json_vendor}'")
            else:
                logging.debug(f"⚠️ No vendor specified for '{json_name}', skipping vendor-based matching")
            
            # Step 3: Try fuzzy name matching with vendor filtering (very lenient threshold)
            if json_vendor:
                # Use very lenient threshold for vendor-based matching for maximum coverage
                vendor_threshold = 30 if json_brand else 25  # Much more lenient for better matching
                fuzzy_matches = self._find_fuzzy_name_matches(json_name, json_vendor, threshold=vendor_threshold)
                if fuzzy_matches:
                    best_match = fuzzy_matches[0]
                    score = fuzzy_matches[0]['fuzzy_score'] / 100.0
                    logging.debug(f"✅ VENDOR FUZZY MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f}, threshold: {vendor_threshold})")
                    return best_match, score, "Vendor-based fuzzy name match"
                else:
                    logging.debug(f"❌ No vendor fuzzy match for '{json_name}' with vendor '{json_vendor}' (threshold: {vendor_threshold})")
            else:
                logging.debug(f"⚠️ No vendor specified for '{json_name}', skipping vendor fuzzy matching")
            
            # Step 4: Try cross-vendor fuzzy matching as fallback (with very low threshold)
            # This helps when vendor names don't match but products are similar
            cross_vendor_matches = self._find_fuzzy_name_matches(json_name, threshold=20)  # Very low threshold for cross-vendor matching
            if cross_vendor_matches:
                best_match = cross_vendor_matches[0]
                score = cross_vendor_matches[0]['fuzzy_score'] / 100.0
                logging.debug(f"✅ CROSS-VENDOR FUZZY MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f}, threshold: 20)")
                return best_match, score, "Cross-vendor fuzzy name match"
            else:
                logging.debug(f"❌ No cross-vendor fuzzy match for '{json_name}' (threshold: 20)")
            
            # Step 5: Try enhanced fuzzy matching with multiple strategies
            enhanced_matches = self._find_enhanced_fuzzy_matches(json_item)
            if enhanced_matches:
                best_match = enhanced_matches[0]
                score = enhanced_matches[0]['fuzzy_score'] / 100.0
                logging.debug(f"✅ ENHANCED FUZZY MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f})")
                return best_match, score, "Enhanced fuzzy match"
            else:
                logging.debug(f"❌ No enhanced fuzzy match for '{json_name}'")
            
            # Step 5.5: Try Cultivera-specific matching
            cultivera_matches = self._find_cultivera_specialized_matches(json_item)
            if cultivera_matches:
                best_match = cultivera_matches[0]
                score = cultivera_matches[0]['fuzzy_score'] / 100.0
                logging.debug(f"✅ CULTIVERA MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f})")
                return best_match, score, "Cultivera specialized match"
            else:
                logging.debug(f"❌ No Cultivera specialized match for '{json_name}'")
            
            # Step 5b: Fallback to general fuzzy matching without vendor requirements (very low threshold)
            general_fuzzy_matches = self._find_fuzzy_name_matches(json_name, threshold=15)  # Very low threshold for maximum coverage
            if general_fuzzy_matches:
                best_match = general_fuzzy_matches[0]
                score = general_fuzzy_matches[0]['fuzzy_score'] / 100.0
                logging.debug(f"✅ GENERAL FUZZY MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f}, threshold: 15)")
                return best_match, score, "General fuzzy match"
            else:
                logging.debug(f"❌ No general fuzzy match for '{json_name}' (threshold: 15)")
            
            # Step 5: Try specialized matching for vendors with generic names (like Ceres)
            if json_vendor and json_vendor.lower() in ['ceres', 'ceres gardens', 'ceres gardens inc']:
                ceres_matches = self._find_ceres_specialized_matches(json_item)
                if ceres_matches:
                    best_match = ceres_matches[0]
                    score = ceres_matches[0]['fuzzy_score'] / 100.0
                    logging.debug(f"✅ CERES SPECIALIZED MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f})")
                    return best_match, score, "Ceres specialized match"
                else:
                    logging.debug(f"❌ No Ceres specialized match for '{json_name}'")

            # Step 6: Try strain-based matching (with optional vendor filtering)
            if json_strain:  # Only require strain, vendor is optional
                strain_matches = self._find_strain_based_matches(json_strain, json_vendor, json_type)
                if strain_matches:
                    best_match = strain_matches[0]
                    logging.debug(f"✅ STRAIN MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                    return best_match, 0.7, "Strain-based match"
                else:
                    logging.debug(f"❌ No strain match for '{json_name}' (strain: {json_strain})")
            else:
                logging.debug(f"⚠️ No strain specified for '{json_name}', skipping strain matching")
            
            # Step 6: Try brand + type + weight matching (with optional vendor filtering)
            if json_brand and json_type and json_weight:  # Only require brand, type, and weight
                brand_type_matches = self._find_brand_type_weight_matches(json_brand, json_type, json_weight, json_vendor)
                if brand_type_matches:
                    best_match = brand_type_matches[0]
                    logging.debug(f"✅ BRAND+TYPE+WEIGHT MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                    return best_match, 0.6, "Brand + type + weight match"
                else:
                    logging.debug(f"❌ No brand+type+weight match for '{json_name}'")
            else:
                logging.debug(f"⚠️ Missing required fields for brand+type+weight matching (brand: {json_brand}, type: {json_type}, weight: {json_weight})")
            
            # Step 7: Try advanced weight-based matching (with optional vendor filtering)
            if json_weight and json_type:  # Only require weight and type
                weight_matches = self._find_weight_based_matches(json_weight, json_type, json_vendor)
                if weight_matches:
                    best_match = weight_matches[0]
                    logging.debug(f"✅ WEIGHT+TYPE MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                    return best_match, 0.5, "Weight + type based match"
            
            # Step 8: Try comprehensive multi-field matching with all available data
            comprehensive_matches = self._find_comprehensive_matches(json_item)
            if comprehensive_matches:
                best_match = comprehensive_matches[0]
                logging.debug(f"✅ COMPREHENSIVE MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                return best_match, 0.4, "Comprehensive multi-field match"
            
            # Step 9: Try partial field matching with any available data
            partial_matches = self._find_partial_field_matches(json_item)
            if partial_matches:
                best_match = partial_matches[0]
                logging.debug(f"✅ PARTIAL MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                return best_match, 0.3, "Partial field match"
            
            # Step 8: Try advanced multi-algorithm matching
            advanced_matches = self._find_advanced_matches(json_item)
            if advanced_matches:
                best_match = advanced_matches[0]
                score = best_match.overall_score / 100.0
                logging.debug(f"✅ ADVANCED MATCH: '{json_name}' → '{best_match.item.get('original_name', 'Unknown')}' (score: {score:.2f}, algorithm: {best_match.algorithm_used})")
                return best_match.item, score, f"Advanced {best_match.algorithm_used} match"
            else:
                logging.debug(f"❌ No advanced match for '{json_name}'")
            
            # Step 8: Try strain + weight matching (with optional vendor filtering)
            if json_strain and json_weight:  # Only require strain and weight
                strain_weight_matches = self._find_strain_weight_matches(json_strain, json_weight, json_vendor)
                if strain_weight_matches:
                    best_match = strain_weight_matches[0]
                    logging.debug(f"✅ STRAIN+WEIGHT MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}'")
                    return best_match, 0.55, "Strain + weight based match"
                else:
                    logging.debug(f"❌ No strain+weight match for '{json_name}'")
            else:
                logging.debug(f"⚠️ Missing required fields for strain+weight matching (strain: {json_strain}, weight: {json_weight})")
            
            # Step 9: Final fallback - try general fuzzy matching without vendor requirements
            general_fuzzy_matches = self._find_fuzzy_name_matches(json_name, threshold=30)  # Very low threshold for final attempt
            if general_fuzzy_matches:
                best_match = general_fuzzy_matches[0]
                score = general_fuzzy_matches[0]['fuzzy_score'] / 100.0
                logging.debug(f"✅ GENERAL FUZZY MATCH: '{json_name}' → '{best_match.get('original_name', 'Unknown')}' (score: {score:.2f}, threshold: 40)")
                return best_match, score, "General fuzzy match (final fallback)"
            else:
                logging.debug(f"❌ No general fuzzy match for '{json_name}' (threshold: 40)")
            
            # No match found
            logging.debug(f"❌ NO MATCH FOUND: '{json_name}' - tried all matching strategies")
            return None, 0.0, "No suitable match found"
            
        except Exception as e:
            logging.error(f"Error in intelligent_match_product: {e}")
            return None, 0.0, f"Error during matching: {str(e)}"
    
    def _find_comprehensive_matches(self, json_item: dict) -> List[dict]:
        """
        Find matches using comprehensive multi-field analysis including all available columns.
        """
        try:
            json_name = str(json_item.get("product_name", "")).strip()
            json_vendor = str(json_item.get("vendor", "")).strip().lower()
            json_brand = str(json_item.get("brand", "")).strip().lower()
            json_type = str(json_item.get("product_type", "")).strip().lower()
            json_weight = str(json_item.get("weight", "")).strip()
            json_strain = str(json_item.get("strain_name", "")).strip().lower()
            json_qty = str(json_item.get("qty", "")).strip()
            json_price = str(json_item.get("price", "")).strip()
            json_thc = str(json_item.get("thc", "")).strip()
            json_cbd = str(json_item.get("cbd", "")).strip()
            
            matches = []
            
            # Get all products for comprehensive matching
            all_products = self._get_all_products()
            
            for product in all_products:
                score = 0.0
                match_details = []
                
                # Name similarity (highest weight)
                if json_name:
                    name_similarity = self._calculate_name_similarity(json_name, product.get('Product Name*', ''))
                    if name_similarity > 0.1:  # Extremely lenient threshold
                        score += name_similarity * 0.4
                        match_details.append(f"name:{name_similarity:.2f}")
                
                # Vendor matching
                if json_vendor:
                    vendor_similarity = self._calculate_vendor_similarity(json_vendor, self._get_product_vendor(product))
                    if vendor_similarity > 0.1:
                        score += vendor_similarity * 0.2
                        match_details.append(f"vendor:{vendor_similarity:.2f}")
                
                # Brand matching
                if json_brand:
                    brand_similarity = self._calculate_brand_similarity(json_brand, product.get('Product Brand', ''))
                    if brand_similarity > 0.1:
                        score += brand_similarity * 0.15
                        match_details.append(f"brand:{brand_similarity:.2f}")
                
                # Type matching
                if json_type:
                    type_similarity = self._calculate_type_similarity(json_type, product.get('Product Type*', ''))
                    if type_similarity > 0.1:
                        score += type_similarity * 0.1
                        match_details.append(f"type:{type_similarity:.2f}")
                
                # Weight matching
                if json_weight:
                    weight_similarity = self._calculate_weight_similarity(json_weight, product.get('Weight*', ''))
                    if weight_similarity > 0.1:
                        score += weight_similarity * 0.1
                        match_details.append(f"weight:{weight_similarity:.2f}")
                
                # Strain matching
                if json_strain:
                    strain_similarity = self._calculate_strain_similarity(json_strain, product.get('Product Strain', ''))
                    if strain_similarity > 0.1:
                        score += strain_similarity * 0.05
                        match_details.append(f"strain:{strain_similarity:.2f}")
                
                # If we have any score at all, include this match
                if score > 0.05:  # Extremely lenient threshold
                    product['comprehensive_score'] = score
                    product['match_details'] = '|'.join(match_details)
                    matches.append(product)
            
            # Sort by comprehensive score
            matches.sort(key=lambda x: x.get('comprehensive_score', 0), reverse=True)
            return matches[:10]  # Return top 10 matches
            
        except Exception as e:
            logging.error(f"Error in comprehensive matching: {e}")
            return []
    
    def _find_partial_field_matches(self, json_item: dict) -> List[dict]:
        """
        Find matches using any available field data with very lenient thresholds.
        """
        try:
            matches = []
            all_products = self._get_all_products()
            
            for product in all_products:
                score = 0.0
                match_fields = []
                
                # Try to match any available field
                for json_key, json_value in json_item.items():
                    if not json_value or str(json_value).strip() == '':
                        continue
                    
                    json_str = str(json_value).strip().lower()
                    
                    # Try to find a corresponding field in the product
                    for product_key, product_value in product.items():
                        if not product_value or str(product_value).strip() == '':
                            continue
                        
                        product_str = str(product_value).strip().lower()
                        
                        # Calculate similarity
                        similarity = self._calculate_text_similarity(json_str, product_str)
                        if similarity > 0.4:  # Lenient threshold
                            score += similarity * 0.1
                            match_fields.append(f"{json_key}->{product_key}:{similarity:.2f}")
                
                # If we found any matches, include this product
                if score > 0.1:  # Very lenient threshold
                    product['partial_score'] = score
                    product['match_fields'] = '|'.join(match_fields)
                    matches.append(product)
            
            # Sort by partial score
            matches.sort(key=lambda x: x.get('partial_score', 0), reverse=True)
            return matches[:5]  # Return top 5 matches
            
        except Exception as e:
            logging.error(f"Error in partial field matching: {e}")
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        if text1 == text2:
            return 1.0
        
        # Simple similarity based on common words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        return len(common_words) / len(total_words) if total_words else 0.0
    
    def _calculate_key_word_similarity(self, json_name: str, product_name: str) -> float:
        """Calculate similarity based on key cannabis product words."""
        if not json_name or not product_name:
            return 0.0
        
        # Key cannabis product words that should match
        key_words = {
            'sativa', 'indica', 'hybrid', 'mix', 'mixed', 'sat', 'ind', 'hyb',
            'gummy', 'gummies', 'edible', 'edibles', 'chocolate', 'brownie', 'cookie',
            'vape', 'cart', 'cartridge', 'disposable', 'pod',
            'flower', 'bud', 'pre-roll', 'preroll', 'joint',
            'concentrate', 'wax', 'shatter', 'rosin', 'live resin', 'distillate',
            'tincture', 'oil', 'topical', 'cream', 'balm', 'salve',
            'capsule', 'pill', 'beverage', 'drink', 'soda',
            'mg', 'g', 'gram', 'ounce', 'oz', 'pound', 'lb',
            'ball', 'bite', 'roll', 'squeeze', 'tube', 'ups', 'xtra', 'extra',
            'dragon', 'caramel', 'assorted', 'dark', 'cbd', 'thc', 'pk'
        }
        
        # Extract words from both names
        json_words = set(re.findall(r'\b\w+\b', json_name.lower()))
        product_words = set(re.findall(r'\b\w+\b', product_name.lower()))
        
        # Find matching key words
        json_key_words = json_words.intersection(key_words)
        product_key_words = product_words.intersection(key_words)
        
        if not json_key_words and not product_key_words:
            return 0.0
        
        # Calculate similarity based on key word matches
        common_key_words = json_key_words.intersection(product_key_words)
        total_key_words = json_key_words.union(product_key_words)
        
        if not total_key_words:
            return 0.0
        
        return len(common_key_words) / len(total_key_words)
    
    def _calculate_pattern_similarity(self, json_name: str, product_name: str) -> float:
        """Calculate similarity based on product naming patterns."""
        if not json_name or not product_name:
            return 0.0
        
        # Pattern matching for Cultivera-style names
        patterns = [
            # Pattern: BRAND_TYPE_FLAVOR_WEIGHT (e.g., "BALL_SAT_CARAMEL_10pk")
            (r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_(\d+pk)$', r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_(\d+pk)$'),
            # Pattern: BRAND_TYPE_WEIGHT (e.g., "BITE_SAT_10pk")
            (r'^([A-Z]+)_([A-Z]+)_(\d+pk)$', r'^([A-Z]+)_([A-Z]+)_(\d+pk)$'),
            # Pattern: BRAND_TYPE_FLAVOR_WEIGHT (e.g., "ROLL_UPS_XTRA_DRAGON_BALM_1:1_3.4oz")
            (r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([0-9:]+)_([0-9.]+oz)$', r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([0-9:]+)_([0-9.]+oz)$'),
            # Pattern: BRAND_TYPE_FLAVOR_WEIGHT (e.g., "SQUEEZE_TUBE_XTRA_DRAGON_CBD_3.4oz")
            (r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([0-9.]+oz)$', r'^([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([A-Z]+)_([0-9.]+oz)$'),
        ]
        
        json_lower = json_name.lower()
        product_lower = product_name.lower()
        
        # Check if both names follow similar patterns
        for json_pattern, product_pattern in patterns:
            json_match = re.match(json_pattern, json_name)
            product_match = re.match(product_pattern, product_name)
            
            if json_match and product_match:
                # Both follow the same pattern, check if components match
                json_groups = json_match.groups()
                product_groups = product_match.groups()
                
                if len(json_groups) == len(product_groups):
                    matches = sum(1 for j, p in zip(json_groups, product_groups) if j.lower() == p.lower())
                    return matches / len(json_groups)
        
        # Special handling for underscore vs space-separated names
        if '_' in json_name and ' ' in product_name:
            # Convert underscore to space for comparison
            json_space = json_name.replace('_', ' ')
            space_similarity = self._calculate_text_similarity(json_space, product_name)
            if space_similarity > 0.3:
                return space_similarity * 0.8  # Weight it slightly less than exact pattern matches
        
        # Check for common prefixes/suffixes
        common_prefixes = ['ball_', 'bite_', 'roll_', 'squeeze_', 'tube_']
        common_suffixes = ['_10pk', '_3.4oz', '_1:1', '_cbd', '_thc']
        
        json_prefix_score = 0
        json_suffix_score = 0
        product_prefix_score = 0
        product_suffix_score = 0
        
        for prefix in common_prefixes:
            if json_lower.startswith(prefix):
                json_prefix_score += 1
            if product_lower.startswith(prefix):
                product_prefix_score += 1
        
        for suffix in common_suffixes:
            if json_lower.endswith(suffix):
                json_suffix_score += 1
            if product_lower.endswith(suffix):
                product_suffix_score += 1
        
        # Calculate pattern similarity
        prefix_similarity = min(json_prefix_score, product_prefix_score) / max(json_prefix_score, product_prefix_score) if max(json_prefix_score, product_prefix_score) > 0 else 0
        suffix_similarity = min(json_suffix_score, product_suffix_score) / max(json_suffix_score, product_suffix_score) if max(json_suffix_score, product_suffix_score) > 0 else 0
        
        return (prefix_similarity + suffix_similarity) / 2
    
    def _find_cultivera_specialized_matches(self, json_item: dict) -> List[dict]:
        """Specialized matching for Cultivera-style products with underscore naming conventions."""
        try:
            json_name = str(json_item.get("product_name", "")).strip().lower()
            json_vendor = str(json_item.get("vendor", "")).strip().lower()
            json_brand = str(json_item.get("brand", "")).strip().lower()
            json_type = str(json_item.get("product_type", "")).strip().lower()
            json_weight = str(json_item.get("weight", "")).strip().lower()
            json_strain = str(json_item.get("strain_name", "")).strip().lower()
            
            if not json_name:
                return []
            
            all_products = self._get_all_products()
            matches = []
            
            # Cultivera-specific matching strategies
            for product in all_products:
                product_name = str(product.get('Product Name*', '') or product.get('original_name', '')).strip().lower()
                product_vendor = str(product.get('Vendor/Supplier*', '') or product.get('Vendor', '')).strip().lower()
                product_brand = str(product.get('Product Brand', '')).strip().lower()
                product_type = str(product.get('Product Type*', '')).strip().lower()
                product_weight = str(product.get('Weight*', '')).strip().lower()
                product_strain = str(product.get('Strain*', '')).strip().lower()
                
                score = 0.0
                match_reasons = []
                
                # Strategy 1: Underscore pattern matching
                if '_' in json_name and '_' in product_name:
                    json_parts = json_name.split('_')
                    product_parts = product_name.split('_')
                    
                    # Check for common parts
                    common_parts = set(json_parts).intersection(set(product_parts))
                    if common_parts:
                        part_similarity = len(common_parts) / max(len(json_parts), len(product_parts))
                        score += part_similarity * 0.4
                        match_reasons.append(f"underscore_parts:{part_similarity:.2f}")
                
                # Strategy 2: Brand prefix matching (BALL_, BITE_, ROLL_, etc.)
                cultivera_prefixes = ['ball', 'bite', 'roll', 'squeeze', 'tube']
                for prefix in cultivera_prefixes:
                    if json_name.startswith(prefix) and product_name.startswith(prefix):
                        score += 0.3
                        match_reasons.append(f"brand_prefix:{prefix}")
                        break
                
                # Strategy 3: Package count matching (10pk, 5pk, etc.)
                json_pk_match = re.search(r'(\d+)pk', json_name)
                product_pk_match = re.search(r'(\d+)pk', product_name)
                if json_pk_match and product_pk_match:
                    if json_pk_match.group(1) == product_pk_match.group(1):
                        score += 0.25
                        match_reasons.append(f"package_count:{json_pk_match.group(1)}")
                
                # Strategy 4: Weight matching (3.4oz, 1oz, etc.)
                json_weight_match = re.search(r'(\d+\.?\d*)oz', json_name)
                product_weight_match = re.search(r'(\d+\.?\d*)oz', product_name)
                if json_weight_match and product_weight_match:
                    if json_weight_match.group(1) == product_weight_match.group(1):
                        score += 0.2
                        match_reasons.append(f"weight_match:{json_weight_match.group(1)}")
                
                # Strategy 5: Strain matching
                if json_strain and product_strain and json_strain != 'mix':
                    strain_similarity = self._calculate_text_similarity(json_strain, product_strain)
                    if strain_similarity > 0.3:
                        score += strain_similarity * 0.15
                        match_reasons.append(f"strain_match:{strain_similarity:.2f}")
                
                # Strategy 6: Type matching
                if json_type and product_type:
                    type_similarity = self._calculate_text_similarity(json_type, product_type)
                    if type_similarity > 0.3:
                        score += type_similarity * 0.1
                        match_reasons.append(f"type_match:{type_similarity:.2f}")
                
                # Strategy 7: Fuzzy matching on cleaned names (remove underscores and numbers)
                json_clean = re.sub(r'[_\d]+', '', json_name)
                product_clean = re.sub(r'[_\d]+', '', product_name)
                if json_clean and product_clean:
                    from fuzzywuzzy import fuzz
                    clean_ratio = fuzz.ratio(json_clean, product_clean)
                    if clean_ratio > 40:
                        score += (clean_ratio / 100.0) * 0.2
                        match_reasons.append(f"clean_fuzzy:{clean_ratio}")
                
                # Only consider matches with reasonable scores
                if score > 0.15:  # Lower threshold for Cultivera products
                    product['fuzzy_score'] = score * 100
                    product['match_reasons'] = ', '.join(match_reasons)
                    product['original_name'] = product.get('Product Name*', 'Unknown')
                    matches.append(product)
            
            # Sort by score descending
            matches.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            logging.info(f"Cultivera specialized matching found {len(matches)} potential matches for '{json_name}'")
            return matches[:5]  # Return top 5 matches
            
        except Exception as e:
            logging.error(f"Error in Cultivera specialized matching: {e}")
            return []
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity with fuzzy matching."""
        if not name1 or not name2:
            return 0.0
        
        # Use fuzzy matching for names
        try:
            from fuzzywuzzy import fuzz
            return fuzz.ratio(name1.lower(), name2.lower()) / 100.0
        except ImportError:
            return self._calculate_text_similarity(name1, name2)
    
    def _calculate_vendor_similarity(self, vendor1: str, vendor2: str) -> float:
        """Calculate vendor similarity."""
        return self._calculate_text_similarity(vendor1, vendor2)
    
    def _calculate_brand_similarity(self, brand1: str, brand2: str) -> float:
        """Calculate brand similarity."""
        return self._calculate_text_similarity(brand1, brand2)
    
    def _calculate_type_similarity(self, type1: str, type2: str) -> float:
        """Calculate product type similarity."""
        return self._calculate_text_similarity(type1, type2)
    
    def _calculate_weight_similarity(self, weight1: str, weight2: str) -> float:
        """Calculate weight similarity."""
        return self._calculate_text_similarity(weight1, weight2)
    
    def _calculate_strain_similarity(self, strain1: str, strain2: str) -> float:
        """Calculate strain similarity."""
        return self._calculate_text_similarity(strain1, strain2)
    
    def _get_product_vendor(self, product: dict) -> str:
        """Safely get vendor from a product dict supporting multiple schemas."""
        try:
            if not isinstance(product, dict):
                return ""
            # Prefer Excel schema exact column first
            vendor = product.get('Vendor/Supplier*')
            if vendor is None or str(vendor).strip() == '':
                # Support simplified key if present
                vendor = product.get('Vendor')
            return str(vendor).strip() if vendor is not None else ""
        except Exception:
            return ""

    def _create_product_from_db_row(self, row: dict) -> dict:
        """Create a product object in the same shape as Excel match from a DB row dict."""
        name = row.get('Product Name*') or row.get('product_name') or ''
        vendor = row.get('Vendor/Supplier*') or row.get('vendor') or ''
        brand = row.get('Product Brand') or row.get('brand') or ''
        ptype = row.get('Product Type*') or row.get('product_type') or ''
        weight = row.get('Weight*') or row.get('weight') or ''
        ratio = row.get('Ratio_or_THC_CBD') or row.get('Ratio') or ''
        strain = row.get('Product Strain') or row.get('strain_name') or ''

        product = {
            'Product Name*': name,
            'Vendor': vendor,
            'Vendor/Supplier*': vendor,
            'Product Brand': brand,
            'Product Type*': ptype,
            'Weight*': weight,
            'Ratio_or_THC_CBD': ratio,
            'Product Strain': strain,
            'displayName': name,
            'Source': 'DB_ALL'
        }
        return product

    def _find_enhanced_fuzzy_matches(self, json_item: dict) -> List[dict]:
        """Enhanced fuzzy matching using multiple strategies for better coverage."""
        try:
            json_name = str(json_item.get("product_name", "")).strip().lower()
            json_vendor = str(json_item.get("vendor", "")).strip().lower()
            json_brand = str(json_item.get("brand", "")).strip().lower()
            json_type = str(json_item.get("product_type", "")).strip().lower()
            json_weight = str(json_item.get("weight", "")).strip().lower()
            
            if not json_name:
                return []
            
            all_products = self._get_all_products()
            matches = []
            
            for product in all_products:
                product_name = str(product.get('Product Name*', '') or product.get('original_name', '')).strip().lower()
                product_vendor = str(product.get('Vendor/Supplier*', '') or product.get('Vendor', '')).strip().lower()
                product_brand = str(product.get('Product Brand', '')).strip().lower()
                product_type = str(product.get('Product Type*', '')).strip().lower()
                product_weight = str(product.get('Weight*', '')).strip().lower()
                
                score = 0.0
                match_reasons = []
                
                # Strategy 1: Fuzzy string matching on product names
                from fuzzywuzzy import fuzz
                name_ratio = fuzz.ratio(json_name, product_name)
                if name_ratio > 30:  # Lower threshold for more matches
                    score += (name_ratio / 100.0) * 0.4
                    match_reasons.append(f"name_fuzzy:{name_ratio}")
                
                # Strategy 2: Partial string matching
                partial_ratio = fuzz.partial_ratio(json_name, product_name)
                if partial_ratio > 40:
                    score += (partial_ratio / 100.0) * 0.3
                    match_reasons.append(f"partial_fuzzy:{partial_ratio}")
                
                # Strategy 3: Token set ratio (ignores word order)
                token_ratio = fuzz.token_set_ratio(json_name, product_name)
                if token_ratio > 35:
                    score += (token_ratio / 100.0) * 0.2
                    match_reasons.append(f"token_fuzzy:{token_ratio}")
                
                # Strategy 4: Vendor/brand matching bonus
                if json_vendor and product_vendor:
                    vendor_similarity = self._calculate_text_similarity(json_vendor, product_vendor)
                    if vendor_similarity > 0.4:
                        score += vendor_similarity * 0.1
                        match_reasons.append(f"vendor_match:{vendor_similarity:.2f}")
                
                # Strategy 5: Type matching bonus
                if json_type and product_type:
                    type_similarity = self._calculate_text_similarity(json_type, product_type)
                    if type_similarity > 0.4:
                        score += type_similarity * 0.1
                        match_reasons.append(f"type_match:{type_similarity:.2f}")
                
                # Strategy 6: Weight matching bonus
                if json_weight and product_weight:
                    weight_similarity = self._calculate_text_similarity(json_weight, product_weight)
                    if weight_similarity > 0.4:
                        score += weight_similarity * 0.1
                        match_reasons.append(f"weight_match:{weight_similarity:.2f}")
                
                # Strategy 7: Key word matching for difficult cases
                key_word_score = self._calculate_key_word_similarity(json_name, product_name)
                if key_word_score > 0:
                    score += key_word_score * 0.15
                    match_reasons.append(f"key_words:{key_word_score:.2f}")
                
                # Strategy 8: Pattern-based matching for Cultivera-style names
                pattern_score = self._calculate_pattern_similarity(json_name, product_name)
                if pattern_score > 0:
                    score += pattern_score * 0.2
                    match_reasons.append(f"pattern_match:{pattern_score:.2f}")
                
                # Strategy 9: Token sort ratio (handles word order variations)
                token_sort_ratio = fuzz.token_sort_ratio(json_name, product_name)
                if token_sort_ratio > 30:
                    score += (token_sort_ratio / 100.0) * 0.2
                    match_reasons.append(f"token_sort_fuzzy:{token_sort_ratio}")
                
                # Only consider matches with reasonable scores (lowered threshold)
                if score > 0.2:  # Lowered from 0.25
                    product['fuzzy_score'] = score * 100
                    product['match_reasons'] = ', '.join(match_reasons)
                    product['original_name'] = product.get('Product Name*', 'Unknown')
                    matches.append(product)
            
            # Sort by score descending
            matches.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            logging.info(f"Enhanced fuzzy matching found {len(matches)} potential matches for '{json_name}'")
            return matches[:8]  # Return top 8 matches (increased from 5)
            
        except Exception as e:
            logging.error(f"Error in enhanced fuzzy matching: {e}")
            return []

    def _find_ceres_specialized_matches(self, json_item: dict) -> List[dict]:
        """Specialized matching for Ceres products that have generic names."""
        try:
            json_name = str(json_item.get("product_name", "")).strip().lower()
            json_vendor = str(json_item.get("vendor", "")).strip().lower()
            json_brand = str(json_item.get("brand", "")).strip().lower()
            json_type = str(json_item.get("product_type", "")).strip().lower()
            json_weight = str(json_item.get("weight", "")).strip().lower()
            json_strain = str(json_item.get("strain_name", "")).strip().lower()
            
            if not json_name:
                return []
            
            all_products = self._get_all_products()
            matches = []
            
            # Ceres-specific matching strategies
            for product in all_products:
                product_name = str(product.get('Product Name*', '') or product.get('original_name', '')).strip().lower()
                product_vendor = str(product.get('Vendor/Supplier*', '') or product.get('Vendor', '')).strip().lower()
                product_brand = str(product.get('Product Brand', '')).strip().lower()
                product_type = str(product.get('Product Type*', '')).strip().lower()
                product_weight = str(product.get('Weight*', '')).strip().lower()
                product_strain = str(product.get('Product Strain', '')).strip().lower()
                
                # Skip if not a Ceres product
                if 'ceres' not in product_vendor.lower() and 'ceres' not in product_brand.lower():
                    continue
                
                score = 0.0
                match_reasons = []
                
                # Strategy 1: Partial word matching for generic names
                json_words = set(json_name.split())
                product_words = set(product_name.split())
                common_words = json_words.intersection(product_words)
                
                if common_words:
                    word_score = len(common_words) / max(len(json_words), len(product_words))
                    score += word_score * 0.4
                    match_reasons.append(f"word_match:{word_score:.2f}")
                
                # Strategy 2: Type matching (very important for Ceres)
                if json_type and product_type:
                    type_similarity = self._calculate_text_similarity(json_type, product_type)
                    if type_similarity > 0.3:
                        score += type_similarity * 0.3
                        match_reasons.append(f"type_match:{type_similarity:.2f}")
                
                # Strategy 3: Weight matching
                if json_weight and product_weight:
                    weight_similarity = self._calculate_text_similarity(json_weight, product_weight)
                    if weight_similarity > 0.3:
                        score += weight_similarity * 0.2
                        match_reasons.append(f"weight_match:{weight_similarity:.2f}")
                
                # Strategy 4: Strain matching (if available)
                if json_strain and product_strain:
                    strain_similarity = self._calculate_text_similarity(json_strain, product_strain)
                    if strain_similarity > 0.3:
                        score += strain_similarity * 0.1
                        match_reasons.append(f"strain_match:{strain_similarity:.2f}")
                
                # Strategy 5: Special Ceres product name patterns
                ceres_patterns = {
                    'sativa': ['sativa', 'sat'],
                    'indica': ['indica', 'ind'],
                    'hybrid': ['hybrid', 'hyb'],
                    'capsules': ['capsule', 'cap', 'caps'],
                    'tincture': ['tincture', 'tinc'],
                    'balm': ['balm', 'cream'],
                    'chews': ['chew', 'gummy', 'edible'],
                    'boost': ['boost', 'immune'],
                    'dragon': ['dragon'],
                    'chill': ['chill', 'relax'],
                    'lifted': ['lifted', 'energ']
                }
                
                for pattern_key, pattern_words in ceres_patterns.items():
                    json_has_pattern = any(word in json_name for word in pattern_words)
                    product_has_pattern = any(word in product_name for word in pattern_words)
                    
                    if json_has_pattern and product_has_pattern:
                        score += 0.15
                        match_reasons.append(f"pattern_match:{pattern_key}")
                
                # Only consider matches with reasonable scores
                if score > 0.2:
                    product['fuzzy_score'] = score * 100
                    product['match_reasons'] = ', '.join(match_reasons)
                    product['original_name'] = product.get('Product Name*', 'Unknown')
                    matches.append(product)
            
            # Sort by score descending
            matches.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            logging.info(f"Ceres specialized matching found {len(matches)} potential matches for '{json_name}'")
            return matches[:5]  # Return top 5 matches
            
        except Exception as e:
            logging.error(f"Error in Ceres specialized matching: {e}")
            return []

    def _get_all_products(self) -> List[dict]:
        """Get all available products for matching, DATABASE FIRST with priority."""
        try:
            candidates: List[dict] = []
            
            # PRIORITY 1: Database products (authoritative source)
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                db_products = product_db.get_all_products()
                if db_products:
                    # Mark database products with priority flag
                    for product in db_products:
                        product['_source'] = 'database'
                        product['_priority'] = 1  # Highest priority
                    candidates.extend(db_products)
                    logging.info(f"Loaded {len(db_products)} products from DATABASE (highest priority)")
            except Exception as db_err:
                logging.warning(f"Database candidates unavailable: {db_err}")

            # PRIORITY 2: Excel rows (secondary source)
            if hasattr(self, 'excel_processor') and self.excel_processor and hasattr(self.excel_processor, 'df') and self.excel_processor.df is not None:
                try:
                    excel_count = 0
                    for _, row in self.excel_processor.df.iterrows():
                        row_dict = row.to_dict()
                        row_dict['_source'] = 'excel'
                        row_dict['_priority'] = 2  # Lower priority than database
                        candidates.append(row_dict)
                        excel_count += 1
                    logging.info(f"Loaded {excel_count} products from EXCEL (secondary priority)")
                except Exception as xl_err:
                    logging.debug(f"Excel candidates unavailable: {xl_err}")

            logging.info(f"Total candidates for matching: {len(candidates)} (Database: {len([c for c in candidates if c.get('_source') == 'database'])}, Excel: {len([c for c in candidates if c.get('_source') == 'excel'])})")
            return candidates
        except Exception as e:
            logging.error(f"Error getting all products: {e}")
            return []
    
    def _find_exact_name_matches(self, json_name: str) -> List[dict]:
        """Find exact name matches in the cache using indexed lookup."""
        normalized_name = self._normalize(json_name)
        
        # Use indexed cache for O(1) lookup instead of O(n) linear search
        if self._indexed_cache and 'exact_names' in self._indexed_cache:
            return self._indexed_cache['exact_names'].get(normalized_name, [])
        
        # Fallback to linear search if index not available
        matches = []
        if self._sheet_cache is not None:
            for cache_item in self._sheet_cache:
                if self._normalize(cache_item.get("original_name", "")) == normalized_name:
                    matches.append(cache_item)
        else:
            # Use database products if sheet cache is None
            all_products = self._get_all_products()
            for product in all_products:
                product_name = product.get("Product Name*", "")
                if self._normalize(product_name) == normalized_name:
                    # Convert to cache format
                    cache_item = {
                        "original_name": product_name,
                        "vendor": product.get("Vendor/Supplier*", ""),
                        "brand": product.get("Product Brand", ""),
                        "type": product.get("Product Type*", ""),
                        "_source": product.get("_source", "database"),
                        "_priority": product.get("_priority", 1)
                    }
                    matches.append(cache_item)
        
        return matches
    
    def _find_vendor_exact_name_matches(self, json_name: str, json_vendor: str) -> List[dict]:
        """Find exact name matches within the same vendor using indexed lookup."""
        normalized_name = self._normalize(json_name)
        
        # Use indexed cache for O(1) lookup
        if self._indexed_cache and 'vendor_exact_names' in self._indexed_cache:
            vendor_key = f"{normalized_name}|{json_vendor.lower()}"
            return self._indexed_cache['vendor_exact_names'].get(vendor_key, [])
        
        # Fallback to linear search if index not available
        matches = []
        if self._sheet_cache is not None:
            for cache_item in self._sheet_cache:
                cache_vendor = str(cache_item.get("vendor", ""))
                if (self._normalize(cache_item.get("original_name", "")) == normalized_name and
                    self._validate_vendor_match(json_vendor, cache_vendor)):
                    matches.append(cache_item)
        else:
            # Use database products if sheet cache is None
            all_products = self._get_all_products()
            for product in all_products:
                product_name = product.get("Product Name*", "")
                cache_vendor = str(product.get("Vendor/Supplier*", ""))
                if (self._normalize(product_name) == normalized_name and
                    self._validate_vendor_match(json_vendor, cache_vendor)):
                    # Convert to cache format
                    cache_item = {
                        "original_name": product_name,
                        "vendor": cache_vendor,
                        "brand": product.get("Product Brand", ""),
                        "type": product.get("Product Type*", ""),
                        "_source": product.get("_source", "database"),
                        "_priority": product.get("_priority", 1)
                    }
                    matches.append(cache_item)
        
        return matches
    
    def _find_fuzzy_name_matches(self, json_name: str, json_vendor: str = None, threshold: int = 50) -> List[dict]:
        """Find fuzzy name matches using optimized fuzzywuzzy."""
        matches = []
        
        # Get all potential candidates
        candidates = []
        if json_vendor:
            # Filter by vendor first - much stricter filtering
            # Use database products if sheet cache is None
            if self._sheet_cache is None:
                all_products = self._get_all_products()
                for product in all_products:
                    cache_vendor = str(product.get("Vendor/Supplier*", "") or product.get("vendor", ""))
                    # Use strict vendor validation
                    if self._validate_vendor_match(json_vendor, cache_vendor):
                        # Convert to cache format
                        cache_item = {
                            "original_name": product.get("Product Name*", ""),
                            "vendor": cache_vendor,
                            "brand": product.get("Product Brand", ""),
                            "type": product.get("Product Type*", ""),
                            "_source": product.get("_source", "database"),
                            "_priority": product.get("_priority", 1)
                        }
                        candidates.append(cache_item)
            else:
                for cache_item in self._sheet_cache:
                    cache_vendor = str(cache_item.get("vendor", ""))
                    # Use strict vendor validation
                    if self._validate_vendor_match(json_vendor, cache_vendor):
                        candidates.append(cache_item)
        else:
            # Use all candidates if no vendor specified
            if self._sheet_cache is None:
                # Use database products if sheet cache is None
                all_products = self._get_all_products()
                candidates = []
                for product in all_products:
                    # Convert to cache format
                    cache_item = {
                        "original_name": product.get("Product Name*", ""),
                        "vendor": product.get("Vendor/Supplier*", ""),
                        "brand": product.get("Product Brand", ""),
                        "type": product.get("Product Type*", ""),
                        "_source": product.get("_source", "database"),
                        "_priority": product.get("_priority", 1)
                    }
                    candidates.append(cache_item)
            else:
                candidates = self._sheet_cache
        
        # Limit candidates to prevent excessive processing
        max_candidates = 1000
        if len(candidates) > max_candidates:
            candidates = candidates[:max_candidates]
        
        # Use fuzzywuzzy to find best matches with early termination
        json_name_lower = json_name.lower()
        for cache_item in candidates:
            cache_name = cache_item.get("original_name", "")
            if cache_name:
                cache_name_lower = cache_name.lower()
                
                # Use only the most effective algorithm first (ratio is fastest)
                ratio = fuzz.ratio(json_name_lower, cache_name_lower)
                
                # Early termination if ratio is too low
                if ratio < threshold - 10:  # Give some buffer
                    continue
                
                # Only run additional algorithms if ratio is promising
                if ratio >= threshold:
                    # Use the best of ratio and partial_ratio (most effective combination)
                    partial_ratio = fuzz.partial_ratio(json_name_lower, cache_name_lower)
                    best_score = max(ratio, partial_ratio)
                else:
                    # Try partial_ratio as fallback
                    partial_ratio = fuzz.partial_ratio(json_name_lower, cache_name_lower)
                    if partial_ratio < threshold:
                        continue
                    best_score = partial_ratio
                
                if best_score >= threshold:
                    cache_item_copy = cache_item.copy()
                    cache_item_copy['fuzzy_score'] = best_score
                    matches.append(cache_item_copy)
                    
                    # Early termination if we have enough good matches
                    if len(matches) >= 10:
                        break
        
        # Sort by score (highest first) and limit results
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        return matches[:5]  # Return only top 5 matches
    
    def _find_strain_based_matches(self, json_strain: str, json_vendor: str = None, json_type: str = None) -> List[dict]:
        """Find matches based on strain name with enhanced strain recognition."""
        matches = []
        
        # Enhanced strain normalization
        normalized_strain = self._normalize_strain_name(json_strain)
        
        for cache_item in self._sheet_cache:
            cache_name = str(cache_item.get("original_name", "")).lower()
            cache_vendor = str(cache_item.get("vendor", ""))
            cache_strain = str(cache_item.get("strain", "")).lower()
            
            # Check multiple strain matching strategies
            strain_match = False
            
            # Strategy 1: Direct strain name match
            if json_strain in cache_name or json_strain in cache_strain:
                strain_match = True
            # Strategy 2: Normalized strain match
            elif normalized_strain and (normalized_strain in cache_name or normalized_strain in cache_strain):
                strain_match = True
            # Strategy 3: Partial strain match (for compound names like "Blue Dream")
            elif self._partial_strain_match(json_strain, cache_name):
                strain_match = True
            
            if strain_match:
                # Apply vendor filtering if specified
                if not json_vendor or self._validate_vendor_match(json_vendor, cache_vendor):
                    # Apply product type filtering if specified
                    if not json_type or self._product_types_compatible(json_type, cache_item):
                        # Calculate strain match score
                        strain_score = self._calculate_strain_match_score(json_strain, cache_name, cache_strain)
                        cache_item_copy = cache_item.copy()
                        cache_item_copy['strain_score'] = strain_score
                        matches.append(cache_item_copy)
        
        # Sort by strain match score
        matches.sort(key=lambda x: x.get('strain_score', 0), reverse=True)
        return matches
    
    def _find_brand_type_weight_matches(self, json_brand: str, json_type: str, json_weight: str, json_vendor: str = None) -> List[dict]:
        """Find matches based on brand, type, and weight combination."""
        matches = []
        
        for cache_item in self._sheet_cache:
            cache_brand = str(cache_item.get("brand", "")).strip().lower()
            cache_name = str(cache_item.get("original_name", "")).lower()
            cache_vendor = str(cache_item.get("vendor", ""))
            
            # Check brand match
            brand_match = (json_brand in cache_brand or cache_brand in json_brand or
                          fuzz.ratio(json_brand, cache_brand) >= 80)
            
            # Check type match
            type_match = self._product_types_compatible(json_type, cache_item)
            
            # Check weight match
            weight_match = self._weights_compatible(json_weight, cache_name)
            
            # Check vendor match
            vendor_match = (not json_vendor or self._validate_vendor_match(json_vendor, cache_vendor))
            
            # Calculate composite score
            score = 0
            if brand_match: score += 0.4
            if type_match: score += 0.3
            if weight_match: score += 0.2
            if vendor_match: score += 0.1
            
            if score >= 0.4:  # Require at least brand + type match (reduced from 0.6 to 0.4)
                cache_item_copy = cache_item.copy()
                cache_item_copy['composite_score'] = score
                matches.append(cache_item_copy)
        
        # Sort by composite score
        matches.sort(key=lambda x: x['composite_score'], reverse=True)
        return matches
    
    def _get_vendor_variations(self, vendor: str) -> List[str]:
        """Get known vendor name variations - much more strict to avoid false matches."""
        vendor_variations = {
            # Only exact variations of the same company
            'dank czar': ['dcz holdings inc', 'dcz holdings inc.', 'dcz', 'dank czar holdings'],
            'dcz holdings': ['dank czar', 'dcz', 'dcz holdings inc', 'dcz holdings inc.'],
            'dcz holdings inc': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc.'],
            'dcz holdings inc.': ['dank czar', 'dcz', 'dcz holdings', 'dcz holdings inc'],
            
            # JSM LLC is separate from Dank Czar - remove cross-references
            'jsm llc': ['jsm', 'jsm labs'],
            
            # Hustler's Ambition variations
            'hustler\'s ambition': ['1555 industrial llc', 'hustlers ambition'],
            'hustlers ambition': ['1555 industrial llc', 'hustler\'s ambition'],
            '1555 industrial llc': ['hustler\'s ambition', 'hustlers ambition'],
            
            # Omega variations only
            'omega': ['omega labs', 'omega cannabis'],
            
            # Airo Pro variations only
            'airo pro': ['airo', 'airopro'],
            'jsm': ['jsm llc', 'jsm labs'],
            'harmony': ['harmony farms', 'harmony cannabis'],
            
            # Additional Cultivera vendor variations
            'blue roots cannabis': ['blue roots', 'blue roots cannabis llc', 'blue roots llc'],
            'grow op farms': ['grow op', 'grow op farms llc', 'grow op llc'],
            'collections cannabis': ['collections', 'collections cannabis llc', 'collections llc'],
            'cloud 9 farms': ['cloud 9', 'cloud 9 farms llc', 'cloud 9 llc'],
            'the collective': ['collective', 'collective cannabis', 'collective llc'],
            '1555 industrial': ['1555 industrial llc', '1555 llc', '1555 industrial cannabis'],
        }
        
        return vendor_variations.get(vendor, [])
    
    def _validate_vendor_match(self, json_vendor: str, cache_vendor: str) -> bool:
        """Validate that vendor match is truly appropriate."""
        if not json_vendor or not cache_vendor:
            return False
            
        json_vendor_lower = json_vendor.strip().lower()
        cache_vendor_lower = cache_vendor.strip().lower()
        
        # Exact match is always valid
        if json_vendor_lower == cache_vendor_lower:
            return True
            
        # Check vendor variations
        vendor_variations = self._get_vendor_variations(json_vendor_lower)
        if cache_vendor_lower in vendor_variations:
            return True
            
        # Check if vendor names are very similar (e.g., "Dank Czar" vs "Dank Czar Holdings")
        if (json_vendor_lower in cache_vendor_lower or 
            cache_vendor_lower in json_vendor_lower):
            # Only allow if the difference is minimal (e.g., "Holdings", "Inc", etc.)
            allowed_suffixes = [' holdings', ' inc', ' inc.', ' llc', ' corp', ' corporation']
            base_vendor = json_vendor_lower
            for suffix in allowed_suffixes:
                if base_vendor.endswith(suffix):
                    base_vendor = base_vendor[:-len(suffix)]
                    break
                    
            if base_vendor in cache_vendor_lower or cache_vendor_lower in base_vendor:
                return True
        
        # IMPROVED: Add fuzzy vendor matching as fallback to improve match rate
        try:
            from fuzzywuzzy import fuzz
            similarity = fuzz.ratio(json_vendor_lower, cache_vendor_lower)
            # Allow vendors with 70% similarity or higher
            if similarity >= 70:
                logging.debug(f"✅ Fuzzy vendor match: '{json_vendor}' ≈ '{cache_vendor}' (similarity: {similarity}%)")
                return True
        except ImportError:
            # Basic fallback if fuzzywuzzy not available
            common_words = set(json_vendor_lower.split()) & set(cache_vendor_lower.split())
            if len(common_words) >= 1 and len(common_words) >= min(len(json_vendor_lower.split()), len(cache_vendor_lower.split())) * 0.5:
                logging.debug(f"✅ Basic vendor match: '{json_vendor}' ≈ '{cache_vendor}' (common words: {common_words})")
                return True
                
        return False
    
    def _find_weight_based_matches(self, json_weight: str, json_type: str, json_vendor: str = None) -> List[dict]:
        """Find matches based on weight and product type compatibility."""
        matches = []
        
        # Normalize weight for comparison
        json_weight_normalized = self._normalize_weight(json_weight)
        if not json_weight_normalized:
            return matches
        
        for cache_item in self._sheet_cache:
            cache_weight = str(cache_item.get("weight", ""))
            cache_type = str(cache_item.get("product_type", "")).lower()
            
            # Check weight compatibility
            if self._weights_compatible(json_weight_normalized, cache_weight):
                # Check product type compatibility
                if self._product_types_compatible(json_type, cache_item):
                    # Apply vendor filtering if specified
                    if not json_vendor or self._validate_vendor_match(json_vendor, str(cache_item.get("vendor", ""))):
                        # Calculate score based on weight similarity
                        weight_score = self._calculate_weight_similarity(json_weight_normalized, cache_weight)
                        cache_item_copy = cache_item.copy()
                        cache_item_copy['weight_score'] = weight_score
                        matches.append(cache_item_copy)
        
        # Sort by weight similarity score
        matches.sort(key=lambda x: x.get('weight_score', 0), reverse=True)
        return matches
    
    def _find_strain_weight_matches(self, json_strain: str, json_weight: str, json_vendor: str = None) -> List[dict]:
        """Find matches based on strain name and weight combination."""
        matches = []
        
        # Normalize weight for comparison
        json_weight_normalized = self._normalize_weight(json_weight)
        if not json_weight_normalized:
            return matches
        
        for cache_item in self._sheet_cache:
            cache_strain = str(cache_item.get("strain", "")).lower()
            cache_weight = str(cache_item.get("weight", ""))
            
            # Check if strain appears in the cache item
            if json_strain in cache_strain or cache_strain in json_strain:
                # Check weight compatibility
                if self._weights_compatible(json_weight_normalized, cache_weight):
                    # Apply vendor filtering if specified
                    if not json_vendor or self._validate_vendor_match(json_vendor, str(cache_item.get("vendor", ""))):
                        # Calculate composite score
                        strain_score = 0.7  # Base score for strain match
                        weight_score = self._calculate_weight_similarity(json_weight_normalized, cache_weight)
                        composite_score = (strain_score + weight_score) / 2
                        
                        cache_item_copy = cache_item.copy()
                        cache_item_copy['composite_score'] = composite_score
                        matches.append(cache_item_copy)
        
        # Sort by composite score
        matches.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        return matches
    
    def _normalize_weight(self, weight: str) -> Optional[float]:
        """Normalize weight string to float value for comparison."""
        try:
            # Remove common units and convert to float
            weight_clean = weight.lower().replace('g', '').replace('gram', '').replace('grams', '').replace('mg', '').replace('milligram', '').replace('milligrams', '').strip()
            return float(weight_clean)
        except (ValueError, AttributeError):
            return None
    
    def _calculate_weight_similarity(self, weight1: float, weight2: float) -> float:
        """Calculate similarity score between two weights."""
        try:
            # Convert to float if strings
            w1 = float(weight1) if isinstance(weight1, str) else weight1
            w2 = float(weight2) if isinstance(weight2, str) else weight2
            
            # Calculate percentage difference
            if w1 == 0 or w2 == 0:
                return 0.0
            
            diff = abs(w1 - w2)
            max_weight = max(w1, w2)
            similarity = 1.0 - (diff / max_weight)
            
            return max(0.0, similarity)
        except (ValueError, TypeError):
            return 0.0
    
    def _normalize_strain_name(self, strain: str) -> Optional[str]:
        """Normalize strain name for better matching."""
        if not strain:
            return None
        
        # Common strain name variations and abbreviations
        strain_variations = {
            'og': 'og kush',
            'kush': 'og kush',
            'blue': 'blue dream',
            'dream': 'blue dream',
            'sour': 'sour diesel',
            'diesel': 'sour diesel',
            'wedding': 'wedding cake',
            'cake': 'wedding cake',
            'runtz': 'runtz',
            'gelato': 'gelato',
            'cookies': 'girl scout cookies',
            'gsc': 'girl scout cookies',
            'mac': 'mac 1',
            'mac1': 'mac 1'
        }
        
        strain_lower = strain.lower().strip()
        return strain_variations.get(strain_lower, strain_lower)
    
    def _partial_strain_match(self, json_strain: str, cache_name: str) -> bool:
        """Check for partial strain matches in compound names."""
        strain_words = json_strain.split()
        if len(strain_words) < 2:
            return False
        
        # Check if multiple words from strain appear in cache name
        matches = 0
        for word in strain_words:
            if len(word) > 2 and word in cache_name:  # Only consider words longer than 2 chars
                matches += 1
        
        # Require at least 2 words to match for compound strains
        return matches >= 2
    
    def _calculate_strain_match_score(self, json_strain: str, cache_name: str, cache_strain: str) -> float:
        """Calculate a score for strain matching quality."""
        score = 0.0
        
        # Exact match gets highest score
        if json_strain == cache_strain:
            score += 1.0
        elif json_strain in cache_strain or cache_strain in json_strain:
            score += 0.8
        
        # Name-based matching
        if json_strain in cache_name:
            score += 0.6
        
        # Partial matching for compound strains
        if self._partial_strain_match(json_strain, cache_name):
            score += 0.4
        
        return min(1.0, score)
    
    def _product_types_compatible(self, json_type: str, cache_item: dict) -> bool:
        """Check if product types are compatible."""
        cache_name = str(cache_item.get("original_name", "")).lower()
        
        # Define product type categories
        type_categories = {
            'flower': ['flower', 'bud', 'nug', 'usable marijuana'],
            'concentrate': ['concentrate', 'rosin', 'wax', 'shatter', 'live resin', 'distillate'],
            'vape': ['vape', 'cartridge', 'cart', 'all-in-one'],
            'edible': ['edible', 'gummy', 'chocolate', 'cookie', 'brownie'],
            'pre-roll': ['pre-roll', 'preroll', 'joint', 'blunt'],
            'tincture': ['tincture', 'drops', 'sublingual'],
            'topical': ['topical', 'cream', 'lotion', 'salve']
        }
        
        # Find JSON type category
        json_category = None
        for category, keywords in type_categories.items():
            if any(keyword in json_type for keyword in keywords):
                json_category = category
                break
        
        # Find cache item category
        cache_category = None
        for category, keywords in type_categories.items():
            if any(keyword in cache_name for keyword in keywords):
                cache_category = category
                break
        
        # Return True if categories match or if either is None (unknown)
        return json_category is None or cache_category is None or json_category == cache_category
    
    def _weights_compatible(self, json_weight: str, cache_name: str) -> bool:
        """Check if weights are compatible."""
        if not json_weight or not cache_name:
            return False
        
        # Extract weight from cache name using regex
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|mg)', cache_name.lower())
        if weight_match:
            cache_weight = float(weight_match.group(1))
            cache_unit = weight_match.group(2)
            
            # Extract weight from JSON
            json_weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|mg)', json_weight.lower())
            if json_weight_match:
                json_weight_val = float(json_weight_match.group(1))
                json_unit = json_weight_match.group(2)
                
                # Convert to same unit for comparison
                if json_unit == 'mg' and cache_unit == 'g':
                    json_weight_val = json_weight_val / 1000
                elif json_unit == 'g' and cache_unit == 'mg':
                    json_weight_val = json_weight_val * 1000
                
                # Allow 10% tolerance
                tolerance = 0.1
                return abs(json_weight_val - cache_weight) / cache_weight <= tolerance
        
        return False

    def get_product_database_priority_info(self) -> Dict[str, Any]:
        """
        Get information about Product Database priority status.
        
        Returns:
            Dictionary containing Product Database status and priority information
        """
        try:
            product_db = ProductDatabase()
            strains = product_db.get_all_strains()
            products = product_db.get_all_products()
            
            return {
                'enabled': True,
                'strain_count': len(strains),
                'product_count': len(products),
                'priority': 'HIGH - Product Database lookups prioritized over JSON exact matching',
                'message': f'Product Database available with {len(strains)} strains and {len(products)} products'
            }
        except Exception as e:
            return {
                'enabled': False,
                'strain_count': 0,
                'product_count': 0,
                'priority': 'DISABLED - JSON exact matching used as fallback',
                'message': f'Product Database not available: {e}'
            }
    
    def _process_description_from_product_name(self, product_name: str, weight: str = None, units: str = None) -> str:
        """Process description using the Excel processor formula with weight formatting."""
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
        
        # Add weight with hyphen staying with weight (space after hyphen) if provided
        if weight and units:
            weight_units = f"{str(round(float(weight or '1')))}{units or 'g'}"
            if weight_units and weight_units.lower() not in ['nan', 'none', 'null', '']:
                return f"{description} -\u00A0{weight_units}"
        
        return description

    def _determine_lineage_for_product(self, product_type: str, existing_lineage: str) -> str:
        """
        Determine the appropriate lineage for a product based on its type.
        
        Args:
            product_type: The product type (e.g., "edible (solid)", "flower", etc.)
            existing_lineage: Any existing lineage from the database
            
        Returns:
            The appropriate lineage string
        """
        # Import constants to check product type classification
        from src.core.constants import CLASSIC_TYPES
        
        # Check if this is a classic product type
        if product_type and product_type.strip().lower() in CLASSIC_TYPES:
            # Classic types (flower, pre-roll, concentrate, etc.) can use existing lineage or default to HYBRID
            return existing_lineage or "HYBRID"
        else:
            # Nonclassic types (edibles, tinctures, topicals, etc.) should ALWAYS be MIXED for blue color
            # This overrides any incorrect lineage values in the database
            return "MIXED"

    def _create_tag_from_database_info(self, db_info: Dict, vendor: str) -> Dict:
        """
        Create a product tag from Product Database information.
        This method is used when a Product Database lookup is successful.
        
        Args:
            db_info: Product information from the database
            vendor: The vendor name
            
        Returns:
            Dictionary containing the product tag information
        """
        try:
            # Helper function to clean product names
            def clean_product_name(name):
                if not name:
                    return name
                import re
                # Only remove obvious suffixes that are clearly not part of the product name
                cleaned = re.sub(r'\s*by\s+Dabstract\s+JSON\s*$', '', name, flags=re.IGNORECASE)
                # Remove extra whitespace but preserve the actual product name
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip()
            
            # Extract all available information from database using correct field names
            brand = db_info.get("Product Brand", "") or db_info.get("brand", "")
            product_type = db_info.get("Product Type*", "") or db_info.get("product_type", "")
            strain = db_info.get("Product Strain", "") or db_info.get("product_strain", "")
            lineage = db_info.get("Lineage", "") or db_info.get("lineage", "")
            price = str(db_info.get("Price", "") or db_info.get("price", ""))
            weight = str(db_info.get("Weight*", "") or db_info.get("weight", ""))
            units = str(db_info.get("Units", "") or db_info.get("units", ""))
            description = db_info.get("Description", "") or db_info.get("description", "")
            thc_result = str(db_info.get("THC test result", "") or db_info.get("thc_test_result", ""))
            cbd_result = str(db_info.get("CBD test result", "") or db_info.get("cbd_test_result", ""))
            test_unit = str(db_info.get("Test result unit (% or mg)", "%") or db_info.get("test_result_unit", "%"))
            batch_num = str(db_info.get("Batch Number", "") or db_info.get("batch_number", ""))
            lot_num = str(db_info.get("Lot Number", "") or db_info.get("lot_number", ""))
            barcode = str(db_info.get("Barcode*", "") or db_info.get("barcode", ""))
            cost = str(db_info.get("cost", ""))
            medical_only = str(db_info.get("Medical Only (Yes/No)", "No") or db_info.get("medical_only", "No"))
            med_price = str(db_info.get("Med Price", "") or db_info.get("med_price", ""))
            expiration = str(db_info.get("Expiration Date(YYYY-MM-DD)", "") or db_info.get("expiration_date", ""))
            is_archived = str(db_info.get("Is Archived? (yes/no)", "no") or db_info.get("is_archived", "no"))
            thc_per_serving = str(db_info.get("THC Per Serving", "") or db_info.get("thc_per_serving", ""))
            allergens = str(db_info.get("Allergens", "") or db_info.get("allergens", ""))
            solvent = str(db_info.get("Solvent", "") or db_info.get("solvent", ""))
            accepted_date = str(db_info.get("Accepted Date", "") or db_info.get("accepted_date", ""))
            internal_id = str(db_info.get("Internal Product Identifier", "") or db_info.get("internal_product_identifier", ""))
            product_tags = str(db_info.get("Product Tags (comma separated)", "") or db_info.get("product_tags", ""))
            image_url = str(db_info.get("Image URL", "") or db_info.get("image_url", ""))
            ingredients = str(db_info.get("Ingredients", "") or db_info.get("ingredients", ""))
            
            # Create tag using database information - prioritize Product Name* from database
            # Always use Product Name* from database if available, otherwise use Description
            primary_product_name = db_info.get("Product Name*", "") or db_info.get("ProductName", "")
            if not primary_product_name and description and description.strip():
                # Use Description from database as primary product name
                primary_product_name = description.strip()
                logging.info(f"📝 Using database Description as primary name: '{primary_product_name}'")
            elif not primary_product_name and strain and lineage and weight and units:
                # Strain-based lookup: create formatted description
                primary_product_name = f"{strain} - {lineage} - {weight}{units}"
                logging.info(f"📝 Created formatted description: '{primary_product_name}'")
            elif not primary_product_name:
                # Fallback to product_name field
                primary_product_name = db_info.get("product_name", "Unknown Product")
                logging.info(f"📝 Using fallback product name: '{primary_product_name}'")
            else:
                logging.info(f"📝 Using database Product Name*: '{primary_product_name}'")
            
            # CRITICAL FIX: Log the AI match information and ensure database values are used
            ai_match_score = db_info.get("ai_match_score", 0)
            ai_confidence = db_info.get("ai_confidence", "low")
            ai_match_type = db_info.get("ai_match_type", "unknown")
            
            logging.info(f"🎯 Creating tag with DATABASE MATCHED VALUES:")
            logging.info(f"   Strain: {strain} (from database)")
            logging.info(f"   Lineage: {lineage} (from database)")
            logging.info(f"   Product Type: {product_type} (from database)")
            logging.info(f"   Weight: {weight}{units} (from database)")
            logging.info(f"   Description: {description} (from database)")
            logging.info(f"   AI Match Score: {ai_match_score:.3f}")
            logging.info(f"   AI Confidence: {ai_confidence}")
            logging.info(f"   AI Match Type: {ai_match_type}")
            
            tag = {
                # Core product information - follow existing tag format
                'Product Name*': primary_product_name,
                'ProductName': primary_product_name,
                'Description': description or primary_product_name,
                'Product Type*': product_type or "Unknown",
                'Product Type': product_type or "Unknown",
                'Vendor': vendor,
                'Vendor/Supplier*': vendor,
                'Product Brand': brand,
                'ProductBrand': brand,
                'Product Strain': strain,
                'Strain Name': strain,
                'Lineage': self._determine_lineage_for_product(product_type, lineage),
                'Weight*': f"{weight or '1'} {units or 'g'}",
                'Weight': f"{weight or '1'} {units or 'g'}",
                'Quantity*': "1",
                'Quantity': "1",
                'Units': units or "g",
                'Price': price or "25",
                'Price* (Tier Name for Bulk)': price or "25",
                
                # Enhanced fields using database information
                'State': 'active',
                'Is Sample? (yes/no)': 'no',
                'Is MJ product?(yes/no)': 'yes',
                'Discountable? (yes/no)': 'yes',
                'Room*': 'Default',
                'Medical Only (Yes/No)': medical_only or 'No',
                'DOH': 'No',
                'DOH Compliant (Yes/No)': 'No',
                
                # Database column mappings
                'Concentrate Type': product_type if product_type and "concentrate" in product_type.lower() else '',
                'Ratio': '',
                'Joint Ratio': '',
                'JointRatio': '',
                'THC test result': thc_result,
                'CBD test result': cbd_result,
                'Test result unit (% or mg)': test_unit,
                'Batch Number': batch_num,
                'Lot Number': lot_num,
                'Barcode*': barcode,
                'Med Price': med_price,
                'Expiration Date(YYYY-MM-DD)': expiration,
                'Is Archived? (yes/no)': is_archived,
                'THC Per Serving': thc_per_serving,
                'Allergens': allergens,
                'Solvent': solvent,
                'Accepted Date': accepted_date,
                'Internal Product Identifier': internal_id,
                'Product Tags (comma separated)': product_tags,
                'Image URL': image_url,
                'Ingredients': ingredients,
                
                # Legacy fields for compatibility - CRITICAL FIX: Use Excel-compatible source
                'Source': 'Excel Import',  # Changed from 'JSON Match - Product Database' to 'Excel Import'
                'Quantity Received*': "1",
                'Weight Unit* (grams/gm or ounces/oz)': units or "g",
                'CombinedWeight': weight or "1",
                'Description_Complexity': '1',
                'Ratio_or_THC_CBD': '',
                'displayName': clean_product_name(primary_product_name),
                'weightWithUnits': f"{str(round(float(weight or '1')))} {units or 'g'}",
                'WeightWithUnits': f"{str(round(float(weight or '1')))} {units or 'g'}",
                'WeightUnits': f"{str(round(float(weight or '1')))} {units or 'g'}",
                
                # Additional fields for consistency
                'vendor': vendor,
                'productBrand': brand,
                'lineage': self._determine_lineage_for_product(product_type, lineage),
                'productType': product_type or "Unknown",
                'weight': weight or "1",
                'units': units or "g",
                'price': price or "25",
                'strain': strain,
                'quantity': "1",
                'thc': thc_result,
                'cbd': cbd_result,
                'test_unit': test_unit,
                'batch_number': batch_num,
                'lot_number': lot_num,
                'barcode': barcode,
                'cost': cost,
                'medical_only': medical_only or "No",
                'med_price': med_price,
                'expiration_date': expiration,
                'is_archived': is_archived or "no",
                'thc_per_serving': thc_per_serving,
                'allergens': allergens,
                'solvent': solvent,
                'accepted_date': accepted_date,
                'internal_id': internal_id,
                'product_tags': product_tags,
                'image_url': image_url,
                'ingredients': ingredients,
                
                # AI Match Information for tracking
                'ai_match_score': ai_match_score,
                'ai_confidence': ai_confidence,
                'ai_match_type': ai_match_type,
            }
            
            logging.info(f"✅ Created tag from Product Database for: {primary_product_name}")
            logging.info(f"   Final tag uses: Strain='{strain}', Lineage='{lineage}', Product Type='{product_type}'")
            return tag
            
        except Exception as e:
            logging.error(f"Error creating tag from database info for '{primary_product_name}': {e}")
            # Fallback to basic tag creation
            return {
                'Product Name*': primary_product_name,
                'ProductName': primary_product_name,
                'Description': primary_product_name,
                'displayName': clean_product_name(primary_product_name),  # Add cleaned displayName
                'Vendor': vendor,
                'Source': 'Excel Import',  # Changed from 'JSON Match - Product Database (Fallback)' to 'Excel Import'
                'Product Type*': 'Unknown',
                'Price': '25',
                'Weight*': '1 g',
                'Units': 'g',
                'Quantity*': '1'
            }
    
    def _process_item_with_main_matching(self, item: Dict, product_name: str, vendor: str, product_type: str, strain: str, global_vendor: str) -> List[Dict]:
        """Process a single item using the main matching logic (database + Excel + Advanced matching)."""
        print(f"🔍 DEBUG: _process_item_with_main_matching called for '{product_name}'")
        try:
            # CRITICAL: Translate CERES codes to readable names for better matching
            original_name = product_name
            translated_name = self._translate_ceres_code_to_name(product_name)
            if translated_name != original_name:
                print(f"🔍 DEBUG: Translated CERES code '{original_name}' to '{translated_name}'")
                product_name = translated_name
            
            # ENHANCED: Create multiple search variations for better CERES matching
            search_variations = self._create_ceres_search_variations(original_name, translated_name, product_type)
            
            # Initialize variables for main matching
            db_match = None
            excel_match = None
            advanced_match = None
            db_score = 0.0
            excel_score = 0.0
            advanced_score = 0.0
            
            # PRIORITY 1: Try Product Database
            try:
                import os
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                product_db.init_database()
                
                # ENHANCED: Try multiple search variations for better CERES matching
                db_match = None
                for search_variation in search_variations:
                    print(f"🔍 DEBUG: Trying database search with variation: '{search_variation}'")
                    db_match = product_db.find_best_product_match(
                        product_name=search_variation,
                        vendor=vendor,
                        product_type=product_type,
                        strain=strain
                    )
                    if db_match:
                        print(f"🔍 DEBUG: Found database match with variation: '{search_variation}'")
                        break
                
                if not db_match:
                    print(f"🔍 DEBUG: No database match found with any search variation")
                
                if db_match:
                    db_score = 70.0  # Base score for database match
                    
                    # Add intelligent scoring based on product type and naming patterns
                    db_product_type = db_match.get('product_type', '')
                    if product_type and db_product_type:
                        if product_type.lower() == db_product_type.lower():
                            db_score += 80.0  # High bonus for exact product type match
                        elif self._are_product_types_compatible(product_type, db_product_type):
                            db_score += 60.0  # Good bonus for compatible product types
                        else:
                            db_score -= 30.0  # Penalty for incompatible product types
                    
                    # Add naming pattern score
                    db_product_name = db_match.get('product_name', '')
                    if db_product_name:
                        db_score += self._calculate_naming_pattern_score(product_name, db_product_name, product_type)
                    
                    # Add vendor match bonus
                    db_vendor = db_match.get('vendor', '')
                    if vendor and db_vendor and vendor.lower() == db_vendor.lower():
                        db_score += 20.0
                    
                    # Add strain match bonus
                    db_strain = db_match.get('product_strain', '')
                    if strain and db_strain and strain.lower() == db_strain.lower():
                        db_score += 15.0
                    
                    db_score = min(100.0, db_score)  # Cap at 100
                    logging.info(f"✅ Found Product Database match for '{product_name}': {db_match.get('product_name', 'Unknown')} (score: {db_score:.1f})")
                else:
                    logging.info(f"📝 No Product Database match found for '{product_name}'")
                    
            except Exception as db_error:
                logging.warning(f"Error accessing Product Database: {db_error}")
            
            # PRIORITY 2: Try Excel data
            if self.excel_processor and self.excel_processor.df is not None and self._sheet_cache:
                df = self.excel_processor.df
                excel_matches_by_name = {}
                
                for idx, row in df.iterrows():
                    try:
                        excel_product_name = str(row.get('Product Name*', '') or row.get('ProductName', '') or row.get('Description', '')).strip().lower()
                        excel_vendor = str(row.get('Vendor', '') or row.get('Vendor/Supplier*', '')).strip().lower()
                        
                        if not excel_product_name:
                            continue
                        
                        # VENDOR ISOLATION: Only process candidates from the same vendor (flexible matching)
                        vendor_match = False
                        if vendor and excel_vendor:
                            vendor_lower = vendor.lower().strip()
                            excel_vendor_lower = excel_vendor.lower().strip()
                            
                            # Normalize both vendors
                            vendor_clean = self._normalize_vendor_name(vendor_lower)
                            excel_vendor_clean = self._normalize_vendor_name(excel_vendor_lower)
                            
                            # Exact match
                            if vendor_clean == excel_vendor_clean:
                                vendor_match = True
                            # Check if one contains the other (for cases like "CERES" vs "CERES - 435011")
                            # But only if one is significantly longer than the other to prevent false matches
                            elif (len(vendor_clean) > len(excel_vendor_clean) * 2 and excel_vendor_clean in vendor_clean) or \
                                 (len(excel_vendor_clean) > len(vendor_clean) * 2 and vendor_clean in excel_vendor_clean):
                                vendor_match = True
                                print(f"🔍 SUBSTRING VENDOR MATCH: '{vendor_clean}' matches '{excel_vendor_clean}' via substring matching")
                            # Check for partial word matches (at least 75% word overlap - much stricter)
                            elif len(vendor_clean.split()) > 1 and len(excel_vendor_clean.split()) > 1:
                                vendor_words = set(vendor_clean.split())
                                excel_words = set(excel_vendor_clean.split())
                                overlap = len(vendor_words.intersection(excel_words))
                                min_words = min(len(vendor_words), len(excel_words))
                                # Check for meaningful word overlap (at least 50% but with additional validation)
                                if overlap / min_words >= 0.50:
                                    # Additional check: ensure the overlapping words are substantial (not just short words)
                                    overlapping_words = vendor_words.intersection(excel_words)
                                    substantial_overlap = any(len(word) >= 4 for word in overlapping_words)
                                    if substantial_overlap:
                                        vendor_match = True
                                        print(f"🔍 WORD OVERLAP VENDOR MATCH: '{vendor_clean}' matches '{excel_vendor_clean}' via word overlap ({overlap / min_words:.2f})")
                            # Fuzzy matching for similar vendor names (much stricter threshold)
                            elif len(vendor_clean) >= 6 and len(excel_vendor_clean) >= 6:
                                try:
                                    from rapidfuzz import fuzz
                                    vendor_ratio = fuzz.ratio(vendor_clean, excel_vendor_clean)
                                    # Increased threshold from 60% to 75% to prevent false matches but allow legitimate ones
                                    if vendor_ratio >= 75:
                                        vendor_match = True
                                        print(f"🔍 FUZZY VENDOR MATCH: '{vendor_clean}' matches '{excel_vendor_clean}' via fuzzy matching ({vendor_ratio}%)")
                                except:
                                    pass
                            # Check for common vendor name patterns
                            elif self._is_vendor_match_flexible(vendor_clean, excel_vendor_clean):
                                vendor_match = True
                                print(f"🔍 FLEXIBLE VENDOR MATCH: '{vendor_clean}' matches '{excel_vendor_clean}' via flexible matching")
                        
                        # Debug logging for vendor isolation
                        if vendor_match:
                            print(f"🔍 VENDOR MATCH: '{product_name}' (vendor: '{vendor}') matches Excel '{excel_product_name}' (vendor: '{excel_vendor}') - SAME VENDOR")
                        else:
                            print(f"🔍 CROSS-VENDOR: '{product_name}' (vendor: '{vendor}') vs Excel '{excel_product_name}' (vendor: '{excel_vendor}') - DIFFERENT VENDORS (allowing with penalty)")
                            # Don't skip - allow cross-vendor matches with penalty
                        
                        # Calculate match score
                        score = 0.0
                        
                        # Exact name match (highest priority)
                        if product_name.lower() == excel_product_name:
                            score += 100.0
                        
                        # Vendor match (heavily weighted) - already confirmed above
                        if vendor_match:
                            score += 100.0  # Heavily increased for vendor matching
                        else:
                            # Cross-vendor penalty (but still allow the match)
                            score -= 20.0  # Small penalty for cross-vendor matches
                        
                        # Product type match (very important for accuracy)
                        excel_product_type = str(row.get('Product Type*', '') or row.get('ProductType', '')).strip().lower()
                        if product_type and excel_product_type:
                            if product_type.lower() == excel_product_type:
                                score += 80.0  # High bonus for exact product type match
                            elif self._are_product_types_compatible(product_type, excel_product_type):
                                score += 60.0  # Good bonus for compatible product types
                            else:
                                score -= 30.0  # Penalty for incompatible product types
                        
                        # Intelligent naming pattern matching
                        score += self._calculate_naming_pattern_score(product_name, excel_product_name, product_type)
                        
                        # Partial name match
                        if product_name.lower() in excel_product_name or excel_product_name in product_name.lower():
                            score += 40.0
                        
                        # Fuzzy string similarity
                        try:
                            from fuzzywuzzy import fuzz
                            similarity = fuzz.ratio(product_name.lower(), excel_product_name)
                            if similarity >= 60:
                                score += similarity * 0.3
                        except ImportError:
                            pass
                        
                        # Store match by product name to prevent duplicates
                        if excel_product_name not in excel_matches_by_name or score > excel_matches_by_name[excel_product_name]['score']:
                            excel_matches_by_name[excel_product_name] = {
                                'row': row,
                                'score': score
                            }
                            
                    except Exception as e:
                        logging.debug(f"Error processing Excel row {idx}: {e}")
                        continue
                
                # Find the best match from deduplicated Excel matches
                if excel_matches_by_name:
                    best_excel_match = max(excel_matches_by_name.values(), key=lambda x: x['score'])
                    excel_score = best_excel_match['score']
                    excel_match = best_excel_match['row']
                    logging.info(f"✅ Found Excel match for '{product_name}': {excel_score:.1f}")
                else:
                    logging.info(f"📝 No Excel match found for '{product_name}' (STRICT VENDOR ISOLATION - no same vendor products found)")
                    print(f"🔍 EXCEL VENDOR: No matches found for vendor '{vendor}' - will try advanced matching")
            
            # PRIORITY 3: Try Advanced Matching (if no good matches found)
            if (not db_match or db_score < 70) and (not excel_match or excel_score < 70):
                try:
                    print(f"🔍 DEBUG: Trying advanced matching for '{product_name}'")
                    
                    # Ensure sheet cache is built
                    if self._sheet_cache is None:
                        print(f"🔍 DEBUG: Building sheet cache for advanced matching")
                        self._build_sheet_cache()
                    
                    # Prepare JSON item for advanced matching
                    json_item = {
                        "product_name": product_name,
                        "vendor": vendor,
                        "brand": item.get("brand", ""),
                        "product_type": product_type,
                        "weight": item.get("weight", ""),
                        "strain_name": strain
                    }
                    
                    # Use advanced matching with Excel cache as candidates
                    if self._sheet_cache:
                        print(f"🔍 DEBUG: Sheet cache has {len(self._sheet_cache)} candidates")
                        advanced_matches = self._find_advanced_matches(json_item)
                        if advanced_matches:
                            best_advanced = advanced_matches[0]
                            advanced_score = best_advanced.overall_score
                            advanced_match = best_advanced.item
                            print(f"🔍 DEBUG: Advanced matching found {len(advanced_matches)} matches, best score {advanced_score:.1f}")
                            print(f"🔍 DEBUG: Best match: {best_advanced.item.get('original_name', 'Unknown')}")
                        else:
                            print(f"🔍 DEBUG: Advanced matching found no matches")
                    else:
                        print(f"🔍 DEBUG: No sheet cache available for advanced matching")
                        
                except Exception as advanced_error:
                    logging.warning(f"Error in advanced matching: {advanced_error}")
                    print(f"🔍 DEBUG: Advanced matching error: {advanced_error}")
            
            # Choose the best match between database, Excel, and advanced matching
            matches = []
            
            # Add database match if found
            if db_match:
                matches.append({
                    'match': self._convert_database_match_to_excel_format(db_match),
                    'score': float(db_score) if db_score is not None else 0.0,
                    'source': 'Product Database Match'
                })
            
            # Add Excel match if found
            if excel_match is not None and not (hasattr(excel_match, 'empty') and excel_match.empty):
                matches.append({
                    'match': excel_match,
                    'score': float(excel_score) if excel_score is not None else 0.0,
                    'source': 'Excel Match'
                })
            
            # Add advanced match if found
            if advanced_match:
                matches.append({
                    'match': advanced_match,
                    'score': float(advanced_score) if advanced_score is not None else 0.0,
                    'source': 'Advanced Match'
                })
            
            # Choose the best match
            if matches:
                best_match_info = max(matches, key=lambda x: x['score'])
                best_match = best_match_info['match']
                best_score = best_match_info['score']
                match_source = best_match_info['source']
                logging.info(f"🏆 Using {match_source} (score: {best_score:.1f})")
            else:
                return []  # No match found
            
            # Process the match if we found one
            best_score_num = float(best_score) if best_score is not None else 0.0
            if best_match is not None and not (hasattr(best_match, 'empty') and best_match.empty) and best_score_num >= 2.0:
                try:
                    # Create product from the match
                    if match_source == 'Product Database Match':
                        product = best_match.copy()
                        product['Original JSON Product Name'] = str(item.get("product_name", ""))
                    elif match_source == 'Advanced Match':
                        # Convert advanced match to product format
                        product = self._create_product_from_advanced_match(best_match, item, global_vendor)
                        product['Original JSON Product Name'] = str(item.get("product_name", ""))
                    else:  # Excel Match
                        product = self._create_product_from_excel_match(best_match, item, global_vendor)
                        product['Original JSON Product Name'] = str(item.get("product_name", ""))
                    
                    return [product]
                    
                except Exception as e:
                    logging.warning(f"Error creating product from match: {e}")
                    return []
            
            return []  # No good match found
            
        except Exception as e:
            logging.warning(f"Error in main matching logic: {e}")
            return []
    
    def _create_product_from_advanced_match(self, advanced_match: Dict, item: Dict, global_vendor: str) -> Dict:
        """Create a product from an advanced match result."""
        try:
            # Extract information from the advanced match
            original_name = advanced_match.get('original_name', '')
            vendor = advanced_match.get('vendor', global_vendor)
            brand = advanced_match.get('brand', '')
            product_type = advanced_match.get('product_type', '')
            weight = advanced_match.get('weight', '')
            units = advanced_match.get('units', '')
            price = advanced_match.get('price', '')
            thc = advanced_match.get('thc', '')
            cbd = advanced_match.get('cbd', '')
            strain = advanced_match.get('strain', '')
            lineage = advanced_match.get('lineage', '')
            description = advanced_match.get('description', original_name)
            
            # Create the product dictionary
            product = {
                'Product Name*': original_name,
                'Vendor': vendor,
                'Product Brand': brand,
                'Product Type*': product_type,
                'Description': description,
                'Weight*': weight,
                'Units': units,
                'Price*': price,
                'THC test result': thc,
                'CBD test result': cbd,
                'Product Strain': strain,
                'Lineage': lineage,
                'Quantity*': '1'
            }
            
            return product
            
        except Exception as e:
            logging.warning(f"Error creating product from advanced match: {e}")
            return {}

    def _create_tag_from_product(self, product: Dict, item: Dict, global_vendor: str) -> Dict[str, Any]:
        """Create a tag from a product object."""
        try:
            # Extract basic information
            product_name = product.get('Product Name*', '') or product.get('ProductName', '') or product.get('Description', '')
            vendor = product.get('Vendor', '') or global_vendor
            brand = product.get('Product Brand', '') or product.get('Brand', '')
            product_type = product.get('Product Type*', '') or product.get('ProductType', '')
            description = product.get('Description', '') or product_name
            weight = product.get('Weight*', '') or product.get('Weight', '')
            units = product.get('Units', '') or product.get('Weight Unit*', '')
            price = product.get('Price*', '') or product.get('Price', '')
            thc = product.get('THC test result', '') or product.get('THC Content', '')
            cbd = product.get('CBD test result', '') or product.get('CBD Content', '')
            strain = product.get('Product Strain', '') or product.get('Strain', '')
            lineage = product.get('Lineage', '')
            
            # Create the tag
            tag = {
                'product_name': product_name,
                'vendor': vendor,
                'brand': brand,
                'product_type': product_type,
                'description': description,
                'weight': weight,
                'units': units,
                'price': price,
                'thc': thc,
                'cbd': cbd,
                'strain': strain,
                'lineage': lineage,
                'source': 'Main Matching Logic'
            }
            
            return tag
            
        except Exception as e:
            logging.warning(f"Error creating tag from product: {e}")
            return {
                'product_name': str(item.get("product_name", "")),
                'vendor': global_vendor,
                'brand': '',
                'product_type': '',
                'description': str(item.get("product_name", "")),
                'weight': '',
                'units': '',
                'price': '',
                'thc': '',
                'cbd': '',
                'strain': '',
                'lineage': '',
                'source': 'Main Matching Logic (Error)'
            }

    def _are_product_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two product types are compatible."""
        if not type1 or not type2:
            return False
        
        type1_lower = type1.lower().strip()
        type2_lower = type2.lower().strip()
        
        # Exact match
        if type1_lower == type2_lower:
            return True
        
        # Define compatibility groups
        compatibility_groups = {
            'edibles': ['solid edible', 'edible', 'gummy', 'chocolate', 'candy', 'cookie', 'brownie'],
            'capsules': ['capsule', 'pill', 'cap'],
            'topicals': ['topical ointment', 'topical', 'cream', 'balm', 'lotion', 'salve'],
            'flower': ['core flower', 'flower', 'bud', 'nug'],
            'concentrates': ['concentrate', 'wax', 'shatter', 'oil', 'resin'],
            'vapes': ['vape', 'cartridge', 'cart', 'pen'],
            'tinctures': ['tincture', 'drops', 'liquid edible']
        }
        
        # Check if both types are in the same compatibility group
        for group, types in compatibility_groups.items():
            if type1_lower in types and type2_lower in types:
                return True
        
        return False
    
    def _calculate_naming_pattern_score(self, json_name: str, excel_name: str, product_type: str) -> float:
        """Calculate intelligent naming pattern score based on product type and naming conventions."""
        score = 0.0
        json_lower = json_name.lower()
        excel_lower = excel_name.lower()
        
        if not product_type:
            return score
        
        product_type_lower = product_type.lower()
        
        # CAPS = Capsules pattern matching
        if product_type_lower == 'capsule':
            # Look for capsule indicators in both names
            capsule_indicators = ['caps', 'capsule', 'pill', 'cap']
            
            json_has_capsule = any(indicator in json_lower for indicator in capsule_indicators)
            excel_has_capsule = any(indicator in excel_lower for indicator in capsule_indicators)
            
            if json_has_capsule and excel_has_capsule:
                score += 50.0  # High bonus for both having capsule indicators
            elif json_has_capsule or excel_has_capsule:
                score += 25.0  # Medium bonus for one having capsule indicators
            else:
                score -= 20.0  # Penalty if neither has capsule indicators
        
        # BALL/BITE = Edibles pattern matching
        elif product_type_lower in ['solid edible', 'edible']:
            edible_indicators = ['ball', 'bite', 'chew', 'gummy', 'chocolate', 'candy', 'cookie']
            
            json_has_edible = any(indicator in json_lower for indicator in edible_indicators)
            excel_has_edible = any(indicator in excel_lower for indicator in edible_indicators)
            
            if json_has_edible and excel_has_edible:
                score += 40.0
            elif json_has_edible or excel_has_edible:
                score += 20.0
            else:
                score -= 15.0
        
        # TINCS = Tinctures pattern matching
        elif product_type_lower in ['liquid edible', 'tincture']:
            tincture_indicators = ['tincs', 'tincture', 'drops', 'liquid']
            
            json_has_tincture = any(indicator in json_lower for indicator in tincture_indicators)
            excel_has_tincture = any(indicator in excel_lower for indicator in tincture_indicators)
            
            if json_has_tincture and excel_has_tincture:
                score += 40.0
            elif json_has_tincture or excel_has_tincture:
                score += 20.0
            else:
                score -= 15.0
        
        # JAR/SQUEEZE/ROLL = Topicals pattern matching
        elif product_type_lower in ['topical ointment', 'topical']:
            topical_indicators = ['jar', 'squeeze', 'roll', 'balm', 'cream', 'ointment', 'salve']
            
            json_has_topical = any(indicator in json_lower for indicator in topical_indicators)
            excel_has_topical = any(indicator in excel_lower for indicator in topical_indicators)
            
            if json_has_topical and excel_has_topical:
                score += 40.0
            elif json_has_topical or excel_has_topical:
                score += 20.0
            else:
                score -= 15.0
        
        # Strain type matching (SAT/IND/MIX)
        strain_indicators = {
            'sativa': ['sat', 'sativa'],
            'indica': ['ind', 'indica'],
            'hybrid': ['mix', 'hybrid', 'mixed']
        }
        
        for strain_type, indicators in strain_indicators.items():
            json_has_strain = any(indicator in json_lower for indicator in indicators)
            excel_has_strain = any(indicator in excel_lower for indicator in indicators)
            
            if json_has_strain and excel_has_strain:
                score += 30.0  # Bonus for matching strain types
            elif json_has_strain or excel_has_strain:
                score += 15.0  # Smaller bonus for partial strain match
        
        # Weight/quantity pattern matching
        weight_patterns = [r'(\d+(?:\.\d+)?)\s*(g|mg|oz|ml)', r'(\d+)pk', r'(\d+)pack']
        
        for pattern in weight_patterns:
            import re
            json_match = re.search(pattern, json_lower)
            excel_match = re.search(pattern, excel_lower)
            
            if json_match and excel_match:
                # Extract the numeric part for comparison
                json_num = float(json_match.group(1))
                excel_num = float(excel_match.group(1))
                
                # Give bonus for similar weights/quantities
                if abs(json_num - excel_num) <= 1:  # Within 1 unit
                    score += 25.0
                elif abs(json_num - excel_num) <= 5:  # Within 5 units
                    score += 15.0
                else:
                    score += 5.0  # Small bonus for having any weight info
        
        return score

    def _create_tag_from_educated_guess(self, educated_guess: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        """
        Create a product tag from educated guess information.
        This method is used when no exact database match is found but similar products exist.
        
        Args:
            educated_guess: Product information from educated guessing
            vendor: The vendor name
            
        Returns:
            Dictionary containing the product tag information
        """
        try:
            # Extract data from educated guess
            product_name = educated_guess.get("product_name", "")
            brand = educated_guess.get("brand", "")
            product_type = educated_guess.get("product_type", "")
            strain = educated_guess.get("strain_name", "")
            lineage = educated_guess.get("lineage", "")
            price = str(educated_guess.get("price", ""))
            weight = str(educated_guess.get("weight", ""))
            units = str(educated_guess.get("units", ""))
            description = educated_guess.get("description", "")
            confidence = educated_guess.get("confidence", "medium")
            
            logging.info(f"🎯 Creating tag with EDUCATED GUESS VALUES:")
            logging.info(f"   Product: {product_name}")
            logging.info(f"   Strain: {strain} (inferred)")
            logging.info(f"   Lineage: {lineage} (inferred)")
            logging.info(f"   Product Type: {product_type} (inferred)")
            logging.info(f"   Weight: {weight}{units} (inferred)")
            logging.info(f"   Price: {price} (inferred)")
            logging.info(f"   Confidence: {confidence}")
            
            # Create tag with educated guess information
            tag = {
                'Product Name*': product_name,
                'ProductName': product_name,
                'Description': description,
                'Product Type*': product_type,
                'Product Type': product_type,
                'Vendor': vendor,
                'Vendor/Supplier*': vendor,
                'Product Brand': brand,
                'ProductBrand': brand,
                'Product Strain': strain,
                'Strain Name': strain,
                'Lineage': lineage,
                'Weight*': f"{weight} {units}" if weight and units else weight,
                'Weight': f"{weight} {units}" if weight and units else weight,
                'Quantity*': '1',
                'Quantity': '1',
                'Units': units,
                'Price': price,
                'Price* (Tier Name for Bulk)': price,
                'Source': f'JSON Match - Educated Guess ({confidence})',
                'Quantity Received*': '1',
                'Weight Unit* (grams/gm or ounces/oz)': units,
                'CombinedWeight': weight,
                'DescAndWeight': self._process_description_from_product_name(product_name, weight, units),  # Use Excel processor formula with weight
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
                'Concentrate Type': product_type if "concentrate" in product_type.lower() else '',
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
            
            logging.info(f"✅ Created tag from Educated Guess for: {product_name}")
            return tag
            
        except Exception as e:
            logging.error(f"Error creating tag from educated guess for '{product_name}': {e}")
            # Fallback to basic tag creation
            return {
                'Product Name*': product_name,
                'ProductName': product_name,
                'Description': product_name,
                'Vendor': vendor,
                'Source': 'Educated Guess (Fallback)',
                'Product Type*': 'Unknown',
                'Price': '25',
                'Weight*': '1 g',
                'Units': 'g',
                'Quantity*': '1'
            }
    
    def _add_educated_guess_to_database(self, educated_guess: Dict[str, Any], vendor: str) -> bool:
        """
        Add an educated guess product to the database so it shows up in the UI.
        
        Args:
            educated_guess: Product information from educated guessing
            vendor: The vendor name
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Extract data from educated guess
            product_name = educated_guess.get("product_name", "")
            brand = educated_guess.get("brand", "")
            product_type = educated_guess.get("product_type", "")
            strain = educated_guess.get("strain_name", "")
            lineage = educated_guess.get("lineage", "")
            price = str(educated_guess.get("price", ""))
            weight = str(educated_guess.get("weight", ""))
            units = str(educated_guess.get("units", ""))
            description = educated_guess.get("description", "")
            confidence = educated_guess.get("confidence", "medium")
            
            logging.info(f"💾 Adding educated guess to database: {product_name}")
            
            # Add to product database
            if hasattr(self, 'product_db') and self.product_db:
                # Check if product already exists
                existing_product = self.product_db.get_product_info(product_name)
                if existing_product:
                    logging.info(f"Product already exists in database: {product_name}")
                    return True
                
                # Add new product to database
                product_data = {
                    "Product Name*": product_name,
                    "Product Type*": product_type,
                    "Vendor/Supplier*": vendor,
                    "Product Brand": brand,
                    "Product Strain": strain,
                    "Lineage": lineage,
                    "Weight*": weight,
                    "Weight Unit* (grams/gm or ounces/oz)": units,
                    "Price* (Tier Name for Bulk)": price,
                    "Description": description,
                    "Source": f"Educated Guess ({confidence})",
                    "Total Occurrences": 1
                }
                
                success = self.product_db.add_or_update_product(product_data)
                if success:
                    logging.info(f"✅ Successfully added educated guess to database: {product_name}")
                    return True
                else:
                    logging.warning(f"❌ Failed to add educated guess to database: {product_name}")
                    return False
            else:
                logging.warning(f"❌ No product database available to add educated guess: {product_name}")
                return False
                
        except Exception as e:
            logging.error(f"Error adding educated guess to database for '{product_name}': {e}")
            return False
            


    def is_product_database_enabled(self) -> bool:
        """
        Check if Product Database integration is enabled and should be prioritized.
        
        Returns:
            True if Product Database should be used, False otherwise
        """
        try:
            # Check if we can initialize the Product Database
            product_db = ProductDatabase()
            # Try to access a simple method to verify it's working
            strains = product_db.get_all_strains()
            return len(strains) > 0
        except Exception as e:
            logging.debug(f"Product Database not available: {e}")
            return False

    def integrate_with_excel_system(self, excel_processor, matched_products: List[Dict]) -> bool:
        """
        Integrate JSON-matched products into the Excel data system.
        This ensures that JSON-matched products can be found during validation
        and label generation.
        
        Args:
            excel_processor: The Excel processor instance
            matched_products: List of products from JSON matching
            
        Returns:
            True if integration was successful, False otherwise
        """
        try:
            if not excel_processor or not hasattr(excel_processor, 'df'):
                logging.warning("Excel processor not available for integration")
                return False
                
            if not matched_products:
                logging.info("No products to integrate with Excel system")
                return True
                
            logging.info(f"Integrating {len(matched_products)} JSON-matched products with Excel system")
            
            # Convert matched products to DataFrame format
            import pandas as pd
            
            # Create a list to store the new rows
            new_rows = []
            
            for product in matched_products:
                # Create a row that matches the Excel DataFrame structure
                row_data = {}
                
                # Map all the fields to Excel columns
                for key, value in product.items():
                    # Handle both the original Excel column names and the JSON matcher field names
                    if key in excel_processor.df.columns:
                        row_data[key] = value
                    else:
                        # Try to find a matching column name
                        matching_col = None
                        for col in excel_processor.df.columns:
                            if col.lower() == key.lower() or col.lower().replace(' ', '').replace('*', '') == key.lower().replace(' ', '').replace('*', ''):
                                matching_col = col
                                break
                        
                        if matching_col:
                            row_data[matching_col] = value
                        else:
                            # If no matching column found, try to add it to the DataFrame
                            if key not in excel_processor.df.columns:
                                excel_processor.df[key] = ''
                            row_data[key] = value
                
                # Ensure all required Excel columns are present
                for col in excel_processor.df.columns:
                    if col not in row_data:
                        row_data[col] = ''
                
                new_rows.append(row_data)
            
            if new_rows:
                # Create DataFrame from new rows
                new_df = pd.DataFrame(new_rows)
                
                # Append to existing DataFrame
                excel_processor.df = pd.concat([excel_processor.df, new_df], ignore_index=True)
                
                logging.info(f"Successfully integrated {len(new_rows)} JSON-matched products into Excel system")
                logging.info(f"Excel DataFrame now contains {len(excel_processor.df)} total records")
                
                return True
            else:
                logging.warning("No valid rows created for Excel integration")
                return False
                
        except Exception as e:
            logging.error(f"Error integrating JSON products with Excel system: {e}")
            return False

    def _infer_product_type_from_name(self, product_name: str) -> str:
        """
        Infer product type from product name by analyzing keywords.
        Uses the same logic as the global infer_product_type_from_name function.
        
        Args:
            product_name: The product name to analyze
            
        Returns:
            Inferred product type or "Unknown Type" if no match
        """
        if not isinstance(product_name, str):
            return "Unknown Type"
        
        name_lower = product_name.lower()
        
        # Check TYPE_OVERRIDES first
        for key, value in TYPE_OVERRIDES.items():
            if key in name_lower:
                return value
        
        # Pattern-based inference - prioritize vape keywords over concentrate keywords
        if any(x in name_lower for x in ["flower", "bud", "nug", "herb", "marijuana", "cannabis"]):
            return "Flower"
        elif any(x in name_lower for x in ["vape", "cart", "cartridge", "disposable", "pod", "battery", "jefe", "twisted", "fire", "pen"]):
            return "Vape Cartridge"
        elif any(x in name_lower for x in ["concentrate", "rosin", "shatter", "wax", "live resin", "diamonds", "sauce", "extract", "oil", "distillate"]):
            return "Concentrate"
        elif any(x in name_lower for x in ["edible", "gummy", "chocolate", "cookie", "brownie", "candy"]):
            return "Edible (Solid)"
        elif any(x in name_lower for x in ["tincture", "oil", "drops", "liquid"]):
            return "Edible (Liquid)"
        elif any(x in name_lower for x in ["pre-roll", "joint", "cigar", "blunt"]):
            return "Pre-roll"
        elif any(x in name_lower for x in ["topical", "cream", "lotion", "salve", "balm"]):
            return "Topical"
        elif any(x in name_lower for x in ["tincture", "sublingual"]):
            return "Tincture"
        else:
            # Default to Vape Cartridge for any remaining unknown types since most products are concentrates
            return "Vape Cartridge"

    def _infer_brand_from_name(self, product_name: str) -> str:
        """
        Infer brand from product name by looking for common brand patterns and database lookups.
        
        Args:
            product_name: The product name to analyze
            
        Returns:
            Inferred brand name or empty string if no match
        """
        if not product_name:
            return ""
        
        # First, try to find brand in database using pattern matching
        try:
            from .product_database import ProductDatabase
            product_db = ProductDatabase()
            
            # Search for similar product names in database to find brand
            import sqlite3
            with sqlite3.connect(product_db.db_path) as conn:
                # Use fuzzy matching to find similar product names
                cursor = conn.execute("""
                    SELECT "Product Brand", "Product Name*" 
                    FROM products 
                    WHERE "Product Brand" IS NOT NULL AND "Product Brand" != '' 
                    AND ("Product Name*" LIKE ? OR normalized_name LIKE ?)
                    LIMIT 5
                """, [f'%{product_name}%', f'%{product_name.lower()}%'])
                
                results = cursor.fetchall()
                if results:
                    # Return the most common brand from matches
                    brands = [row[0] for row in results if row[0]]
                    if brands:
                        # Return the first non-empty brand
                        return brands[0]
        except Exception as e:
            logging.warning(f"Database brand lookup failed: {e}")
        
        # Enhanced pattern-based inference using product type patterns
        name_lower = product_name.lower()
        
        # Try to infer brand based on product patterns that match known brands
        inferred_brand = self._infer_brand_from_product_patterns(product_name)
        if inferred_brand:
            return inferred_brand
        
        # Fallback to exact brand keyword matching
        brand_patterns = {
            'Oleum': ['oleum'],
            'Dabstract': ['dabstract'],
            'Constellation Cannabis': ['constellation'],
            'Mary Jones Cannabis Co': ['mary jones'],
            'Collections Cannabis': ['collections'],
            'Blue Roots Cannabis': ['blue roots'],
            'Grow Op Farms': ['grow op'],
            'Cloud 9 Farms': ['cloud 9'],
            'The Collective': ['collective'],
            'Fifty Fold': ['fifty fold'],
            'Seattle Sluggerz': ['seattle sluggerz'],
            'Hibro Wholesale': ['hibro'],
            'Core Reactor': ['core reactor'],
            'Diamond Knot': ['diamond knot'],
            'Terp Slurper': ['terp slurper']
        }
        
        # Check for exact brand matches
        for brand, keywords in brand_patterns.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return brand
        
        # Try to extract brand from product name structure
        # Priority 1: Look for "by Brand" pattern (most reliable)
        import re
        by_brand_match = re.search(r'\bby\s+([A-Za-z][A-Za-z\s&]+?)(?:\s+-\s*|\s*$)', product_name, re.IGNORECASE)
        if by_brand_match:
            brand = by_brand_match.group(1).strip()
            # Clean up common suffixes
            brand = re.sub(r'\s+(cannabis|co|company|brand|products?)$', '', brand, flags=re.IGNORECASE)
            if len(brand) > 1:
                return brand
        
        return ""

    def _infer_brand_from_product_patterns(self, product_name: str) -> str:
        """
        Infer brand by matching product patterns to known branded products.
        
        Args:
            product_name: The product name to analyze
            
        Returns:
            Inferred brand name or empty string if no match
        """
        try:
            if not product_name:
                return ""
            
            name_lower = product_name.lower()
            
            # Define brand-specific product patterns
            # These patterns are based on actual branded products in the data
            brand_patterns = {
                'Oleum': [
                    # Live Resin patterns
                    'live resin cartridge',
                    'live resin disposable',
                    'live resin vape',
                    # Liquid Diamond patterns  
                    'liquid diamond disposable',
                    'liquid diamond vape',
                    # Honey Crystal patterns
                    'honey crystal',
                    # General Oleum patterns
                    'by oleum',
                    'oleum -'
                ],
                'Dabstract': [
                    'dabstract',
                    'by dabstract'
                ],
                'Constellation Cannabis': [
                    'constellation',
                    'by constellation'
                ],
                'Mary Jones Cannabis Co': [
                    'mary jones',
                    'by mary jones'
                ],
                'Collections Cannabis': [
                    'collections',
                    'by collections'
                ],
                'Blue Roots Cannabis': [
                    'blue roots',
                    'by blue roots'
                ],
                'Grow Op Farms': [
                    'grow op',
                    'by grow op'
                ],
                'Cloud 9 Farms': [
                    'cloud 9',
                    'by cloud 9'
                ],
                'The Collective': [
                    'collective',
                    'by collective'
                ],
                'Fifty Fold': [
                    'fifty fold',
                    'by fifty fold'
                ],
                'Seattle Sluggerz': [
                    'seattle sluggerz',
                    'by seattle sluggerz'
                ],
                'Hibro Wholesale': [
                    'hibro',
                    'by hibro'
                ],
                'Core Reactor': [
                    'core reactor',
                    'by core reactor'
                ],
                'Diamond Knot': [
                    'diamond knot',
                    'by diamond knot'
                ],
                'Terp Slurper': [
                    'terp slurper',
                    'by terp slurper'
                ]
            }
            
            # Check for pattern matches
            for brand, patterns in brand_patterns.items():
                for pattern in patterns:
                    if pattern in name_lower:
                        logging.info(f"🏷️ Inferred brand '{brand}' from pattern '{pattern}' in '{product_name}'")
                        return brand
            
            # Special case: Look for similar product patterns in database
            # This helps match products that share similar naming conventions
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                
                # Extract key terms from the product name
                key_terms = self._extract_key_terms_for_brand_matching(product_name)
                
                if key_terms:
                    # Search for products with similar terms that have brands
                    import sqlite3
                    with sqlite3.connect(product_db.db_path) as conn:
                        cursor = conn.execute("""
                            SELECT "Product Brand", "Product Name*" 
                            FROM products 
                            WHERE "Product Brand" IS NOT NULL AND "Product Brand" != '' 
                            AND (
                                "Product Name*" LIKE ? OR 
                                "Product Name*" LIKE ? OR 
                                "Product Name*" LIKE ? OR
                                "Product Name*" LIKE ?
                            )
                            LIMIT 10
                        """, [
                            f'%{key_terms[0]}%' if len(key_terms) > 0 else '',
                            f'%{key_terms[1]}%' if len(key_terms) > 1 else '',
                            f'%{key_terms[2]}%' if len(key_terms) > 2 else '',
                            f'%{key_terms[3]}%' if len(key_terms) > 3 else ''
                        ])
                        
                        results = cursor.fetchall()
                        if results:
                            # Count brand occurrences
                            from collections import Counter
                            brands = [row[0] for row in results if row[0]]
                            if brands:
                                brand_counter = Counter(brands)
                                most_common_brand = brand_counter.most_common(1)[0][0]
                                logging.info(f"🏷️ Inferred brand '{most_common_brand}' from similar products for '{product_name}'")
                                return most_common_brand
            except Exception as e:
                logging.warning(f"Database pattern matching failed: {e}")
            
            return ""
            
        except Exception as e:
            logging.warning(f"Error in brand pattern inference: {e}")
            return ""
    
    def _extract_key_terms_for_brand_matching(self, product_name: str) -> list:
        """
        Extract key terms from product name that are likely to match branded products.
        
        Args:
            product_name: The product name to analyze
            
        Returns:
            List of key terms for brand matching
        """
        try:
            if not product_name:
                return []
            
            name_lower = product_name.lower()
            
            # Extract meaningful terms that are likely to appear in branded products
            key_terms = []
            
            # Product type terms
            product_type_terms = [
                'live resin', 'liquid diamond', 'honey crystal', 'distillate', 
                'cartridge', 'disposable', 'vape', 'concentrate', 'extract',
                'rosin', 'wax', 'shatter', 'diamonds', 'sauce'
            ]
            
            for term in product_type_terms:
                if term in name_lower:
                    key_terms.append(term)
            
            # Strain-like terms (but be careful not to use strain names as brand indicators)
            # Only use very common terms that appear in multiple branded products
            common_terms = [
                'gelato', 'cookies', 'kush', 'diesel', 'haze', 'skunk',
                'purple', 'blue', 'green', 'white', 'black', 'gold'
            ]
            
            for term in common_terms:
                if term in name_lower:
                    key_terms.append(term)
            
            # Return the most relevant terms (limit to 4 to avoid too many database queries)
            return key_terms[:4]
            
        except Exception as e:
            logging.warning(f"Error extracting key terms: {e}")
            return []
    
    def _extract_key_terms_for_strain_matching(self, product_name: str) -> list:
        """
        Extract key terms from product name that are likely to match strains in database.
        
        Args:
            product_name: The product name to analyze
            
        Returns:
            List of key terms for strain matching
        """
        try:
            if not product_name:
                return []
            
            name_lower = product_name.lower()
            
            # Extract meaningful terms that are likely to appear in strain names
            key_terms = []
            
            # Common strain name patterns
            strain_patterns = [
                'blue', 'green', 'purple', 'white', 'black', 'gold', 'red', 'pink', 'orange',
                'dream', 'crack', 'kush', 'haze', 'diesel', 'og', 'gelato', 'cookies', 'runtz',
                'wedding', 'cake', 'sherbet', 'berry', 'fruit', 'citrus', 'mint', 'vanilla',
                'strawberry', 'blueberry', 'banana', 'mango', 'pineapple', 'lemon', 'lime',
                'cherry', 'grape', 'apple', 'orange', 'guava', 'dragon', 'passion', 'peach',
                'apricot', 'watermelon', 'cantaloupe', 'honeydew', 'kiwi', 'plum', 'raspberry',
                'blackberry', 'yoda', 'amnesia', 'afghani', 'hashplant', 'super', 'boof',
                'grandy', 'candy', 'tricho', 'jordan', 'cosmic', 'combo', 'honey', 'bread',
                'mintz', 'grinch', 'ak-47', 'northern', 'lights', 'skunk', 'jack', 'herer',
                'durban', 'poison', 'trainwreck', 'chemdawg', 'sour', 'cheese', 'master',
                'hindu', 'afghan', 'bubba', 'granddaddy', 'grand', 'daddy', 'maui', 'wowie',
                'gsc', 'thin', 'mint', 'forum', 'cut', 'animal', 'white', 'pink', 'zombie',
                'rainbow', 'trophy', 'sunset', 'pie', 'cream', 'gas', 'gelatti', 'shortcake',
                'grapefruit', 'rain', 'crepe', 'trunk', 'funk', 'sub', 'woofer', 'golden',
                'chicken', 'waffles', 'punch', 'crasher', 'mimosa', 'goji', 'velvet', 'truffle',
                'emerald', 'bollywood', 'lemonade', 'burst', 'wave', 'soda', 'bliss', 'eyes',
                'ztripez', 'metaverse', 'galactic', 'gdpunch', 'ape', 'zoda', 'goji'
            ]
            
            for pattern in strain_patterns:
                if pattern in name_lower:
                    key_terms.append(pattern)
            
            # Also extract individual words that might be strain names
            words = product_name.split()
            for word in words:
                word_clean = re.sub(r'[^a-zA-Z]', '', word)
                if len(word_clean) >= 3 and word_clean.isalpha():
                    key_terms.append(word_clean.lower())
            
            # Return unique terms (limit to 5 to avoid too many database queries)
            unique_terms = list(set(key_terms))[:5]
            return unique_terms
            
        except Exception as e:
            logging.warning(f"Error extracting key terms for strain matching: {e}")
            return []

    def _format_weight_with_hyphen(self, weight: str, units: str, combined_weight: str = None, description: str = None) -> str:
        """
        Format weight with hyphen and nonbreaking space, using combined weight value.
        For JSON matched items, replaces weight value with " - " + combined weight.
        If combined weight is empty, extracts weight from end of product description.
        
        Args:
            weight: The weight value as string (original weight)
            units: The units (e.g., "g", "mg", "oz")
            combined_weight: The combined weight value from the database
            description: The product description (used to extract weight if combined_weight is empty)
            
        Returns:
            Formatted weight string with hyphen and nonbreaking space
        """
        # For JSON matched items, use combined weight value
        if combined_weight and str(combined_weight).strip():
            # Use the combined weight value directly, but format it properly
            weight_value = self._format_weight_value(str(combined_weight).strip())
            logging.info(f"🏷️ Using combined weight '{weight_value}' for JSON matched item")
            return f" - {weight_value}"
        
        # If combined weight is empty, try to extract from description
        if description and not combined_weight:
            weight_from_desc = self._extract_weight_from_description(description)
            if weight_from_desc:
                logging.info(f"🏷️ Extracted weight '{weight_from_desc}' from description for JSON matched item")
                return f" - {weight_from_desc}"
        
        # Fallback to original weight formatting if no combined weight available
        if not weight or not units:
            return f" - {weight or '0'}{units or 'g'}"
        
        try:
            # Convert to float to check if it's a whole number
            weight_float = float(weight)
            if weight_float == int(weight_float):
                # It's a whole number, remove decimal point
                formatted_weight = str(int(weight_float))
            else:
                # Keep decimal point for non-whole numbers
                formatted_weight = str(weight_float)
        except (ValueError, TypeError):
            # If conversion fails, use original weight
            formatted_weight = str(weight)
        
        return f" - {formatted_weight}{units}"

    def _extract_weight_from_description(self, description: str) -> str:
        """
        Enhanced weight extraction from product descriptions and names.
        Looks for patterns like "1.0g", "3.5g", "1oz", "10pk", "3.4oz", etc.
        
        Args:
            description: The product description string
            
        Returns:
            Extracted weight string or empty string if not found
        """
        if not description:
            return ""
        
        import re
        
        # Enhanced patterns for weight extraction
        weight_patterns = [
            # Standard weight patterns: 1.0g, 3.5g, 1oz, 100mg, etc.
            r'(\d+\.?\d*)\s*(g|oz|mg|grams?|ounces?)\s*$',
            # Package count patterns: 10pk, 5pk, 20pk, etc.
            r'(\d+)\s*pk\s*$',
            # Volume patterns: 3.4oz, 1oz, 0.5oz, etc.
            r'(\d+\.?\d*)\s*oz\s*$',
            # Weight in product names: BALL_SAT_CARAMEL_10pk, ROLL_UPS_3.4oz
            r'_(\d+\.?\d*)\s*(g|oz|mg|pk)\s*$',
            # Mixed patterns: 1:1_3.4oz, CBD_3.4oz
            r'(\d+\.?\d*)\s*(g|oz|mg|pk)\s*$',
        ]
        
        description_clean = description.strip()
        
        for pattern in weight_patterns:
            match = re.search(pattern, description_clean, re.IGNORECASE)
            if match:
                weight_value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else ""
                
                # Normalize units
                if unit.lower() in ['grams', 'gram']:
                    unit = 'g'
                elif unit.lower() in ['ounces', 'ounce']:
                    unit = 'oz'
                elif unit.lower() == 'pk':
                    unit = 'pk'
                
                # Format the result
                if unit:
                    return f"{weight_value}{unit}"
                else:
                    return weight_value
        
        return ""

    def _format_weight_value(self, weight_string: str) -> str:
        """
        Format weight value by removing decimal point for whole numbers.
        Examples: "1.0g" -> "1g", "3.5g" -> "3.5g", "2.0oz" -> "2oz"
        
        Args:
            weight_string: The weight string (e.g., "1.0g", "3.5g", "2.0oz")
            
        Returns:
            Formatted weight string with decimal removed for whole numbers
        """
        if not weight_string:
            return weight_string
        
        import re
        
        # Pattern to match weight with decimal: "1.0g", "3.5g", "2.0oz", etc.
        weight_pattern = r'^(\d+)\.0+([a-zA-Z]+)$'
        
        match = re.match(weight_pattern, weight_string.strip())
        if match:
            # It's a whole number with .0, remove the decimal
            number = match.group(1)
            unit = match.group(2)
            formatted = f"{number}{unit}"
            logging.info(f"🏷️ Formatted weight '{weight_string}' -> '{formatted}' (removed .0)")
            return formatted
        
        # No change needed for non-whole numbers or already formatted weights
        return weight_string

    def _get_default_lineage_for_product_type(self, product_type: str) -> str:
        """
        Get default lineage based on product type.
        Uses intelligent lineage assignment based on product type characteristics.
        
        Args:
            product_type: The product type string
            
        Returns:
            Default lineage string based on product type
        """
        if not product_type:
            return 'HYBRID'  # Default to HYBRID instead of MIXED
        
        product_type_lower = str(product_type).lower().strip()
        
        # Define product type to lineage mapping
        type_lineage_mapping = {
            # Flower and plant-based products - typically HYBRID
            'flower': 'HYBRID',
            'bud': 'HYBRID', 
            'nug': 'HYBRID',
            'herb': 'HYBRID',
            'marijuana': 'HYBRID',
            'cannabis': 'HYBRID',
            'mini buds': 'HYBRID',
            'shake': 'HYBRID',
            'trim': 'HYBRID',
            
            # Pre-rolls - typically HYBRID
            'pre-roll': 'HYBRID',
            'joint': 'HYBRID',
            'cigar': 'HYBRID',
            'blunt': 'HYBRID',
            
            # Concentrates - typically HYBRID (single strain extracts)
            'concentrate': 'HYBRID',
            'rosin': 'HYBRID',
            'wax': 'HYBRID',
            'shatter': 'HYBRID',
            'live resin': 'HYBRID',
            'diamonds': 'HYBRID',
            'sauce': 'HYBRID',
            'extract': 'HYBRID',
            'oil': 'HYBRID',
            'distillate': 'HYBRID',
            'honey crystal': 'HYBRID',
            'liquid diamond': 'HYBRID',
            
            # Vape products - typically HYBRID
            'vape': 'HYBRID',
            'cart': 'HYBRID',
            'cartridge': 'HYBRID',
            'disposable': 'HYBRID',
            'pod': 'HYBRID',
            'disposable vape': 'HYBRID',
            'vape cartridge': 'HYBRID',
            
            # Edibles - typically MIXED (nonclassic types get blue color)
            'edible': 'MIXED',
            'gummy': 'MIXED',
            'chocolate': 'MIXED',
            'cookie': 'MIXED',
            'brownie': 'MIXED',
            'candy': 'MIXED',
            'beverage': 'MIXED',
            
            # Tinctures and oils - typically MIXED (nonclassic types get blue color)
            'tincture': 'MIXED',
            'drops': 'MIXED',
            'liquid': 'MIXED',
            'sublingual': 'MIXED',
            
            # Topicals - typically MIXED (nonclassic types get blue color)
            'topical': 'MIXED',
            'cream': 'MIXED',
            'lotion': 'MIXED',
            'salve': 'MIXED',
            'balm': 'MIXED',
            
            # RSO and full extract - typically HYBRID
            'rso': 'HYBRID',
            'feco': 'HYBRID',
            'full extract': 'HYBRID',
            'co2': 'HYBRID',
            'tanker': 'HYBRID',
            
            # Capsules - typically MIXED (nonclassic type)
            'capsule': 'MIXED',
            
            # Only truly mixed products should be MIXED
            'mixed': 'MIXED',
            'blend': 'MIXED',
            'combination': 'MIXED',
            
            # Paraphernalia and non-cannabis products
            'paraphernalia': 'PARAPHERNALIA',
            'accessory': 'PARAPHERNALIA',
            'equipment': 'PARAPHERNALIA'
        }
        
        # Check for exact matches first
        for type_key, lineage in type_lineage_mapping.items():
            if type_key in product_type_lower:
                logging.info(f"🧬 Assigned lineage '{lineage}' based on product type '{product_type}'")
                return lineage
        
        # If no specific match found, default based on product type classification
        # Import CLASSIC_TYPES to determine if this is a nonclassic product
        from src.core.constants import CLASSIC_TYPES
        is_nonclassic = product_type.lower() not in [ct.lower() for ct in CLASSIC_TYPES]
        
        if is_nonclassic:
            logging.info(f"🧬 No specific lineage mapping found for nonclassic product type '{product_type}', defaulting to MIXED")
            return 'MIXED'
        else:
            logging.info(f"🧬 No specific lineage mapping found for classic product type '{product_type}', defaulting to HYBRID")
            return 'HYBRID'

    def _find_strain_in_database(self, product_name: str, product_db) -> Optional[str]:
        """
        Find strain information in the database by searching for similar product names.
        
        Args:
            product_name: The product name to search for
            product_db: The ProductDatabase instance
            
        Returns:
            Strain name if found, None otherwise
        """
        try:
            # Search for products with similar names in the database
            similar_products = product_db.find_best_product_match(product_name)
            
            if similar_products and similar_products.get('product_strain'):
                return similar_products['product_strain']
            
            # If no direct match, try searching by product name parts
            name_parts = product_name.lower().split()
            for part in name_parts:
                if len(part) > 3:  # Only search for meaningful parts
                    # Search for products containing this part
                    search_result = product_db.find_best_product_match(part)
                    if search_result and search_result.get('product_strain'):
                        logging.info(f"Found strain '{search_result['product_strain']}' for part '{part}' of '{product_name}'")
                        return search_result['product_strain']
            
            return None
            
        except Exception as e:
            logging.warning(f"Error searching database for strain: {e}")
            return None

    def _extract_strain_from_product_name(self, product_name: str) -> Optional[str]:
        """
        Extract strain name from product name for database lookup.
        
        Args:
            product_name: The full product name
            
        Returns:
            Extracted strain name or None if no strain found
        """
        try:
            if not product_name:
                return None
                
            # Common strain keywords to look for
            strain_keywords = [
                # Popular strains
                "blue dream", "green crack", "maui wowie", "granddaddy purple", "bubba kush",
                "master kush", "hindu kush", "afghan kush", "sour diesel", "nyc diesel",
                "girl scout cookies", "gsc", "thin mint", "forum cut", "animal cookies",
                "white runtz", "pink runtz", "zombie runtz", "rainbow runtz", "trophy runtz",
                "gelato", "gelato 33", "gelato 41", "gelato 47", "sunset sherbet", "sherbet",
                "wedding cake", "wedding crasher", "wedding pie", "wedding mint",
                "blueberry", "strawberry", "banana", "mango", "pineapple", "lemon", "lime", 
                "cherry", "grape", "apple", "orange", "guava", "dragon", "fruit", "passion", 
                "peach", "apricot", "watermelon", "cantaloupe", "honeydew", "kiwi", "plum", 
                "raspberry", "blackberry", "yoda", "amnesia", "afghani", "hashplant", "super", 
                "boof", "grandy", "candy", "tricho", "jordan", "cosmic", "combo", "honey", 
                "bread", "mintz", "grinch", "ak-47", "white widow", "northern lights", "skunk", 
                "jack herer", "durban poison", "trainwreck", "chemdawg", "sour", "cheese", 
                "dream", "crack", "maui", "granddaddy", "grand daddy", "bubba", "master", 
                "hindu", "afghan", "master", "sour", "cheese", "dream", "high life", "white gummie",
                "seattle trophy wife", "tangerine queen", "cenex", "triangle kush", "red velvet cake",
                "grape goji", "watermelon mojito", "candy pound cake", "truffle cake", "emerald apricot",
                "bollywood runtz", "mango punch", "raspberry lemonade", "strawberry burst", "watermelon wave",
                "grape soda", "strawberry bliss", "25 eyes", "cherry ztripez", "metaverse", "galactic jack",
                "gdpunch", "grape ape", "rainbow cake", "strawberry mimosa", "yoda og", "goji og",
                "cookies and cream", "grape gas gelatti", "maui wowie", "strawberry shortcake", "grapefruit",
                "purple rain", "crepe ape", "trunk funk", "sub woofer", "golden pineapple", "chicken & waffles"
            ]
            
            product_lower = product_name.lower()
            
            # If no exact match, try to extract from common patterns FIRST
            import re
            
            # Look for "Strain Name (Strain/weight)" pattern - CRITICAL FOR JSON MATCHED PRODUCTS
            # This should take priority over keyword matching for better accuracy
            parentheses_match = re.search(r'\(([^/]+)/', product_name)
            if parentheses_match:
                potential_strain = parentheses_match.group(1).strip()
                # Clean up the strain name - remove extra descriptive text after dash
                if " - " in potential_strain:
                    potential_strain = potential_strain.split(" - ")[0].strip()
                if len(potential_strain) > 2:  # Must be at least 3 characters
                    logging.debug(f"Extracted potential strain '{potential_strain}' from parentheses pattern")
                    return potential_strain.title()
            
            # ENHANCED: Look for strain as first 1-3 words of product name (most common pattern)
            # This handles cases like "GSC Live Resin Cartridge 1.0g" -> "GSC"
            # or "Purple Punch Live Resin Disposable Vape 1.0g" -> "Purple Punch"
            # or "Jet Fuel Gelato Live Resin by Oleum - 1g" -> "Jet Fuel Gelato"
            words = product_name.split()
            if len(words) >= 2:
                product_type_words = ['live', 'liquid', 'diamond', 'honey', 'crystal', 'resin', 'distillate', 'extract', 'concentrate', 'oil', 'wax', 'shatter', 'rosin', 'sauce', 'diamonds', 'terp', 'terps', 'terpene', 'terpenes', 'disposable', 'vape', 'cartridge']
                
                # Try first three words as strain (for three-word strains like "Jet Fuel Gelato")
                if len(words) >= 3:
                    three_words = f"{words[0]} {words[1]} {words[2]}"
                    if len(three_words) > 6 and all(word.isalpha() for word in words[:3]):
                        # Check if none of the words are common product type words
                        if not any(word.lower() in product_type_words for word in words[:3]):
                            logging.debug(f"Extracted potential strain '{three_words}' from first three words pattern")
                            return three_words.title()
                        else:
                            logging.debug(f"Skipping three-word strain '{three_words}' due to product type words")
                
                # Try first two words as strain (for multi-word strains like "Purple Punch")
                if len(words) >= 2:
                    two_words = f"{words[0]} {words[1]}"
                    if len(two_words) > 4 and all(word.isalpha() for word in words[:2]):
                        # Check if neither word is a common product type word
                        if not any(word.lower() in product_type_words for word in words[:2]):
                            logging.debug(f"Extracted potential strain '{two_words}' from first two words pattern")
                            return two_words.title()
                
                # Try first word as strain
                first_word = words[0]
                if len(first_word) > 2 and first_word.isalpha():
                    # Check if it's not a common product type word
                    product_type_words = ['live', 'liquid', 'diamond', 'honey', 'crystal', 'resin', 'distillate', 'extract', 'concentrate', 'oil', 'wax', 'shatter', 'rosin', 'sauce', 'diamonds', 'terp', 'terps', 'terpene', 'terpenes', 'disposable', 'vape', 'cartridge']
                    if first_word.lower() not in product_type_words:
                        logging.debug(f"Extracted potential strain '{first_word}' from first word pattern")
                        # Preserve original case for acronyms (all caps)
                        if first_word.isupper() and len(first_word) <= 4:
                            return first_word
                        else:
                            return first_word.title()
            
            # Look for "Strain Name -" pattern
            if " - " in product_name:
                parts = product_name.split(" - ")
                if len(parts) > 1:
                    potential_strain = parts[1].split()[0]  # First word after dash
                    if len(potential_strain) > 2:  # Must be at least 3 characters
                        logging.debug(f"Extracted potential strain '{potential_strain}' from dash pattern")
                        return potential_strain.title()
            
            # Look for exact strain matches in keywords list (fallback)
            # But only if we haven't already found a strain from first word patterns
            for strain in strain_keywords:
                if strain in product_lower:
                    # Skip if this is just a product type word
                    if strain.lower() in ['honey', 'crystal', 'live', 'liquid', 'diamond', 'resin', 'disposable', 'vape', 'cartridge']:
                        continue
                    logging.debug(f"Found strain '{strain}' in product name '{product_name}'")
                    return strain.title()
            
            # Look for "Strain Name LR" pattern (Live Resin)
            lr_match = re.search(r'^([A-Za-z\s]+)\s+LR', product_name, re.IGNORECASE)
            if lr_match:
                potential_strain = lr_match.group(1).strip()
                if len(potential_strain) > 2:
                    logging.debug(f"Extracted potential strain '{potential_strain}' from LR pattern")
                    return potential_strain.title()
            
            # Look for "Strain Name Dabstract" pattern
            dabstract_match = re.search(r'^([A-Za-z\s]+)\s+Dabstract', product_name, re.IGNORECASE)
            if dabstract_match:
                potential_strain = dabstract_match.group(1).strip()
                if len(potential_strain) > 2:
                    logging.debug(f"Extracted potential strain '{potential_strain}' from Dabstract pattern")
                    return potential_strain.title()
            
            # Look for "Strain Name Gummiez" pattern
            gummiez_match = re.search(r'^([A-Za-z\s]+)\s+Gummiez', product_name, re.IGNORECASE)
            if gummiez_match:
                potential_strain = gummiez_match.group(1).strip()
                if len(potential_strain) > 2:
                    logging.debug(f"Extracted potential strain '{potential_strain}' from Gummiez pattern")
                    return potential_strain.title()
            
            # FALLBACK: Try to find strain in database by searching for similar product names
            try:
                from .product_database import ProductDatabase
                product_db = ProductDatabase()
                
                # Search for products with similar names that have strains
                import sqlite3
                with sqlite3.connect(product_db.db_path) as conn:
                    # Extract key terms from product name for matching
                    key_terms = self._extract_key_terms_for_strain_matching(product_name)
                    
                    if key_terms:
                        # Search for products with similar terms that have strains
                        placeholders = ' OR '.join(['"Product Name*" LIKE ?'] * len(key_terms))
                        query = f"""
                            SELECT "Product Strain", "Product Name*" 
                            FROM products 
                            WHERE "Product Strain" IS NOT NULL AND "Product Strain" != '' 
                            AND ({placeholders})
                            LIMIT 5
                        """
                        
                        cursor = conn.execute(query, [f'%{term}%' for term in key_terms])
                        results = cursor.fetchall()
                        
                        if results:
                            # Count strain occurrences
                            from collections import Counter
                            strains = [row[0] for row in results if row[0]]
                            if strains:
                                strain_counter = Counter(strains)
                                most_common_strain = strain_counter.most_common(1)[0][0]
                                logging.debug(f"Found strain '{most_common_strain}' from database similarity for '{product_name}'")
                                return most_common_strain
            except Exception as e:
                logging.debug(f"Database strain lookup failed: {e}")
            
            logging.debug(f"No strain extracted from product name: {product_name}")
            return None
            
        except Exception as e:
            logging.warning(f"Error extracting strain from product name '{product_name}': {e}")
            return None

    def _extract_key_terms(self, name: str) -> Set[str]:
        """Extract meaningful product terms, excluding common prefixes/suffixes."""
        try:
            # Debug logging to see what type of input we're getting
            if not isinstance(name, str):
                logging.warning(f"_extract_key_terms received non-string input: {type(name)} - {name}")
                if isinstance(name, list):
                    logging.warning(f"_extract_key_terms received a list: {name}")
                    # If it's a list, try to join it or take the first element
                    if name:
                        name = str(name[0]) if isinstance(name[0], str) else str(name[0])
                    else:
                        name = ""
                else:
                    name = str(name) if name is not None else ""
            
            # Ensure input is a string
            name = str(name or "")
            name_lower = name.lower()
            
            # Split on both spaces and hyphens to break compound terms
            words = set()
            for part in name_lower.replace('_', ' ').split():
                # Split each part on hyphens as well
                sub_parts = part.split('-')
                for sub_part in sub_parts:
                    if sub_part.strip():  # Only add non-empty parts
                        words.add(sub_part.strip())
            
            # Common words to exclude
            common_words = {
                'medically', 'compliant', '1g', '2g', '3.5g', '7g', '14g', '28g', 'oz', 'gram', 'grams',
                'pk', 'pack', 'packs', 'piece', 'pieces', 'roll', 'rolls', 'stix', 'stick', 'sticks', 'brand', 'vendor', 'product',
                'the', 'and', 'or', 'with', 'for', 'of', 'by', 'from', 'to', 'in', 'on', 'at', 'a', 'an', 'mg', 'thc', 'cbd'
            }
            
            # Filter out common words and short words (less than 2 characters for words like "all", "in", "one")
            key_terms = {word for word in words if word not in common_words and len(word) >= 2}
            
            # Add product type indicators for better matching
            product_types = {
                'rosin', 'wax', 'shatter', 'live', 'resin', 'distillate', 'cartridge', 'pre-roll', 'pre-rolls',
                'blunt', 'blunts', 'edible', 'edibles', 'tincture', 'tinctures', 'topical', 'topicals',
                'concentrate', 'concentrates', 'flower', 'buds', 'infused', 'flavour', 'flavor'
            }
            
            # Add product type terms if found
            for word in words:
                if word in product_types:
                    key_terms.add(word)
            
            # Add strain names (common cannabis strain words)
            strain_indicators = {
                'gmo', 'runtz', 'cookies', 'cream', 'wedding', 'cake', 'blueberry', 'banana', 'strawberry',
                'grape', 'lemon', 'lime', 'orange', 'cherry', 'apple', 'mango', 'pineapple', 'passion',
                'dragon', 'fruit', 'guava', 'pink', 'lemonade', 'haze', 'kush', 'diesel', 'og', 'sherbet',
                'gelato', 'mintz', 'grinch', 'cosmic', 'combo', 'honey', 'bread', 'tricho', 'jordan',
                'super', 'boof', 'grandy', 'candy', 'afghani', 'hashplant', 'yoda', 'amnesia'
            }
            
            # Add strain terms if found
            for word in words:
                if word in strain_indicators:
                    key_terms.add(word)
            
            # Add vendor/brand terms (but exclude common prefixes)
            vendor_prefixes = {'medically', 'compliant', 'by'}
            name_parts = name_lower.split()
            for i, part in enumerate(name_parts):
                if part not in vendor_prefixes and len(part) >= 3:
                    # Add single vendor words only
                    key_terms.add(part)
                  
            return key_terms
        except Exception as e:
            logging.warning(f"Error in _extract_key_terms: {e}")
            return set()

    def _create_synthetic_match(self, product_name: str, vendor: str, brand: str, product_type: str, strain: str, weight: str) -> Optional[str]:
        """Create a synthetic match when no real match can be found to ensure 100% coverage."""
        try:
            # Find any row in the Excel data that we can use as a template
            if self.excel_processor and self.excel_processor.df is not None:
                df = self.excel_processor.df
                
                # Look for any row with similar characteristics
                for idx, row in df.iterrows():
                    try:
                        # Check if this row has basic product information
                        excel_product_name = str(row.get('Product Name*', '') or row.get('ProductName', '') or row.get('Description', '')).strip()
                        excel_vendor = str(row.get('Vendor', '') or row.get('Vendor/Supplier*', '')).strip()
                        excel_product_type = str(row.get('Product Type*', '')).strip()
                        
                        if excel_product_name and excel_product_type:
                            # Use this row as a template for synthetic matching
                            logging.info(f"🔧 Creating synthetic match for '{product_name}' using template row '{excel_product_name}'")
                            return str(idx)
                    except Exception as e:
                        continue
                
                # If no template found, use the first available row
                if len(df) > 0:
                    logging.info(f"🔧 Creating synthetic match for '{product_name}' using first available row")
                    return str(df.index[0])
            
            return None
        except Exception as e:
            logging.warning(f"Error creating synthetic match: {e}")
            return None

    def _find_fallback_match(self, product_name: str, vendor: str, brand: str, product_type: str, strain: str, weight: str) -> Optional[str]:
        """
        Emergency fallback matching to ensure 100% coverage.
        This method finds any possible match using very loose criteria.
        """
        try:
            if not self.excel_processor or self.excel_processor.df is None:
                return None
                
            df = self.excel_processor.df
            product_name_lower = product_name.lower()
            
            # Strategy 1: Find any row with similar product type
            if product_type:
                for idx, row in df.iterrows():
                    excel_type = str(row.get('Product Type*', '') or row.get('Product Type', '')).lower()
                    if product_type.lower() in excel_type or excel_type in product_type.lower():
                        logging.info(f"🆘 Emergency match by product type: '{product_name}' → '{row.get('Product Name*', 'Unknown')}'")
                        return str(idx)
            
            # Strategy 2: Find any row with similar weight
            if weight:
                weight_num = re.search(r'(\d+(?:\.\d+)?)', weight)
                if weight_num:
                    weight_val = float(weight_num.group(1))
                    for idx, row in df.iterrows():
                        excel_weight = str(row.get('Weight*', '') or row.get('Weight', ''))
                        excel_weight_num = re.search(r'(\d+(?:\.\d+)?)', excel_weight)
                        if excel_weight_num:
                            excel_weight_val = float(excel_weight_num.group(1))
                            if abs(weight_val - excel_weight_val) <= 2.0:  # Within 2 units
                                logging.info(f"🆘 Emergency match by weight: '{product_name}' → '{row.get('Product Name*', 'Unknown')}'")
                                return str(idx)
            
            # Strategy 3: Find any row with any word in common (very loose)
            product_words = set(product_name_lower.split())
            for idx, row in df.iterrows():
                excel_name = str(row.get('Product Name*', '') or row.get('ProductName', '') or row.get('Description', '')).lower()
                excel_words = set(excel_name.split())
                if product_words.intersection(excel_words):
                    logging.info(f"🆘 Emergency match by word overlap: '{product_name}' → '{row.get('Product Name*', 'Unknown')}'")
                    return str(idx)
            
            # Strategy 4: Just pick the first available row (last resort)
            if len(df) > 0:
                first_idx = df.index[0]
                logging.info(f"🆘 Emergency match using first available row: '{product_name}' → '{df.iloc[0].get('Product Name*', 'Unknown')}'")
                return str(first_idx)
                
            return None
            
        except Exception as e:
            logging.error(f"Error in emergency fallback matching: {e}")
            return None

    def _enhance_product_with_json_data(self, product: dict, json_item: dict) -> None:
        """
        Enhance a product with additional data from JSON item.
        This is used when we have a partial match but want to add more data from JSON.
        
        Args:
            product: The product dictionary to enhance
            json_item: The original JSON item with additional data
        """
        try:
            # Add JSON quantity if available and product doesn't have it
            current_qty = product.get('Quantity*') if hasattr(product, 'get') else (product['Quantity*'] if hasattr(product, 'index') and 'Quantity*' in product.index else '') if hasattr(product, 'index') else ''
            if not current_qty and json_item.get('qty'):
                product['Quantity*'] = str(json_item.get('qty'))
            
            # Add JSON weight if available and product doesn't have it
            current_weight = product.get('Weight*') if hasattr(product, 'get') else (product['Weight*'] if hasattr(product, 'index') and 'Weight*' in product.index else '') if hasattr(product, 'index') else ''
            if not current_weight and json_item.get('unit_weight'):
                product['Weight*'] = str(json_item.get('unit_weight'))
            
            # Add JSON price if available and product doesn't have it
            current_price = product.get('Price') if hasattr(product, 'get') else (product['Price'] if hasattr(product, 'index') and 'Price' in product.index else '') if hasattr(product, 'index') else ''
            if not current_price and json_item.get('price'):
                product['Price'] = str(json_item.get('price'))
            
            # Add JSON strain if available and product doesn't have it
            current_strain = product.get('Product Strain') if hasattr(product, 'get') else (product['Product Strain'] if hasattr(product, 'index') and 'Product Strain' in product.index else '') if hasattr(product, 'index') else ''
            if not current_strain and json_item.get('strain_name'):
                product['Product Strain'] = str(json_item.get('strain_name'))
            
            # Add JSON brand if available and product doesn't have it
            current_brand = product.get('Product Brand') if hasattr(product, 'get') else (product['Product Brand'] if hasattr(product, 'index') and 'Product Brand' in product.index else '') if hasattr(product, 'index') else ''
            if not current_brand and json_item.get('brand'):
                product['Product Brand'] = str(json_item.get('brand'))
            
            # Add JSON vendor if available and product doesn't have it
            current_vendor = product.get('Vendor') if hasattr(product, 'get') else (product['Vendor'] if hasattr(product, 'index') and 'Vendor' in product.index else '') if hasattr(product, 'index') else ''
            if not current_vendor and json_item.get('vendor'):
                product['Vendor'] = str(json_item.get('vendor'))
            
            # Add JSON product type if available and product doesn't have it
            current_type = product.get('Product Type*') if hasattr(product, 'get') else (product['Product Type*'] if hasattr(product, 'index') and 'Product Type*' in product.index else '') if hasattr(product, 'index') else ''
            if not current_type and json_item.get('inventory_type'):
                product['Product Type*'] = str(json_item.get('inventory_type'))
            
            # Try to extract THC/CBD values from JSON data
            current_thc = product.get('THC test result') if hasattr(product, 'get') else product.get('THC test result', '') if 'THC test result' in product else ''
            if not current_thc or current_thc == '':
                thc_value = (json_item.get('THC test result') or 
                            json_item.get('thc') or 
                            json_item.get('thc_percent') or 
                            json_item.get('thc_percentage') or 
                            json_item.get('total_thc') or 
                            json_item.get('total_thc_percent'))
                if thc_value:
                    product['THC test result'] = str(thc_value)
                    logging.info(f"🧪 Enhanced with THC value from JSON: {thc_value}")
            
            current_cbd = product.get('CBD test result') if hasattr(product, 'get') else product.get('CBD test result', '') if 'CBD test result' in product else ''
            if not current_cbd or current_cbd == '':
                cbd_value = (json_item.get('CBD test result') or 
                            json_item.get('cbd') or 
                            json_item.get('cbd_percent') or 
                            json_item.get('cbd_percentage') or 
                            json_item.get('total_cbd') or 
                            json_item.get('total_cbd_percent'))
                if cbd_value:
                    product['CBD test result'] = str(cbd_value)
                    logging.info(f"🧪 Enhanced with CBD value from JSON: {cbd_value}")
            
            # Try to extract from lab_result_data as well
            lab_result_data = json_item.get("lab_result_data", {})
            if lab_result_data:
                cannabinoids = extract_cannabinoids(lab_result_data)
                current_thc = product.get('THC test result') if hasattr(product, 'get') else product.get('THC test result', '') if 'THC test result' in product else ''
                if 'thc' in cannabinoids and (not current_thc or current_thc == ''):
                    product['THC test result'] = str(cannabinoids['thc'])
                    logging.info(f"🧪 Enhanced with THC value from lab_result_data: {cannabinoids['thc']}")
                current_cbd = product.get('CBD test result') if hasattr(product, 'get') else product.get('CBD test result', '') if 'CBD test result' in product else ''
                if 'cbd' in cannabinoids and (not current_cbd or current_cbd == ''):
                    product['CBD test result'] = str(cannabinoids['cbd'])
                    logging.info(f"🧪 Enhanced with CBD value from lab_result_data: {cannabinoids['cbd']}")
            
            logging.info(f"✅ Enhanced product with JSON data: '{product.get('Product Name*', 'Unknown')}'")
            
        except Exception as e:
            logging.warning(f"Error enhancing product with JSON data: {e}")

    def _create_database_entry_for_unmatched_json(self, tag: dict, product_db) -> None:
        """
        Create a new database entry for an unmatched JSON tag.
        This ensures that unmatched JSON products are added to the product database
        for future matching and reference.
        
        Args:
            tag: The tag dictionary created from JSON data
            product_db: The ProductDatabase instance
        """
        try:
            # Extract key information from the tag
            product_name = tag.get('Product Name*', '').strip()
            vendor = tag.get('Vendor', '').strip()
            brand = tag.get('Product Brand', '').strip()
            product_type = tag.get('Product Type*', '').strip()
            weight = tag.get('Weight*', '').strip()
            price = tag.get('Price', '').strip()
            strain = tag.get('Product Strain', '').strip()
            lineage = tag.get('Lineage', '').strip()
            description = tag.get('Description', '').strip()
            
            # ENHANCED STRAIN EXTRACTION: If no strain in tag, try to find in database
            if not strain and product_name:
                # First try to extract strain from product name
                extracted_strain = self._extract_strain_from_product_name(product_name)
                if extracted_strain:
                    strain = extracted_strain
                    logging.info(f"🧬 Extracted strain '{strain}' from product name '{product_name}' for database entry")
                else:
                    # Try to find strain in database
                    try:
                        db_strain = self._find_strain_in_database(product_name, product_db)
                        if db_strain:
                            strain = db_strain
                            logging.info(f"🗄️ Found strain '{strain}' in database for product '{product_name}' in database entry")
                    except Exception as db_error:
                        logging.warning(f"Failed to search database for strain in database entry: {db_error}")
            
            if not product_name:
                logging.warning("Cannot create database entry: missing product name")
                return
            
            logging.info(f"🗄️ Creating new database entry for unmatched JSON product: '{product_name}'")
            
            # Prepare product data for database insertion using correct column names
            product_data = {
                'Product Name*': product_name,
                'normalized_name': product_name.lower().strip(),
                'Vendor/Supplier*': vendor,
                'Product Brand': brand,
                'Product Type*': product_type,
                'Weight*': weight,
                'Price': price,
                'Product Strain': strain,
                'Lineage': lineage,
                'Description': description,
                'state': 'active',
                'is_mj_product': 'yes',
                'doh_compliant': 'no'
            }
            
            # Add the product to the database
            product_id = product_db.add_or_update_product(product_data)
            
            # If we have strain information, also add/update the strain
            if strain:
                try:
                    strain_id = product_db.add_or_update_strain(strain, lineage)
                    logging.info(f"✅ Added strain '{strain}' to database with ID: {strain_id}")
                except Exception as strain_error:
                    logging.warning(f"Failed to add strain '{strain}' to database: {strain_error}")
            
            logging.info(f"✅ Successfully created database entry for '{product_name}' with ID: {product_id}")
            
        except Exception as e:
            logging.error(f"Error creating database entry for unmatched JSON tag: {e}")
            # Don't re-raise the exception to avoid breaking the main flow
    
    def _find_advanced_matches(self, json_item: dict) -> List[MatchResult]:
        """
        Use the advanced matching system to find the best matches for a JSON item.
        
        Args:
            json_item: The JSON item to match
            
        Returns:
            List of MatchResult objects sorted by overall score
        """
        try:
            if not self._sheet_cache:
                logging.warning("No sheet cache available for advanced matching")
                return []
            
            # DEBUG: Check vendor data in sheet cache before advanced matching
            if self._sheet_cache:
                sample_vendors = []
                for i, item in enumerate(self._sheet_cache[:5]):
                    vendor = str(item.get("vendor", "")).strip()
                    sample_vendors.append(f"'{vendor}'")
                print(f"🔍 DEBUG: Sheet cache vendor data (first 5): {sample_vendors}")
            
            # Use the advanced matcher to find matches (AI-powered aggressive matching within vendor)
            matches = self.advanced_matcher.find_best_matches(
                json_item=json_item,
                candidates=self._sheet_cache,
                threshold=1.0,  # Ultra-low threshold for AI-powered matching
                max_results=50
            )
            
            if matches:
                logging.debug(f"🔍 ADVANCED MATCHING: Found {len(matches)} matches for '{json_item.get('product_name', 'Unknown')}'")
                for i, match in enumerate(matches[:3]):  # Log top 3 matches
                    logging.debug(f"  {i+1}. {match.item.get('original_name', 'Unknown')} (score: {match.overall_score:.1f}, {match.algorithm_used})")
            
            return matches
            
        except Exception as e:
            logging.error(f"Error in advanced matching: {e}")
            return []
    
    def _normalize_vendor_name(self, vendor_name: str) -> str:
        """Normalize vendor name for comparison."""
        if not vendor_name:
            return ""
        
        # Convert to lowercase and strip
        vendor_name = vendor_name.lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        import re
        vendor_name = re.sub(r'[^\w\s-]', ' ', vendor_name)
        
        # Normalize whitespace
        vendor_name = re.sub(r'\s+', ' ', vendor_name)
        
        return vendor_name.strip()

    def _translate_ceres_code_to_name(self, product_name: str) -> str:
        """Translate CERES product codes to human-readable names for better matching."""
        if not product_name:
            return product_name
            
        # Convert to lowercase for processing
        name_lower = product_name.lower()
        
        # Handle ratio codes first (before other replacements)
        import re
        name_lower = re.sub(r'(\d+):(\d+)', r'\1 to \2', name_lower)
        name_lower = re.sub(r'(\d+):(\d+):(\d+)', r'\1 to \2 to \3', name_lower)
        name_lower = re.sub(r'(\d+):(\d+):(\d+):(\d+)', r'\1 to \2 to \3 to \4', name_lower)
        
        # Convert underscores to spaces
        name_lower = name_lower.replace('_', ' ')
        
        # CERES code mapping patterns (apply after ratio and underscore conversion)
        code_mappings = {
            # Product type codes (order matters - longer codes first)
            'squeeze tube': 'squeeze tube',
            'roll up': 'roll up',
            'chocolate ball': 'chocolate ball',
            'chocolate bite': 'chocolate bite', 
            'fruit chew': 'fruit chew',
            'capsule': 'capsule',
            'tincture': 'tincture',
            'jar': 'jar',
            
            # Strain codes
            'sativa': 'sativa',
            'indica': 'indica',
            'mixed': 'mixed',
            
            # Flavor codes
            'sour apple': 'sour apple',
            'gold max': 'gold max',
            'xtra strength': 'xtra strength',
            'caramel': 'caramel',
            'assorted': 'assorted',
            'dark': 'dark',
            'milk': 'milk',
            'cherry': 'cherry',
            'mango': 'mango',
            'watermelon': 'watermelon',
            'tropical': 'tropical',
            'guava': 'guava',
            'citrus': 'citrus',
            'dragon': 'dragon',
            'balance': 'balance',
            'chill': 'chill',
            'lifted': 'lifted',
            'relief': 'relief',
            'berry': 'berry',
            
            # Pack size codes
            '10 pack': '10 pack',
            '20 pack': '20 pack',
            'single': 'single',
            '1 pack': '1 pack',
            
            # Potency codes
            '1000mg': '1000mg',
            '100ml': '100ml',
            '3.4oz': '3.4oz',
            '2oz': '2oz',
        }
        
        # Apply code mappings (order matters - longer patterns first)
        for code, replacement in sorted(code_mappings.items(), key=lambda x: len(x[0]), reverse=True):
            name_lower = name_lower.replace(code, replacement)
        
        # Clean up extra spaces
        name_lower = re.sub(r'\s+', ' ', name_lower).strip()
        
        return name_lower

    def _create_ceres_search_variations(self, original_name: str, translated_name: str, product_type: str) -> List[str]:
        """Create multiple search variations for CERES products to improve matching."""
        variations = []
        
        # Start with original and translated names
        variations.append(original_name.lower())
        if translated_name != original_name:
            variations.append(translated_name.lower())
        
        # Extract key terms from translated name
        terms = translated_name.lower().split()
        
        # Create variations based on key product patterns
        if 'chew' in translated_name.lower():
            # Fruit chew variations
            if 'ind' in translated_name.lower():
                variations.append('indica fruit chew')
                variations.append('indica chew')
            if 'sat' in translated_name.lower():
                variations.append('sativa fruit chew')
                variations.append('sativa chew')
            if 'mango' in translated_name.lower():
                variations.append('mango fruit chew')
                variations.append('mango chew')
            if 'watermelon' in translated_name.lower():
                variations.append('watermelon fruit chew')
                variations.append('watermelon chew')
            if 'cherry' in translated_name.lower():
                variations.append('cherry fruit chew')
                variations.append('cherry chew')
        
        elif 'ball' in translated_name.lower():
            # Chocolate ball variations
            if 'ind' in translated_name.lower():
                variations.append('indica chocolate ball')
                variations.append('indica ball')
            if 'sat' in translated_name.lower():
                variations.append('sativa chocolate ball')
                variations.append('sativa ball')
            if 'caramel' in translated_name.lower():
                variations.append('caramel chocolate ball')
                variations.append('caramel ball')
            if 'dragon' in translated_name.lower():
                variations.append('dragon chocolate ball')
                variations.append('dragon ball')
        
        elif 'bite' in translated_name.lower():
            # Chocolate bite variations
            if 'ind' in translated_name.lower():
                variations.append('indica chocolate bite')
                variations.append('indica bite')
            if 'sat' in translated_name.lower():
                variations.append('sativa chocolate bite')
                variations.append('sativa bite')
        
        elif 'caps' in translated_name.lower():
            # Capsule variations
            if 'balance' in translated_name.lower():
                variations.append('balance capsule')
                variations.append('balance cap')
            if 'chill' in translated_name.lower():
                variations.append('chill capsule')
                variations.append('chill cap')
            if 'lifted' in translated_name.lower():
                variations.append('lifted capsule')
                variations.append('lifted cap')
        
        elif 'tincs' in translated_name.lower():
            # Tincture variations
            if 'relief' in translated_name.lower():
                variations.append('relief tincture')
                variations.append('relief tinc')
        
        elif 'squeeze tube' in translated_name.lower() or 'roll up' in translated_name.lower():
            # Topical variations
            if 'dragon' in translated_name.lower():
                variations.append('dragon balm')
                variations.append('dragon topical')
            if 'xtra' in translated_name.lower():
                variations.append('xtra strength dragon balm')
                variations.append('xtra dragon balm')
            if 'gold max' in translated_name.lower():
                variations.append('gold max dragon balm')
                variations.append('max dragon balm')
        
        # Add strain-based variations
        if 'ind' in translated_name.lower():
            variations.append('indica')
        if 'sat' in translated_name.lower():
            variations.append('sativa')
        if 'mix' in translated_name.lower() or 'mixed' in translated_name.lower():
            variations.append('mixed')
        
        # Remove duplicates and empty strings
        variations = list(set([v.strip() for v in variations if v.strip()]))
        
        return variations
    
    def _is_vendor_match_flexible(self, vendor1: str, vendor2: str) -> bool:
        """Check if two vendor names represent the same vendor using various patterns."""
        if not vendor1 or not vendor2:
            return False
        
        # Remove common business suffixes and variations
        suffixes = [
            'llc', 'inc', 'corp', 'ltd', 'co', 'company', 'holdings', 'group', 'brands',
            'enterprises', 'industries', 'solutions', 'systems', 'services', 'products',
            'farms', 'garden', 'cultivation', 'cannabis', 'hemp', 'marijuana',
            'wholesale', 'distribution', 'supply', 'cooperative', 'collective'
        ]
        
        v1_clean = vendor1.lower().strip()
        v2_clean = vendor2.lower().strip()
        
        # Remove suffixes and clean up
        for suffix in suffixes:
            v1_clean = v1_clean.replace(f' {suffix}', '').replace(f'-{suffix}', '').replace(f'_{suffix}', '')
            v2_clean = v2_clean.replace(f' {suffix}', '').replace(f'-{suffix}', '').replace(f'_{suffix}', '')
        
        # Remove common prefixes
        prefixes = ['the', 'a', 'an']
        for prefix in prefixes:
            if v1_clean.startswith(f'{prefix} '):
                v1_clean = v1_clean[len(prefix)+1:]
            if v2_clean.startswith(f'{prefix} '):
                v2_clean = v2_clean[len(prefix)+1:]
        
        # Clean up extra spaces and special characters
        import re
        v1_clean = re.sub(r'\s+', ' ', v1_clean).strip()
        v2_clean = re.sub(r'\s+', ' ', v2_clean).strip()
        
        # Check if cleaned names match exactly
        if v1_clean == v2_clean:
            return True
        
        # Check for acronym matches (e.g., "CERES" vs "Ceres Holdings")
        if len(v1_clean) <= 6 and len(v2_clean) > 6:
            if v1_clean in v2_clean:
                return True
        elif len(v2_clean) <= 6 and len(v1_clean) > 6:
            if v2_clean in v1_clean:
                return True
        
        # Check for partial matches with high confidence - MUCH MORE RESTRICTIVE
        if len(v1_clean) >= 4 and len(v2_clean) >= 4:
            # Only allow subset matches if one name is significantly longer (3x) than the other
            # This prevents short names from matching long ones inappropriately
            if len(v1_clean) > len(v2_clean) * 3:
                if v2_clean in v1_clean:
                    return True
            elif len(v2_clean) > len(v1_clean) * 3:
                if v1_clean in v2_clean:
                    return True
            
            # Check for word overlap (at least 75% of words match - much stricter)
            v1_words = set(v1_clean.split())
            v2_words = set(v2_clean.split())
            if len(v1_words) > 0 and len(v2_words) > 0:
                overlap = len(v1_words.intersection(v2_words))
                min_words = min(len(v1_words), len(v2_words))
                # Increased threshold from 50% to 75% to prevent false matches
                if overlap / min_words >= 0.75:
                    return True
            
            # Check for phonetic similarity (Soundex) - only for very similar names
            try:
                import jellyfish
                # Only allow phonetic matches if names are already quite similar
                if len(v1_clean) >= 5 and len(v2_clean) >= 5:
                    if jellyfish.soundex(v1_clean) == jellyfish.soundex(v2_clean):
                        # Additional check: ensure at least 60% character similarity
                        char_similarity = len(set(v1_clean).intersection(set(v2_clean))) / max(len(set(v1_clean)), len(set(v2_clean)))
                        if char_similarity >= 0.6:
                            return True
            except:
                pass
        
        return False