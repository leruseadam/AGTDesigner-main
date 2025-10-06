# AI-Enhanced JSON Matching for Label Maker

## Overview

The JSON matcher has been enhanced with AI-powered matching capabilities to provide more accurate and intelligent matching between JSON data and Excel inventory. This enhancement maintains the strict vendor matching requirements while significantly improving brand and product matching accuracy.

## Key Features

### 1. **ABSOLUTE Vendor Matching (AI-Enhanced)**
- **Requirement**: Vendors must match exactly or be known variations
- **AI Enhancement**: Semantic similarity matching for vendor names that are similar but not identical
- **Fallback**: Traditional exact matching and known variations
- **Confidence**: High confidence threshold (0.8+) for AI matches

### 2. **NEAR PERFECT Brand Matching (AI-Enhanced)**
- **Requirement**: Brands must match very closely
- **AI Enhancement**: Semantic similarity using sentence transformers
- **Scoring**: 
  - 0.95+ confidence: +0.15 bonus (Near perfect)
  - 0.90+ confidence: +0.12 bonus (Very high)
  - 0.80+ confidence: +0.10 bonus (High)
  - 0.70+ confidence: +0.05 bonus (Good)
  - Below 0.70: No bonus

### 3. **Context-Aware Product Matching**
- **Multi-factor Analysis**: Product name, type, and strain
- **Weighted Scoring**: 
  - Product name: 60% weight
  - Product type: 25% weight
  - Strain: 15% weight
- **AI Enhancement**: Semantic similarity for each factor

## Installation

### Option 1: Automated Installation
```bash
python install_ai_dependencies.py
```

### Option 2: Manual Installation
```bash
pip install -r requirements_ai.txt
```

### Required Packages
- `sentence-transformers` - Core AI similarity engine
- `torch` - PyTorch framework
- `transformers` - Hugging Face transformers
- `numpy` - Numerical computing
- `scikit-learn` - Machine learning utilities

## How It Works

### 1. **Semantic Similarity Calculation**
```python
def calculate_semantic_similarity(text1: str, text2: str) -> float:
    # Uses sentence-transformers to create embeddings
    # Calculates cosine similarity between text representations
    # Falls back to traditional string similarity if AI unavailable
```

### 2. **AI-Enhanced Vendor Matching**
```python
def ai_enhanced_vendor_matching(json_vendor: str, cache_vendor: str) -> Tuple[bool, float]:
    # 1. Exact match (confidence: 1.0)
    # 2. Known variations (confidence: 0.95)
    # 3. AI semantic similarity (confidence: 0.85+)
    # 4. Substring matching (confidence: 0.8+)
```

### 3. **AI-Enhanced Brand Matching**
```python
def ai_enhanced_brand_matching(json_brand: str, cache_brand: str) -> float:
    # 1. Exact match
    # 2. AI semantic similarity
    # 3. Substring analysis
    # 4. Traditional string similarity (fallback)
```

## Performance Considerations

### **Memory Usage**
- Sentence transformer model: ~90MB
- First-time loading: ~2-3 seconds
- Subsequent uses: ~100ms

### **Processing Speed**
- Traditional matching: ~1ms per comparison
- AI-enhanced matching: ~10-50ms per comparison
- **Optimization**: AI matching only used when traditional methods fail

### **Fallback Strategy**
- AI methods gracefully fall back to traditional methods
- No performance impact if AI packages unavailable
- Maintains backward compatibility

## Configuration

### **Confidence Thresholds**
```python
# Vendor matching (ABSOLUTE requirement)
VENDOR_AI_THRESHOLD = 0.8  # 80% confidence required

# Brand matching (NEAR PERFECT requirement)
BRAND_AI_THRESHOLD = 0.7   # 70% confidence for bonus
BRAND_PERFECT_THRESHOLD = 0.95  # 95% for maximum bonus
```

### **Model Selection**
```python
# Default model: all-MiniLM-L6-v2
# - Fast and lightweight
# - Good accuracy for vendor/brand matching
# - ~90MB model size
```

## Examples

### **Vendor Matching Examples**
```
JSON Vendor: "dank czar"
Excel Vendor: "dcz holdings inc"
Result: ✅ MATCH (Known variation, confidence: 0.95)

JSON Vendor: "omega labs"
Excel Vendor: "omega cannabis"
Result: ✅ MATCH (AI semantic similarity, confidence: 0.87)

JSON Vendor: "completely different"
Excel Vendor: "another company"
Result: ❌ NO MATCH (Below threshold)
```

### **Brand Matching Examples**
```
JSON Brand: "ceres"
Excel Brand: "ceres botanicals"
Result: ✅ HIGH CONFIDENCE (0.92, bonus: +0.12)

JSON Brand: "airo pro"
Excel Brand: "airo"
Result: ✅ PERFECT MATCH (0.98, bonus: +0.15)

JSON Brand: "different brand"
Excel Brand: "unrelated brand"
Result: ❌ LOW CONFIDENCE (0.45, bonus: +0.00)
```

## Troubleshooting

### **Common Issues**

1. **Import Errors**
   ```bash
   pip install sentence-transformers
   pip install torch
   ```

2. **Model Download Issues**
   ```bash
   # Clear cache and retry
   rm -rf ~/.cache/torch/sentence_transformers
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

3. **Memory Issues**
   - Reduce batch size in processing
   - Use CPU-only version: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

### **Performance Issues**
- AI matching automatically disabled if too slow
- Traditional methods used as fallback
- Check logs for performance warnings

## Monitoring and Logging

### **Debug Logs**
```python
logging.debug(f"AI vendor matching successful: '{json_vendor}' vs '{cache_vendor}' (confidence: {vendor_confidence:.2f})")
logging.debug(f"AI brand matching successful: '{json_brand}' vs '{cache_brand}' (confidence: {brand_confidence:.2f}, bonus: {brand_bonus:.2f})")
```

### **Performance Metrics**
- Vendor match confidence scores
- Brand match confidence scores
- Processing time per item
- Fallback method usage

## Future Enhancements

### **Planned Features**
- Custom model training for domain-specific matching
- Batch processing optimization
- GPU acceleration support
- Advanced context analysis

### **Model Improvements**
- Larger, more accurate models
- Multi-language support
- Domain-specific embeddings

## Support

For issues or questions about AI-enhanced matching:
1. Check the troubleshooting section above
2. Review debug logs for specific error messages
3. Verify AI dependencies are properly installed
4. Test with simple examples first

---

**Note**: AI-enhanced matching is designed to be a drop-in replacement that maintains all existing functionality while providing significant improvements in accuracy and intelligence.
