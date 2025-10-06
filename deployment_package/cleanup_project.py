#!/usr/bin/env python3
"""
Clean up project folder by removing unneeded files:
- Summary markdown files (*_SUMMARY.md, *_FIX_SUMMARY.md, etc.)
- Debug files (debug_*.py, debug_*.html, debug_*.docx)
- Test files (test_*.py, test_*.html, test_*.docx, test_*.json)
- Backup files and directories (*.backup, *_backup.*, backup_*)
- Corrupted files (*corrupted*, *.corrupted)
- Old files (*_old.*, *.old)
- Log files (*.log)
- Temporary Word documents (~$*.docx)
- Random database files (not core ones)
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime
import re

def get_file_info(file_path):
    """Get file modification time and size for reporting."""
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

def should_keep_file(file_path):
    """Determine if a file should be kept (return True) or removed (return False)."""
    
    filename = os.path.basename(file_path)
    filepath_str = str(file_path)
    
    # ALWAYS KEEP - Critical application files
    keep_patterns = [
        # Core application files
        r'^app\.py$',
        r'^wsgi\.py$',
        r'^config\.py$',
        r'^requirements\.txt$',
        r'^README\.md$',
        r'^LICENSE$',
        r'^setup\.py$',
        r'^manage\.py$',
        
        # Important directories and their contents
        r'^src/',
        r'^static/',
        r'^templates/',
        r'^uploads/',
        r'^logs/',
        r'^venv/',
        r'^\.venv/',
        r'^node_modules/',
        r'^__pycache__/',
        r'^\.git/',
        
        # Important configuration files
        r'\.gitignore$',
        r'\.env$',
        r'\.env\..*$',
        r'package\.json$',
        r'package-lock\.json$',
        r'yarn\.lock$',
        
        # Our new cleanup script
        r'^cleanup_uploads\.py$',
        r'^cleanup_project\.py$',
        
        # Keep the activate script
        r'^activate_venv\.sh$',
    ]
    
    # Check if file should be kept
    for pattern in keep_patterns:
        if re.search(pattern, filename) or re.search(pattern, filepath_str):
            return True
    
    # REMOVE - Files matching these patterns should be removed
    remove_patterns = [
        # Summary files
        r'.*_SUMMARY\.md$',
        r'.*_FIX_SUMMARY\.md$', 
        r'.*_GUIDE\.md$',
        r'.*_REPORT\.md$',
        r'.*SUMMARY\.md$',
        r'COMPREHENSIVE_.*\.md$',
        r'ENHANCED_.*\.md$',
        r'EMERGENCY_.*\.md$',
        r'CRITICAL_.*\.md$',
        r'NUCLEAR_.*\.md$',
        r'MINI_TEMPLATE_.*\.md$',
        r'JSON_MATCHING_.*\.md$',
        r'THC_CBD_.*\.md$',
        r'TEMPLATE_.*\.md$',
        r'AI_POWERED_.*\.md$',
        r'UPLOAD_.*\.md$',
        r'EXCEL_.*\.md$',
        r'LINEAGE_.*\.md$',
        r'DATABASE_.*\.md$',
        r'PYTHONANYWHERE_.*\.md$',
        
        # Debug files
        r'^debug_.*\.py$',
        r'^debug_.*\.html$',
        r'^debug_.*\.docx$',
        r'^debug_.*\.json$',
        r'^debug_.*\.sh$',
        
        # Test files
        r'^test_.*\.py$',
        r'^test_.*\.html$',
        r'^test_.*\.docx$',
        r'^test_.*\.json$',
        r'^test_.*\.sh$',
        
        # Backup files and directories
        r'.*\.backup$',
        r'.*_backup\..*$',
        r'^backup_.*',
        r'^.*_backup$',
        
        # Corrupted files
        r'.*corrupted.*',
        r'.*\.corrupted$',
        
        # Old files
        r'.*_old\..*$',
        r'.*\.old$',
        
        # Log files
        r'.*\.log$',
        
        # Temporary Word files
        r'^~\$.*\.docx$',
        
        # Fix files
        r'.*_fix\.py$',
        r'^fix_.*\.py$',
        r'alternative_fixes\.py$',
        r'apply_.*_fix.*\.py$',
        r'replace_corrupted.*\.py$',
        
        # Specific unwanted files
        r'^check_.*\.py$',
        r'^add_.*\.py$',
        r'^auto_.*\.py$',
        r'^backfill_.*\.py$',
        r'^build_.*\.sh$',
        r'^deploy_.*\.py$',
        
        # Database files that aren't core
        r'product_database\.db\.backup$',
        r'product_database\.db\.corrupted$',
        r'.*\.db\.backup$',
        r'.*\.db\.corrupted$',
        
        # Spec files
        r'.*\.spec$',
    ]
    
    # Check if file should be removed
    for pattern in remove_patterns:
        if re.search(pattern, filename):
            return False
    
    # Default: keep files that don't match removal patterns
    return True

def cleanup_project():
    """Clean up the project folder."""
    
    project_dir = Path(".")
    if not project_dir.exists():
        print("Project directory does not exist!")
        return
    
    print("=== PROJECT FOLDER CLEANUP ===")
    print(f"Cleaning up: {project_dir.absolute()}")
    
    kept_files = []
    removed_files = []
    removed_dirs = []
    removed_size = 0
    
    # Get all files and directories
    all_items = []
    for root, dirs, files in os.walk("."):
        # Add directories
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            all_items.append(dir_path)
        
        # Add files  
        for file_name in files:
            file_path = Path(root) / file_name
            all_items.append(file_path)
    
    # Sort by depth (deepest first) to handle nested items
    all_items.sort(key=lambda x: (len(x.parts), str(x)), reverse=True)
    
    for item in all_items:
        # Skip if already removed (parent directory was removed)
        if not item.exists():
            continue
            
        item_name = item.name
        relative_path = item.relative_to(".")
        
        # Skip hidden files/directories unless they're important
        if item_name.startswith('.') and item_name not in ['.env', '.gitignore']:
            continue
            
        should_keep = should_keep_file(relative_path)
        
        if should_keep:
            kept_files.append(str(relative_path))
            if len(kept_files) <= 20:  # Only show first 20 for readability
                print(f"✓ Keeping: {relative_path}")
        else:
            # Remove the file/directory
            try:
                if item.is_dir():
                    # Calculate directory size
                    dir_size = 0
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            try:
                                file_path = Path(root) / file
                                dir_size += file_path.stat().st_size
                            except:
                                continue
                    
                    shutil.rmtree(item)
                    removed_size += dir_size
                    removed_dirs.append(str(relative_path))
                    print(f"✗ Removed directory: {relative_path} ({dir_size:,} bytes)")
                else:
                    file_size = item.stat().st_size
                    item.unlink()
                    removed_size += file_size
                    removed_files.append(str(relative_path))
                    if len(removed_files) <= 50:  # Show first 50 removed files
                        print(f"✗ Removed file: {relative_path} ({file_size:,} bytes)")
                    elif len(removed_files) == 51:
                        print("... (additional files removed, see summary)")
                        
            except Exception as e:
                print(f"Error removing {relative_path}: {e}")
    
    # Summary
    print(f"\n=== CLEANUP SUMMARY ===")
    print(f"Files kept: {len(kept_files)}")
    print(f"Files removed: {len(removed_files)}")
    print(f"Directories removed: {len(removed_dirs)}")
    print(f"Total space freed: {removed_size:,} bytes ({removed_size / 1024 / 1024:.1f} MB)")
    
    if removed_dirs:
        print(f"\n=== REMOVED DIRECTORIES ({len(removed_dirs)}) ===")
        for dir_name in sorted(removed_dirs)[:20]:
            print(f"  - {dir_name}")
        if len(removed_dirs) > 20:
            print(f"  ... and {len(removed_dirs) - 20} more directories")
    
    if removed_files:
        print(f"\n=== REMOVED FILES SUMMARY ===")
        
        # Group by file type
        file_types = {}
        for file_path in removed_files:
            if '.' in file_path:
                ext = '.' + file_path.split('.')[-1]
            else:
                ext = 'no extension'
            
            if ext not in file_types:
                file_types[ext] = 0
            file_types[ext] += 1
        
        print("Removed files by type:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ext}: {count} files")
    
    # Show what's left in root directory
    print(f"\n=== REMAINING ROOT DIRECTORY CONTENTS ===")
    root_items = [item for item in Path(".").iterdir() if not item.name.startswith('.')]
    if root_items:
        for item in sorted(root_items):
            if item.is_dir():
                print(f"  📁 {item.name}/")
            else:
                try:
                    size = item.stat().st_size
                    print(f"  📄 {item.name} ({size:,} bytes)")
                except:
                    print(f"  📄 {item.name}")
    else:
        print("  (only hidden files remain)")

if __name__ == "__main__":
    # Confirm before proceeding
    print("This will remove summary files, debug files, test files, backups, and other unneeded files.")
    print("Core application files will be preserved.")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response == 'y':
        cleanup_project()
        print("\n✅ Project cleanup completed!")
    else:
        print("❌ Project cleanup cancelled.")