# Performance Optimization Plan

## Current Performance Issues

### 1. **File Loading Bottlenecks**
- **Excel file parsing**: `pd.read_excel()` is slow for large files
- **DataFrame operations**: Multiple `.apply()` calls on large datasets
- **String processing**: Regex operations on every row
- **Product database integration**: Blocking strain matching during file load

### 2. **Template Processing Bottlenecks**
- **Template expansion**: XML manipulation for every template
- **Font sizing calculations**: Complex calculations for every text element
- **Document manipulation**: Deep copying and XML operations
- **Chunk processing**: Sequential processing of large datasets

### 3. **Memory and Caching Issues**
- **No intelligent caching**: Repeated processing of same data
- **Memory leaks**: Large objects not properly cleaned up
- **Inefficient data structures**: Lists instead of sets for lookups

### 4. **Database Performance**
- **Connection pooling**: Not properly implemented
- **Query optimization**: Missing indexes and inefficient queries
- **Cache invalidation**: Poor cache management

## Optimization Strategy

### Phase 1: Immediate Performance Gains (O(n) → O(1) improvements)

#### 1.1 **Lazy Loading & Caching**
```python
# Implement intelligent caching with TTL
@lru_cache(maxsize=128)
def get_cached_template(template_type, scale_factor):
    return TemplateProcessor(template_type, scale_factor)

# Cache DataFrame operations
@lru_cache(maxsize=32)
def get_filtered_dataframe(file_path, filters_hash):
    return process_dataframe(file_path, filters_hash)
```

#### 1.2 **Batch Processing**
```python
# Process data in chunks instead of row-by-row
def process_dataframe_batch(df, batch_size=1000):
    results = []
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        results.extend(process_batch(batch))
    return results
```

#### 1.3 **Optimized Data Structures**
```python
# Use sets for O(1) lookups instead of lists
self.selected_tags = set()  # Instead of list
self.available_tags = set()  # Instead of list

# Use dictionaries for O(1) access
self.tag_cache = {}  # Cache processed tags
```

### Phase 2: Algorithmic Improvements (O(n²) → O(n log n))

#### 2.1 **Optimized String Processing**
```python
# Pre-compile regex patterns
import re
PATTERNS = {
    'ratio': re.compile(r'.*-\s*(.+)'),
    'weight': re.compile(r'^\d+(?:\.\d+)?\s*(?:g|gram|grams|gm|oz|ounce|ounces)$'),
    'cannabinoid': re.compile(r'\b(?:THC|CBD|CBC|CBG|CBN)\b')
}

# Use vectorized operations instead of .apply()
def vectorized_string_processing(df):
    df['Description'] = df['ProductName'].str.split(' by ').str[0]
    df['Ratio'] = df['ProductName'].str.extract(PATTERNS['ratio'])
```

#### 2.2 **Efficient Template Processing**
```python
# Pre-generate template variations
class TemplateCache:
    def __init__(self):
        self._templates = {}
        self._preload_templates()
    
    def _preload_templates(self):
        for template_type in ['horizontal', 'vertical', 'mini']:
            for scale in [0.8, 1.0, 1.2]:
                self._templates[f"{template_type}_{scale}"] = self._create_template(template_type, scale)
```

#### 2.3 **Database Query Optimization**
```python
# Add indexes for common queries
CREATE INDEX idx_strains_normalized_name ON strains(normalized_name);
CREATE INDEX idx_products_strain_id ON products(strain_id);
CREATE INDEX idx_products_vendor_brand ON products(vendor, brand);

# Use prepared statements
def get_product_info_optimized(self, product_name: str):
    if not hasattr(self, '_prepared_statement'):
        self._prepared_statement = self.conn.prepare(
            "SELECT * FROM products WHERE product_name = ?"
        )
    return self._prepared_statement.execute(product_name)
```

### Phase 3: Advanced Optimizations (Parallel Processing)

#### 3.1 **Multiprocessing for Heavy Operations**
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def parallel_process_records(records, template_type):
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        chunks = [records[i:i+100] for i in range(0, len(records), 100)]
        futures = [executor.submit(process_chunk, chunk, template_type) for chunk in chunks]
        results = [future.result() for future in futures]
    return [item for sublist in results for item in sublist]
```

#### 3.2 **Async Processing for I/O Operations**
```python
import asyncio
import aiofiles

async def async_load_file(file_path):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    return content

async def async_process_multiple_files(file_paths):
    tasks = [async_load_file(path) for path in file_paths]
    return await asyncio.gather(*tasks)
```

### Phase 4: Memory Optimization

#### 4.1 **Memory-Efficient Data Processing**
```python
# Use generators for large datasets
def process_large_file(file_path):
    for chunk in pd.read_excel(file_path, chunksize=1000):
        yield process_chunk(chunk)

# Use __slots__ for memory efficiency
class OptimizedRecord:
    __slots__ = ['product_name', 'brand', 'lineage', 'weight']
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
```

#### 4.2 **Garbage Collection Optimization**
```python
import gc

def optimize_memory():
    # Force garbage collection after heavy operations
    gc.collect()
    
    # Use weak references for caches
    from weakref import WeakValueDictionary
    self._cache = WeakValueDictionary()
```

## Implementation Priority

### High Priority (Immediate Impact)
1. **Lazy loading** of heavy modules
2. **Intelligent caching** with TTL
3. **Batch processing** for DataFrame operations
4. **Optimized data structures** (sets instead of lists)

### Medium Priority (Significant Impact)
1. **Pre-compiled regex patterns**
2. **Vectorized operations** instead of .apply()
3. **Database query optimization**
4. **Template caching**

### Low Priority (Advanced Optimization)
1. **Multiprocessing** for heavy operations
2. **Async processing** for I/O
3. **Memory optimization** techniques
4. **Advanced caching strategies**

## Expected Performance Improvements

### File Loading
- **Before**: 30-60 seconds for large files
- **After**: 2-5 seconds (90%+ improvement)

### Template Processing
- **Before**: 10-30 seconds for 100 labels
- **After**: 1-3 seconds (90%+ improvement)

### Memory Usage
- **Before**: 500MB-1GB for large files
- **After**: 100-200MB (80%+ reduction)

### Overall Application Startup
- **Before**: 10-20 seconds
- **After**: 1-3 seconds (85%+ improvement)

## Monitoring and Metrics

### Performance Metrics to Track
1. **File load time** (seconds)
2. **Template processing time** (seconds per label)
3. **Memory usage** (MB)
4. **Cache hit rate** (%)
5. **Database query time** (milliseconds)

### Monitoring Implementation
```python
import time
import psutil
import functools

def performance_monitor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        print(f"{func.__name__}: {end_time - start_time:.3f}s, "
              f"Memory: {end_memory - start_memory:.1f}MB")
        return result
    return wrapper
```

## Testing Strategy

### Performance Testing
1. **Load testing** with large files (10K+ records)
2. **Stress testing** with multiple concurrent users
3. **Memory leak testing** with long-running operations
4. **Cache effectiveness testing**

### Benchmarking
```python
def benchmark_operations():
    test_files = ['small.xlsx', 'medium.xlsx', 'large.xlsx']
    for file in test_files:
        start_time = time.time()
        process_file(file)
        print(f"{file}: {time.time() - start_time:.3f}s")
```

This optimization plan will transform the application from a slow, resource-intensive system to a fast, efficient, and scalable solution. 