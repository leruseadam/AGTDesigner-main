#!/usr/bin/env python3
"""
PythonAnywhere Production Logging Configuration
Fixes BlockingIOError issues by using non-blocking logging
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def configure_production_logging():
    """Configure logging for PythonAnywhere production environment"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid conflicts
    root_logger.handlers.clear()
    
    # Create file handler with rotation to prevent large log files
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB max file size
        backupCount=5,          # Keep 5 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Create console handler (non-blocking)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce verbosity of specific loggers that might cause issues
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Set specific loggers to reduce noise
    logging.getLogger('src.core.data.excel_processor').setLevel(logging.WARNING)
    logging.getLogger('src.core.data.product_database').setLevel(logging.WARNING)
    
    print("✅ Production logging configured successfully")
    print(f"📁 Log file: {log_file}")
    print("🔇 Reduced verbosity for production environment")

if __name__ == "__main__":
    configure_production_logging()
