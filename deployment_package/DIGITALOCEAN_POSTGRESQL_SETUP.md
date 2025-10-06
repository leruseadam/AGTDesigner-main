# DigitalOcean PostgreSQL Setup Guide

## Step 1: Create Droplet
1. Go to [DigitalOcean](https://digitalocean.com)
2. Create new Droplet
3. Choose Ubuntu 22.04 LTS
4. Size: $6/month (1GB RAM, 1 CPU)
5. Add SSH key
6. Create droplet

## Step 2: Install PostgreSQL
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install PostgreSQL
apt install postgresql postgresql-contrib -y

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql
```

## Step 3: Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE labelmaker;
CREATE USER labelmaker WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE labelmaker TO labelmaker;
ALTER USER labelmaker CREATEDB;
\q
```

## Step 4: Configure Remote Access
```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/postgresql.conf

# Find and uncomment:
listen_addresses = '*'

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add line:
host    all             all             0.0.0.0/0               md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Step 5: Configure Firewall
```bash
# Allow PostgreSQL port
ufw allow 5432
ufw enable
```

## Step 6: Test Connection
```bash
# From your local machine
psql -h your-droplet-ip -U labelmaker -d labelmaker
```

## Cost: $6/month
- 1GB RAM
- 1 CPU
- 25GB SSD
- Full control
- Best performance
