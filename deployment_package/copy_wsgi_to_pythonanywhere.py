#!/usr/bin/env python3
"""
Script to copy the local wsgi_pythonanywhere_python311.py to the PythonAnywhere
web app's WSGI file location (/var/www/www_agtpricetags_com_wsgi.py).
Includes backup and verification.
"""

import os
import shutil
import sys
import time

def copy_wsgi_file():
    """Copies the local WSGI file to the PythonAnywhere web app location."""
    print("🚀 Copying WSGI File to PythonAnywhere Location...")
    print("=" * 50)

    local_wsgi_path = os.path.join(os.getcwd(), 'wsgi_pythonanywhere_python311.py')
    pythonanywhere_wsgi_path = '/var/www/www_agtpricetags_com_wsgi.py'
    backup_path = f"{pythonanywhere_wsgi_path}.backup_{time.strftime('%Y%m%d%H%M%S')}"

    if not os.path.exists(local_wsgi_path):
        print(f"❌ Error: Local WSGI file not found at {local_wsgi_path}")
        sys.exit(1)

    print(f"Source WSGI file: {local_wsgi_path}")
    print(f"Destination WSGI file: {pythonanywhere_wsgi_path}")

    try:
        # Create a backup of the existing WSGI file
        if os.path.exists(pythonanywhere_wsgi_path):
            print(f"Creating backup of existing WSGI file to: {backup_path}")
            shutil.copy2(pythonanywhere_wsgi_path, backup_path)
            print("✅ Backup created successfully.")
        else:
            print("⚠️ No existing WSGI file found at destination, skipping backup.")

        # Copy the new WSGI file
        shutil.copy2(local_wsgi_path, pythonanywhere_wsgi_path)
        print(f"✅ Successfully copied {local_wsgi_path} to {pythonanywhere_wsgi_path}")

        # Verify content
        with open(pythonanywhere_wsgi_path, 'r') as f:
            content = f.read()
            
        if "application = app" in content and "DB_HOST" in content:
            print("✅ Verified WSGI file contains 'application = app' and 'DB_HOST' environment variable.")
        else:
            print("❌ Verification failed: WSGI file content does not look correct.")
            print("   Please check the content of the copied file manually.")
            sys.exit(1)

        print("\n🎉 WSGI file copied and verified successfully!")
        print("💡 Remember to reload your web app on PythonAnywhere's Web tab to apply changes.")

    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {pythonanywhere_wsgi_path}.")
        print("   💡 You might need to run this script with `sudo` if you have the necessary permissions,")
        print("      or manually copy the file using the PythonAnywhere 'Files' interface.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    copy_wsgi_file()