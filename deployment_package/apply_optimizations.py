#!/usr/bin/env python3
"""
Apply performance optimizations to existing Flask app
"""

def apply_optimizations_to_app():
    """Apply all performance optimizations"""
    
    try:
        # Import optimization modules
        from pythonanywhere_optimizations import *
        from fast_upload_handler import create_fast_upload_handler
        from fast_docx_generator import create_fast_generator_routes
        
        print("✅ Performance optimizations loaded")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to load optimizations: {e}")
        return False

# Auto-apply optimizations when imported
if __name__ != "__main__":
    apply_optimizations_to_app()
