#!/usr/bin/env python3
"""
Clean up uploads folder and keep only currently needed database files.
This script will:
1. Keep essential database files
2. Keep the most recent "A Greener Today - Bothell" Excel file  
3. Keep important subdirectories
4. Remove old/unused files to free up space
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

def get_file_info(file_path):
    """Get file modification time and size for comparison."""
    try:
        stat = os.stat(file_path)
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'mtime_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error getting info for {file_path}: {e}")
        return None

def cleanup_uploads():
    """Clean up the uploads folder."""
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("uploads directory does not exist!")
        return
    
    print("=== UPLOADS FOLDER CLEANUP ===")
    print(f"Cleaning up: {uploads_dir.absolute()}")
    
    # Files/patterns to KEEP
    keep_patterns = [
        # Essential database files - main and AGT_Bothell
        "product_database.db",
        "product_database.db-shm", 
        "product_database.db-wal",
        "product_database_AGT_Bothell.db",
        "product_database_AGT_Bothell.db-shm",
        "product_database_AGT_Bothell.db-wal",
        
        # Important subdirectories
        "product_database/",
        "strain_data/",
    ]
    
    # Find the most recent "A Greener Today - Bothell" Excel file
    bothell_files = []
    for excel_file in uploads_dir.glob("*.xlsx"):
        if "A Greener Today" in excel_file.name and "Bothell" in excel_file.name:
            info = get_file_info(excel_file)
            if info:
                bothell_files.append(info)
    
    # Sort by modification time (newest first)
    bothell_files.sort(key=lambda x: x['mtime'], reverse=True)
    
    most_recent_bothell = None
    if bothell_files:
        most_recent_bothell = bothell_files[0]['name']
        keep_patterns.append(most_recent_bothell)
        print(f"✓ Keeping most recent Bothell file: {most_recent_bothell} ({bothell_files[0]['mtime_str']})")
    
    # Get all files in uploads directory
    all_items = list(uploads_dir.iterdir())
    
    kept_files = []
    removed_files = []
    removed_size = 0
    
    for item in all_items:
        item_name = item.name
        
        # Skip hidden files like .DS_Store 
        if item_name.startswith('.'):
            continue
            
        # Check if this item should be kept
        should_keep = False
        
        for pattern in keep_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if item.is_dir() and item_name == pattern.rstrip('/'):
                    should_keep = True
                    break
            else:
                # File pattern  
                if item_name == pattern:
                    should_keep = True
                    break
        
        if should_keep:
            kept_files.append(item_name)
            print(f"✓ Keeping: {item_name}")
        else:
            # Remove the file/directory
            try:
                if item.is_dir():
                    dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    shutil.rmtree(item)
                    removed_size += dir_size
                    print(f"✗ Removed directory: {item_name} ({dir_size:,} bytes)")
                else:
                    file_size = item.stat().st_size
                    item.unlink()
                    removed_size += file_size
                    print(f"✗ Removed file: {item_name} ({file_size:,} bytes)")
                removed_files.append(item_name)
            except Exception as e:
                print(f"Error removing {item_name}: {e}")
    
    # Summary
    print(f"\n=== CLEANUP SUMMARY ===")
    print(f"Files/directories kept: {len(kept_files)}")
    print(f"Files/directories removed: {len(removed_files)}")
    print(f"Space freed: {removed_size:,} bytes ({removed_size / 1024 / 1024:.1f} MB)")
    
    print(f"\n=== KEPT FILES ===")
    for item in sorted(kept_files):
        print(f"  - {item}")
    
    if removed_files:
        print(f"\n=== REMOVED FILES ===") 
        for item in sorted(removed_files):
            print(f"  - {item}")
    
    # Show what's left after cleanup
    print(f"\n=== FINAL UPLOADS DIRECTORY CONTENTS ===")
    remaining_items = list(uploads_dir.iterdir())
    if remaining_items:
        total_size = 0
        for item in sorted(remaining_items):
            if item.name.startswith('.'):
                continue
            try:
                if item.is_dir():
                    dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    total_size += dir_size
                    print(f"  📁 {item.name}/ ({dir_size:,} bytes)")
                else:
                    file_size = item.stat().st_size
                    total_size += file_size
                    file_info = get_file_info(item)
                    print(f"  📄 {item.name} ({file_size:,} bytes, {file_info['mtime_str'] if file_info else 'unknown date'})")
            except Exception as e:
                print(f"  ⚠️  {item.name} (error reading: {e})")
        
        print(f"\nTotal remaining size: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)")
    else:
        print("  (empty)")

if __name__ == "__main__":
    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Confirm before proceeding
    print("This will clean up the uploads folder and remove old/unused files.")
    print("Essential database files and the most recent Bothell Excel file will be kept.")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response == 'y':
        cleanup_uploads()
        print("\n✅ Cleanup completed!")
    else:
        print("❌ Cleanup cancelled.")