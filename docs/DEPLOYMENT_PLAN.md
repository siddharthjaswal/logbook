# Logbook API - Production Deployment Guide

## Overview

Complete production deployment guide for **api.travlogue.in** using existing **Hetzner server** (currently hosting digitalgears.in and triplecaptain.in), **GoDaddy domain**, and **systemd service**.

---

## Your Infrastructure

- **Domain**: travlogue.in (GoDaddy)
- **Server**: Hetzner VPS (shared with digitalgears.in, triplecaptain.in)
- **Existing Services**:
  - digitalgears.in → Docker Container (Port 3001)
  - triplecaptain.in → Docker Container (Port 3000)
- **Stack**: FastAPI, PostgreSQL, Uvicorn, Nginx, Let's Encrypt SSL

---

## Multi-Service Architecture

```
Hetzner Server (Single IP Address)
    ↓
Nginx (Port 80/443) - Reverse Proxy
    ├─ digitalgears.in → Docker Container (Port 3001)
    ├─ triplecaptain.in → Docker Container (Port 3000)
    └─ api.travlogue.in → Uvicorn/FastAPI (Port 8000) ← NEW
        ↓
PostgreSQL (Port 5432)
```

**Key Points:**
- ✅ One server hosts multiple domains/services
- ✅ Each domain has its own Nginx virtual host configuration
- ✅ Separate SSL certificates per domain
- ✅ Nginx routes traffic based on domain name
- ✅ FastAPI runs as systemd service (not Docker)

---

## Port Allocation

| Domain/Service | Port | Type | Container/Service Name |
|----------------|------|------|------------------------|
| digitalgears.in | 3001 | Docker | digitalgears |
| triplecaptain.in | 3000 | Docker | triple-captain |
| **api.travlogue.in** | **8000** | **Systemd** | **logbook** |
| PostgreSQL | 5432 | Native | postgresql |

---

## Phase 1: DNS Setup (GoDaddy)

### Step 1: Get Your Hetzner Server IP

You already know this (same IP used by digitalgears.in and triplecaptain.in):

```bash
# SSH to your Hetzner server
ssh deploy@YOUR_HETZNER_IP

# Confirm your public IP
curl ifconfig.me
```

### Step 2: Configure DNS on GoDaddy

1. Log in to [GoDaddy](https://dcc.godaddy.com/domains)
2. Select `travlogue.in` → Manage DNS
3. Add A Record for API subdomain (using SAME IP as other domains):

```
Type    Name    Value                      TTL
A       api     YOUR_HETZNER_IP            600
```

4. Wait 5-10 minutes for DNS propagation

### Step 3: Verify DNS

```bash
# On your local machine
dig api.travlogue.in

# Should return the SAME IP as:
dig digitalgears.in
dig triplecaptain.in

# All three should point to your Hetzner server
```

---

## Phase 2: Server Preparation

### Step 1: Check Current Setup

```bash
# SSH to server (as deploy user)
ssh deploy@YOUR_HETZNER_IP

# Check what's running
docker ps

# Check Nginx configs
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/

# Check ports in use
sudo lsof -i :3000   # triplecaptain
sudo lsof -i :3001   # digitalgears
sudo lsof -i :8000   # Should be free for Logbook

# Check existing SSL certificates
sudo certbot certificates
```

### Step 2: Install Additional Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3.11 (for FastAPI)
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL (if not already installed)
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Build essentials (for some Python packages)
sudo apt install -y build-essential

# Git (if not already installed)
git --version || sudo apt install -y git

# Verify installations
python3.11 --version
psql --version
```

---

## Phase 3: PostgreSQL Database Setup

### Step 1: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql
```

In PostgreSQL prompt:

```sql
-- Create production database
CREATE DATABASE logbook_prod;

-- Create database user with strong password
CREATE USER logbook_user WITH ENCRYPTED PASSWORD 'STRONG_SECURE_PASSWORD_HERE';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE logbook_prod TO logbook_user;

-- Connect to database and grant schema permissions
\c logbook_prod
GRANT ALL ON SCHEMA public TO logbook_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO logbook_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO logbook_user;

-- Exit
\q
```

### Step 2: Test Database Connection

```bash
# Test connection
psql -h localhost -U logbook_user -d logbook_prod

# If successful, you'll see:
# logbook_prod=>

# Exit with:
\q
```

---

## Phase 4: GitHub Setup

### Step 1: Verify GitHub CLI (Already Installed)

```bash
# Check if gh is installed
gh --version

# If not installed:
# curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
# echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
# sudo apt update && sudo apt install gh
```

### Step 2: Authenticate (if not already done)

```bash
gh auth login
# Follow prompts to authenticate with GitHub
```

---

## Phase 5: Deploy Application Code

### Step 1: Create Application Directory

```bash
# Create directory structure
mkdir -p /home/deploy/logbook
cd /home/deploy/logbook

# Clone repository
git clone https://github.com/siddharthjaswal/logbook.git
cd logbook

# Verify code
ls -la
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### Step 3: Create Production Environment File

```bash
# Create .env file
nano /home/deploy/logbook/logbook/.env
```

Add the following (replace placeholders):

```env
# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://logbook_user:YOUR_DB_PASSWORD@localhost:5432/logbook_prod

# Security (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(64))")
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE

# Google OAuth
GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# CORS (update with your frontend domains)
CORS_ORIGINS=["https://travlogue.in","https://www.travlogue.in","https://app.travlogue.in"]

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Logbook API
VERSION=1.0.0

# OAuth Redirect (update when frontend is ready)
OAUTH_REDIRECT_URL=https://travlogue.in/auth/callback
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Step 4: Run Database Migrations

```bash
# Activate virtual environment
source /home/deploy/logbook/logbook/venv/bin/activate

# Navigate to project root
cd /home/deploy/logbook/logbook

# Run Alembic migrations
alembic upgrade head

# Verify tables were created
psql -h localhost -U logbook_user -d logbook_prod -c "\dt"
```

### Step 5: Test Application

```bash
# Test run (from /home/deploy/logbook/logbook)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test:
curl http://YOUR_SERVER_IP:8000/health
curl http://YOUR_SERVER_IP:8000/docs

# Stop test (Ctrl+C)
```

---

## Phase 6: Systemd Service Setup

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/logbook.service
```

Add the following:

```ini
[Unit]
Description=Logbook FastAPI Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/logbook/logbook
Environment="PATH=/home/deploy/logbook/logbook/venv/bin"
EnvironmentFile=/home/deploy/logbook/logbook/.env

ExecStart=/home/deploy/logbook/logbook/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --proxy-headers

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/deploy/logbook/logbook

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable logbook

# Start service
sudo systemctl start logbook

# Check status
sudo systemctl status logbook

# View logs
sudo journalctl -u logbook -f

# Test locally
curl http://localhost:8000/health
```

---

## Phase 7: Nginx Configuration

### Step 1: Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/logbook-api
```

Add the following:

```nginx
# Upstream to Logbook FastAPI app
upstream logbook_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.travlogue.in;

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://api.travlogue.in$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.travlogue.in;

    # SSL certificates (will be created by certbot)
    ssl_certificate /etc/letsencrypt/live/api.travlogue.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.travlogue.in/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/api.travlogue.in/chain.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Max upload size
    client_max_body_size 10M;

    # Logging
    access_log /var/log/nginx/logbook-api-access.log;
    error_log /var/log/nginx/logbook-api-error.log;

    # Proxy to FastAPI
    location / {
        proxy_pass http://logbook_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
```

### Step 2: Enable Site (Don't Reload Yet)

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/logbook-api /etc/nginx/sites-enabled/

# Don't reload Nginx yet - need SSL certificate first
```

---

## Phase 8: SSL Certificate Setup

### Step 1: Temporarily Configure for HTTP Only

```bash
# Edit the config
sudo nano /etc/nginx/sites-available/logbook-api
```

Comment out the HTTPS server block temporarily:

```nginx
# Upstream
upstream logbook_backend {
    server 127.0.0.1:8000;
}

# HTTP only (for Let's Encrypt)
server {
    listen 80;
    listen [::]:80;
    server_name api.travlogue.in;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        root /var/www/html;
        index index.html;
    }
}

# Comment out HTTPS block
# server {
#     listen 443 ssl http2;
#     ...
# }
```

Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 2: Get SSL Certificate

```bash
# Get certificate (certbot should already be installed)
sudo certbot --nginx -d api.travlogue.in

# Follow prompts:
# - Enter email for renewal notifications
# - Agree to terms
# - Certbot will configure Nginx
```

### Step 3: Restore Full Nginx Config

```bash
# Edit again
sudo nano /etc/nginx/sites-available/logbook-api
```

Restore the full configuration (from Phase 7, Step 1).

Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Verify SSL

```bash
# Check certificate
sudo certbot certificates

# Test HTTPS
curl https://api.travlogue.in/health
curl https://api.travlogue.in/docs

# Test redirect
curl -I http://api.travlogue.in
# Should return 301 redirect to HTTPS
```

---

## Phase 9: Deployment Script

### Create Deployment Script

```bash
nano /home/deploy/logbook/deploy.sh
```

Add:

```bash
#!/bin/bash
set -e

echo "🚀 Starting Logbook API deployment..."

# Navigate to project
cd /home/deploy/logbook/logbook

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --upgrade

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Restart application
echo "🔄 Restarting application..."
sudo systemctl restart logbook

# Wait for service to start
sleep 3

# Check status
sudo systemctl status logbook --no-pager

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo "✅ Deployment complete!"
echo "🌐 API available at: https://api.travlogue.in"
```

Make executable:

```bash
chmod +x /home/deploy/logbook/deploy.sh
```

### Deploy Updates

```bash
# Future deployments:
/home/deploy/logbook/deploy.sh
```

---

## Monitoring & Maintenance

### View All Services

```bash
# Check all running services
docker ps                          # Docker containers
sudo systemctl status logbook      # Logbook API
sudo systemctl status postgresql   # Database
sudo systemctl status nginx        # Nginx

# Check all SSL certificates
sudo certbot certificates
```

### Service Logs

```bash
# Logbook API logs
sudo journalctl -u logbook -f

# Nginx logs
sudo tail -f /var/log/nginx/logbook-api-access.log
sudo tail -f /var/log/nginx/logbook-api-error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Docker container logs (other services)
docker logs -f triple-captain
docker logs -f digitalgears
```

### Health Checks

```bash
# Test all services locally
curl http://localhost:8000/health        # Logbook API
curl http://localhost:3000/api/health    # Triple Captain
curl http://localhost:3001               # Digital Gears

# Test externally
curl https://api.travlogue.in/health
curl https://triplecaptain.in/api/health
curl https://digitalgears.in
```

### Restart Services

```bash
# Restart specific service
sudo systemctl restart logbook

# Reload Nginx (no downtime)
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# Restart Docker containers
docker restart triple-captain
docker restart digitalgears

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Update Bruno Configuration

Update your Bruno environment variables:

```json
{
  "baseUrl": "https://api.travlogue.in/api/v1",
  "accessToken": ""
}
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u logbook -n 50 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Check permissions
ls -la /home/deploy/logbook/logbook

# Check environment file
cat /home/deploy/logbook/logbook/.env
```

### Database Connection Errors

```bash
# Test connection
psql -h localhost -U logbook_user -d logbook_prod

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep logbook
```

### Nginx 502 Bad Gateway

```bash
# Check if app is running
sudo systemctl status logbook
curl http://localhost:8000/health

# Check Nginx logs
sudo tail -f /var/log/nginx/logbook-api-error.log

# Test upstream
sudo netstat -tuln | grep 8000
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew --cert-name api.travlogue.in

# Test renewal
sudo certbot renew --dry-run
```

---

## Server Resource Overview

### Current Allocation

| Service | Port | Type | Memory | Notes |
|---------|------|------|--------|-------|
| digitalgears.in | 3001 | Docker | ~150MB | Next.js app |
| triplecaptain.in | 3000 | Docker | ~150MB | Next.js app |
| **api.travlogue.in** | **8000** | **Systemd** | **~200MB** | **FastAPI (4 workers)** |
| PostgreSQL | 5432 | Native | ~50MB | Database |
| Nginx | 80/443 | Native | ~10MB | Reverse proxy |

### Monitor Resources

```bash
# Overall server resources
htop

# Container resources
docker stats

# Logbook API resources
ps aux | grep uvicorn

# Disk usage
df -h

# Memory usage
free -h
```

---

## Security Checklist

- ✅ SSH key authentication (deploy user)
- ✅ UFW firewall (ports 22, 80, 443)
- ✅ SSL/TLS with Let's Encrypt
- ✅ Security headers in Nginx
- ✅ Systemd service isolation
- ✅ Environment variables secured
- ✅ Database user with limited permissions
- ✅ No root access for application

---

## Backup Strategy

### What to Backup

1. **Database** - PostgreSQL logbook_prod
2. **Environment File** - /home/deploy/logbook/logbook/.env
3. **Nginx Config** - /etc/nginx/sites-available/logbook-api

### Backup Script

```bash
# Create backup script
nano /home/deploy/backup-logbook.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/home/deploy/backups/logbook"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U logbook_user logbook_prod | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup environment file
cp /home/deploy/logbook/logbook/.env $BACKUP_DIR/env_$DATE

# Backup Nginx config
sudo cp /etc/nginx/sites-available/logbook-api $BACKUP_DIR/nginx_$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_*" -mtime +7 -delete
find $BACKUP_DIR -name "nginx_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /home/deploy/backup-logbook.sh

# Schedule with cron (daily at 3 AM)
crontab -e
# Add:
0 3 * * * /home/deploy/backup-logbook.sh >> /var/log/logbook-backup.log 2>&1
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] DNS configured (api.travlogue.in → server IP)
- [ ] Server accessible via SSH (deploy user)
- [ ] Python 3.11 installed
- [ ] PostgreSQL installed and configured
- [ ] Port 8000 available
- [ ] Nginx running

### Application Setup
- [ ] Code cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Database migrations run
- [ ] Systemd service created and running

### Nginx & SSL
- [ ] Nginx config created
- [ ] Nginx config enabled
- [ ] SSL certificate obtained
- [ ] HTTPS working
- [ ] Health endpoint accessible

### Post-Deployment
- [ ] Test API endpoints with Bruno
- [ ] Check logs for errors
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Update frontend .env with API URL

---

## Quick Reference

### Daily Operations

```bash
# Check API status
sudo systemctl status logbook
curl https://api.travlogue.in/health

# View logs
sudo journalctl -u logbook -f

# Restart API
sudo systemctl restart logbook

# Deploy updates
/home/deploy/logbook/deploy.sh
```

### Emergency Commands

```bash
# Stop API
sudo systemctl stop logbook

# Check what's using port 8000
sudo lsof -i :8000

# Kill process on port 8000
sudo kill -9 $(sudo lsof -t -i:8000)

# Check server resources
htop
df -h
free -h
```

---

## Production URLs

- **API Base**: https://api.travlogue.in/api/v1
- **API Docs**: https://api.travlogue.in/docs
- **Health Check**: https://api.travlogue.in/health
- **Frontend** (when ready): https://travlogue.in
- **Existing Services**:
  - https://digitalgears.in
  - https://triplecaptain.in

---

**Last Updated**: 2025-11-11
**Status**: Ready for Deployment
**Domain**: api.travlogue.in
**Server**: Hetzner VPS (Shared)
**Stack**: FastAPI + PostgreSQL + Nginx + Systemd

🚀 Ready to deploy Logbook API alongside existing services!
