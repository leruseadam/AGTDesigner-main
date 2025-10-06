"""
Enhanced JSON Matcher with Performance, Accuracy, and Algorithm Improvements
=============================================================================

This is an upgraded version of the JSON matching system with:
- Performance improvements (faster matching)
- Accuracy improvements (better matching results) 
- New matching algorithms and strategies
- Better handling of specific product types

Key Improvements:
1. Multi-threaded parallel processing
2. Advanced caching with TTL and smart invalidation
3. Machine learning-based similarity scoring
4. Product type-specific matching strategies
5. Fuzzy matching with multiple algorithms
6. Semantic similarity using embeddings
7. Performance profiling and optimization
"""

import re
import json
import logging
import time
import hashlib
import multiprocessing
import requests
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import lru_cache, wraps
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum

# Advanced fuzzy matching libraries
from fuzzywuzzy import fuzz, process
from difflib import SequenceMatcher
import jellyfish
try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
    from scipy.spatial.distance import euclidean, cosine  # type: ignore
    _SKLEARN_AVAILABLE = True
except Exception as _e:
    logging.warning(f"EnhancedJSONMatcher: scikit-learn not available, disabling semantic/ML features: {_e}")
    TfidfVectorizer = None  # type: ignore
    cosine_similarity = None  # type: ignore
    StandardScaler = None  # type: ignore
    try:
        from scipy.spatial.distance import euclidean, cosine  # type: ignore
    except Exception:
        euclidean = None  # type: ignore
        cosine = None  # type: ignore
    _SKLEARN_AVAILABLE = False

# Product-specific imports
from .field_mapping import get_canonical_field
from .product_database import ProductDatabase
from .ai_product_matcher import AIProductMatcher
from .advanced_matcher import AdvancedMatcher, MatchResult

class MatchStrategy(Enum):
    """Different matching strategies for different product types"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    ML_ENHANCED = "ml_enhanced"

@dataclass
class MatchResult:
    """Enhanced match result with detailed scoring"""
    score: float
    match_data: Dict[str, Any]
    strategy_used: MatchStrategy
    confidence: float
    processing_time: float
    match_factors: Dict[str, float] = field(default_factory=dict)
    
@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata"""
    data: Any
    created: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

class PerformanceProfiler:
    """Performance profiling and optimization tracker"""
    
    def __init__(self):
        self.timing_data = defaultdict(list)
        self.cache_stats = defaultdict(int)
        
    def time_function(self, func_name: str):
        """Decorator for timing function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                execution_time = end_time - start_time
                self.timing_data[func_name].append(execution_time)
                
                # Log slow operations
                if execution_time > 1.0:  # Log operations taking more than 1 second
                    logging.warning(f"Slow operation detected: {func_name} took {execution_time:.3f}s")
                
                return result
            return wrapper
        return decorator
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'function_timings': {},
            'cache_statistics': dict(self.cache_stats),
            'total_functions_profiled': len(self.timing_data)
        }
        
        for func_name, times in self.timing_data.items():
            if times:
                report['function_timings'][func_name] = {
                    'avg_time': np.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_calls': len(times),
                    'total_time': sum(times)
                }
        
        return report

class SmartCache:
    """Advanced caching system with TTL, LRU, and smart invalidation"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 10000):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.access_order = []  # For LRU eviction
        
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check"""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        now = datetime.now()
        
        # Check TTL
        if now > entry.created + timedelta(seconds=entry.ttl_seconds):
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return None
            
        # Update access tracking
        entry.access_count += 1
        entry.last_accessed = now
        
        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry.data
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional custom TTL"""
        ttl = ttl or self.default_ttl
        
        # Evict if at max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
            
        self.cache[key] = CacheEntry(
            data=value,
            created=datetime.now(),
            ttl_seconds=ttl
        )
        
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        regex = re.compile(pattern)
        keys_to_remove = [key for key in self.cache.keys() if regex.match(key)]
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
                
        return len(keys_to_remove)

class ProductTypeSpecificMatcher:
    """Specialized matching strategies for different product types"""
    
    def __init__(self):
        self.type_strategies = {
            'flower': self._match_flower,
            'concentrate': self._match_concentrate,
            'vape_cartridge': self._match_vape,
            'edible': self._match_edible,
            'pre_roll': self._match_preroll,
            'topical': self._match_topical,
            'tincture': self._match_tincture
        }
    
    def _get_product_name(self, product: Dict) -> str:
        """Get product name from JSON product, handling different field names"""
        # Check for Cultivera format first (product_name)
        name = product.get('product_name', '')
        if name:
            return str(name)
        
        # Fallback to other common formats
        name = product.get('inventory_name', '')
        if name:
            return str(name)
            
        name = product.get('Product Name*', '')
        if name:
            return str(name)
            
        return ''
        
    def match_by_type(self, product_type: str, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Match using product type-specific strategy"""
        strategy = self.type_strategies.get(product_type.lower().replace('-', '_'), self._match_generic)
        return strategy(json_product, database_products)
        
    def _match_flower(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Flower-specific matching focusing on strain, weight, and THC content"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        for db_product in database_products:
            score = 0.0
            factors = {}
            
            # Strain name matching (40% weight for flower)
            db_name = str(db_product.get('Product Name*', '')).lower()
            strain_score = fuzz.token_sort_ratio(json_name, db_name) / 100.0
            factors['strain_match'] = strain_score
            score += strain_score * 0.4
            
            # Weight matching (25% weight)
            weight_score = self._compare_weights(json_product, db_product)
            factors['weight_match'] = weight_score
            score += weight_score * 0.25
            
            # THC content matching (20% weight)
            thc_score = self._compare_thc_content(json_product, db_product)
            factors['thc_match'] = thc_score
            score += thc_score * 0.2
            
            # Vendor matching (15% weight)
            vendor_score = self._compare_vendors(json_product, db_product)
            factors['vendor_match'] = vendor_score
            score += vendor_score * 0.15
            
            if score > 0.1:  # Ultra-lenient threshold for flower
                matches.append(MatchResult(
                    score=score,
                    match_data=db_product,
                    strategy_used=MatchStrategy.HYBRID,
                    confidence=min(score * 1.2, 1.0),
                    processing_time=0.0,
                    match_factors=factors
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _match_concentrate(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Concentrate-specific matching focusing on extraction method and potency"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        # Extract concentrate type indicators
        concentrate_indicators = ['live resin', 'rosin', 'shatter', 'wax', 'badder', 'diamonds', 'sauce']
        json_concentrate_type = None
        for indicator in concentrate_indicators:
            if indicator in json_name:
                json_concentrate_type = indicator
                break
                
        for db_product in database_products:
            score = 0.0
            factors = {}
            
            db_name = str(db_product.get('Product Name*', '')).lower()
            
            # Concentrate type matching (35% weight)
            if json_concentrate_type:
                type_score = 1.0 if json_concentrate_type in db_name else 0.3
            else:
                type_score = fuzz.partial_ratio(json_name, db_name) / 100.0
            factors['concentrate_type_match'] = type_score
            score += type_score * 0.35
            
            # Strain matching (30% weight)
            strain_score = self._extract_strain_similarity(json_name, db_name)
            factors['strain_match'] = strain_score
            score += strain_score * 0.3
            
            # Potency matching (20% weight)
            potency_score = self._compare_potency(json_product, db_product)
            factors['potency_match'] = potency_score
            score += potency_score * 0.2
            
            # Vendor matching (15% weight)
            vendor_score = self._compare_vendors(json_product, db_product)
            factors['vendor_match'] = vendor_score
            score += vendor_score * 0.15
            
            if score > 0.15:  # Ultra-lenient threshold for concentrates
                matches.append(MatchResult(
                    score=score,
                    match_data=db_product,
                    strategy_used=MatchStrategy.HYBRID,
                    confidence=min(score * 1.1, 1.0),
                    processing_time=0.0,
                    match_factors=factors
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _match_vape(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Vape cartridge matching focusing on strain, potency, and hardware type"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        # Vape-specific indicators
        vape_indicators = ['cart', 'cartridge', 'pod', 'disposable', 'pen', '510']
        
        for db_product in database_products:
            score = 0.0
            factors = {}
            
            db_name = str(db_product.get('Product Name*', '')).lower()
            
            # Vape type matching (25% weight)
            vape_type_score = 0.0
            for indicator in vape_indicators:
                if indicator in json_name and indicator in db_name:
                    vape_type_score = 1.0
                    break
                elif indicator in json_name or indicator in db_name:
                    vape_type_score = 0.5
                    
            factors['vape_type_match'] = vape_type_score
            score += vape_type_score * 0.25
            
            # Strain matching (30% weight)
            strain_score = self._extract_strain_similarity(json_name, db_name)
            factors['strain_match'] = strain_score
            score += strain_score * 0.3
            
            # Volume/size matching (20% weight)
            volume_score = self._compare_volumes(json_product, db_product)
            factors['volume_match'] = volume_score
            score += volume_score * 0.2
            
            # THC potency (15% weight)
            thc_score = self._compare_thc_content(json_product, db_product)
            factors['thc_match'] = thc_score
            score += thc_score * 0.15
            
            # Brand/vendor matching (10% weight)
            vendor_score = self._compare_vendors(json_product, db_product)
            factors['vendor_match'] = vendor_score
            score += vendor_score * 0.1
            
            if score > 0.1:  # Ultra-lenient threshold for vapes
                matches.append(MatchResult(
                    score=score,
                    match_data=db_product,
                    strategy_used=MatchStrategy.HYBRID,
                    confidence=score,
                    processing_time=0.0,
                    match_factors=factors
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _match_edible(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Edible-specific matching focusing on dosage, flavor, and form factor"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        # Extract dosage information
        json_dosage = self._extract_dosage(json_name)
        
        for db_product in database_products:
            score = 0.0
            factors = {}
            
            db_name = str(db_product.get('Product Name*', '')).lower()
            
            # Dosage matching (35% weight)
            db_dosage = self._extract_dosage(db_name)
            if json_dosage and db_dosage:
                dosage_diff = abs(json_dosage - db_dosage) / max(json_dosage, db_dosage)
                dosage_score = max(0, 1.0 - dosage_diff)
            else:
                dosage_score = 0.5  # Unknown dosage gets neutral score
                
            factors['dosage_match'] = dosage_score
            score += dosage_score * 0.35
            
            # Form factor matching (25% weight)
            form_score = self._compare_edible_forms(json_name, db_name)
            factors['form_match'] = form_score
            score += form_score * 0.25
            
            # Flavor matching (20% weight)
            flavor_score = self._compare_flavors(json_name, db_name)
            factors['flavor_match'] = flavor_score
            score += flavor_score * 0.2
            
            # Brand matching (20% weight)
            brand_score = self._compare_brands(json_product, db_product)
            factors['brand_match'] = brand_score
            score += brand_score * 0.2
            
            if score > 0.1:  # Ultra-lenient threshold for edibles
                matches.append(MatchResult(
                    score=score,
                    match_data=db_product,
                    strategy_used=MatchStrategy.HYBRID,
                    confidence=score,
                    processing_time=0.0,
                    match_factors=factors
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _match_preroll(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Pre-roll specific matching focusing on JointRatio, strain, and pack size"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        for db_product in database_products:
            db_name = str(db_product.get('Product Name*', '')).lower()
            
            score = 0
            factors = {}
            
            # Product name similarity (30% weight)
            name_score = fuzz.ratio(json_name, db_name) / 100.0
            factors['name_match'] = name_score
            score += name_score * 0.30
            
            # Strain name matching (25% weight for pre-rolls)
            strain_score = self._compare_strains(json_product, db_product)
            factors['strain_match'] = strain_score
            score += strain_score * 0.25
            
            # JointRatio matching (25% weight) - unique to pre-rolls
            joint_ratio_score = self._compare_joint_ratios(json_product, db_product)
            factors['joint_ratio_match'] = joint_ratio_score
            score += joint_ratio_score * 0.25
            
            # THC content matching (15% weight)
            thc_score = self._compare_thc_content(json_product, db_product)
            factors['thc_match'] = thc_score
            score += thc_score * 0.15
            
            # Vendor matching (5% weight)
            vendor_score = self._compare_vendors(json_product, db_product)
            factors['vendor_match'] = vendor_score
            score += vendor_score * 0.05
            
            if score > 0.1:  # Threshold for pre-roll matches
                matches.append(MatchResult(
                    score=score,
                    matched_product=db_product,
                    algorithm="Enhanced PreRoll",
                    factors=factors
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)[:10]
        
    def _match_topical(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Topical-specific matching"""
        matches = []
        # Topical matching focuses on application method, CBD/THC ratio
        # Implementation similar to other product types
        return matches
        
    def _match_tincture(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Tincture-specific matching"""
        matches = []
        # Tincture matching focuses on concentration, volume, carrier oil
        # Implementation similar to other product types
        return matches
        
    def _match_generic(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Generic matching for unknown product types"""
        matches = []
        json_name = self._get_product_name(json_product).lower()
        
        for db_product in database_products:
            db_name = str(db_product.get('Product Name*', '')).lower()
            
            # Simple fuzzy matching
            score = fuzz.ratio(json_name, db_name) / 100.0
            
            if score > 0.1:  # Ultra-lenient threshold for generic
                matches.append(MatchResult(
                    score=score,
                    match_data=db_product,
                    strategy_used=MatchStrategy.FUZZY,
                    confidence=score * 0.8,  # Lower confidence for generic matching
                    processing_time=0.0,
                    match_factors={'name_similarity': score}
                ))
                
        return sorted(matches, key=lambda x: x.score, reverse=True)
    
    # Helper methods for specific comparisons
    def _compare_weights(self, json_product: Dict, db_product: Dict) -> float:
        """Compare product weights with tolerance"""
        # Extract weight from both products
        json_weight = self._extract_weight(self._get_product_name(json_product))
        db_weight = self._extract_weight(str(db_product.get('Product Name*', '')))
        
        if not json_weight or not db_weight:
            return 0.5  # Unknown weight gets neutral score
            
        # Calculate similarity with tolerance
        weight_diff = abs(json_weight - db_weight) / max(json_weight, db_weight)
        return max(0, 1.0 - weight_diff)
        
    def _extract_weight(self, text: str) -> Optional[float]:
        """Extract weight in grams from text"""
        # Look for patterns like "3.5g", "1/8oz", "1oz", etc.
        weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*g(?:ram)?s?',
            r'(\d+(?:\.\d+)?)\s*oz(?:unce)?s?',
            r'(\d+)/(\d+)\s*oz',  # Fractions like 1/8oz
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    weight = float(match.group(1))
                    if 'oz' in pattern:
                        weight *= 28.35  # Convert oz to grams
                    return weight
                elif len(match.groups()) == 2:  # Fraction
                    numerator = float(match.group(1))
                    denominator = float(match.group(2))
                    weight = (numerator / denominator) * 28.35  # oz to grams
                    return weight
        
        return None
        
    def _compare_thc_content(self, json_product: Dict, db_product: Dict) -> float:
        """Compare THC content percentages"""
        # Extract THC percentages from lab results or product names
        json_thc = self._extract_thc_percentage(json_product)
        db_thc = self._extract_thc_percentage(db_product)
        
        if not json_thc or not db_thc:
            return 0.5
            
        thc_diff = abs(json_thc - db_thc) / max(json_thc, db_thc)
        return max(0, 1.0 - thc_diff)
        
    def _extract_thc_percentage(self, product: Dict) -> Optional[float]:
        """Extract THC percentage from product data"""
        # Check lab results first
        lab_results = product.get('lab_result_data', {})
        if isinstance(lab_results, dict):
            thc = lab_results.get('thc', lab_results.get('THC'))
            if thc:
                try:
                    return float(thc)
                except:
                    pass
                    
        # Check product name for THC percentage
        name = str(product.get('inventory_name', '') or product.get('Product Name*', ''))
        thc_match = re.search(r'(\d+(?:\.\d+)?)%?\s*thc', name, re.IGNORECASE)
        if thc_match:
            return float(thc_match.group(1))
            
        return None
        
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

    def _compare_vendors(self, json_product: Dict, db_product: Dict) -> float:
        """Compare vendor names with fuzzy matching"""
        json_vendor = str(json_product.get('vendor', '') or json_product.get('vendor_name', '')).lower().strip()
        db_vendor = str(db_product.get('Vendor/Supplier*', '') or db_product.get('Vendor', '')).lower().strip()
        
        # If no vendor info available, return neutral score
        if not json_vendor or not db_vendor or json_vendor == 'no_vendor':
            return 0.3  # Neutral score when vendor comparison isn't possible
            
        # Perfect match
        if json_vendor == db_vendor:
            return 1.0
            
        # Use fuzzy matching for vendor comparison
        score = fuzz.ratio(json_vendor, db_vendor) / 100.0
        
        # Also try partial matching for compound vendor names
        partial_score = fuzz.partial_ratio(json_vendor, db_vendor) / 100.0
        
        return max(score, partial_score)

    def _compare_joint_ratios(self, json_product: Dict, db_product: Dict) -> float:
        """Compare joint ratios for pre-roll products (e.g., '0.5g x 2 Pack', '1g x 1')"""
        # Try to extract joint ratio from JSON product name
        json_name = self._get_product_name(json_product).lower()
        db_joint_ratio = str(db_product.get('JointRatio', '')).lower().strip()
        
        # If no database JointRatio, return neutral score
        if not db_joint_ratio or db_joint_ratio in ['', 'null', 'none', '0']:
            return 0.3
        
        # Look for pack indicators in JSON name
        json_pack_indicators = []
        
        # Extract pack size patterns (e.g., "2 pack", "twin pack", "single", "1g x 2")
        pack_patterns = [
            r'(\d+)\s*pack',           # "2 pack", "twin pack"
            r'(\d+)\s*count',          # "5 count"
            r'twin|double',            # "twin pack" -> 2
            r'single',                 # "single" -> 1
            r'(\d+(?:\.\d+)?)\s*g\s*x\s*(\d+)',  # "0.5g x 2"
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*g',  # "2 x 0.5g"
        ]
        
        for pattern in pack_patterns:
            matches = re.findall(pattern, json_name)
            if matches:
                if pattern in [r'twin|double']:
                    json_pack_indicators.append('2')
                elif pattern in [r'single']:
                    json_pack_indicators.append('1')
                else:
                    for match in matches:
                        if isinstance(match, tuple):
                            json_pack_indicators.extend(match)
                        else:
                            json_pack_indicators.append(match)
        
        # Compare with database JointRatio
        best_score = 0.0
        
        # Direct fuzzy comparison
        fuzzy_score = fuzz.ratio(json_name, db_joint_ratio) / 100.0
        best_score = max(best_score, fuzzy_score)
        
        # Pattern-based comparison
        for indicator in json_pack_indicators:
            if indicator in db_joint_ratio:
                best_score = max(best_score, 0.8)
        
        # Special patterns (e.g., if JSON has "twin" and DB has "x 2")
        if 'twin' in json_name and ('x 2' in db_joint_ratio or '2 pack' in db_joint_ratio):
            best_score = max(best_score, 0.9)
        
        if 'single' in json_name and ('x 1' in db_joint_ratio or '1 pack' in db_joint_ratio or '1g' in db_joint_ratio):
            best_score = max(best_score, 0.9)
        
        return best_score

    def _compare_strains(self, json_product: Dict, db_product: Dict) -> float:
        """Compare strain names with fuzzy matching"""
        # Extract strain from JSON
        json_strain = ""
        for field in ['strain', 'strain_name', 'product_strain']:
            if field in json_product:
                json_strain = str(json_product[field]).lower().strip()
                break
        
        # If no explicit strain field, try to extract from product name
        if not json_strain:
            json_name = self._get_product_name(json_product).lower()
            # Look for common strain patterns in name
            strain_patterns = [
                r'og\s+kush', r'sour\s+diesel', r'blue\s+dream', r'white\s+widow',
                r'granddaddy\s+purple', r'green\s+crack', r'northern\s+lights'
            ]
            for pattern in strain_patterns:
                if re.search(pattern, json_name):
                    json_strain = re.search(pattern, json_name).group()
                    break
        
        # Extract strain from database
        db_strain = str(db_product.get('Product Strain', '') or db_product.get('Strain', '')).lower().strip()
        
        # If no strain info available, return neutral score
        if not json_strain or not db_strain or db_strain in ['', 'mixed', 'unknown']:
            return 0.5
        
        # Perfect match
        if json_strain == db_strain:
            return 1.0
        
        # Fuzzy matching
        score = fuzz.ratio(json_strain, db_strain) / 100.0
        partial_score = fuzz.partial_ratio(json_strain, db_strain) / 100.0
        
        return max(score, partial_score)
        
    def _extract_strain_similarity(self, json_name: str, db_name: str) -> float:
        """Extract and compare strain names"""
        # Remove common product type words to focus on strain names
        common_words = ['cart', 'cartridge', 'live', 'resin', 'rosin', 'wax', 'shatter', 'gummy', 'chocolate']
        
        json_clean = json_name
        db_clean = db_name
        
        for word in common_words:
            json_clean = re.sub(rf'\b{word}\b', '', json_clean, flags=re.IGNORECASE)
            db_clean = re.sub(rf'\b{word}\b', '', db_clean, flags=re.IGNORECASE)
            
        return fuzz.token_sort_ratio(json_clean.strip(), db_clean.strip()) / 100.0
        
    def _compare_potency(self, json_product: Dict, db_product: Dict) -> float:
        """Compare overall potency/cannabinoid content"""
        # This is a simplified version - could be expanded
        return self._compare_thc_content(json_product, db_product)
        
    def _compare_volumes(self, json_product: Dict, db_product: Dict) -> float:
        """Compare product volumes (for vapes, tinctures, etc.)"""
        json_volume = self._extract_volume(self._get_product_name(json_product))
        db_volume = self._extract_volume(str(db_product.get('Product Name*', '')))
        
        if not json_volume or not db_volume:
            return 0.5
            
        volume_diff = abs(json_volume - db_volume) / max(json_volume, db_volume)
        return max(0, 1.0 - volume_diff)
        
    def _extract_volume(self, text: str) -> Optional[float]:
        """Extract volume in ml from text"""
        volume_patterns = [
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*cc',
            r'(\d+(?:\.\d+)?)\s*fl\s*oz'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                volume = float(match.group(1))
                if 'fl' in pattern and 'oz' in pattern:
                    volume *= 29.5735  # Convert fl oz to ml
                return volume
                
        return None
        
    def _extract_dosage(self, text: str) -> Optional[float]:
        """Extract dosage in mg from text"""
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*mg',
            r'(\d+(?:\.\d+)?)\s*milligram'
        ]
        
        for pattern in dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
                
        return None
        
    def _compare_edible_forms(self, json_name: str, db_name: str) -> float:
        """Compare edible form factors"""
        forms = ['gummy', 'chocolate', 'cookie', 'brownie', 'candy', 'mint', 'tablet', 'capsule']
        
        json_forms = [form for form in forms if form in json_name.lower()]
        db_forms = [form for form in forms if form in db_name.lower()]
        
        if not json_forms or not db_forms:
            return 0.5
            
        # Check for matching forms
        matches = len(set(json_forms) & set(db_forms))
        total = len(set(json_forms) | set(db_forms))
        
        return matches / total if total > 0 else 0
        
    def _compare_flavors(self, json_name: str, db_name: str) -> float:
        """Compare flavor profiles"""
        flavors = ['cherry', 'strawberry', 'grape', 'orange', 'lemon', 'lime', 'berry', 'mint', 
                  'chocolate', 'vanilla', 'caramel', 'apple', 'peach', 'mango', 'pineapple']
        
        json_flavors = [flavor for flavor in flavors if flavor in json_name.lower()]
        db_flavors = [flavor for flavor in flavors if flavor in db_name.lower()]
        
        if not json_flavors or not db_flavors:
            return 0.5
            
        matches = len(set(json_flavors) & set(db_flavors))
        total = len(set(json_flavors) | set(db_flavors))
        
        return matches / total if total > 0 else 0.5
        
    def _compare_brands(self, json_product: Dict, db_product: Dict) -> float:
        """Compare brand names"""
        json_brand = str(json_product.get('brand_name', '')).lower().strip()
        db_brand = str(db_product.get('Product Brand', '')).lower().strip()
        
        if not json_brand or not db_brand:
            return 0.5
            
        return fuzz.ratio(json_brand, db_brand) / 100.0

# Enhanced JSON field mapping for hybrid approach
ENHANCED_JSON_FIELD_MAP = {
    "product_name": "Product Name*",
    "description": "Description", 
    "vendor": "Vendor/Supplier*",
    "brand": "Product Brand",
    "price": "Price",
    "weight": "Weight*",
    "strain": "Product Strain",
    "product_type": "Product Type*",
    "sku": "Internal Product Identifier",
    "batch_number": "Batch Number",
    "lot_number": "Lot Number",
    "room": "Room*",
    "quantity": "Quantity*",
    "units": "Units",
    "unit_weight_uom": "Units",
    "thc_percentage": "THC test result",
    "cbd_percentage": "CBD test result",
    "harvest_date": "Accepted Date",
    "package_date": "Accepted Date",
    "lineage": "Lineage"
}

class EnhancedJSONMatcher:
    """
    Enhanced JSON Matcher with comprehensive improvements:
    - Performance optimizations with caching and parallel processing
    - Accuracy improvements with multiple matching algorithms  
    - Product type-specific matching strategies
    - ML-enhanced similarity scoring
    """
    
    def __init__(self, excel_processor):
        self.excel_processor = excel_processor
        self.profiler = PerformanceProfiler()
        self.cache = SmartCache(default_ttl=3600, max_size=10000)
        self.product_matcher = ProductTypeSpecificMatcher()
        
        # Caches for performance
        self._sheet_cache = None
        self._indexed_cache = None
        self._ml_cache = {}
        self._embedding_cache = {}
        
        # ML components (only if sklearn is available)
        self.tfidf_vectorizer = None
        self.product_embeddings = None
        self.scaler = StandardScaler() if _SKLEARN_AVAILABLE and StandardScaler is not None else None
        
        # Threading
        self.max_workers = min(32, (multiprocessing.cpu_count() or 1) + 4)

    def _to_json_safe(self, obj):
        """Recursively convert objects to JSON-serializable forms."""
        try:
            # Enum -> value or name
            if isinstance(obj, Enum):
                return getattr(obj, 'value', obj.name)
            # Numpy scalars -> python scalars
            try:
                import numpy as _np  # local import to avoid global dependency during patching
                if isinstance(obj, _np.generic):
                    return obj.item()
            except Exception:
                pass
            # Pandas types
            try:
                import pandas as _pd
                if isinstance(obj, _pd.Timestamp):
                    return obj.isoformat()
            except Exception:
                pass
            if isinstance(obj, dict):
                return {k: self._to_json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [self._to_json_safe(v) for v in obj]
            if isinstance(obj, tuple):
                return [self._to_json_safe(v) for v in obj]
            return obj
        except Exception:
            return str(obj)

    def _is_void_product(self, product: dict) -> bool:
        """Return True if product name contains VOID (case-insensitive)."""
        try:
            name = (product.get('Product Name*') or product.get('ProductName') or product.get('displayName') or '')
            return 'void' in str(name).lower()
        except Exception:
            return False

    def _parse_dt(self, value: str):
        """Parse various date formats to a sortable timestamp; return 0 if unknown."""
        try:
            from datetime import datetime
            if not value:
                return 0
            s = str(value).strip()
            # Try ISO first
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    return int(datetime.strptime(s, fmt).timestamp())
                except Exception:
                    continue
            # Fallback: pandas to_datetime if available
            try:
                import pandas as _pd
                return int(_pd.to_datetime(s, errors='coerce').timestamp()) if _pd.to_datetime(s, errors='coerce') is not None else 0
            except Exception:
                return 0
        except Exception:
            return 0

    def _extract_json_price(self, json_data: list, product_dict: dict) -> str:
        """Extract price from JSON data for the matched product."""
        try:
            # Find the matching JSON item for this product
            product_name = product_dict.get('Product Name*') or product_dict.get('ProductName') or ''
            
            for json_item in json_data:
                json_name = json_item.get('product_name') or json_item.get('inventory_name') or ''
                
                # Enhanced name matching to find the corresponding JSON item
                # Try exact match first, then partial match
                if (product_name.lower().strip() == json_name.lower().strip() or
                    json_name.lower().strip() in product_name.lower().strip() or
                    product_name.lower().strip() in json_name.lower().strip()):
                    # Extract price from JSON item
                    price_candidates = [
                        json_item.get('price'),
                        json_item.get('Price'),
                        json_item.get('line_price'),
                        json_item.get('retail_price'),
                        json_item.get('unit_price'),
                        json_item.get('sale_price'),
                        json_item.get('unit_cost'),
                        json_item.get('cost'),
                        json_item.get('Cost')
                    ]
                    
                    for price in price_candidates:
                        if price is not None:
                            price_str = str(price).strip()
                            if price_str and price_str.lower() != 'none' and price_str not in ('0', '0.0', '0.00'):
                                logging.info(f"💰 Using JSON price '{price_str}' for '{product_name}'")
                                return price_str
                    break
            
            return None
        except Exception as e:
            logging.warning(f"Error extracting JSON price: {e}")
            return None

    def _extract_json_weight(self, json_data: list, product_dict: dict) -> str:
        """Extract weight from JSON data for the matched product."""
        try:
            # Find the matching JSON item for this product
            product_name = product_dict.get('Product Name*') or product_dict.get('ProductName') or ''
            
            for json_item in json_data:
                json_name = json_item.get('product_name') or json_item.get('inventory_name') or ''
                
                # Enhanced name matching to find the corresponding JSON item
                # Try exact match first, then partial match
                if (product_name.lower().strip() == json_name.lower().strip() or
                    json_name.lower().strip() in product_name.lower().strip() or
                    product_name.lower().strip() in json_name.lower().strip()):
                    # Extract weight from JSON item
                    weight_candidates = [
                        json_item.get('weight'),
                        json_item.get('Weight'),
                        json_item.get('weight_with_units'),
                        json_item.get('weight_units'),
                        json_item.get('size'),
                        json_item.get('Size'),
                        json_item.get('quantity'),
                        json_item.get('Quantity')
                    ]
                    
                    for weight in weight_candidates:
                        if weight is not None:
                            weight_str = str(weight).strip()
                            if weight_str and weight_str.lower() != 'none' and weight_str not in ('0', '0.0', '0.00'):
                                logging.info(f"⚖️ Using JSON weight '{weight_str}' for '{product_name}'")
                                return weight_str
                    break
            
            return None
        except Exception as e:
            logging.warning(f"Error extracting JSON weight: {e}")
            return None

    def _merge_json_data_hybrid(self, product_dict: dict, json_items: list, match_result=None) -> dict:
        """
        DATABASE-PRIORITY approach: Use 100% database-derived information.
        JSON is only used for matching purposes, all data comes from database.
        """
        if not json_items:
            logging.debug("🔄 DATABASE PRIORITY: No JSON items to merge")
            return product_dict
            
        # Find the best matching JSON item for this product (for matching purposes only)
        json_item = None
        product_name = (product_dict.get('Product Name*') or 
                       product_dict.get('ProductName') or '').lower().strip()
        
        logging.debug(f"🔍 DATABASE PRIORITY: Looking for JSON match for '{product_name}' (matching only)")
        
        # Try to find exact or best matching JSON item with multiple strategies
        best_match_score = 0
        for i, item in enumerate(json_items):
            item_name = (item.get('product_name') or 
                        item.get('inventory_name') or '').lower().strip()
            if item_name:
                # Strategy 1: Word overlap similarity
                similarity = len(set(item_name.split()) & set(product_name.split())) / max(len(set(item_name.split())), len(set(product_name.split())), 1)
                
                # Strategy 2: Substring matching
                substring_score = 0
                if item_name in product_name or product_name in item_name:
                    substring_score = 0.8
                
                # Strategy 3: Fuzzy matching (simple)
                common_chars = set(item_name) & set(product_name)
                fuzzy_score = len(common_chars) / max(len(set(item_name)), len(set(product_name)), 1) * 0.6
                
                # Combined score
                total_score = max(similarity, substring_score, fuzzy_score)
                
                if total_score > best_match_score:
                    best_match_score = total_score
                    json_item = item
                    logging.debug(f"🎯 DATABASE PRIORITY: Better match found at index {i}: '{item_name}' (score: {total_score:.3f})")
        
        # CRITICAL FIX: If no good match found, still use first JSON item but with lower confidence
        if not json_item and json_items:
            json_item = json_items[0]
            best_match_score = 0.1  # Low confidence fallback
            json_item_name = (json_item.get('product_name') or json_item.get('inventory_name') or 'UNKNOWN')
            logging.info(f"🔄 DATABASE PRIORITY: No good match found, using first JSON item '{json_item_name}' as fallback")
            
        if not json_item:
            logging.warning("🔄 DATABASE PRIORITY: No JSON item available for match")
            return product_dict
            
        # Create database-priority product: 100% database data
        db_priority_product = dict(product_dict)  # Start with database match - this is our complete data source
        
        logging.info(f"� DATABASE PRIORITY: Using 100% database-derived information for '{product_name}'")
        logging.debug(f"💽 DATABASE PRIORITY: Database product contains {len(db_priority_product)} fields")
        
        # IMPORTANT: NO JSON data merging - all information comes from database
        # JSON is only used for matching purposes, not for data extraction
        
        # Ensure all critical fields have database values or safe defaults
        critical_fields = {
            'Price': '25.00',  # Default price if missing
            'Weight*': '1',    # Default weight if missing
            'Units': 'g',      # Default units if missing
            'THC test result': '0.00',  # Default THC if missing
            'CBD test result': '0.00',  # Default CBD if missing
            'Quantity*': '1',  # Default quantity if missing
            'Product Type*': 'Unknown',  # Default type if missing
            'Lineage': 'MIXED',  # Default lineage if missing
        }
        
        # SPECIAL HANDLING FOR PRE-ROLL PRODUCTS: Use JointRatio instead of Weight* 
        product_type = (db_priority_product.get('Product Type*') or '').lower().strip()
        is_preroll = 'pre-roll' in product_type or 'infused pre-roll' in product_type
        
        logging.info(f"🔍 ENHANCED MATCHER DEBUG: Product '{db_priority_product.get('Product Name*', 'N/A')}' Type: '{product_type}' Is Pre-roll: {is_preroll}")
        
        if is_preroll:
            # For pre-roll products, preserve JointRatio and update Weight* for display
            joint_ratio = db_priority_product.get('JointRatio', '').strip()
            logging.info(f"🔍 PRE-ROLL JOINT RATIO: Found '{joint_ratio}' for product '{db_priority_product.get('Product Name*', 'N/A')}'")
            if joint_ratio and joint_ratio not in ['', 'NULL', 'null', '0', '0.0', 'None', 'nan']:
                # Preserve JointRatio field and set Weight* for display compatibility
                db_priority_product['Weight*'] = joint_ratio
                # Ensure JointRatio field is explicitly preserved for template processing
                db_priority_product['JointRatio'] = joint_ratio
                logging.info(f"🚬 PRE-ROLL FIXED: Using JointRatio '{joint_ratio}' as Weight* for {product_type}")
            else:
                # Default JointRatio if missing - preserve both fields
                default_ratio = '0.5g x 2 Pack'
                db_priority_product['JointRatio'] = default_ratio
                db_priority_product['Weight*'] = default_ratio
                logging.debug(f"🚬 PRE-ROLL PRIORITY: Set default JointRatio '{default_ratio}' for {product_type}")
        
        filled_defaults = 0
        for field, default_value in critical_fields.items():
            current_value = db_priority_product.get(field)
            if not current_value or str(current_value).strip() in ['', 'NULL', 'null', '0', '0.0', 'None', 'nan']:
                db_priority_product[field] = default_value
                filled_defaults += 1
                logging.debug(f"� DATABASE PRIORITY: Set default for {field} = '{default_value}'")
        
        if filled_defaults > 0:
            logging.info(f"� DATABASE PRIORITY: Applied {filled_defaults} default values for missing database fields")
                
        # CRITICAL: Add metadata about the database priority approach
        db_priority_product['Source'] = 'Database Priority (100% DB)'
        db_priority_product['JSON_Source'] = 'Matching Only'
        db_priority_product['Match_Confidence'] = f"{best_match_score:.3f}"
        db_priority_product['Data_Source'] = 'Database'
        
        # Preserve original match information
        if hasattr(match_result, 'score'):
            db_priority_product['Match_Score'] = float(getattr(match_result, 'score', 0.8))
        else:
            db_priority_product['Match_Score'] = 0.8  # Default score
            
        if hasattr(match_result, 'algorithm'):
            db_priority_product['Match_Algorithm'] = str(getattr(match_result, 'algorithm', 'Enhanced'))
        elif hasattr(match_result, 'strategy_used'):
            strategy = getattr(match_result, 'strategy_used')
            db_priority_product['Match_Algorithm'] = str(getattr(strategy, 'value', str(strategy)))
        else:
            db_priority_product['Match_Algorithm'] = 'Enhanced'
            
        # CRITICAL: Add JSON item tracking for debugging (matching info only)
        json_item_name = json_item.get('product_name') or json_item.get('inventory_name') or 'UNKNOWN'
        db_priority_product['JSON_Item_Name'] = json_item_name
        db_priority_product['JSON_Fields_Used'] = 0  # No JSON fields used for data
        db_priority_product['Default_Fields_Applied'] = filled_defaults
            
        logging.info(f"💽 DATABASE PRIORITY COMPLETE: '{product_name}' using 100% database data, matched with JSON '{json_item_name}' (match score: {best_match_score:.3f}, defaults applied: {filled_defaults})")
        return db_priority_product

    def _select_db_price(self, product: dict) -> str:
        """Pick the best available price field from a DB product record."""
        try:
            candidate_keys = [
                'Price',
                'Price* (Tier Name for Bulk)',
                'Med Price',
                'Price*'
            ]
            for key in candidate_keys:
                if key in product:
                    v = product.get(key)
                    if v is None:
                        continue
                    s = str(v).strip()
                    if s and s.lower() != 'none' and s not in ('0', '0.0', '0.00'):
                        return s
            return '0'
        except Exception:
            return '0'

    def _format_price(self, value: str) -> str:
        """Format price to omit trailing .00 but keep two decimals for non-whole numbers."""
        try:
            s = str(value).strip().replace('$', '')
            # Handle comma thousands
            s = s.replace(',', '')
            num = float(s) if s else 0.0
            if abs(num - int(num)) < 1e-9:
                return f"{int(num)}"
            return f"{num:.2f}"
        except Exception:
            return str(value)

    def _normalize_unit_label(self, unit: str) -> str:
        """Normalize unit strings to short symbols (g, oz, mg, ml)."""
        try:
            if not unit:
                return ''
            u = str(unit).strip().lower()
            if u in ('g', 'gram', 'grams', 'gm', 'grams/gm', 'grams/gm or ounces/oz'):
                return 'g'
            if u in ('oz', 'ounce', 'ounces', 'ounces/oz'):
                return 'oz'
            if u in ('mg', 'milligram', 'milligrams'):
                return 'mg'
            if u in ('ml', 'milliliter', 'milliliters'):
                return 'ml'
            return u
        except Exception:
            return str(unit)

    def _infer_units_from_text(self, product: dict) -> str:
        """Try to infer units from product name/description tokens like '3.5g' or '1oz'."""
        try:
            text = (
                product.get('Product Name*') or product.get('ProductName') or product.get('Description') or ''
            )
            s = str(text)
            m = re.search(r"\b\d+(?:\.\d+)?\s*(g|oz|mg|ml)\b", s, flags=re.IGNORECASE)
            if m:
                return self._normalize_unit_label(m.group(1))
            return ''
        except Exception:
            return ''

    def _select_units(self, product: dict) -> str:
        """Pick the best units field (prefer weight unit column over 'each')."""
        try:
            # Prefer explicit weight unit column
            wu_key = 'Weight Unit* (grams/gm or ounces/oz)'
            weight_unit = product.get(wu_key)
            weight_unit_norm = self._normalize_unit_label(weight_unit) if weight_unit else ''
            if weight_unit_norm:
                return weight_unit_norm
            # Check alternative DB fields
            alt_wu = product.get('weight_units') or product.get('WeightUnits')
            alt_wu_norm = self._normalize_unit_label(alt_wu) if alt_wu else ''
            if alt_wu_norm:
                return alt_wu_norm
            # Parse combined field like "3.5g"
            combo = product.get('weight_with_units') or product.get('CombinedWeight') or product.get('DescAndWeight')
            if combo:
                m = re.search(r"\b\d+(?:\.\d+)?\s*(g|oz|mg|ml)\b", str(combo), flags=re.IGNORECASE)
                if m:
                    return self._normalize_unit_label(m.group(1))
            # Next, existing Units if not 'each'
            units = product.get('Units')
            if units and str(units).strip().lower() not in ('each', 'ea'):
                return self._normalize_unit_label(units)
            # Infer from name
            inferred = self._infer_units_from_text(product)
            if inferred:
                return inferred
            # Fallback to existing Units even if 'each'
            return self._normalize_unit_label(units or '')
        except Exception:
            return str(product.get('Units', ''))

    def _normalize_vendor(self, vendor: str) -> str:
        """Normalize vendor strings to improve matching across formats.
        Examples:
          'CERES - 435011' -> 'ceres'
          'Ceres, Inc.' -> 'ceres inc'
        """
        try:
            if not vendor:
                return ''
            v = str(vendor).lower().strip()
            # Replace ampersands with 'and'
            v = v.replace('&', ' and ')
            # Remove obvious license/id suffixes like ' - 435011' or '-435011'
            v = re.sub(r"\s*-\s*\d+[\w-]*$", '', v)
            # Remove any trailing all-digit tokens
            v = re.sub(r"\b\d+\b", '', v)
            # Collapse punctuation to spaces
            v = re.sub(r"[^a-z0-9]+", ' ', v)
            # Collapse repeated spaces
            v = re.sub(r"\s+", ' ', v).strip()
            return v
        except Exception:
            return str(vendor).lower().strip()
        
    @lru_cache(maxsize=1000)
    def _normalize_text(self, text: str) -> str:
        """Cached text normalization"""
        if not text:
            return ""
        
        # Remove special characters, normalize whitespace
        normalized = re.sub(r'[^\w\s-]', '', str(text).lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _get_product_name(self, product: Dict) -> str:
        """Get product name from JSON product, handling different field names"""
        # Check for Cultivera format first (product_name)
        name = product.get('product_name', '')
        if name:
            return str(name)
        
        # Fallback to other common formats
        name = product.get('inventory_name', '')
        if name:
            return str(name)
            
        name = product.get('Product Name*', '')
        if name:
            return str(name)
            
        return ''
    
    def _vendors_match(self, vendor1: str, vendor2: str) -> bool:
        """Check if two vendor names represent the same vendor using fuzzy matching"""
        if not vendor1 or not vendor2:
            return False
            
        vendor1 = vendor1.lower().strip()
        vendor2 = vendor2.lower().strip()
        
        if vendor1 == vendor2:
            return True
            
        # Use fuzzy matching to handle slight variations
        similarity = fuzz.ratio(vendor1, vendor2)
        if similarity >= 80:  # 80% similarity threshold
            return True
            
        # Check if one vendor name is contained in the other (for abbreviations)
        if len(vendor1) >= 3 and len(vendor2) >= 3:
            if vendor1 in vendor2 or vendor2 in vendor1:
                return True
                
        return False
        
    def _build_ml_models(self):
        """Build machine learning models for enhanced matching"""
        if not self.excel_processor or self.excel_processor.df is None or self.excel_processor.df.empty:
            return
            
        if not _SKLEARN_AVAILABLE or TfidfVectorizer is None:
            logging.info("Skipping ML model build (scikit-learn unavailable)")
            return
        logging.info("Building ML models for enhanced matching...")
        start_time = time.perf_counter()
        
        try:
            df = self.excel_processor.df
            
            # Get product names for TF-IDF
            product_names = []
            for col in ["Product Name*", "ProductName", "Description"]:
                if col in df.columns:
                    names = df[col].dropna().astype(str).tolist()
                    product_names.extend(names)
                    break
            
            if not product_names:
                logging.warning("No product names found for ML model building")
                return
                
            # Build TF-IDF model
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english',
                lowercase=True
            )
            
            # Normalize product names
            normalized_names = [self._normalize_text(name) for name in product_names]
            self.product_embeddings = self.tfidf_vectorizer.fit_transform(normalized_names)
            
            build_time = time.perf_counter() - start_time
            logging.info(f"ML models built successfully in {build_time:.3f}s")
            
        except Exception as e:
            logging.error(f"Error building ML models: {e}")
            
    def match_products(self, json_data: List[Dict], strategy: MatchStrategy = MatchStrategy.HYBRID) -> List[MatchResult]:
        """
        Enhanced product matching with multiple strategies and parallel processing
        """
        if not json_data:
            return []
            
        # Build ML models if not already built
        if self.tfidf_vectorizer is None:
            self._build_ml_models()
            
        # Cache key for this matching request
        cache_key = self._generate_match_cache_key(json_data, strategy)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logging.info("Returning cached matching results")
            return cached_result
            
        start_time = time.perf_counter()
        all_matches = []
        
        # Process in parallel batches
        batch_size = max(10, len(json_data) // self.max_workers)
        batches = [json_data[i:i + batch_size] for i in range(0, len(json_data), batch_size)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch, strategy): batch 
                for batch in batches
            }
            
            for future in as_completed(future_to_batch):
                try:
                    batch_matches = future.result()
                    all_matches.extend(batch_matches)
                except Exception as e:
                    logging.error(f"Error processing batch: {e}")
                    
        # Sort by score and apply post-processing
        all_matches.sort(key=lambda x: x.score, reverse=True)
        
        # Post-processing: remove low-confidence duplicates
        filtered_matches = self._filter_duplicate_matches(all_matches)
        
        processing_time = time.perf_counter() - start_time
        logging.info(f"Enhanced matching completed: {len(filtered_matches)} matches found in {processing_time:.3f}s")
        
        # Cache the results
        self.cache.set(cache_key, filtered_matches, ttl=1800)  # 30 minute cache
        
        return filtered_matches
        
    def _process_batch(self, json_batch: List[Dict], strategy: MatchStrategy) -> List[MatchResult]:
        """Process a batch of JSON products"""
        batch_matches = []
        
        for json_product in json_batch:
            try:
                product_matches = self._match_single_product(json_product, strategy)
                batch_matches.extend(product_matches)
            except Exception as e:
                logging.error(f"Error matching product {json_product.get('inventory_name', 'unknown')}: {e}")
                
        return batch_matches
        
    def _match_single_product(self, json_product: Dict, strategy: MatchStrategy) -> List[MatchResult]:
        """Match a single JSON product using the specified strategy"""
        start_time = time.perf_counter()
        
        # CRITICAL FIX: Extract vendor information from product name if not present
        if not json_product.get('vendor') or json_product.get('vendor') == 'NO_VENDOR':
            product_name = self._get_product_name(json_product) or json_product.get('product_name', '')
            if product_name:
                extracted_vendor = self._extract_vendor(product_name)
                if extracted_vendor:
                    json_product['vendor'] = extracted_vendor
                    logging.debug(f"🔍 VENDOR EXTRACTION: '{product_name}' -> vendor: '{extracted_vendor}'")
        
        # Determine product type for specialized matching
        product_type = self._classify_product_type(json_product)
        
        # Get database products (with caching)
        database_products = self._get_database_products()
        
        # VENDOR RESTRICTION: Filter database products to match the JSON product's vendor
        json_vendor = self._normalize_vendor(json_product.get('vendor', ''))
        if json_vendor and json_vendor != 'no_vendor':
            # Filter database products to only include those from the same vendor
            vendor_filtered_products = []
            for db_product in database_products:
                raw_db_vendor = str(db_product.get('Vendor/Supplier*', '') or db_product.get('Vendor', '') or db_product.get('Product Brand', ''))
                db_vendor = self._normalize_vendor(raw_db_vendor)
                
                # Check for exact vendor match or partial match
                if (json_vendor == db_vendor or 
                    (json_vendor and db_vendor and (json_vendor in db_vendor or db_vendor in json_vendor)) or
                    self._vendors_match(json_vendor, db_vendor)):
                    vendor_filtered_products.append(db_product)
            
            if vendor_filtered_products:
                database_products = vendor_filtered_products
                logging.debug(f"🏢 VENDOR FILTER: Restricted to {len(database_products)} products from vendor '{json_vendor}'")
            else:
                logging.warning(f"⚠️ VENDOR FILTER: No products found for vendor '{json_vendor}', using all products")
        
        database_products = database_products
        
        matches = []
        
        if strategy == MatchStrategy.EXACT:
            matches = self._exact_match(json_product, database_products)
        elif strategy == MatchStrategy.FUZZY:
            matches = self._fuzzy_match(json_product, database_products)
        elif strategy == MatchStrategy.SEMANTIC:
            matches = self._semantic_match(json_product, database_products)
        elif strategy == MatchStrategy.ML_ENHANCED:
            matches = self._ml_enhanced_match(json_product, database_products)
        else:  # HYBRID
            matches = self._hybrid_match(json_product, database_products, product_type)
            
        # Set processing time for all matches
        processing_time = time.perf_counter() - start_time
        for match in matches:
            match.processing_time = processing_time
            
        return matches[:50]  # Return top 50 matches per product for maximum results
        
    def _hybrid_match(self, json_product: Dict, database_products: List[Dict], product_type: str) -> List[MatchResult]:
        """Hybrid matching combining multiple strategies"""
        
        # Start with product-type specific matching
        type_matches = self.product_matcher.match_by_type(product_type, json_product, database_products)
        
        # Enhance with semantic similarity if we have ML models
        if self.tfidf_vectorizer and self.product_embeddings is not None:
            semantic_matches = self._semantic_match(json_product, database_products)
            
            # Combine scores using weighted average
            combined_matches = self._combine_match_results(type_matches, semantic_matches)
        else:
            combined_matches = type_matches
            
        # Apply fuzzy matching as fallback for low-scoring items
        if not combined_matches or (combined_matches and combined_matches[0].score < 0.7):
            fuzzy_matches = self._fuzzy_match(json_product, database_products)
            if fuzzy_matches:
                # Blend the top fuzzy match with existing matches
                combined_matches = self._blend_match_results(combined_matches, fuzzy_matches[:3])
                
        return combined_matches
        
    def _exact_match(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Exact string matching"""
        matches = []
        json_name = self._normalize_text(self._get_product_name(json_product))
        
        for db_product in database_products:
            db_name = self._normalize_text(str(db_product.get('Product Name*', '')))
            
            if json_name == db_name:
                matches.append(MatchResult(
                    score=1.0,
                    match_data=db_product,
                    strategy_used=MatchStrategy.EXACT,
                    confidence=1.0,
                    processing_time=0.0,
                    match_factors={'exact_match': 1.0}
                ))
                
        return matches
        
    def _fuzzy_match(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Enhanced fuzzy matching with multiple algorithms"""
        matches = []
        json_name = self._get_product_name(json_product)
        
        # Get all database product names
        db_names = [str(db.get('Product Name*', '')) for db in database_products]
        
        # Use fuzzywuzzy's process.extract for efficient fuzzy matching
        fuzzy_results = process.extract(json_name, db_names, limit=50, scorer=fuzz.token_sort_ratio)
        
        for db_name, score in fuzzy_results:
            if score >= 30:  # Ultra-low fuzzy score threshold for more matches
                # Find the corresponding database product
                db_product = next((db for db in database_products if str(db.get('Product Name*', '')) == db_name), None)
                
                if db_product:
                    # Calculate additional similarity metrics
                    ratio_score = fuzz.ratio(json_name, db_name) / 100.0
                    partial_score = fuzz.partial_ratio(json_name, db_name) / 100.0
                    token_set_score = fuzz.token_set_ratio(json_name, db_name) / 100.0
                    
                    # Weighted combination of different fuzzy metrics
                    final_score = (
                        (score / 100.0) * 0.4 +  # token_sort_ratio
                        ratio_score * 0.3 +       # ratio
                        partial_score * 0.2 +     # partial_ratio
                        token_set_score * 0.1     # token_set_ratio
                    )
                    
                    matches.append(MatchResult(
                        score=final_score,
                        match_data=db_product,
                        strategy_used=MatchStrategy.FUZZY,
                        confidence=final_score * 0.9,  # Slightly lower confidence for fuzzy
                        processing_time=0.0,
                        match_factors={
                            'token_sort': score / 100.0,
                            'ratio': ratio_score,
                            'partial': partial_score,
                            'token_set': token_set_score
                        }
                    ))
                    
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _semantic_match(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """Semantic similarity matching using TF-IDF and cosine similarity"""
        if not self.tfidf_vectorizer or self.product_embeddings is None:
            return []
            
        matches = []
        json_name = self._normalize_text(self._get_product_name(json_product))
        
        try:
            # Transform the JSON product name
            json_vector = self.tfidf_vectorizer.transform([json_name])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(json_vector, self.product_embeddings).flatten()
            
            # Get top similar products
            top_indices = similarities.argsort()[-20:][::-1]  # Top 20
            
            for idx in top_indices:
                similarity_score = similarities[idx]
                if similarity_score > 0.1:  # Minimum semantic similarity threshold
                    if idx < len(database_products):
                        matches.append(MatchResult(
                            score=similarity_score,
                            match_data=database_products[idx],
                            strategy_used=MatchStrategy.SEMANTIC,
                            confidence=similarity_score,
                            processing_time=0.0,
                            match_factors={'semantic_similarity': similarity_score}
                        ))
                        
        except Exception as e:
            logging.error(f"Error in semantic matching: {e}")
            
        return sorted(matches, key=lambda x: x.score, reverse=True)
        
    def _ml_enhanced_match(self, json_product: Dict, database_products: List[Dict]) -> List[MatchResult]:
        """ML-enhanced matching with feature engineering"""
        # This could include more sophisticated ML models like:
        # - Neural networks for similarity learning
        # - Feature engineering with product attributes
        # - Clustering-based similarity
        
        # For now, combine semantic and fuzzy matching with learned weights
        semantic_matches = self._semantic_match(json_product, database_products)
        fuzzy_matches = self._fuzzy_match(json_product, database_products)
        
        # Use learned weights (could be trained on historical data)
        combined_matches = self._combine_match_results(
            semantic_matches, fuzzy_matches, 
            weights=(0.6, 0.4)  # Prefer semantic over fuzzy
        )
        
        return combined_matches
        
    def _classify_product_type(self, json_product: Dict) -> str:
        """Classify product type from JSON data"""
        inventory_type = str(json_product.get('inventory_type', '')).lower()
        product_name = self._get_product_name(json_product).lower()
        
        # Product type classification logic
        if any(term in inventory_type or term in product_name for term in ['flower', 'bud']):
            return 'flower'
        elif any(term in inventory_type or term in product_name for term in ['concentrate', 'extract', 'oil', 'wax', 'shatter', 'rosin', 'resin']):
            return 'concentrate'
        elif any(term in inventory_type or term in product_name for term in ['cart', 'vape', 'pen', 'disposable']):
            return 'vape_cartridge'
        elif any(term in inventory_type or term in product_name for term in ['edible', 'gummy', 'chocolate', 'cookie']):
            return 'edible'
        elif any(term in inventory_type or term in product_name for term in ['pre-roll', 'preroll', 'joint', 'infused pre-roll']):
            return 'pre_roll'
        elif any(term in inventory_type or term in product_name for term in ['topical', 'balm', 'cream', 'lotion']):
            return 'topical'
        elif any(term in inventory_type or term in product_name for term in ['tincture', 'drops', 'oil']):
            return 'tincture'
        else:
            return 'unknown'
            
    def _get_database_products(self) -> List[Dict]:
        """Get database products with caching"""
        cache_key = "database_products"
        cached_products = self.cache.get(cache_key)
        
        if cached_products:
            return cached_products
            
        # Try to get from ProductDatabase first (more reliable)
        try:
            from .product_database import get_database_path
            from .product_database import ProductDatabase
            import os
            
            # Use the correct database path - prioritize AGT_Bothell database
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            db_path = os.path.join(current_dir, 'uploads', 'product_database_AGT_Bothell.db')
            
            # Fallback to main database if AGT_Bothell doesn't exist
            if not os.path.exists(db_path):
                db_path = os.path.join(current_dir, 'uploads', 'product_database.db')
            
            if os.path.exists(db_path):
                product_db = ProductDatabase(db_path)
                products = product_db.get_all_products()
                logging.info(f"EnhancedJSONMatcher: Loaded {len(products)} products from ProductDatabase at {db_path}")
                
                # Cache for 1 hour
                self.cache.set(cache_key, products, ttl=3600)
                return products
                
        except Exception as e:
            logging.warning(f"EnhancedJSONMatcher: Could not load from ProductDatabase: {e}")
            
        # Fallback to excel processor
        if not self.excel_processor or self.excel_processor.df.empty:
            logging.warning("EnhancedJSONMatcher: No database or excel processor data available")
            return []
            
        df = self.excel_processor.df
        products = df.to_dict('records')
        logging.info(f"EnhancedJSONMatcher: Loaded {len(products)} products from Excel processor")
        
        # Cache for 1 hour
        self.cache.set(cache_key, products, ttl=3600)
        
        return products
        
    def _combine_match_results(self, matches1: List[MatchResult], matches2: List[MatchResult], 
                             weights: Tuple[float, float] = (0.5, 0.5)) -> List[MatchResult]:
        """Combine two sets of match results with weighted scores"""
        combined = {}
        
        # Add first set of matches
        for match in matches1:
            key = str(match.match_data.get('Product Name*', ''))
            combined[key] = {
                'match': match,
                'score1': match.score * weights[0],
                'score2': 0
            }
            
        # Add second set of matches
        for match in matches2:
            key = str(match.match_data.get('Product Name*', ''))
            if key in combined:
                combined[key]['score2'] = match.score * weights[1]
            else:
                combined[key] = {
                    'match': match,
                    'score1': 0,
                    'score2': match.score * weights[1]
                }
                
        # Create combined results
        result = []
        for key, data in combined.items():
            combined_score = data['score1'] + data['score2']
            match = data['match']
            match.score = combined_score
            match.strategy_used = MatchStrategy.HYBRID
            result.append(match)
            
        return sorted(result, key=lambda x: x.score, reverse=True)
        
    def _blend_match_results(self, primary_matches: List[MatchResult], 
                           fallback_matches: List[MatchResult]) -> List[MatchResult]:
        """Blend primary matches with fallback matches"""
        if not primary_matches:
            return fallback_matches
            
        if not fallback_matches:
            return primary_matches
            
        # Start with primary matches
        result = primary_matches.copy()
        
        # Add fallback matches that aren't already present
        primary_names = {str(m.match_data.get('Product Name*', '')) for m in primary_matches}
        
        for fallback_match in fallback_matches:
            fallback_name = str(fallback_match.match_data.get('Product Name*', ''))
            if fallback_name not in primary_names:
                # Reduce fallback score slightly
                fallback_match.score *= 0.9
                fallback_match.confidence *= 0.9
                result.append(fallback_match)
                
        return sorted(result, key=lambda x: x.score, reverse=True)
        
    def _filter_duplicate_matches(self, matches: List[MatchResult]) -> List[MatchResult]:
        """Remove duplicate matches and low-confidence results"""
        seen_products = set()
        filtered_matches = []
        
        for match in matches:
            product_key = str(match.match_data.get('Product Name*', ''))
            
            if product_key not in seen_products and match.score > 0.05:  # Ultra-low final threshold
                seen_products.add(product_key)
                filtered_matches.append(match)
                
        return filtered_matches
        
    def _generate_match_cache_key(self, json_data: List[Dict], strategy: MatchStrategy) -> str:
        """Generate cache key for matching request"""
        # Create a hash of the JSON data structure and strategy
        data_hash = hashlib.md5(str(json_data).encode()).hexdigest()
        return f"match_{strategy.value}_{data_hash}"
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return self.profiler.get_performance_report()
        
    def clear_cache(self):
        """Clear all caches"""
        self.cache = SmartCache(default_ttl=3600, max_size=10000)
        self._sheet_cache = None
        self._indexed_cache = None
        self._ml_cache.clear()
        self._embedding_cache.clear()
        
    def warm_cache(self):
        """Warm up caches for better performance"""
        logging.info("Warming up caches...")
        
        # Build ML models
        self._build_ml_models()
        
        # Pre-load database products
        self._get_database_products()
        
        logging.info("Cache warm-up completed")

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
        
    def fetch_and_match(self, url: str) -> List[Dict]:
        """
        Fetch JSON from URL and match products using enhanced matching.
        This method provides compatibility with the existing JSONMatcher interface.
        
        Args:
            url: URL to fetch JSON data from (HTTP URL or data URL)
            
        Returns:
            List of matched product dictionaries
        """
        try:
            logging.info(f"EnhancedJSONMatcher: Fetching and matching from URL: {url[:100]}...")
            
            # Handle data URLs
            if url.lower().startswith("data:"):
                if ',' in url:
                    header, data_part = url.split(',', 1)
                    if 'base64' in header:
                        decoded_data = base64.b64decode(data_part).decode('utf-8')
                        payload = json.loads(decoded_data)
                    else:
                        payload = json.loads(data_part)
                else:
                    raise ValueError("Invalid data URL format")
                    
            else:
                # Handle HTTP URLs
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                payload = response.json()
                
            # Extract items from payload
            document_vendor = None  # Extract document-level vendor information
            
            if isinstance(payload, list):
                json_items = payload
            elif isinstance(payload, dict):
                # Check for document-level vendor information first
                document_vendor = (payload.get("from_license_name") or 
                                 payload.get("vendor_name") or 
                                 payload.get("supplier_name"))
                                 
                json_items = payload.get("inventory_transfer_items", [])
                if not json_items:
                    json_items = payload.get("items", [])
                if not json_items:
                    json_items = payload.get("products", [])
                if not json_items:
                    json_items = payload.get("inventory", [])
            else:
                json_items = []
                
            logging.info(f"EnhancedJSONMatcher: Extracted {len(json_items)} items from JSON")
            
            # Log document-level vendor if found
            if document_vendor:
                logging.info(f"🏢 DOCUMENT VENDOR: Found document-level vendor '{document_vendor}' for all {len(json_items)} items")
            
            if not json_items:
                logging.warning("No items found in JSON data")
                return []
                
            # Convert to list of dicts if needed and normalize field names
            json_data = []
            for item in json_items:
                if isinstance(item, dict):
                    # Normalize field names for consistent processing
                    normalized_item = dict(item)
                    
                    # Convert product_name to inventory_name if needed
                    if 'product_name' in normalized_item and 'inventory_name' not in normalized_item:
                        normalized_item['inventory_name'] = normalized_item['product_name']
                    
                    # CRITICAL FIX: Assign document-level vendor to all items
                    if document_vendor:
                        normalized_item['vendor'] = document_vendor
                        logging.debug(f"🏢 ASSIGNED VENDOR: '{normalized_item.get('inventory_name', 'UNKNOWN')}' -> vendor: '{document_vendor}'")
                    elif 'vendor' in normalized_item and normalized_item['vendor'] and normalized_item['vendor'] != 'NO_VENDOR':
                        # Keep existing vendor info
                        pass
                    else:
                        # Only extract vendor from product name if no vendor info is available
                        product_name = normalized_item.get('inventory_name', '') or normalized_item.get('product_name', '')
                        if product_name:
                            extracted_vendor = self._extract_vendor(product_name)
                            if extracted_vendor and len(extracted_vendor) > 2:  # Avoid very short vendor names
                                normalized_item['vendor'] = extracted_vendor
                                logging.debug(f"🔍 EXTRACTED VENDOR: '{product_name}' -> vendor: '{extracted_vendor}'")
                    
                    json_data.append(normalized_item)
                    
            if not json_data:
                logging.warning("No valid items found in JSON data")
                return []
                
            # Use enhanced matching
            match_results = self.match_products(json_data, strategy=MatchStrategy.HYBRID)
            
            # Convert match results to product dictionaries for compatibility
            matched_products = []
            for match_result in match_results:
                product_dict = None
                # Case 1: advanced matcher result object with .product
                if hasattr(match_result, 'product') and getattr(match_result, 'product'):
                    product_dict = dict(getattr(match_result, 'product'))
                    score_val = getattr(match_result, 'score', 0.8)
                    algo_val = getattr(match_result, 'algorithm', 'Enhanced')
                # Case 1b: advanced matcher using .match_data instead of .product
                elif hasattr(match_result, 'match_data') and getattr(match_result, 'match_data'):
                    if isinstance(getattr(match_result, 'match_data'), dict):
                        product_dict = dict(getattr(match_result, 'match_data'))
                        score_val = getattr(match_result, 'score', 0.8)
                        algo_val = getattr(match_result, 'strategy_used', 'Enhanced')
                # Case 2: plain dict result that already looks like a product
                elif isinstance(match_result, dict):
                    # Some flows return {'product': {...}, 'score': 0.9, ...}
                    if 'product' in match_result and isinstance(match_result['product'], dict):
                        product_dict = dict(match_result['product'])
                        score_val = match_result.get('score', 0.8)
                        algo_val = match_result.get('algorithm', 'Enhanced')
                    else:
                        # Treat the dict as the product itself
                        product_dict = dict(match_result)
                        score_val = match_result.get('score', 0.8)
                        algo_val = match_result.get('algorithm', 'Enhanced')
                
                if product_dict:
                    if not isinstance(algo_val, str):
                        algo_val = getattr(algo_val, 'value', str(algo_val))
                    
                    # HYBRID APPROACH: Merge JSON data with database match
                    hybrid_product = self._merge_json_data_hybrid(product_dict, json_data, match_result)
                    
                    # Ensure match metadata is preserved
                    hybrid_product['Match_Score'] = score_val
                    hybrid_product['Match_Algorithm'] = algo_val
                    
                    # Ensure Description reflects the matched DB item values (not JSON codes)
                    if not hybrid_product.get('Description'):
                        description_value = (hybrid_product.get('Product Name*') or 
                                             hybrid_product.get('ProductName') or '')
                        hybrid_product['Description'] = description_value
                    
                    # Final price and weight handling with JSON priority
                    json_price = self._extract_json_price(json_data, hybrid_product)
                    if json_price:
                        hybrid_product['Price'] = self._format_price(json_price)
                    elif not hybrid_product.get('Price'):
                        db_price_raw = self._select_db_price(hybrid_product)
                        hybrid_product['Price'] = self._format_price(db_price_raw)
                    
                    json_weight = self._extract_json_weight(json_data, hybrid_product)
                    if json_weight:
                        hybrid_product['Weight*'] = json_weight
                        hybrid_product['WeightUnits'] = json_weight
                        hybrid_product['WeightWithUnits'] = json_weight
                    
                    # Ensure Units prefer weight units over 'each'
                    hybrid_product['Units'] = self._select_units(hybrid_product)
                    hybrid_product = self._to_json_safe(hybrid_product)
                    matched_products.append(hybrid_product)
                    
            # Filter out *VOID* products
            try:
                pre_filter_count = len(matched_products)
                matched_products = [p for p in matched_products if not self._is_void_product(p)]
                if len(matched_products) != pre_filter_count:
                    logging.info(f"EnhancedJSONMatcher: Removed {pre_filter_count - len(matched_products)} VOID products")
            except Exception as e:
                logging.warning(f"EnhancedJSONMatcher: VOID filter failed: {e}")

            # Reduce to at most one unique product per JSON item (prefer highest score, then most recent)
            try:
                max_items = len(json_items)
                # Sort by score desc, then recency desc
                def _recency(p: dict) -> int:
                    return max(
                        self._parse_dt(p.get('Accepted Date')),
                        self._parse_dt(p.get('last_seen_date')),
                        self._parse_dt(p.get('updated_at')),
                        0
                    )
                matched_products.sort(key=lambda p: (p.get('Match_Score', 0), _recency(p)), reverse=True)
                seen_names = set()
                reduced = []
                for p in matched_products:
                    name = p.get('Product Name*') or p.get('ProductName') or p.get('displayName') or ''
                    if not name:
                        continue
                    key = name.strip().lower()
                    if key in seen_names:
                        continue
                    seen_names.add(key)
                    reduced.append(p)
                    if len(reduced) >= max_items:
                        break
                logging.info(f"EnhancedJSONMatcher: Reduced {len(matched_products)} -> {len(reduced)} to match JSON item count {max_items}")
                matched_products = reduced
            except Exception as e:
                logging.warning(f"EnhancedJSONMatcher: Reduction step failed: {e}")
            
            logging.info(f"EnhancedJSONMatcher: Successfully matched {len(matched_products)} products")
            return matched_products
            
        except Exception as e:
            logging.error(f"EnhancedJSONMatcher fetch_and_match error: {str(e)}")
            # Fallback to basic JSONMatcher if available
            try:
                from .json_matcher import JSONMatcher
                basic_matcher = JSONMatcher(self.excel_processor)
                return basic_matcher.fetch_and_match(url)
            except Exception as fallback_error:
                logging.error(f"Fallback to basic matcher also failed: {fallback_error}")
                return []

# Backward compatibility functions
def map_inventory_type_to_product_type(inventory_type, inventory_category=None, product_name=None):
    """Maintain compatibility with existing code"""
    # Import and use the existing function
    from . import json_matcher
    return json_matcher.map_inventory_type_to_product_type(inventory_type, inventory_category, product_name)

def extract_products_from_manifest(manifest_data):
    """Maintain compatibility with existing code"""
    from . import json_matcher
    return json_matcher.extract_products_from_manifest(manifest_data)

def map_json_to_db_fields(json_product, available_tags=None):
    """Maintain compatibility with existing code"""
    from . import json_matcher
    return json_matcher.map_json_to_db_fields(json_product, available_tags)