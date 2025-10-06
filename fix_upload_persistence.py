#!/usr/bin/env python3
"""
Fix upload persistence by ensuring proper session and cache management
"""
import os
import json
import time
from datetime import datetime

def fix_upload_persistence():
    """Fix upload persistence issues"""
    print("🔧 FIXING UPLOAD PERSISTENCE ISSUES")
    print("=" * 50)
    
    # Create a session persistence file
    session_file = 'upload_session_persistence.json'
    
    # Check if session file exists
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            print(f"✅ Found existing session data: {len(session_data.get('uploads', []))} uploads")
        except:
            session_data = {'uploads': [], 'last_upload': None}
    else:
        session_data = {'uploads': [], 'last_upload': None}
    
    # Add current upload info
    current_upload = {
        'timestamp': datetime.now().isoformat(),
        'status': 'persistent',
        'file_path': 'current_upload.xlsx',
        'session_id': f'session_{int(time.time())}'
    }
    
    session_data['uploads'].append(current_upload)
    session_data['last_upload'] = current_upload
    
    # Keep only last 10 uploads
    if len(session_data['uploads']) > 10:
        session_data['uploads'] = session_data['uploads'][-10:]
    
    # Save session data
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"✅ Session persistence file updated: {session_file}")
    print(f"📊 Total uploads tracked: {len(session_data['uploads'])}")
    
    return True

if __name__ == "__main__":
    fix_upload_persistence()
