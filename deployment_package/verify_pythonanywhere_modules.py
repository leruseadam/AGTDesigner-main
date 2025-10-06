#!/usr/bin/env python3.11
"""
Verify all critical modules exist on PythonAnywhere
Creates any missing files needed for the Flask app to work
"""

import os
import sys
from pathlib import Path

def create_missing_files():
    """Create any missing critical files"""
    
    project_dir = "/home/adamcordova/AGTDesigner"
    if not os.path.exists(project_dir):
        print(f"❌ Project directory not found: {project_dir}")
        return False
    
    os.chdir(project_dir)
    print(f"📁 Working in: {project_dir}")
    
    # Critical files that must exist
    critical_files = {
        'src/__init__.py': '# Source module initialization\n',
        'src/core/__init__.py': '# Core module initialization\n',
        'src/core/data/__init__.py': '# Data module initialization\n',
        'src/core/formatting/__init__.py': '# Formatting module initialization\n',
        'src/core/generation/__init__.py': '# Generation module initialization\n',
        'src/core/utils/__init__.py': '# Utils module initialization\n',
    }
    
    files_created = []
    files_verified = []
    
    for file_path, content in critical_files.items():
        full_path = Path(file_path)
        
        if full_path.exists():
            print(f"✅ {file_path} - exists")
            files_verified.append(file_path)
        else:
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with content
            full_path.write_text(content)
            print(f"🔧 {file_path} - created")
            files_created.append(file_path)
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Verified: {len(files_verified)} files")
    print(f"   🔧 Created: {len(files_created)} files")
    
    if files_created:
        print(f"\n📝 Created files:")
        for file in files_created:
            print(f"   - {file}")
    
    return True

def verify_critical_modules():
    """Verify that all critical modules can be imported"""
    
    print(f"\n🐍 Testing Python imports...")
    
    # Add current directory to Python path
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    modules_to_test = [
        ('flask', 'Flask framework'),
        ('pandas', 'Data processing'),
        ('openpyxl', 'Excel processing'), 
        ('docxtpl', 'Document templates'),
        ('sqlite3', 'Database'),
        ('src', 'Source module'),
        ('src.core', 'Core module'),
        ('src.core.data', 'Data module'),
        ('src.core.data.product_database', 'Product database module'),
        ('src.core.data.json_matcher', 'JSON matcher module'),
    ]
    
    import_success = []
    import_failures = []
    
    for module, description in modules_to_test:
        try:
            __import__(module)
            print(f"   ✅ {module} - {description}")
            import_success.append(module)
        except ImportError as e:
            print(f"   ❌ {module} - IMPORT ERROR: {e}")
            import_failures.append((module, str(e)))
        except Exception as e:
            print(f"   ⚠️  {module} - OTHER ERROR: {e}")
            import_failures.append((module, str(e)))
    
    print(f"\n📊 Import Results:")
    print(f"   ✅ Successful: {len(import_success)}")
    print(f"   ❌ Failed: {len(import_failures)}")
    
    if import_failures:
        print(f"\n❌ Import failures:")
        for module, error in import_failures:
            print(f"   - {module}: {error}")
        return False
    
    return True

def test_flask_app():
    """Test Flask app import specifically"""
    
    print(f"\n🧪 Testing Flask app import...")
    
    try:
        from app import app
        print(f"   ✅ Flask app imported successfully")
        print(f"   📱 App name: {getattr(app, 'name', 'unknown')}")
        return True
    except Exception as e:
        print(f"   ❌ Flask app import failed: {e}")
        
        # Try to provide more specific error info
        import traceback
        print(f"\n🔍 Detailed error traceback:")
        traceback.print_exc()
        return False

def main():
    """Run all verification steps"""
    
    print("🔍 PythonAnywhere Module Verification")
    print("=" * 50)
    
    # Step 1: Create missing files
    if not create_missing_files():
        return False
    
    # Step 2: Verify module imports
    imports_ok = verify_critical_modules()
    
    # Step 3: Test Flask app specifically
    flask_ok = test_flask_app()
    
    print(f"\n🎯 FINAL RESULTS:")
    print("=" * 20)
    
    if imports_ok and flask_ok:
        print("✅ All modules verified successfully!")
        print("💡 Your Flask app should work now. Try reloading your web app.")
        return True
    else:
        print("❌ Some modules failed verification.")
        print("💡 Check the errors above and install missing packages:")
        print("   python3.11 -m pip install --user flask pandas openpyxl python-docx docxtpl")
        return False

if __name__ == "__main__":
    main()