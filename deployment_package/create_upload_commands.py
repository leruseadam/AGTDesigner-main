#!/usr/bin/env python3
"""
Upload PostgreSQL Files to PythonAnywhere
Creates the files directly on PythonAnywhere with correct content
"""

def create_upload_commands():
    """Create commands to upload files to PythonAnywhere"""
    
    print("📁 Upload Commands for PythonAnywhere")
    print("=" * 50)
    print()
    print("Run these commands on PythonAnywhere:")
    print()
    
    # Test file
    print("1️⃣ Create test file:")
    print("cat > test_pythonanywhere_postgresql.py << 'EOF'")
    with open('test_pythonanywhere_postgresql.py', 'r') as f:
        print(f.read())
    print("EOF")
    print()
    
    # Config file
    print("2️⃣ Create config file:")
    print("cat > pythonanywhere_postgresql_config.py << 'EOF'")
    with open('pythonanywhere_postgresql_config.py', 'r') as f:
        print(f.read())
    print("EOF")
    print()
    
    # Migration file
    print("3️⃣ Create migration file:")
    print("cat > migrate_to_pythonanywhere_postgresql.py << 'EOF'")
    with open('migrate_to_pythonanywhere_postgresql.py', 'r') as f:
        print(f.read())
    print("EOF")
    print()
    
    print("4️⃣ Make files executable:")
    print("chmod +x test_pythonanywhere_postgresql.py")
    print("chmod +x migrate_to_pythonanywhere_postgresql.py")
    print()
    
    print("5️⃣ Install PostgreSQL client:")
    print("pip3.11 install --user psycopg2-binary")
    print()
    
    print("6️⃣ Test connection:")
    print("python3.11 test_pythonanywhere_postgresql.py")
    print()
    
    print("7️⃣ Migrate data:")
    print("python3.11 migrate_to_pythonanywhere_postgresql.py")

if __name__ == "__main__":
    create_upload_commands()
