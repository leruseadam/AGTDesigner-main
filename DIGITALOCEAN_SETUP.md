# DigitalOcean Setup Guide for Label Maker App

## Why DigitalOcean?

- **$5-12/month** vs $20+ for PythonAnywhere upgrade
- **Dedicated resources** vs shared hosting
- **Full control** over server optimization
- **Better performance** for file processing and document generation

## Quick Setup (30 minutes)

### Step 1: Create Droplet
1. Sign up at [DigitalOcean](https://digitalocean.com)
2. Create new Droplet:
   - **OS**: Ubuntu 22.04 LTS
   - **Size**: Basic $6/month (1GB RAM, 1 CPU) or $12/month (2GB RAM, 1 CPU)
   - **Region**: Choose closest to your users
   - **Authentication**: SSH key (recommended) or password

### Step 2: Initial Server Setup
```bash
# Connect to your droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Python 3.11
apt install python3.11 python3.11-venv python3.11-dev -y

# Install system dependencies
apt install nginx sqlite3 git -y

# Create app user
adduser --disabled-password --gecos "" labelmaker
usermod -aG sudo labelmaker
```

### Step 3: Deploy Your App
```bash
# Switch to app user
su - labelmaker

# Clone your repository
git clone YOUR_REPO_URL /home/labelmaker/labelmaker
cd /home/labelmaker/labelmaker

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test the app
python app.py
```

### Step 4: Configure Nginx + WSGI
```bash
# Install Gunicorn
pip install gunicorn

# Create WSGI file
cat > wsgi.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add project directory to path
sys.path.insert(0, '/home/labelmaker/labelmaker')

# Change to project directory
os.chdir('/home/labelmaker/labelmaker')

from app import app as application

if __name__ == "__main__":
    application.run()
EOF

# Create systemd service
sudo tee /etc/systemd/system/labelmaker.service << 'EOF'
[Unit]
Description=Label Maker App
After=network.target

[Service]
User=labelmaker
Group=labelmaker
WorkingDirectory=/home/labelmaker/labelmaker
Environment="PATH=/home/labelmaker/labelmaker/venv/bin"
ExecStart=/home/labelmaker/labelmaker/venv/bin/gunicorn --workers 3 --bind unix:/home/labelmaker/labelmaker/labelmaker.sock -m 007 wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/labelmaker << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/labelmaker/labelmaker/labelmaker.sock;
    }

    location /static {
        alias /home/labelmaker/labelmaker/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/labelmaker /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
sudo systemctl start labelmaker
sudo systemctl enable labelmaker
```

## Performance Optimizations

### Memory Optimization
```bash
# Add to /etc/sysctl.conf
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "vm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Database Optimization
```bash
# Create optimized database configuration
cat > database_config.py << 'EOF'
import sqlite3

# Optimize SQLite for performance
def optimize_database(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.close()
EOF
```

## Migration Steps

### 1. Export Data from PythonAnywhere
```bash
# On PythonAnywhere
python export_database_for_pythonanywhere.py
# Download the exported files
```

### 2. Import to DigitalOcean
```bash
# On DigitalOcean droplet
# Upload exported files
python import_pythonanywhere_database.py
```

### 3. Update DNS
- Point your domain to DigitalOcean droplet IP
- Or use DigitalOcean's free subdomain

## Cost Comparison

| Platform | Monthly Cost | Performance | Control |
|----------|-------------|-------------|---------|
| PythonAnywhere Middle | $10 | Shared, Limited | Low |
| PythonAnywhere Next | $20 | Shared, Better | Low |
| DigitalOcean $6 | $6 | Dedicated, Good | High |
| DigitalOcean $12 | $12 | Dedicated, Excellent | High |

## Expected Performance Improvements

- **File uploads**: 3-5x faster
- **Document generation**: 2-3x faster  
- **Page loads**: 2-4x faster
- **Concurrent users**: Much better handling

## Backup Plan

If DigitalOcean doesn't work out:
1. **Railway**: $5/month, easier setup
2. **Koyeb**: $1.61/month, Docker-based
3. **Upgrade PythonAnywhere**: $20/month, no migration needed

## Support

- DigitalOcean has excellent documentation
- Active community forums
- 24/7 support on paid plans
- Your app will be much more responsive

---

**Recommendation**: Start with the $6 DigitalOcean droplet. The performance improvement will be immediately noticeable, and you can always upgrade to the $12 plan if needed.
