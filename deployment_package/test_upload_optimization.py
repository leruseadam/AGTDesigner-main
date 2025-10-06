#!/usr/bin/env python3
"""
Test script for Excel upload optimization
Tests the performance improvements made to Excel file processing
"""

import os
import sys
import time
import pandas as pd
import tempfile
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_excel_file(num_rows=10000):
    """Create a test Excel file with sample data"""
    print(f"Creating test Excel file with {num_rows:,} rows...")
    
    # Sample product data
    product_types = ['Flower', 'Concentrate', 'Edible', 'Topical', 'Vape Cartridge']
    lineages = ['Indica', 'Sativa', 'Hybrid', 'CBD']
    brands = ['Brand A', 'Brand B', 'Brand C', 'Brand D', 'Brand E']
    
    data = {
        'Product Name*': [f'Product {i}' for i in range(num_rows)],
        'Product Type*': [product_types[i % len(product_types)] for i in range(num_rows)],
        'Lineage': [lineages[i % len(lineages)] for i in range(num_rows)],
        'Product Brand': [brands[i % len(brands)] for i in range(num_rows)],
        'Product Strain': [f'Strain {i % 100}' for i in range(num_rows)],
        'Price': [f'${(i % 100) + 10}.00' for i in range(num_rows)],
        'THC %': [f'{(i % 30) + 5}.5' for i in range(num_rows)],
        'CBD %': [f'{(i % 10) + 1}.0' for i in range(num_rows)],
        'Weight': [f'{(i % 5) + 1}g' for i in range(num_rows)]
    }
    
    df = pd.DataFrame(data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    df.to_excel(temp_file.name, index=False, engine='openpyxl')
    temp_file.close()
    
    print(f"✅ Created test file: {temp_file.name}")
    print(f"   Size: {os.path.getsize(temp_file.name):,} bytes")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    
    return temp_file.name

def test_old_upload_method(file_path):
    """Test the old upload method with 1000 row limit"""
    print("\n=== Testing OLD Upload Method (1000 rows) ===")
    start_time = time.time()
    
    try:
        # Simulate old method
        df = pd.read_excel(file_path, nrows=1000, engine='openpyxl')
        
        load_time = time.time() - start_time
        print(f"✅ Old method completed in {load_time:.3f}s")
        print(f"   Rows loaded: {len(df):,}")
        print(f"   Data coverage: {len(df)/10000*100:.1f}% of original file")
        
        return load_time, len(df)
        
    except Exception as e:
        print(f"❌ Old method failed: {e}")
        return None, 0

def test_new_upload_method(file_path):
    """Test the new optimized upload method with 50000 row limit"""
    print("\n=== Testing NEW Optimized Upload Method (50000 rows) ===")
    start_time = time.time()
    
    try:
        # Simulate new optimized method
        df = pd.read_excel(file_path, nrows=50000, engine='openpyxl', dtype=str, na_filter=False)
        
        load_time = time.time() - start_time
        print(f"✅ New method completed in {load_time:.3f}s")
        print(f"   Rows loaded: {len(df):,}")
        print(f"   Data coverage: {len(df)/10000*100:.1f}% of original file")
        
        return load_time, len(df)
        
    except Exception as e:
        print(f"❌ New method failed: {e}")
        return None, 0

def test_ultra_fast_method(file_path):
    """Test the ultra-fast method if available"""
    print("\n=== Testing ULTRA-FAST Method ===")
    start_time = time.time()
    
    try:
        from src.core.data.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        
        # Try ultra-fast load if available
        if hasattr(processor, 'ultra_fast_load'):
            success = processor.ultra_fast_load(file_path)
            if success:
                load_time = time.time() - start_time
                print(f"✅ Ultra-fast method completed in {load_time:.3f}s")
                print(f"   Rows loaded: {len(processor.df):,}")
                return load_time, len(processor.df)
        
        # Try PythonAnywhere fast load
        if hasattr(processor, 'pythonanywhere_fast_load'):
            success = processor.pythonanywhere_fast_load(file_path)
            if success:
                load_time = time.time() - start_time
                print(f"✅ PythonAnywhere fast method completed in {load_time:.3f}s")
                print(f"   Rows loaded: {len(processor.df):,}")
                return load_time, len(processor.df)
        
        print("❌ Ultra-fast methods not available")
        return None, 0
        
    except Exception as e:
        print(f"❌ Ultra-fast method failed: {e}")
        return None, 0

def main():
    """Run the upload optimization tests"""
    print("🚀 Excel Upload Optimization Test")
    print("=" * 50)
    
    # Create test file
    test_file = create_test_excel_file(10000)
    
    try:
        # Test different methods
        old_time, old_rows = test_old_upload_method(test_file)
        new_time, new_rows = test_new_upload_method(test_file)
        ultra_time, ultra_rows = test_ultra_fast_method(test_file)
        
        # Compare results
        print("\n" + "=" * 50)
        print("📊 PERFORMANCE COMPARISON")
        print("=" * 50)
        
        if old_time and new_time:
            speedup = old_time / new_time
            row_increase = (new_rows - old_rows) / old_rows * 100
            
            print(f"Old Method:     {old_time:.3f}s, {old_rows:,} rows")
            print(f"New Method:     {new_time:.3f}s, {new_rows:,} rows")
            print(f"Speedup:        {speedup:.1f}x faster")
            print(f"Data Increase:  {row_increase:.1f}% more data")
            
            if speedup > 1:
                print("✅ NEW METHOD IS FASTER!")
            else:
                print("⚠️  NEW METHOD IS SLOWER")
        
        if ultra_time:
            print(f"Ultra-Fast:     {ultra_time:.3f}s, {ultra_rows:,} rows")
            if new_time and ultra_time < new_time:
                ultra_speedup = new_time / ultra_time
                print(f"Ultra-Fast Speedup: {ultra_speedup:.1f}x faster than new method")
        
        print("\n🎯 OPTIMIZATION SUMMARY:")
        print("- Increased row limit from 1,000 to 50,000 rows")
        print("- Added dtype=str and na_filter=False for speed")
        print("- Implemented multiple loading method fallbacks")
        print("- Added background processing capabilities")
        print("- Enhanced error handling and logging")
        
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")
        except:
            pass

if __name__ == "__main__":
    main()
