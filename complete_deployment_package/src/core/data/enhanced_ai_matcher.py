"""
Enhanced AI Product Matcher with Advanced Machine Learning
==========================================================

This enhanced AI product matcher provides:
- Advanced neural similarity learning
- Multi-modal feature extraction
- Ensemble matching with confidence scoring
- Real-time learning from matching feedback
- Advanced product type recognition
"""

import numpy as np
import pandas as pd
import re
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
import joblib
from fuzzywuzzy import fuzz
import jellyfish
from collections import defaultdict

@dataclass
class MatchFeatures:
    """Features extracted for ML-based matching"""
    text_similarity: float
    semantic_similarity: float
    weight_similarity: float
    price_similarity: float
    vendor_similarity: float
    brand_similarity: float
    type_similarity: float
    cannabinoid_similarity: float
    length_similarity: float
    token_overlap: float
    edit_distance: float
    phonetic_similarity: float

@dataclass
class EnhancedMatchResult:
    """Enhanced match result with detailed analytics"""
    score: float
    confidence: float
    match_data: Dict[str, Any]
    features: MatchFeatures
    explanation: str
    processing_time: float
    model_versions: Dict[str, str]

class FeatureExtractor:
    """Advanced feature extraction for product matching"""
    
    def __init__(self):
        self.cannabinoid_patterns = {
            'thc': r'(\d+(?:\.\d+)?)\s*%?\s*thc',
            'cbd': r'(\d+(?:\.\d+)?)\s*%?\s*cbd',
            'thca': r'(\d+(?:\.\d+)?)\s*%?\s*thca',
            'cbda': r'(\d+(?:\.\d+)?)\s*%?\s*cbda'
        }
        
        self.weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*g(?:ram)?s?',
            r'(\d+(?:\.\d+)?)\s*oz(?:unce)?s?',
            r'(\d+)/(\d+)\s*oz',
            r'(\d+(?:\.\d+)?)\s*mg'
        ]
        
        self.price_patterns = [
            r'\$(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*dollar',
            r'price:\s*(\d+(?:\.\d+)?)'
        ]
        
    def extract_comprehensive_features(self, json_product: Dict, db_product: Dict) -> MatchFeatures:
        """Extract comprehensive features for ML matching"""
        
        json_name = str(json_product.get('inventory_name', ''))
        db_name = str(db_product.get('Product Name*', ''))
        
        # Text similarity features
        text_sim = self._calculate_text_similarity(json_name, db_name)
        
        # Semantic similarity (using TF-IDF)
        semantic_sim = self._calculate_semantic_similarity(json_name, db_name)
        
        # Weight similarity
        weight_sim = self._calculate_weight_similarity(json_product, db_product)
        
        # Price similarity  
        price_sim = self._calculate_price_similarity(json_product, db_product)
        
        # Vendor similarity
        vendor_sim = self._calculate_vendor_similarity(json_product, db_product)
        
        # Brand similarity
        brand_sim = self._calculate_brand_similarity(json_product, db_product)
        
        # Product type similarity
        type_sim = self._calculate_type_similarity(json_product, db_product)
        
        # Cannabinoid profile similarity
        cannabinoid_sim = self._calculate_cannabinoid_similarity(json_product, db_product)
        
        # String length similarity
        length_sim = self._calculate_length_similarity(json_name, db_name)
        
        # Token overlap
        token_overlap = self._calculate_token_overlap(json_name, db_name)
        
        # Edit distance
        edit_dist = self._calculate_normalized_edit_distance(json_name, db_name)
        
        # Phonetic similarity
        phonetic_sim = self._calculate_phonetic_similarity(json_name, db_name)
        
        return MatchFeatures(
            text_similarity=text_sim,
            semantic_similarity=semantic_sim,
            weight_similarity=weight_sim,
            price_similarity=price_sim,
            vendor_similarity=vendor_sim,
            brand_similarity=brand_sim,
            type_similarity=type_sim,
            cannabinoid_similarity=cannabinoid_sim,
            length_similarity=length_sim,
            token_overlap=token_overlap,
            edit_distance=edit_dist,
            phonetic_similarity=phonetic_sim
        )
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate comprehensive text similarity"""
        if not text1 or not text2:
            return 0.0
            
        # Combine multiple fuzzy matching algorithms
        ratio = fuzz.ratio(text1, text2) / 100.0
        partial = fuzz.partial_ratio(text1, text2) / 100.0
        token_sort = fuzz.token_sort_ratio(text1, text2) / 100.0
        token_set = fuzz.token_set_ratio(text1, text2) / 100.0
        
        # Weighted combination
        return (ratio * 0.3 + partial * 0.2 + token_sort * 0.3 + token_set * 0.2)
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF"""
        if not text1 or not text2:
            return 0.0
            
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def _calculate_weight_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate weight similarity with unit normalization"""
        json_weight = self._extract_weight(str(json_product.get('inventory_name', '')))
        db_weight = self._extract_weight(str(db_product.get('Product Name*', '')))
        
        if not json_weight or not db_weight:
            return 0.5  # Neutral score for missing data
            
        # Calculate relative difference
        max_weight = max(json_weight, db_weight)
        min_weight = min(json_weight, db_weight)
        similarity = min_weight / max_weight
        
        return similarity
    
    def _extract_weight(self, text: str) -> Optional[float]:
        """Extract weight in grams from text"""
        text_lower = text.lower()
        
        for pattern in self.weight_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if len(match.groups()) == 1:
                    weight = float(match.group(1))
                    if 'oz' in pattern:
                        weight *= 28.35  # Convert to grams
                    elif 'mg' in pattern:
                        weight /= 1000  # Convert to grams
                    return weight
                elif len(match.groups()) == 2:  # Fraction
                    numerator = float(match.group(1))
                    denominator = float(match.group(2))
                    weight = (numerator / denominator) * 28.35
                    return weight
        
        return None
    
    def _calculate_price_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate price similarity"""
        json_price = self._extract_price(json_product)
        db_price = self._extract_price(db_product)
        
        if not json_price or not db_price:
            return 0.5
            
        # Calculate relative price difference with tolerance
        max_price = max(json_price, db_price)
        min_price = min(json_price, db_price)
        
        if max_price == 0:
            return 1.0 if min_price == 0 else 0.0
            
        similarity = min_price / max_price
        
        # Apply tolerance for reasonable price variations
        if similarity > 0.8:  # Within 20% is considered very similar
            return 1.0
        elif similarity > 0.6:  # Within 40% is moderately similar
            return 0.8
        else:
            return similarity
    
    def _extract_price(self, product: Dict) -> Optional[float]:
        """Extract price from product data"""
        # Check direct price fields
        for price_field in ['price', 'cost', 'unit_price', 'Price', 'Cost']:
            if price_field in product and product[price_field]:
                try:
                    return float(product[price_field])
                except:
                    pass
        
        # Check product name/description for price patterns
        text = str(product.get('inventory_name', '') or product.get('Product Name*', ''))
        
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return None
    
    def _calculate_vendor_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate vendor name similarity"""
        json_vendor = str(json_product.get('vendor_name', '')).lower().strip()
        db_vendor = str(db_product.get('Vendor/Supplier*', '') or 
                       db_product.get('Vendor', '')).lower().strip()
        
        if not json_vendor or not db_vendor:
            return 0.5
        
        return fuzz.ratio(json_vendor, db_vendor) / 100.0
    
    def _calculate_brand_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate brand similarity"""
        json_brand = str(json_product.get('brand_name', '')).lower().strip()
        db_brand = str(db_product.get('Product Brand', '')).lower().strip()
        
        if not json_brand or not db_brand:
            return 0.5
            
        return fuzz.ratio(json_brand, db_brand) / 100.0
    
    def _calculate_type_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate product type similarity"""
        json_type = str(json_product.get('inventory_type', '')).lower()
        db_type = str(db_product.get('Product Type', '') or 
                     db_product.get('Type', '')).lower()
        
        if not json_type or not db_type:
            return 0.5
            
        # Direct comparison
        if json_type == db_type:
            return 1.0
            
        # Fuzzy comparison for similar types
        return fuzz.ratio(json_type, db_type) / 100.0
    
    def _calculate_cannabinoid_similarity(self, json_product: Dict, db_product: Dict) -> float:
        """Calculate cannabinoid profile similarity"""
        json_cannabinoids = self._extract_cannabinoids(json_product)
        db_cannabinoids = self._extract_cannabinoids(db_product)
        
        if not json_cannabinoids or not db_cannabinoids:
            return 0.5
        
        # Calculate similarity for each cannabinoid
        similarities = []
        
        for cannabinoid in ['thc', 'cbd', 'thca', 'cbda']:
            json_val = json_cannabinoids.get(cannabinoid, 0)
            db_val = db_cannabinoids.get(cannabinoid, 0)
            
            if json_val == 0 and db_val == 0:
                similarities.append(1.0)
            elif json_val == 0 or db_val == 0:
                similarities.append(0.0)
            else:
                max_val = max(json_val, db_val)
                min_val = min(json_val, db_val)
                similarities.append(min_val / max_val)
        
        return np.mean(similarities) if similarities else 0.5
    
    def _extract_cannabinoids(self, product: Dict) -> Dict[str, float]:
        """Extract cannabinoid percentages from product"""
        cannabinoids = {}
        
        # Check lab results
        lab_results = product.get('lab_result_data', {})
        if isinstance(lab_results, dict):
            for cannabinoid in ['thc', 'cbd', 'thca', 'cbda']:
                value = lab_results.get(cannabinoid) or lab_results.get(cannabinoid.upper())
                if value:
                    try:
                        cannabinoids[cannabinoid] = float(value)
                    except:
                        pass
        
        # Check product name
        text = str(product.get('inventory_name', '') or product.get('Product Name*', ''))
        
        for cannabinoid, pattern in self.cannabinoid_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match and cannabinoid not in cannabinoids:
                try:
                    cannabinoids[cannabinoid] = float(match.group(1))
                except:
                    pass
        
        return cannabinoids
    
    def _calculate_length_similarity(self, text1: str, text2: str) -> float:
        """Calculate string length similarity"""
        if not text1 or not text2:
            return 0.0
            
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        min_len = min(len1, len2)
        
        if max_len == 0:
            return 1.0
            
        return min_len / max_len
    
    def _calculate_token_overlap(self, text1: str, text2: str) -> float:
        """Calculate token overlap similarity"""
        if not text1 or not text2:
            return 0.0
            
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_normalized_edit_distance(self, text1: str, text2: str) -> float:
        """Calculate normalized Levenshtein distance"""
        if not text1 or not text2:
            return 0.0
            
        distance = jellyfish.levenshtein_distance(text1.lower(), text2.lower())
        max_len = max(len(text1), len(text2))
        
        if max_len == 0:
            return 1.0
            
        return 1.0 - (distance / max_len)
    
    def _calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity using Soundex"""
        if not text1 or not text2:
            return 0.0
            
        try:
            soundex1 = jellyfish.soundex(text1)
            soundex2 = jellyfish.soundex(text2)
            
            return 1.0 if soundex1 == soundex2 else 0.0
        except:
            return 0.0

class EnsembleMLMatcher:
    """Ensemble machine learning matcher with multiple models"""
    
    def __init__(self):
        self.models = {}
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_versions = {}
        
    def train_models(self, training_data: List[Tuple[Dict, Dict, float]]):
        """Train ensemble models on labeled training data"""
        logging.info(f"Training ensemble models on {len(training_data)} examples...")
        
        if len(training_data) < 10:
            logging.warning("Insufficient training data, using default models")
            self._initialize_default_models()
            return
            
        # Extract features and labels
        features_list = []
        labels = []
        
        for json_product, db_product, score in training_data:
            features = self.feature_extractor.extract_comprehensive_features(json_product, db_product)
            feature_vector = self._features_to_vector(features)
            features_list.append(feature_vector)
            labels.append(score)
        
        X = np.array(features_list)
        y = np.array(labels)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        # Train multiple models
        self.models['random_forest'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.models['gradient_boosting'] = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        self.models['neural_network'] = MLPRegressor(
            hidden_layer_sizes=(100, 50),
            max_iter=500,
            alpha=0.01,
            random_state=42
        )
        
        # Train models
        for name, model in self.models.items():
            try:
                model.fit(X_train, y_train)
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)
                
                logging.info(f"{name} - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
                self.model_versions[name] = f"v1.0_{int(time.time())}"
                
            except Exception as e:
                logging.error(f"Error training {name}: {e}")
                
        self.is_trained = True
        logging.info("Ensemble model training completed")
    
    def _initialize_default_models(self):
        """Initialize models with default parameters when training data is insufficient"""
        self.models['random_forest'] = RandomForestRegressor(n_estimators=50, random_state=42)
        self.models['gradient_boosting'] = GradientBoostingRegressor(n_estimators=50, random_state=42)
        
        # Create dummy training data for default models
        dummy_X = np.random.rand(20, 12)  # 12 features
        dummy_y = np.random.rand(20)
        
        dummy_X_scaled = self.scaler.fit_transform(dummy_X)
        
        for name, model in self.models.items():
            model.fit(dummy_X_scaled, dummy_y)
            self.model_versions[name] = "v1.0_default"
    
    def predict_similarity(self, json_product: Dict, db_product: Dict) -> EnhancedMatchResult:
        """Predict similarity score using ensemble of models"""
        start_time = time.perf_counter()
        
        # Extract features
        features = self.feature_extractor.extract_comprehensive_features(json_product, db_product)
        feature_vector = self._features_to_vector(features)
        
        if not self.is_trained:
            # Fallback to simple scoring
            score = self._calculate_simple_score(features)
            confidence = 0.6  # Lower confidence for untrained models
        else:
            # Use ensemble prediction
            X_scaled = self.scaler.transform([feature_vector])
            
            predictions = []
            valid_predictions = 0
            
            for name, model in self.models.items():
                try:
                    pred = model.predict(X_scaled)[0]
                    predictions.append(max(0, min(1, pred)))  # Clamp to [0,1]
                    valid_predictions += 1
                except Exception as e:
                    logging.warning(f"Model {name} prediction failed: {e}")
            
            if predictions:
                # Weighted ensemble (could be learned)
                weights = [0.4, 0.4, 0.2] if len(predictions) >= 3 else [0.5] * len(predictions)
                weights = weights[:len(predictions)]
                
                score = np.average(predictions, weights=weights)
                
                # Calculate confidence based on prediction agreement
                if len(predictions) > 1:
                    std_dev = np.std(predictions)
                    confidence = max(0.5, 1.0 - (std_dev * 2))  # Lower std = higher confidence
                else:
                    confidence = 0.7
            else:
                score = self._calculate_simple_score(features)
                confidence = 0.5
        
        # Generate explanation
        explanation = self._generate_explanation(features, score)
        
        processing_time = time.perf_counter() - start_time
        
        return EnhancedMatchResult(
            score=score,
            confidence=confidence,
            match_data=db_product,
            features=features,
            explanation=explanation,
            processing_time=processing_time,
            model_versions=self.model_versions.copy()
        )
    
    def _features_to_vector(self, features: MatchFeatures) -> np.ndarray:
        """Convert features object to numpy vector"""
        return np.array([
            features.text_similarity,
            features.semantic_similarity,
            features.weight_similarity,
            features.price_similarity,
            features.vendor_similarity,
            features.brand_similarity,
            features.type_similarity,
            features.cannabinoid_similarity,
            features.length_similarity,
            features.token_overlap,
            features.edit_distance,
            features.phonetic_similarity
        ])
    
    def _calculate_simple_score(self, features: MatchFeatures) -> float:
        """Calculate simple weighted score when ML models aren't available"""
        weights = {
            'text_similarity': 0.25,
            'semantic_similarity': 0.20,
            'weight_similarity': 0.15,
            'vendor_similarity': 0.10,
            'brand_similarity': 0.10,
            'type_similarity': 0.08,
            'cannabinoid_similarity': 0.07,
            'price_similarity': 0.05
        }
        
        score = 0.0
        for feature_name, weight in weights.items():
            feature_value = getattr(features, feature_name, 0.0)
            score += feature_value * weight
            
        return min(1.0, max(0.0, score))
    
    def _generate_explanation(self, features: MatchFeatures, score: float) -> str:
        """Generate human-readable explanation for the match"""
        explanations = []
        
        if features.text_similarity > 0.8:
            explanations.append("Very similar product names")
        elif features.text_similarity > 0.6:
            explanations.append("Moderately similar product names")
        
        if features.vendor_similarity > 0.8:
            explanations.append("Same vendor/supplier")
        elif features.vendor_similarity > 0.6:
            explanations.append("Similar vendor names")
            
        if features.weight_similarity > 0.9:
            explanations.append("Identical weights")
        elif features.weight_similarity > 0.7:
            explanations.append("Similar weights")
            
        if features.brand_similarity > 0.8:
            explanations.append("Same brand")
            
        if features.cannabinoid_similarity > 0.8:
            explanations.append("Very similar cannabinoid profile")
        elif features.cannabinoid_similarity > 0.6:
            explanations.append("Similar potency")
        
        if not explanations:
            if score > 0.7:
                explanations.append("Good overall match")
            elif score > 0.5:
                explanations.append("Moderate match")
            else:
                explanations.append("Low confidence match")
        
        return "; ".join(explanations)
    
    def save_models(self, filepath: str):
        """Save trained models to disk"""
        if self.is_trained:
            model_data = {
                'models': self.models,
                'scaler': self.scaler,
                'model_versions': self.model_versions,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, filepath)
            logging.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.model_versions = model_data.get('model_versions', {})
            self.is_trained = model_data.get('is_trained', False)
            logging.info(f"Models loaded from {filepath}")
        except Exception as e:
            logging.error(f"Error loading models: {e}")
            self._initialize_default_models()

class EnhancedAIProductMatcher:
    """Enhanced AI Product Matcher with advanced ML capabilities"""
    
    def __init__(self):
        self.ensemble_matcher = EnsembleMLMatcher()
        self.match_history = []  # For continuous learning
        self.performance_stats = defaultdict(list)
        
    def match_products(self, json_products: List[Dict], db_products: List[Dict], 
                      strategy: str = "ml_enhanced") -> List[EnhancedMatchResult]:
        """Match products using enhanced AI algorithms"""
        
        start_time = time.perf_counter()
        all_matches = []
        
        for json_product in json_products:
            product_matches = []
            
            for db_product in db_products:
                if strategy == "ml_enhanced":
                    match_result = self.ensemble_matcher.predict_similarity(json_product, db_product)
                else:
                    # Fallback to feature-based matching
                    match_result = self._feature_based_match(json_product, db_product)
                
                if match_result.score > 0.3:  # Minimum threshold
                    product_matches.append(match_result)
            
            # Sort by score and keep top matches
            product_matches.sort(key=lambda x: x.score, reverse=True)
            all_matches.extend(product_matches[:10])  # Top 10 per product
        
        total_time = time.perf_counter() - start_time
        self.performance_stats['total_processing_time'].append(total_time)
        self.performance_stats['products_processed'].append(len(json_products))
        
        logging.info(f"Enhanced AI matching completed: {len(all_matches)} matches in {total_time:.3f}s")
        
        return all_matches
    
    def _feature_based_match(self, json_product: Dict, db_product: Dict) -> EnhancedMatchResult:
        """Fallback feature-based matching"""
        features = self.ensemble_matcher.feature_extractor.extract_comprehensive_features(
            json_product, db_product
        )
        
        score = self.ensemble_matcher._calculate_simple_score(features)
        explanation = self.ensemble_matcher._generate_explanation(features, score)
        
        return EnhancedMatchResult(
            score=score,
            confidence=0.6,
            match_data=db_product,
            features=features,
            explanation=explanation,
            processing_time=0.0,
            model_versions={"fallback": "v1.0"}
        )
    
    def train_from_feedback(self, feedback_data: List[Tuple[Dict, Dict, float]]):
        """Train models from user feedback"""
        if len(feedback_data) > 0:
            logging.info(f"Training from {len(feedback_data)} feedback examples")
            self.ensemble_matcher.train_models(feedback_data)
    
    def add_match_feedback(self, json_product: Dict, db_product: Dict, 
                          user_score: float, predicted_score: float):
        """Add feedback for continuous learning"""
        feedback_entry = {
            'json_product': json_product,
            'db_product': db_product,
            'user_score': user_score,
            'predicted_score': predicted_score,
            'timestamp': time.time()
        }
        self.match_history.append(feedback_entry)
        
        # Retrain if we have enough feedback
        if len(self.match_history) >= 50:
            training_data = [
                (entry['json_product'], entry['db_product'], entry['user_score'])
                for entry in self.match_history[-100:]  # Use last 100 examples
            ]
            self.train_from_feedback(training_data)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance analytics report"""
        if not self.performance_stats['total_processing_time']:
            return {"message": "No performance data available"}
        
        return {
            'average_processing_time': np.mean(self.performance_stats['total_processing_time']),
            'total_products_processed': sum(self.performance_stats['products_processed']),
            'match_history_size': len(self.match_history),
            'model_versions': self.ensemble_matcher.model_versions,
            'is_trained': self.ensemble_matcher.is_trained
        }