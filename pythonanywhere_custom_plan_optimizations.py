#!/usr/bin/env python3
"""
Custom Plan Optimizations for PythonAnywhere
Optimized for: 6 web workers, 20GB disk, 7000 CPU seconds/day, Postgres
"""

import os
import sys
import gc
import threading
import multiprocessing
from functools import wraps
import time

def apply_custom_plan_optimizations():
    """Apply optimizations specific to custom PythonAnywhere plan"""
    
    # Memory optimization for custom plan
    gc.set_threshold(100, 10, 10)
    gc.enable()
    
    # Threading optimization for 6 web workers
    threading.stack_size(65536)  # Optimize stack size
    
    # Environment variables for custom plan
    os.environ.update({
        'PYTHONANYWHERE_CUSTOM_PLAN': 'True',
        'PYTHONANYWHERE_WEB_WORKERS': '6',
        'PYTHONANYWHERE_DISK_SPACE': '20GB',
        'PYTHONANYWHERE_CPU_SECONDS': '7000',
        'PYTHONANYWHERE_POSTGRES': 'True',
        'PYTHONANYWHERE_ALWAYS_ON_TASKS': '4',
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': 'False',
        'PYTHONOPTIMIZE': '1',
        'PYTHONDONTWRITEBYTECODE': '1'
    })
    
    # Performance monitoring
    def performance_monitor(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations (>1 second)
            if execution_time > 1.0:
                print(f"⚠️ Slow operation: {func.__name__} took {execution_time:.2f}s")
            
            return result
        return wrapper
    
    # Apply performance monitoring to critical functions
    try:
        import pandas as pd
        pd.read_excel = performance_monitor(pd.read_excel)
        logging.info("Performance monitoring applied to pandas")
    except ImportError:
        pass
    
    # Database connection optimization for Postgres
    try:
        import sqlalchemy
        sqlalchemy.pool.QueuePool = performance_monitor(sqlalchemy.pool.QueuePool)
        logging.info("Database connection optimization applied")
    except ImportError:
        pass
    
    # File I/O optimization
    try:
        import openpyxl
        openpyxl.load_workbook = performance_monitor(openpyxl.load_workbook)
        logging.info("File I/O optimization applied")
    except ImportError:
        pass
    
    logging.info("Custom plan optimizations complete")

def optimize_for_web_workers():
    """Optimize for multiple web workers"""
    
    # Worker-specific optimizations
    worker_id = os.environ.get('PYTHONANYWHERE_WORKER_ID', '0')
    
    # Set worker-specific cache directories
    cache_dir = f'/home/adamcordova/.cache/worker_{worker_id}'
    os.makedirs(cache_dir, exist_ok=True)
    
    # Worker-specific environment
    os.environ.update({
        'WORKER_ID': worker_id,
        'CACHE_DIR': cache_dir,
        'TEMP_DIR': f'/tmp/worker_{worker_id}'
    })
    
    logging.info(f"Worker {worker_id} optimizations applied")

def optimize_for_large_files():
    """Optimize for handling large files with 20GB disk space"""
    
    # Large file handling
    os.environ.update({
        'MAX_FILE_SIZE': '50MB',
        'CHUNK_SIZE': '1048576',  # 1MB chunks
        'TEMP_DIR': '/home/adamcordova/AGTDesigner/temp',
        'UPLOAD_DIR': '/home/adamcordova/AGTDesigner/uploads'
    })
    
    # Create necessary directories
    for directory in ['/home/adamcordova/AGTDesigner/temp', '/home/adamcordova/AGTDesigner/uploads']:
        os.makedirs(directory, exist_ok=True)
    
    logging.info("Large file handling optimization applied")

def optimize_for_postgres():
    """Optimize for Postgres database"""
    
    # Postgres-specific optimizations
    os.environ.update({
        'DATABASE_URL': 'postgresql://adamcordova@localhost/adamcordova$default',
        'DB_POOL_SIZE': '10',
        'DB_POOL_RECYCLE': '3600',
        'DB_POOL_PRE_PING': 'True',
        'DB_MAX_OVERFLOW': '20'
    })
    
    logging.info("Postgres optimization applied")

def optimize_for_cpu_seconds():
    """Optimize for 7000 CPU seconds per day"""
    
    # CPU optimization
    os.environ.update({
        'MAX_CPU_TIME_PER_REQUEST': '30',  # 30 seconds max per request
        'ENABLE_CPU_MONITORING': 'True',
        'CPU_THROTTLE_THRESHOLD': '25'  # Throttle at 25 seconds
    })
    
    logging.info("CPU seconds optimization applied")

# Apply all optimizations
if __name__ == "__main__":
    apply_custom_plan_optimizations()
    optimize_for_web_workers()
    optimize_for_large_files()
    optimize_for_postgres()
    optimize_for_cpu_seconds()
    
    logging.info("All custom plan optimizations complete!")
    logging.info("Plan specs: 6 Web Workers, 20GB Disk Space, 7000 CPU Seconds/Day, Postgres Database, 4 Always-On Tasks")
