"""
Advanced matching system using multiple algorithms and libraries for improved JSON matching.
Combines fuzzy string matching, semantic similarity, and performance optimizations.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from functools import lru_cache
import time

# Import all available matching libraries
try:
    from rapidfuzz import fuzz as rapidfuzz_fuzz, process as rapidfuzz_process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("RapidFuzz not available, falling back to FuzzyWuzzy")

try:
    from fuzzywuzzy import fuzz as fuzzywuzzy_fuzz, process as fuzzywuzzy_process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logging.warning("FuzzyWuzzy not available")

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False
    logging.warning("Jellyfish not available")

try:
    import difflib
    DIFFLIB_AVAILABLE = True
except ImportError:
    DIFFLIB_AVAILABLE = False
    logging.warning("difflib not available")

@dataclass
class MatchResult:
    """Represents a matching result with detailed scoring information."""
    item: Dict
    overall_score: float
    exact_match: bool = False
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0
    phonetic_score: float = 0.0
    vendor_match: bool = False
    brand_match: bool = False
    type_match: bool = False
    weight_match: bool = False
    strain_match: bool = False
    match_reason: str = ""
    algorithm_used: str = ""

class AdvancedMatcher:
    """
    Advanced matching system that combines multiple algorithms for optimal results.
    """
    
    def __init__(self):
        self.performance_cache = {}
        self.normalization_cache = {}
        self.key_terms_cache = {}
        self.algorithm_weights = {
            'exact': 1.0,
            'fuzzy': 0.8,
            'semantic': 0.7,
            'phonetic': 0.6,
            'vendor': 0.5,
            'brand': 0.4,
            'type': 0.3,
            'weight': 0.2,
            'strain': 0.1
        }
        
        # Performance settings
        self.max_cache_size = 10000
        self.cache_cleanup_threshold = 0.8
        
        # Common words to ignore in matching
        self.common_words = {
            'the', 'and', 'or', 'for', 'with', 'by', 'from', 'to', 'of', 'in', 'on', 'at',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must',
            'shall', 'a', 'an', 'as', 'if', 'when', 'where', 'why', 'how', 'what', 'who'
        }
        
        # Product type mappings for better matching
        self.product_type_mappings = {
            'flower': ['flower', 'bud', 'nug', 'buds', 'nugs', 'cannabis', 'marijuana'],
            'edible': ['edible', 'gummy', 'gummies', 'chocolate', 'candy', 'cookie', 'brownie'],
            'concentrate': ['concentrate', 'wax', 'shatter', 'rosin', 'live resin', 'distillate'],
            'topical': ['topical', 'cream', 'balm', 'lotion', 'salve', 'ointment'],
            'tincture': ['tincture', 'drops', 'liquid', 'oil'],
            'cartridge': ['cartridge', 'cart', 'vape', 'pen']
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching."""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase and strip
        text = text.lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _is_vendor_match(self, vendor1: str, vendor2: str) -> bool:
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
        
        # Check for partial matches with high confidence
        if len(v1_clean) >= 3 and len(v2_clean) >= 3:
            # Check if one is a subset of the other
            if v1_clean in v2_clean or v2_clean in v1_clean:
                return True
            
            # Check for word overlap (at least 50% of words match)
            v1_words = set(v1_clean.split())
            v2_words = set(v2_clean.split())
            if len(v1_words) > 0 and len(v2_words) > 0:
                overlap = len(v1_words.intersection(v2_words))
                min_words = min(len(v1_words), len(v2_words))
                if overlap / min_words >= 0.5:
                    return True
            
            # Check for phonetic similarity (Soundex)
            try:
                import jellyfish
                if jellyfish.soundex(v1_clean) == jellyfish.soundex(v2_clean):
                    return True
            except:
                pass
        
        return False
    
    def calculate_ai_powered_scores(self, json_name: str, candidate_name: str, json_item: Dict, candidate: Dict) -> Dict:
        """Calculate AI-powered scores for difficult product name matching."""
        scores = {}
        
        try:
            # 1. N-gram similarity (character-level)
            scores['ngram'] = self._calculate_ngram_similarity(json_name, candidate_name)
            
            # 2. Levenshtein distance ratio
            scores['levenshtein'] = self._calculate_levenshtein_ratio(json_name, candidate_name)
            
            # 3. Jaccard similarity on words
            scores['jaccard'] = self._calculate_jaccard_similarity(json_name, candidate_name)
            
            # 4. Subsequence matching
            scores['subsequence'] = self._calculate_subsequence_score(json_name, candidate_name)
            
            # 5. Soundex similarity
            scores['soundex'] = self._calculate_soundex_similarity(json_name, candidate_name)
            
            # 6. Metaphone similarity
            scores['metaphone'] = self._calculate_metaphone_similarity(json_name, candidate_name)
            
            # 7. Partial string matching
            scores['partial'] = self._calculate_partial_match_score(json_name, candidate_name)
            
            # 8. Keyword extraction and matching
            scores['keywords'] = self._calculate_keyword_similarity(json_name, candidate_name)
            
            # 9. Weight/size pattern matching
            scores['weight_pattern'] = self._calculate_weight_pattern_score(json_name, candidate_name)
            
            # 10. Product type pattern matching
            scores['type_pattern'] = self._calculate_type_pattern_score(json_name, candidate_name, json_item, candidate)
            
        except Exception as e:
            logging.debug(f"Error in AI-powered scoring: {e}")
            # Return default scores if there's an error
            scores = {key: 0.0 for key in ['ngram', 'levenshtein', 'jaccard', 'subsequence', 'soundex', 'metaphone', 'partial', 'keywords', 'weight_pattern', 'type_pattern']}
        
        return scores
    
    def calculate_overall_score_with_ai(self, match_result: MatchResult, ai_scores: Dict) -> float:
        """Calculate overall score including AI-powered scores."""
        # Base score from original calculation
        base_score = self.calculate_overall_score(match_result)
        
        # AI score boost (weighted average of AI scores) - more generous
        ai_boost = 0.0
        if ai_scores:
            # Weight different AI algorithms - increased weights for better matching
            weights = {
                'ngram': 0.20,  # Increased from 0.15
                'levenshtein': 0.20,  # Increased from 0.15
                'jaccard': 0.15,  # Increased from 0.10
                'subsequence': 0.15,  # Increased from 0.10
                'soundex': 0.10,  # Keep same
                'metaphone': 0.10,  # Keep same
                'partial': 0.15,  # Increased from 0.10
                'keywords': 0.15,  # Increased from 0.10
                'weight_pattern': 0.10,  # Increased from 0.05
                'type_pattern': 0.10  # Increased from 0.05
            }
            
            weighted_ai_score = sum(ai_scores.get(key, 0) * weight for key, weight in weights.items())
            ai_boost = weighted_ai_score * 0.5  # Increased from 30% to 50% weight for AI scores
        
        # Combine base score with AI boost
        final_score = base_score + ai_boost
        
        # Ensure minimum score for vendor matches - more generous
        if match_result.vendor_match and final_score < 25:  # Increased from 20
            final_score = max(25, final_score)
        
        # Ensure minimum score for any meaningful match
        if (match_result.vendor_match or match_result.brand_match or match_result.type_match) and final_score < 20:
            final_score = max(20, final_score)
        
        return min(100.0, final_score)  # Cap at 100
    
    def _calculate_ngram_similarity(self, str1: str, str2: str, n: int = 3) -> float:
        """Calculate n-gram similarity between two strings."""
        try:
            from rapidfuzz import fuzz
            return fuzz.ratio(str1, str2)
        except:
            return 0.0
    
    def _calculate_levenshtein_ratio(self, str1: str, str2: str) -> float:
        """Calculate Levenshtein distance ratio."""
        try:
            from rapidfuzz import fuzz
            return fuzz.ratio(str1, str2)
        except:
            return 0.0
    
    def _calculate_jaccard_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaccard similarity based on word sets."""
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 and not words2:
            return 100.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return (intersection / union) * 100.0
    
    def _calculate_subsequence_score(self, str1: str, str2: str) -> float:
        """Calculate subsequence matching score."""
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        # Check if str1 is a subsequence of str2 or vice versa
        if self._is_subsequence(str1_lower, str2_lower) or self._is_subsequence(str2_lower, str1_lower):
            return 80.0
        
        return 0.0
    
    def _is_subsequence(self, s1: str, s2: str) -> bool:
        """Check if s1 is a subsequence of s2."""
        i = j = 0
        while i < len(s1) and j < len(s2):
            if s1[i] == s2[j]:
                i += 1
            j += 1
        return i == len(s1)
    
    def _calculate_soundex_similarity(self, str1: str, str2: str) -> float:
        """Calculate Soundex similarity."""
        try:
            import jellyfish
            soundex1 = jellyfish.soundex(str1)
            soundex2 = jellyfish.soundex(str2)
            return 100.0 if soundex1 == soundex2 else 0.0
        except:
            return 0.0
    
    def _calculate_metaphone_similarity(self, str1: str, str2: str) -> float:
        """Calculate Metaphone similarity."""
        try:
            import jellyfish
            meta1 = jellyfish.metaphone(str1)
            meta2 = jellyfish.metaphone(str2)
            return 100.0 if meta1 == meta2 else 0.0
        except:
            return 0.0
    
    def _calculate_partial_match_score(self, str1: str, str2: str) -> float:
        """Calculate partial string matching score."""
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        # Check for partial matches
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 70.0
        
        # Check for word-level partial matches
        words1 = str1_lower.split()
        words2 = str2_lower.split()
        
        matches = 0
        for word1 in words1:
            for word2 in words2:
                if len(word1) >= 3 and len(word2) >= 3:
                    if word1 in word2 or word2 in word1:
                        matches += 1
                        break
        
        if words1 and words2:
            return (matches / min(len(words1), len(words2))) * 100.0
        
        return 0.0
    
    def _calculate_keyword_similarity(self, str1: str, str2: str) -> float:
        """Calculate keyword-based similarity."""
        # Extract key terms (remove common words)
        common_words = {'the', 'and', 'or', 'for', 'with', 'by', 'from', 'to', 'of', 'in', 'on', 'at', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'a', 'an', 'as', 'if', 'it', 'this', 'that', 'these', 'those'}
        
        words1 = [w for w in str1.lower().split() if w not in common_words and len(w) >= 3]
        words2 = [w for w in str2.lower().split() if w not in common_words and len(w) >= 3]
        
        if not words1 and not words2:
            return 100.0
        if not words1 or not words2:
            return 0.0
        
        matches = len(set(words1).intersection(set(words2)))
        return (matches / max(len(words1), len(words2))) * 100.0
    
    def _calculate_weight_pattern_score(self, str1: str, str2: str) -> float:
        """Calculate weight/size pattern matching score."""
        import re
        
        # Extract weight patterns (e.g., "3.5g", "28g", "1oz", "2oz")
        weight_pattern = r'(\d+(?:\.\d+)?)\s*(g|oz|gram|ounce|lb|pound)'
        
        weights1 = re.findall(weight_pattern, str1.lower())
        weights2 = re.findall(weight_pattern, str2.lower())
        
        if not weights1 and not weights2:
            return 50.0  # Neutral score if no weights found
        if not weights1 or not weights2:
            return 0.0
        
        # Check if any weights match
        for w1 in weights1:
            for w2 in weights2:
                if w1 == w2:
                    return 100.0
        
        return 0.0
    
    def _calculate_type_pattern_score(self, str1: str, str2: str, json_item: Dict, candidate: Dict) -> float:
        """Calculate product type pattern matching score."""
        # Extract product types from both items
        json_type = str(json_item.get('product_type', '')).lower()
        candidate_type = str(candidate.get('Product Type*', '')).lower()
        
        if not json_type and not candidate_type:
            return 50.0
        if not json_type or not candidate_type:
            return 0.0
        
        # Check for type matches
        if json_type in candidate_type or candidate_type in json_type:
            return 100.0
        
        # Check for common type patterns
        type_patterns = {
            'flower': ['flower', 'bud', 'buds', 'nugs', 'nuggets'],
            'edible': ['edible', 'gummy', 'gummies', 'chocolate', 'candy', 'cookie', 'brownie'],
            'concentrate': ['concentrate', 'wax', 'shatter', 'rosin', 'live resin', 'bho'],
            'vape': ['vape', 'cartridge', 'cart', 'disposable', 'pen'],
            'pre-roll': ['pre-roll', 'preroll', 'joint', 'blunt', 'cigarillo']
        }
        
        for category, patterns in type_patterns.items():
            json_has_pattern = any(pattern in json_type for pattern in patterns)
            candidate_has_pattern = any(pattern in candidate_type for pattern in patterns)
            
            if json_has_pattern and candidate_has_pattern:
                return 100.0
        
        return 0.0
    
    def _cleanup_cache(self):
        """Clean up caches when they get too large."""
        if len(self.performance_cache) > self.max_cache_size * self.cache_cleanup_threshold:
            # Remove oldest 20% of entries
            items_to_remove = int(len(self.performance_cache) * 0.2)
            keys_to_remove = list(self.performance_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.performance_cache[key]
        
        if len(self.normalization_cache) > self.max_cache_size * self.cache_cleanup_threshold:
            items_to_remove = int(len(self.normalization_cache) * 0.2)
            keys_to_remove = list(self.normalization_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.normalization_cache[key]
        
        if len(self.key_terms_cache) > self.max_cache_size * self.cache_cleanup_threshold:
            items_to_remove = int(len(self.key_terms_cache) * 0.2)
            keys_to_remove = list(self.key_terms_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.key_terms_cache[key]
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching with caching."""
        if not isinstance(text, str):
            return ""
        
        # Check cache first
        if text in self.normalization_cache:
            return self.normalization_cache[text]
        
        # Convert to lowercase and strip
        normalized = text.lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', ' ', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        result = normalized.strip()
        
        # Cache the result
        self.normalization_cache[text] = result
        
        # Cleanup cache if needed
        self._cleanup_cache()
        
        return result
    
    def extract_key_terms(self, text: str) -> Set[str]:
        """Extract meaningful key terms from text with caching."""
        if not text:
            return set()
        
        # Check cache first
        if text in self.key_terms_cache:
            return self.key_terms_cache[text]
        
        normalized = self.normalize_text(text)
        words = set(normalized.split())
        
        # Filter out common words and short words
        key_terms = {
            word for word in words 
            if len(word) > 2 and word not in self.common_words
        }
        
        # Cache the result
        self.key_terms_cache[text] = key_terms
        
        # Cleanup cache if needed
        self._cleanup_cache()
        
        return key_terms
    
    def calculate_fuzzy_score(self, text1: str, text2: str) -> Tuple[float, str]:
        """Calculate fuzzy matching score using the best available algorithm with caching."""
        if not text1 or not text2:
            return 0.0, "no_text"
        
        # Create cache key
        cache_key = f"{text1}|{text2}"
        if cache_key in self.performance_cache:
            return self.performance_cache[cache_key]
        
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        if text1_norm == text2_norm:
            result = (100.0, "exact")
            self.performance_cache[cache_key] = result
            return result
        
        scores = []
        algorithms = []
        
        # Try RapidFuzz first (fastest and most accurate)
        if RAPIDFUZZ_AVAILABLE:
            try:
                ratio = rapidfuzz_fuzz.ratio(text1_norm, text2_norm)
                partial_ratio = rapidfuzz_fuzz.partial_ratio(text1_norm, text2_norm)
                token_sort_ratio = rapidfuzz_fuzz.token_sort_ratio(text1_norm, text2_norm)
                token_set_ratio = rapidfuzz_fuzz.token_set_ratio(text1_norm, text2_norm)
                
                # Use the best score from RapidFuzz
                best_score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
                scores.append(best_score)
                algorithms.append("rapidfuzz")
            except Exception as e:
                logging.warning(f"RapidFuzz error: {e}")
        
        # Fallback to FuzzyWuzzy
        if FUZZYWUZZY_AVAILABLE:
            try:
                ratio = fuzzywuzzy_fuzz.ratio(text1_norm, text2_norm)
                partial_ratio = fuzzywuzzy_fuzz.partial_ratio(text1_norm, text2_norm)
                token_sort_ratio = fuzzywuzzy_fuzz.token_sort_ratio(text1_norm, text2_norm)
                token_set_ratio = fuzzywuzzy_fuzz.token_set_ratio(text1_norm, text2_norm)
                
                best_score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
                scores.append(best_score)
                algorithms.append("fuzzywuzzy")
            except Exception as e:
                logging.warning(f"FuzzyWuzzy error: {e}")
        
        # Fallback to difflib
        if DIFFLIB_AVAILABLE and not scores:
            try:
                matcher = difflib.SequenceMatcher(None, text1_norm, text2_norm)
                score = matcher.ratio() * 100
                scores.append(score)
                algorithms.append("difflib")
            except Exception as e:
                logging.warning(f"difflib error: {e}")
        
        if scores:
            best_score = max(scores)
            best_algorithm = algorithms[scores.index(best_score)]
            result = (best_score, best_algorithm)
            self.performance_cache[cache_key] = result
            return result
        
        result = (0.0, "none")
        self.performance_cache[cache_key] = result
        return result
    
    def calculate_phonetic_score(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity using Jellyfish algorithms."""
        if not JELLYFISH_AVAILABLE or not text1 or not text2:
            return 0.0
        
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        if text1_norm == text2_norm:
            return 100.0
        
        try:
            # Jaro-Winkler similarity (good for names)
            jaro_winkler = jellyfish.jaro_winkler_similarity(text1_norm, text2_norm)
            
            # Soundex comparison
            soundex1 = jellyfish.soundex(text1_norm)
            soundex2 = jellyfish.soundex(text2_norm)
            soundex_match = 100.0 if soundex1 == soundex2 else 0.0
            
            # Metaphone comparison
            metaphone1 = jellyfish.metaphone(text1_norm)
            metaphone2 = jellyfish.metaphone(text2_norm)
            metaphone_match = 100.0 if metaphone1 == metaphone2 else 0.0
            
            # Average the phonetic scores
            phonetic_score = (jaro_winkler * 100 + soundex_match + metaphone_match) / 3
            return phonetic_score
            
        except Exception as e:
            logging.warning(f"Phonetic matching error: {e}")
            return 0.0
    
    def calculate_semantic_score(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity based on key terms and context."""
        if not text1 or not text2:
            return 0.0
        
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        if text1_norm == text2_norm:
            return 100.0
        
        # Extract key terms
        terms1 = self.extract_key_terms(text1)
        terms2 = self.extract_key_terms(text2)
        
        if not terms1 or not terms2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(terms1.intersection(terms2))
        union = len(terms1.union(terms2))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Weight by term importance (longer terms are more important)
        weighted_score = 0.0
        total_weight = 0.0
        
        for term in terms1.intersection(terms2):
            weight = len(term)  # Longer terms get more weight
            weighted_score += weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_similarity = weighted_score / total_weight
            # Combine Jaccard and weighted similarity
            semantic_score = (jaccard_similarity * 0.7 + weighted_similarity * 0.3) * 100
        else:
            semantic_score = jaccard_similarity * 100
        
        return semantic_score
    
    def calculate_contextual_scores(self, json_item: Dict, cache_item: Dict) -> Dict[str, float]:
        """Calculate contextual matching scores for various attributes."""
        scores = {}
        
        # Vendor matching
        json_vendor = self.normalize_text(str(json_item.get("vendor", "")))
        cache_vendor = self.normalize_text(str(cache_item.get("vendor", "")))
        if json_vendor and cache_vendor:
            vendor_fuzzy, _ = self.calculate_fuzzy_score(json_vendor, cache_vendor)
            scores['vendor'] = vendor_fuzzy
        else:
            scores['vendor'] = 0.0
        
        # Brand matching
        json_brand = self.normalize_text(str(json_item.get("brand", "")))
        cache_brand = self.normalize_text(str(cache_item.get("brand", "")))
        if json_brand and cache_brand:
            brand_fuzzy, _ = self.calculate_fuzzy_score(json_brand, cache_brand)
            scores['brand'] = brand_fuzzy
        else:
            scores['brand'] = 0.0
        
        # Product type matching
        json_type = self.normalize_text(str(json_item.get("product_type", "")))
        cache_type = self.normalize_text(str(cache_item.get("product_type", "")))
        if json_type and cache_type:
            type_fuzzy, _ = self.calculate_fuzzy_score(json_type, cache_type)
            scores['type'] = type_fuzzy
        else:
            scores['type'] = 0.0
        
        # Weight matching
        json_weight = self.normalize_text(str(json_item.get("weight", "")))
        cache_weight = self.normalize_text(str(cache_item.get("weight", "")))
        if json_weight and cache_weight:
            weight_fuzzy, _ = self.calculate_fuzzy_score(json_weight, cache_weight)
            scores['weight'] = weight_fuzzy
        else:
            scores['weight'] = 0.0
        
        # Strain matching
        json_strain = self.normalize_text(str(json_item.get("strain_name", "")))
        cache_strain = self.normalize_text(str(cache_item.get("strain_name", "")))
        if json_strain and cache_strain:
            strain_fuzzy, _ = self.calculate_fuzzy_score(json_strain, cache_strain)
            scores['strain'] = strain_fuzzy
        else:
            scores['strain'] = 0.0
        
        return scores
    
    def calculate_overall_score(self, match_result: MatchResult) -> float:
        """Calculate overall matching score using weighted algorithm."""
        if match_result.exact_match:
            return 100.0
        
        # Start with fuzzy score as base - ensure minimum score
        base_score = max(10.0, match_result.fuzzy_score)  # Ensure minimum 10 points
        
        # Apply semantic and phonetic scores more heavily
        semantic_contribution = max(5.0, match_result.semantic_score * 0.4)  # Increased weight and minimum
        phonetic_contribution = max(3.0, match_result.phonetic_score * 0.3)  # Increased weight and minimum
        
        # Apply contextual bonuses (much more generous for better matching)
        contextual_bonus = 0.0
        if match_result.vendor_match:
            contextual_bonus += 60  # Even more generous for vendor matching
        if match_result.brand_match:
            contextual_bonus += 25  # Increased from 20
        if match_result.type_match:
            contextual_bonus += 20  # Increased from 15
        if match_result.weight_match:
            contextual_bonus += 15  # Increased from 10
        if match_result.strain_match:
            contextual_bonus += 12  # Increased from 8
        
        # Calculate final score with much more generous weighting
        final_score = min(100.0, base_score + semantic_contribution + phonetic_contribution + contextual_bonus)
        
        # Ensure minimum score for any match with contextual bonuses (much more generous)
        if contextual_bonus > 0 and final_score < 30:  # Increased from 20
            final_score = max(30, final_score)
        
        # Extra bonus for vendor matches to ensure they get through
        if match_result.vendor_match and final_score < 25:  # Increased from 15
            final_score = max(25, final_score)
        
        # Additional boost for any meaningful match
        if (match_result.vendor_match or match_result.brand_match or match_result.type_match) and final_score < 20:
            final_score = max(20, final_score)
        
        return final_score
    
    def find_best_matches(self, json_item: Dict, candidates: List[Dict], 
                         threshold: float = 1.0, max_results: int = 50) -> List[MatchResult]:
        """Find the best matches for a JSON item from a list of candidates."""
        if not json_item or not candidates:
            return []
        
        json_name = str(json_item.get("product_name", "")).strip()
        json_vendor = self.normalize_text(str(json_item.get("vendor", "")).strip())
        
        if not json_name:
            return []
        
        matches = []
        start_time = time.time()
        
        # Filter candidates by vendor first (if vendor is specified)
        filtered_candidates = candidates
        if json_vendor:
            filtered_candidates = []
            vendor_matches = 0
            total_candidates = len(candidates)
            
            print(f"🔍 ADVANCED VENDOR FILTERING: Looking for vendor '{json_vendor}' in {total_candidates} candidates")
            
            # Show some sample candidates for debugging
            if total_candidates > 0:
                sample_candidates = candidates[:5]
                print(f"🔍 SAMPLE CANDIDATES:")
                for i, candidate in enumerate(sample_candidates):
                    candidate_name = str(candidate.get("original_name", "")).strip()
                    candidate_vendor = str(candidate.get("vendor", "")).strip()
                    print(f"  {i+1}. '{candidate_name}' (vendor: '{candidate_vendor}')")
            
            for candidate in candidates:
                candidate_vendor = self.normalize_text(str(candidate.get("vendor", "")).strip())
                
                # Enhanced flexible vendor matching - check all variations
                vendor_match = False
                if candidate_vendor and json_vendor:
                    # Normalize both vendors for comparison
                    json_vendor_clean = self.normalize_text(json_vendor)
                    candidate_vendor_clean = self.normalize_text(candidate_vendor)
                    
                    # 1. Exact match after normalization
                    if json_vendor_clean == candidate_vendor_clean:
                        vendor_match = True
                    # 2. One contains the other (for cases like "CERES" vs "CERES - 435011")
                    elif json_vendor_clean in candidate_vendor_clean or candidate_vendor_clean in json_vendor_clean:
                        vendor_match = True
                    # 3. Word overlap (at least 50% of words match)
                    elif len(json_vendor_clean.split()) > 0 and len(candidate_vendor_clean.split()) > 0:
                        json_words = set(json_vendor_clean.split())
                        candidate_words = set(candidate_vendor_clean.split())
                        overlap = len(json_words.intersection(candidate_words))
                        min_words = min(len(json_words), len(candidate_words))
                        if overlap / min_words >= 0.5:
                            vendor_match = True
                    # 4. Fuzzy matching for similar names (more lenient for vendor names)
                    elif len(json_vendor_clean) >= 3 and len(candidate_vendor_clean) >= 3:  # Reduced from 4 to 3
                        try:
                            from rapidfuzz import fuzz
                            vendor_ratio = fuzz.ratio(json_vendor_clean, candidate_vendor_clean)
                            partial_ratio = fuzz.partial_ratio(json_vendor_clean, candidate_vendor_clean)
                            # Use the higher of the two ratios and lower threshold
                            best_ratio = max(vendor_ratio, partial_ratio)
                            if best_ratio >= 60:  # Reduced from 70 to 60 for more lenient matching
                                vendor_match = True
                        except:
                            pass
                    # 5. Check for common vendor name patterns
                    elif self._is_vendor_match_flexible(json_vendor_clean, candidate_vendor_clean):
                        vendor_match = True
                
                if vendor_match:
                    filtered_candidates.append(candidate)
                    vendor_matches += 1
                    if vendor_matches <= 3:  # Log first 3 matches
                        print(f"🔍 ADVANCED VENDOR MATCH {vendor_matches}: '{json_vendor}' matches '{candidate_vendor}'")
                elif candidate_vendor:  # Log first few non-matches
                    if vendor_matches < 3:
                        print(f"🔍 ADVANCED VENDOR SKIP: '{json_vendor}' != '{candidate_vendor}'")
            
            # If vendor matches are low (less than 10), also allow cross-vendor matching for better results
            if len(filtered_candidates) < 10:
                if filtered_candidates:
                    print(f"🔍 ADVANCED VENDOR: Only found {len(filtered_candidates)} vendor matches - allowing cross-vendor for better coverage")
                else:
                    print(f"🔍 ADVANCED VENDOR: No vendor matches found for '{json_vendor}' - allowing cross-vendor matching")
                    
                # Show what vendors are actually available
                available_vendors = set()
                for candidate in candidates[:50]:  # Check first 50 candidates
                    candidate_vendor = str(candidate.get("vendor", "")).strip()
                    if candidate_vendor:
                        available_vendors.add(candidate_vendor)
                
                print(f"🔍 AVAILABLE VENDORS: {sorted(list(available_vendors))[:20]}...")
                
                # Add more candidates from cross-vendor matching (limit to reasonable number)
                cross_vendor_candidates = [c for c in candidates if c not in filtered_candidates][:50-len(filtered_candidates)]
                filtered_candidates.extend(cross_vendor_candidates)
                print(f"🔍 ADVANCED VENDOR: Added {len(cross_vendor_candidates)} cross-vendor candidates for total of {len(filtered_candidates)}")
            
            # If still no vendor matches found, try full cross-vendor matching
            if not filtered_candidates:
                # Show what vendors are actually available
                available_vendors = set()
                for candidate in candidates[:50]:  # Check first 50 candidates
                    candidate_vendor = str(candidate.get("vendor", "")).strip()
                    if candidate_vendor:
                        available_vendors.add(candidate_vendor)
                
                print(f"🔍 ADVANCED VENDOR: No vendor matches found for '{json_vendor}'")
                print(f"🔍 AVAILABLE VENDORS: {sorted(list(available_vendors))[:20]}...")
                print(f"🔍 ADVANCED VENDOR: No vendor matches found - allowing cross-vendor matching")
                
                # DEBUG: Try to find any vendor that might match using flexible matching
                print(f"🔍 DEBUG: Looking for flexible matches to '{json_vendor}'...")
                potential_matches = []
                json_vendor_clean = self.normalize_text(json_vendor)
                
                for vendor in sorted(list(available_vendors)):
                    vendor_clean = self.normalize_text(vendor)
                    
                    # Check for various matching patterns
                    is_match = False
                    match_reason = ""
                    
                    # 1. Exact match after normalization
                    if json_vendor_clean == vendor_clean:
                        is_match = True
                        match_reason = "exact normalized"
                    
                    # 2. One contains the other
                    elif json_vendor_clean in vendor_clean or vendor_clean in json_vendor_clean:
                        is_match = True
                        match_reason = "contains"
                    
                    # 3. Word overlap (at least 50% of words match)
                    elif len(json_vendor_clean.split()) > 0 and len(vendor_clean.split()) > 0:
                        json_words = set(json_vendor_clean.split())
                        vendor_words = set(vendor_clean.split())
                        overlap = len(json_words.intersection(vendor_words))
                        min_words = min(len(json_words), len(vendor_words))
                        if overlap / min_words >= 0.5:
                            is_match = True
                            match_reason = f"word overlap ({overlap}/{min_words})"
                    
                    # 4. Fuzzy matching for similar names
                    elif len(json_vendor_clean) >= 4 and len(vendor_clean) >= 4:
                        try:
                            from rapidfuzz import fuzz
                            ratio = fuzz.ratio(json_vendor_clean, vendor_clean)
                            if ratio >= 70:  # 70% similarity threshold
                                is_match = True
                                match_reason = f"fuzzy ({ratio}%)"
                        except:
                            pass
                    
                    # 5. Check for common business name patterns
                    elif self._is_vendor_match_flexible(json_vendor_clean, vendor_clean):
                        is_match = True
                        match_reason = "business pattern"
                    
                    if is_match:
                        potential_matches.append(vendor)
                        print(f"🔍 DEBUG: POTENTIAL MATCH: '{json_vendor}' vs '{vendor}' ({match_reason})")
                
                # If we found potential matches, use them instead of returning empty
                if potential_matches:
                    print(f"🔍 DEBUG: Found {len(potential_matches)} potential CERES matches, using them")
                    # Filter candidates to only include these potential matches
                    filtered_candidates = []
                    for candidate in candidates:
                        candidate_vendor = str(candidate.get("vendor", "")).strip()
                        if candidate_vendor in potential_matches:
                            filtered_candidates.append(candidate)
                    print(f"🔍 DEBUG: Filtered to {len(filtered_candidates)} candidates from potential CERES vendors")
                    # Continue with the filtered candidates instead of returning empty
                else:
                    print(f"🔍 DEBUG: No vendor matches found in Excel data - allowing cross-vendor matching")
                    # Allow cross-vendor matching instead of returning empty
                    filtered_candidates = candidates  # Use all candidates for cross-vendor matching
            else:
                print(f"🔍 ADVANCED VENDOR: Filtered to {len(filtered_candidates)} candidates from same vendor '{json_vendor}' (found {vendor_matches} vendor matches)")
        
        for candidate in filtered_candidates:
            candidate_name = str(candidate.get("original_name", "")).strip()
            if not candidate_name:
                continue
            
            # Check for exact match first
            if self.normalize_text(json_name) == self.normalize_text(candidate_name):
                match_result = MatchResult(
                    item=candidate,
                    overall_score=100.0,
                    exact_match=True,
                    fuzzy_score=100.0,
                    match_reason="Exact name match",
                    algorithm_used="exact"
                )
                matches.append(match_result)
                continue
            
            # Calculate fuzzy score
            fuzzy_score, algorithm = self.calculate_fuzzy_score(json_name, candidate_name)
            # Don't skip based on fuzzy score alone - let overall score decide
            
            # Calculate semantic score
            semantic_score = self.calculate_semantic_score(json_name, candidate_name)
            
            # Calculate phonetic score
            phonetic_score = self.calculate_phonetic_score(json_name, candidate_name)
            
            # AI-POWERED DIFFICULT MATCHING: Additional algorithms for hard cases
            ai_scores = self.calculate_ai_powered_scores(json_name, candidate_name, json_item, candidate)
            
            # Calculate contextual scores
            contextual_scores = self.calculate_contextual_scores(json_item, candidate)
            
            # Create match result
            match_result = MatchResult(
                item=candidate,
                overall_score=0.0,  # Will be calculated
                exact_match=False,
                fuzzy_score=fuzzy_score,
                semantic_score=semantic_score,
                phonetic_score=phonetic_score,
                vendor_match=contextual_scores['vendor'] > 80,
                brand_match=contextual_scores['brand'] > 80,
                type_match=contextual_scores['type'] > 80,
                weight_match=contextual_scores['weight'] > 80,
                strain_match=contextual_scores['strain'] > 80,
                match_reason=f"AI-powered match using {algorithm}",
                algorithm_used=algorithm
            )
            
            # Add AI scores to match result
            match_result.ai_scores = ai_scores
            
            # Calculate overall score with AI enhancement
            match_result.overall_score = self.calculate_overall_score_with_ai(match_result, ai_scores)
            
            # Debug logging for first few candidates
            if len(matches) < 3:  # Only log first few to avoid spam
                logging.debug(f"🔍 ADVANCED DEBUG: '{json_name}' vs '{candidate_name}' - fuzzy: {fuzzy_score:.1f}, semantic: {semantic_score:.1f}, phonetic: {phonetic_score:.1f}, overall: {match_result.overall_score:.1f}")
            
            if match_result.overall_score >= threshold:
                matches.append(match_result)
        
        # Sort by overall score (descending)
        matches.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Limit results
        matches = matches[:max_results]
        
        # Log performance
        elapsed_time = time.time() - start_time
        logging.debug(f"Advanced matching completed in {elapsed_time:.3f}s, found {len(matches)} matches")
        
        return matches
    
    def get_matching_stats(self) -> Dict[str, any]:
        """Get statistics about the matching system."""
        return {
            'libraries_available': {
                'rapidfuzz': RAPIDFUZZ_AVAILABLE,
                'fuzzywuzzy': FUZZYWUZZY_AVAILABLE,
                'jellyfish': JELLYFISH_AVAILABLE,
                'difflib': DIFFLIB_AVAILABLE
            },
            'algorithm_weights': self.algorithm_weights,
            'cache_sizes': {
                'performance_cache': len(self.performance_cache),
                'normalization_cache': len(self.normalization_cache),
                'key_terms_cache': len(self.key_terms_cache)
            },
            'total_cache_size': len(self.performance_cache) + len(self.normalization_cache) + len(self.key_terms_cache),
            'max_cache_size': self.max_cache_size
        }
    
    def clear_caches(self):
        """Clear all caches to free memory."""
        self.performance_cache.clear()
        self.normalization_cache.clear()
        self.key_terms_cache.clear()
        logging.info("All matching caches cleared")
