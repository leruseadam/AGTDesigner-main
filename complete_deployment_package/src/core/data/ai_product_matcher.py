#!/usr/bin/env python3
"""
AI-Powered Product Matching System

This module provides sophisticated product matching using:
- Fuzzy string matching with multiple algorithms
- Similarity scoring based on multiple factors
- Intelligent pattern recognition
- Weight, vendor, price, brand, and lineage matching
- Machine learning-inspired scoring system
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from difflib import SequenceMatcher
from dataclasses import dataclass
from collections import defaultdict
import math

# Make jellyfish optional - fallback to basic string matching if not available
JELLYFISH_AVAILABLE = False
jellyfish = None

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False
    logging.warning("jellyfish module not available - using basic string matching fallback")

# Fallback functions when jellyfish is not available
def _jaro_winkler_similarity_fallback(s1: str, s2: str) -> float:
    """Fallback Jaro-Winkler similarity using basic string operations"""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    # Basic similarity based on common characters
    common_chars = set(s1.lower()) & set(s2.lower())
    if not common_chars:
        return 0.0
    
    # Simple similarity calculation
    max_len = max(len(s1), len(s2))
    similarity = len(common_chars) / max_len
    
    # Boost for prefix similarity (Jaro-Winkler characteristic)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i].lower() == s2[i].lower():
            prefix_len += 1
        else:
            break
    
    if prefix_len > 0:
        similarity += prefix_len * 0.1
    
    return min(similarity, 1.0)

def _levenshtein_distance_fallback(s1: str, s2: str) -> int:
    """Fallback Levenshtein distance using basic algorithm"""
    if len(s1) < len(s2):
        return _levenshtein_distance_fallback(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

@dataclass
class MatchScore:
    """Represents a match score with detailed breakdown"""
    product_name: str
    strain_name: str
    total_score: float
    name_similarity: float
    weight_match: float
    vendor_match: float
    price_match: float
    brand_match: float
    lineage_match: float
    confidence: str  # "high", "medium", "low"
    match_type: str  # "exact", "fuzzy", "strain_only"
    details: Dict[str, Any]

class AIProductMatcher:
    """
    AI-powered product matching system that considers multiple factors
    for accurate product-to-strain matching.
    """
    
    def __init__(self, product_database):
        self.product_db = product_database
        self.strain_cache = {}
        self.product_cache = {}
        self._build_caches()
        
        # Scoring weights for different factors
        self.weights = {
            'name_similarity': 0.35,      # Product name similarity
            'weight_match': 0.20,         # Weight matching
            'vendor_match': 0.15,         # Vendor matching
            'price_match': 0.10,          # Price matching
            'brand_match': 0.10,          # Brand matching
            'lineage_match': 0.10,        # Lineage matching
        }
        
        # Thresholds for confidence levels - Much more lenient for better matching
        self.confidence_thresholds = {
            'high': 0.65,    # Lowered from 0.75
            'medium': 0.45,  # Lowered from 0.55
            'low': 0.25      # Lowered from 0.35
        }
    
    def _build_caches(self):
        """Build caches for faster lookups"""
        try:
            # Cache all strains
            strains = self.product_db.get_all_strains()
            for strain in strains:
                strain_info = self.product_db.get_strain_info(strain)
                if strain_info:
                    self.strain_cache[strain.lower()] = strain_info
            
            # Cache all products
            # Note: This would need to be implemented in ProductDatabase
            logging.info(f"Built caches with {len(self.strain_cache)} strains")
        except Exception as e:
            logging.warning(f"Error building caches: {e}")
    
    def extract_product_features(self, product_data: Dict) -> Dict[str, Any]:
        """
        Extract and normalize product features from JSON data
        """
        features = {}
        
        # Product name
        product_name = str(product_data.get("product_name", "")).strip()
        features['product_name'] = product_name
        features['product_name_clean'] = self._clean_product_name(product_name)
        
        # Extract strain from product name
        features['extracted_strain'] = self._extract_strain_from_name(product_name)
        
        # Weight and units
        weight_info = self._extract_weight_and_units(product_name, product_data)
        features.update(weight_info)
        
        # Vendor
        features['vendor'] = str(product_data.get("vendor", "")).strip()
        
        # Price/Cost
        price_info = self._extract_price_info(product_data)
        features.update(price_info)
        
        # Brand
        features['brand'] = str(product_data.get("brand", "")).strip()
        
        # Product type
        features['product_type'] = self._infer_product_type(product_name)
        
        return features
    
    def _clean_product_name(self, product_name: str) -> str:
        """Clean product name for better matching"""
        if not product_name:
            return ""
        
        # Remove common suffixes and prefixes
        cleaned = product_name.lower()
        
        # Remove weight patterns
        cleaned = re.sub(r'/\d+[gml]', '', cleaned)
        cleaned = re.sub(r'\d+[gml]\s*$', '', cleaned)
        
        # Remove common product type words
        product_types = ['flower', 'bud', 'pre-roll', 'preroll', 'cartridge', 'vape', 'edible', 'gummy']
        for ptype in product_types:
            cleaned = cleaned.replace(ptype, '').replace(ptype.replace('-', ''), '')
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_strain_from_name(self, product_name: str) -> Optional[str]:
        """Extract strain name using multiple patterns"""
        if not product_name:
            return None
        
        # Pattern 1: "Brand - Strain Name (weight)"
        match = re.search(r'^([^-]+)\s*-\s*([^(]+?)(?:\s*\([^)]+\))?$', product_name)
        if match:
            potential_strain = match.group(2).strip()
            if len(potential_strain) > 2:
                return potential_strain
        
        # Pattern 2: "Strain Name (weight)"
        match = re.search(r'\(([^/]+)/', product_name)
        if match:
            potential_strain = match.group(1).strip()
            if len(potential_strain) > 2:
                return potential_strain
        
        # Pattern 3: Look for strain keywords
        strain_keywords = [
            'blue dream', 'green crack', 'maui wowie', 'granddaddy purple', 'bubba kush',
            'master kush', 'hindu kush', 'afghan kush', 'sour diesel', 'nyc diesel',
            'girl scout cookies', 'og kush', 'white widow', 'northern lights', 'skunk',
            'jack herer', 'durban poison', 'lemon haze', 'super silver haze', 'amnesia haze'
        ]
        
        product_lower = product_name.lower()
        for strain in strain_keywords:
            if strain in product_lower:
                return strain.title()
        
        return None
    
    def _extract_weight_and_units(self, product_name: str, product_data: Dict) -> Dict[str, Any]:
        """Extract weight and units information"""
        weight_info = {'weight': None, 'units': None, 'weight_numeric': None}
        
        # Try to extract from product name first
        weight_match = re.search(r'/(\d+(?:\.\d+)?)([gml])', product_name)
        if weight_match:
            weight_info['weight'] = weight_match.group(1)
            weight_info['units'] = weight_match.group(2)
            weight_info['weight_numeric'] = float(weight_match.group(1))
            return weight_info
        
        # Try to extract from product data
        weight = product_data.get('weight') or product_data.get('Weight') or product_data.get('weight_grams')
        if weight:
            weight_info['weight'] = str(weight)
            weight_info['units'] = 'g'  # Default to grams
            try:
                weight_info['weight_numeric'] = float(weight)
            except (ValueError, TypeError):
                pass
        
        return weight_info
    
    def _extract_price_info(self, product_data: Dict) -> Dict[str, Any]:
        """Extract price and cost information"""
        price_info = {'price': None, 'cost': None, 'price_numeric': None, 'cost_numeric': None}
        
        # Extract price
        price = product_data.get('price') or product_data.get('Price') or product_data.get('retail_price')
        if price:
            price_info['price'] = str(price)
            try:
                price_info['price_numeric'] = float(str(price).replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                pass
        
        # Extract cost
        cost = product_data.get('cost') or product_data.get('Cost') or product_data.get('wholesale_price')
        if cost:
            price_info['cost'] = str(cost)
            try:
                price_info['cost_numeric'] = float(str(cost).replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                pass
        
        return price_info
    
    def _infer_product_type(self, product_name: str) -> str:
        """Infer product type from product name"""
        name_lower = product_name.lower()
        
        if any(word in name_lower for word in ['flower', 'bud', 'nug']):
            return 'Flower'
        elif any(word in name_lower for word in ['pre-roll', 'preroll', 'joint']):
            return 'Pre-Roll'
        elif any(word in name_lower for word in ['cartridge', 'vape', 'pen']):
            return 'Vape Cartridge'
        elif any(word in name_lower for word in ['edible', 'gummy', 'chocolate', 'cookie']):
            return 'Edible'
        elif any(word in name_lower for word in ['concentrate', 'wax', 'shatter', 'rosin']):
            return 'Concentrate'
        else:
            return 'Unknown'
    
    def find_best_matches(self, product_features: Dict, max_matches: int = 5) -> List[MatchScore]:
        """
        Find the best matches for a product using AI-powered scoring
        """
        matches = []
        
        # Get all potential strains to match against
        potential_strains = self._get_potential_strains(product_features)
        
        for strain_name, strain_info in potential_strains:
            match_score = self._calculate_match_score(product_features, strain_name, strain_info)
            if match_score.total_score > self.confidence_thresholds['low']:
                matches.append(match_score)
        
        # Sort by total score (descending) and return top matches
        matches.sort(key=lambda x: x.total_score, reverse=True)
        return matches[:max_matches]
    
    def _get_potential_strains(self, product_features: Dict) -> List[Tuple[str, Dict]]:
        """Get potential strains to match against"""
        potential_strains = []
        
        # If we extracted a strain name, prioritize exact matches
        extracted_strain = product_features.get('extracted_strain')
        if extracted_strain:
            # Look for exact strain name matches
            for strain_name, strain_info in self.strain_cache.items():
                if strain_name.lower() == extracted_strain.lower():
                    potential_strains.append((strain_name, strain_info))
            
            # Look for partial matches
            for strain_name, strain_info in self.strain_cache.items():
                if extracted_strain.lower() in strain_name.lower() or strain_name.lower() in extracted_strain.lower():
                    potential_strains.append((strain_name, strain_info))
        
        # Add all strains for comprehensive matching
        for strain_name, strain_info in self.strain_cache.items():
            if (strain_name, strain_info) not in potential_strains:
                potential_strains.append((strain_name, strain_info))
        
        return potential_strains
    
    def _calculate_match_score(self, product_features: Dict, strain_name: str, strain_info: Dict) -> MatchScore:
        """Calculate comprehensive match score for a product-strain pair"""
        
        # 1. Name similarity score
        name_similarity = self._calculate_name_similarity(
            product_features['product_name_clean'], 
            strain_name
        )
        
        # 2. Weight match score
        weight_match = self._calculate_weight_match(
            product_features.get('weight_numeric'),
            strain_info
        )
        
        # 3. Vendor match score
        vendor_match = self._calculate_vendor_match(
            product_features.get('vendor'),
            strain_info
        )
        
        # 4. Price match score
        price_match = self._calculate_price_match(
            product_features.get('price_numeric'),
            product_features.get('cost_numeric'),
            strain_info
        )
        
        # 5. Brand match score
        brand_match = self._calculate_brand_match(
            product_features.get('brand'),
            strain_info
        )
        
        # 6. Lineage match score
        lineage_match = self._calculate_lineage_match(
            product_features.get('product_type'),
            strain_info
        )
        
        # Calculate weighted total score
        total_score = (
            name_similarity * self.weights['name_similarity'] +
            weight_match * self.weights['weight_match'] +
            vendor_match * self.weights['vendor_match'] +
            price_match * self.weights['price_match'] +
            brand_match * self.weights['brand_match'] +
            lineage_match * self.weights['lineage_match']
        )
        
        # Determine confidence level
        confidence = self._determine_confidence(total_score)
        
        # Determine match type
        individual_scores = {
            'weight_match': weight_match,
            'vendor_match': vendor_match,
            'brand_match': brand_match,
            'lineage_match': lineage_match
        }
        match_type = self._determine_match_type(name_similarity, total_score, individual_scores)
        
        # Create match score object
        match_score = MatchScore(
            product_name=product_features['product_name'],
            strain_name=strain_name,
            total_score=total_score,
            name_similarity=name_similarity,
            weight_match=weight_match,
            vendor_match=vendor_match,
            price_match=price_match,
            brand_match=brand_match,
            lineage_match=lineage_match,
            confidence=confidence,
            match_type=match_type,
            details={
                'extracted_strain': product_features.get('extracted_strain'),
                'product_type': product_features.get('product_type'),
                'weight': product_features.get('weight'),
                'units': product_features.get('units'),
                'vendor': product_features.get('vendor'),
                'price': product_features.get('price'),
                'cost': product_features.get('cost'),
                'brand': product_features.get('brand'),
                'strain_lineage': strain_info.get('canonical_lineage', 'Unknown')
            }
        )
        
        return match_score
    
    def _calculate_name_similarity(self, product_name: str, strain_name: str) -> float:
        """Calculate name similarity using multiple algorithms"""
        if not product_name or not strain_name:
            return 0.0
        
        # Multiple similarity algorithms
        similarities = []
        
        # 1. Sequence matcher (difflib)
        seq_similarity = SequenceMatcher(None, product_name.lower(), strain_name.lower()).ratio()
        similarities.append(seq_similarity)
        
        # 2. Jaro-Winkler distance
        try:
            if JELLYFISH_AVAILABLE:
                jaro_similarity = jellyfish.jaro_winkler_similarity(product_name.lower(), strain_name.lower())
            else:
                jaro_similarity = _jaro_winkler_similarity_fallback(product_name.lower(), strain_name.lower())
            similarities.append(jaro_similarity)
        except:
            pass
        
        # 3. Levenshtein distance (normalized)
        try:
            max_len = max(len(product_name), len(strain_name))
            if max_len > 0:
                if JELLYFISH_AVAILABLE:
                    levenshtein_similarity = 1 - (jellyfish.levenshtein_distance(product_name.lower(), strain_name.lower()) / max_len)
                else:
                    levenshtein_similarity = 1 - (_levenshtein_distance_fallback(product_name.lower(), strain_name.lower()) / max_len)
                similarities.append(levenshtein_similarity)
        except:
            pass
        
        # 4. Token-based similarity
        product_tokens = set(product_name.lower().split())
        strain_tokens = set(strain_name.lower().split())
        if product_tokens and strain_tokens:
            token_similarity = len(product_tokens.intersection(strain_tokens)) / len(product_tokens.union(strain_tokens))
            similarities.append(token_similarity)
        
        # Return average of all similarities
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_weight_match(self, product_weight: Optional[float], strain_info: Dict) -> float:
        """Calculate weight match score"""
        if product_weight is None:
            return 0.5  # Neutral score if no weight info
        
        # Check if weight matches any known weight patterns in the strain info
        strain_weight = strain_info.get('weight', '')
        if strain_weight:
            try:
                strain_weight_numeric = float(str(strain_weight).replace('g', '').replace('oz', ''))
                # Calculate weight similarity (closer weights get higher scores)
                weight_diff = abs(product_weight - strain_weight_numeric)
                if weight_diff == 0:
                    return 1.0  # Exact match
                elif weight_diff <= 0.1:
                    return 0.9  # Very close
                elif weight_diff <= 0.5:
                    return 0.8  # Close
                elif weight_diff <= 1.0:
                    return 0.7  # Reasonable
                else:
                    return 0.6  # Different but still relevant
            except (ValueError, TypeError):
                pass
        
        # Check for common weight patterns
        common_weights = [1.0, 3.5, 7.0, 14.0, 28.0]  # Common cannabis weights
        for common_weight in common_weights:
            if abs(product_weight - common_weight) <= 0.1:
                return 0.8
        
        return 0.6  # Neutral score for weight matching
    
    def _calculate_vendor_match(self, product_vendor: Optional[str], strain_info: Dict) -> float:
        """Calculate vendor match score"""
        if not product_vendor:
            return 0.5  # Neutral score if no vendor info
        
        # Check if vendor matches any known vendor patterns in the strain info
        vendor_lower = product_vendor.lower().strip()
        
        # Look for vendor information in strain details
        strain_vendor = strain_info.get('vendor', '').lower()
        if strain_vendor and vendor_lower in strain_vendor:
            return 0.9
        
        # Check for common vendor patterns
        common_vendors = ['phat panda', 'dank czar', 'moonshot', 'blueberry', 'galactic']
        for common_vendor in common_vendors:
            if common_vendor in vendor_lower:
                return 0.8
        
        # Check for vendor-strain relationships in the database
        strain_name = strain_info.get('strain_name', '').lower()
        if strain_name and vendor_lower:
            # This could be enhanced with historical vendor-strain relationships
            return 0.6
        
        return 0.5  # Neutral score if no clear match
    
    def _calculate_price_match(self, product_price: Optional[float], product_cost: Optional[float], strain_info: Dict) -> float:
        """Calculate price match score"""
        if product_price is None and product_cost is None:
            return 0.5  # Neutral score if no price info
        
        # Check if price matches any known price patterns in the strain info
        strain_price = strain_info.get('price', '')
        if strain_price:
            try:
                strain_price_numeric = float(str(strain_price).replace('$', '').replace(',', ''))
                if product_price:
                    # Calculate price similarity (closer prices get higher scores)
                    price_diff = abs(product_price - strain_price_numeric)
                    price_ratio = min(product_price, strain_price_numeric) / max(product_price, strain_price_numeric)
                    
                    if price_diff <= 1.0:
                        return 0.9  # Very close
                    elif price_diff <= 5.0:
                        return 0.8  # Close
                    elif price_ratio >= 0.8:
                        return 0.7  # Reasonable
                    else:
                        return 0.6  # Different but still relevant
            except (ValueError, TypeError):
                pass
        
        # Check for common price ranges
        if product_price:
            if 20 <= product_price <= 30:
                return 0.7  # Common flower price range
            elif 40 <= product_price <= 60:
                return 0.7  # Common concentrate price range
            elif 15 <= product_price <= 25:
                return 0.7  # Common pre-roll price range
        
        return 0.6  # Neutral score for price matching
    
    def _calculate_brand_match(self, product_brand: Optional[str], strain_info: Dict) -> float:
        """Calculate brand match score"""
        if not product_brand:
            return 0.5  # Neutral score if no brand info
        
        brand_lower = product_brand.lower().strip()
        
        # Check if brand matches strain info
        strain_brand = strain_info.get('brand', '').lower()
        if strain_brand and brand_lower in strain_brand:
            return 0.9
        
        # Check for common brand patterns
        common_brands = ['phat panda', 'dank czar', 'moonshot', 'blueberry', 'galactic']
        for common_brand in common_brands:
            if common_brand in brand_lower:
                return 0.8
        
        # Check for brand-strain relationships
        strain_name = strain_info.get('strain_name', '').lower()
        if strain_name and brand_lower:
            # This could be enhanced with historical brand-strain relationships
            return 0.6
        
        return 0.5  # Neutral score if no clear match
    
    def _calculate_lineage_match(self, product_type: Optional[str], strain_info: Dict) -> float:
        """Calculate lineage match score"""
        if not product_type or product_type == 'Unknown':
            return 0.5  # Neutral score if no product type
        
        strain_lineage = strain_info.get('canonical_lineage', 'Unknown')
        
        # Product type to lineage compatibility scoring
        type_lineage_compatibility = {
            'Flower': {'SATIVA': 0.9, 'INDICA': 0.9, 'HYBRID': 0.9, 'HYBRID/SATIVA': 0.8, 'HYBRID/INDICA': 0.8},
            'Pre-Roll': {'SATIVA': 0.9, 'INDICA': 0.9, 'HYBRID': 0.9, 'HYBRID/SATIVA': 0.8, 'HYBRID/INDICA': 0.8},
            'Vape Cartridge': {'SATIVA': 0.8, 'INDICA': 0.8, 'HYBRID': 0.9, 'HYBRID/SATIVA': 0.8, 'HYBRID/INDICA': 0.8},
            'Edible': {'SATIVA': 0.7, 'INDICA': 0.7, 'HYBRID': 0.8, 'HYBRID/SATIVA': 0.7, 'HYBRID/INDICA': 0.7},
            'Concentrate': {'SATIVA': 0.8, 'INDICA': 0.8, 'HYBRID': 0.9, 'HYBRID/SATIVA': 0.8, 'HYBRID/INDICA': 0.8}
        }
        
        compatibility = type_lineage_compatibility.get(product_type, {})
        return compatibility.get(strain_lineage, 0.5)
    
    def _determine_confidence(self, total_score: float) -> str:
        """Determine confidence level based on total score"""
        if total_score >= self.confidence_thresholds['high']:
            return 'high'
        elif total_score >= self.confidence_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _determine_match_type(self, name_similarity: float, total_score: float, individual_scores: Dict[str, float]) -> str:
        """Determine the type of match based on comprehensive scoring"""
        # Check for exact name match
        if name_similarity >= 0.95:
            return 'exact'
        
        # Check for high confidence across multiple fields
        if total_score >= self.confidence_thresholds['high']:
            return 'fuzzy'
        
        # Check if we have good matches in specific fields
        good_field_matches = 0
        if individual_scores.get('weight_match', 0) >= 0.7:
            good_field_matches += 1
        if individual_scores.get('vendor_match', 0) >= 0.7:
            good_field_matches += 1
        if individual_scores.get('brand_match', 0) >= 0.7:
            good_field_matches += 1
        if individual_scores.get('lineage_match', 0) >= 0.7:
            good_field_matches += 1
        
        # If we have good matches in multiple fields, it's a comprehensive match
        if good_field_matches >= 2:
            return 'comprehensive'
        elif good_field_matches >= 1:
            return 'partial'
        else:
            return 'strain_only'
    
    def get_match_summary(self, matches: List[MatchScore]) -> Dict[str, Any]:
        """Get a summary of the matches"""
        if not matches:
            return {'status': 'no_matches', 'message': 'No matches found'}
        
        best_match = matches[0]
        
        summary = {
            'status': 'success',
            'best_match': {
                'strain_name': best_match.strain_name,
                'confidence': best_match.confidence,
                'total_score': round(best_match.total_score, 3),
                'match_type': best_match.match_type
            },
            'score_breakdown': {
                'name_similarity': round(best_match.name_similarity, 3),
                'weight_match': round(best_match.weight_match, 3),
                'vendor_match': round(best_match.vendor_match, 3),
                'price_match': round(best_match.price_match, 3),
                'brand_match': round(best_match.brand_match, 3),
                'lineage_match': round(best_match.lineage_match, 3)
            },
            'total_matches': len(matches),
            'all_matches': [
                {
                    'strain_name': m.strain_name,
                    'total_score': round(m.total_score, 3),
                    'confidence': m.confidence,
                    'match_type': m.match_type
                }
                for m in matches[:3]  # Top 3 matches
            ]
        }
        
        return summary
