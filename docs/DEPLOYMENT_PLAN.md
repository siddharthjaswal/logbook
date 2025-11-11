# Logbook API Deployment Plan
## Hosting on Private Server with travlogue.in

---

## 🎯 Deployment Overview

**Domain:** `travlogue.in`
**API Subdomain:** `api.travlogue.in`
**Server:** Private VPS with Nginx
**Database:** PostgreSQL
**Application:** FastAPI + Uvicorn (systemd service)
**SSL:** Let's Encrypt (Certbot)

### URL Structure
```
Production API: https://api.travlogue.in/api/v1
Health Check:   https://api.travlogue.in/health
API Docs:       https://api.travlogue.in/docs
```

---

## 📋 Prerequisites Checklist

- [ ] Server with Ubuntu/Debian (or similar)
- [ ] Root or sudo access
- [ ] Domain `travlogue.in` with DNS access
- [ ] Nginx already installed and running
- [ ] Basic firewall configured (UFW)
- [ ] SSH key-based authentication set up

---

## 🏗️ Architecture

```
Internet
   ↓
DNS (travlogue.in)
   ↓
Nginx (Port 80/443) → SSL Termination
   ↓
Reverse Proxy → Uvicorn (Port 8000)
   ↓
FastAPI Application
   ↓
PostgreSQL (Port 5432)
```

---

## 📝 Step-by-Step Deployment Guide

### Phase 1: DNS Configuration

#### 1.1 Add DNS Records
Login to your domain registrar and add:

```
Type    Name    Value               TTL
A       api     YOUR_SERVER_IP      3600
AAAA    api     YOUR_SERVER_IPv6    3600  (if available)
```

**Verify DNS propagation:**
```bash
dig api.travlogue.in
# or
nslookup api.travlogue.in
```

---

### Phase 2: Server Preparation

#### 2.1 Update System
```bash
sudo apt update
sudo apt upgrade -y
```

#### 2.2 Install Dependencies
```bash
# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Git (if not installed)
sudo apt install -y git

# Build essentials (for some Python packages)
sudo apt install -y build-essential libpq-dev
```

#### 2.3 Create Application User
```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash logbook
sudo usermod -aG sudo logbook  # Only if needed for specific tasks

# Set up directory structure
sudo mkdir -p /var/www/logbook
sudo chown logbook:logbook /var/www/logbook
```

---

### Phase 3: PostgreSQL Database Setup

#### 3.1 Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE logbook_prod;
CREATE USER logbook_user WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE logbook_prod TO logbook_user;

# Grant schema permissions
\c logbook_prod
GRANT ALL ON SCHEMA public TO logbook_user;

# Exit
\q
```

#### 3.2 Configure PostgreSQL for Remote Access (if needed)
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add/modify:
listen_addresses = 'localhost'  # Keep localhost only for security

# Edit pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add:
local   logbook_prod    logbook_user                    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 3.3 Test Database Connection
```bash
psql -h localhost -U logbook_user -d logbook_prod
# Enter password when prompted
# \q to exit
```

---

### Phase 4: GitHub CLI Setup

#### 4.1 Install GitHub CLI
```bash
# Add GitHub CLI repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Install
sudo apt update
sudo apt install gh -y
```

#### 4.2 Authenticate GitHub CLI
```bash
# Login to GitHub
gh auth login

# Follow prompts:
# - Choose: GitHub.com
# - Protocol: HTTPS
# - Authenticate: Login with a web browser (or paste token)
# - Select scopes: repo, workflow
```

#### 4.3 Set Up Deploy Keys (Alternative Method)
```bash
# Generate SSH key for deployment
ssh-keygen -t ed25519 -C "logbook-deploy" -f ~/.ssh/logbook_deploy

# Add to GitHub
cat ~/.ssh/logbook_deploy.pub
# Go to GitHub → Repository → Settings → Deploy keys → Add deploy key
# Paste the public key

# Configure SSH
nano ~/.ssh/config
# Add:
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/logbook_deploy
```

---

### Phase 5: Application Deployment

#### 5.1 Clone Repository
```bash
# Switch to logbook user
sudo su - logbook

# Navigate to app directory
cd /var/www/logbook

# Clone repository
git clone https://github.com/siddharthjaswal/logbook.git
cd logbook

# Or if using SSH:
# git clone git@github.com:siddharthjaswal/logbook.git
```

#### 5.2 Set Up Python Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### 5.3 Create Production Environment File
```bash
# Create .env file
nano /var/www/logbook/logbook/.env
```

Add the following content:
```env
# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://logbook_user:STRONG_PASSWORD_HERE@localhost:5432/logbook_prod

# Security
SECRET_KEY=generate-a-very-long-random-secret-key-here
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# CORS (update with your frontend domain)
CORS_ORIGINS=["https://travlogue.in", "https://www.travlogue.in"]

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Logbook API
VERSION=1.0.0

# OAuth Redirect
OAUTH_REDIRECT_URL=https://travlogue.in/auth/callback
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### 5.4 Run Database Migrations
```bash
# Activate virtual environment if not already active
source /var/www/logbook/logbook/venv/bin/activate

# Run Alembic migrations
cd /var/www/logbook/logbook
alembic upgrade head
```

#### 5.5 Test Application Locally
```bash
# Test run
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Visit http://YOUR_SERVER_IP:8000/docs
# Press Ctrl+C to stop
```

---

### Phase 6: Systemd Service Setup

#### 6.1 Create Systemd Service File
```bash
sudo nano /etc/systemd/system/logbook.service
```

Add the following content:
```ini
[Unit]
Description=Logbook FastAPI Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=logbook
Group=logbook
WorkingDirectory=/var/www/logbook/logbook
Environment="PATH=/var/www/logbook/logbook/venv/bin"
EnvironmentFile=/var/www/logbook/logbook/.env
ExecStart=/var/www/logbook/logbook/venv/bin/uvicorn app.main:app \
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
ReadWritePaths=/var/www/logbook/logbook

[Install]
WantedBy=multi-user.target
```

#### 6.2 Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable logbook

# Start service
sudo systemctl start logbook

# Check status
sudo systemctl status logbook

# View logs
sudo journalctl -u logbook -f
```

---

### Phase 7: Nginx Configuration

#### 7.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/logbook-api
```

Add the following content:
```nginx
# Upstream configuration
upstream logbook_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.travlogue.in;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.travlogue.in;

    # SSL Configuration (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/api.travlogue.in/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/api.travlogue.in/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/logbook-api-access.log;
    error_log /var/log/nginx/logbook-api-error.log;

    # Max upload size (for file uploads if needed)
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://logbook_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;

        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if you add them later)
    location /static {
        alias /var/www/logbook/logbook/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 7.2 Enable Site
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/logbook-api /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

### Phase 8: SSL Certificate Setup

#### 8.1 Obtain SSL Certificate with Certbot
```bash
# Stop Nginx temporarily if needed
# sudo systemctl stop nginx

# Request certificate
sudo certbot --nginx -d api.travlogue.in

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Certbot will automatically update your Nginx config
```

#### 8.2 Test SSL Certificate
```bash
# Check certificate
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

#### 8.3 Set Up Auto-Renewal
```bash
# Certbot should set this up automatically
# Verify cron job exists
sudo systemctl status certbot.timer

# Manual renewal command (if needed)
sudo certbot renew
```

---

### Phase 9: Firewall Configuration

#### 9.1 Configure UFW (if not already done)
```bash
# Check firewall status
sudo ufw status

# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
# Or individually:
# sudo ufw allow 80/tcp
# sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Verify
sudo ufw status numbered
```

---

### Phase 10: Deployment Workflow

#### 10.1 Initial Deployment Checklist
- [ ] DNS configured and propagated
- [ ] PostgreSQL database created and accessible
- [ ] Application code cloned from GitHub
- [ ] Virtual environment created and dependencies installed
- [ ] `.env` file configured with production values
- [ ] Database migrations run successfully
- [ ] Systemd service created and running
- [ ] Nginx configured and running
- [ ] SSL certificate obtained and active
- [ ] Firewall configured correctly

#### 10.2 Deployment Script
Create a deployment script for future updates:

```bash
sudo nano /var/www/logbook/deploy.sh
```

```bash
#!/bin/bash
set -e

echo "🚀 Starting Logbook API deployment..."

# Navigate to project directory
cd /var/www/logbook/logbook

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

# Check status
sleep 2
sudo systemctl status logbook --no-pager

echo "✅ Deployment complete!"
echo "🌐 API available at: https://api.travlogue.in"
```

Make it executable:
```bash
sudo chmod +x /var/www/logbook/deploy.sh
sudo chown logbook:logbook /var/www/logbook/deploy.sh
```

#### 10.3 Update Workflow
```bash
# Switch to logbook user
sudo su - logbook

# Run deployment script
/var/www/logbook/deploy.sh
```

---

### Phase 11: Monitoring & Maintenance

#### 11.1 View Logs
```bash
# Application logs
sudo journalctl -u logbook -f

# Nginx access logs
sudo tail -f /var/log/nginx/logbook-api-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/logbook-api-error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### 11.2 Health Checks
```bash
# Check service status
sudo systemctl status logbook

# Check if API is responding
curl https://api.travlogue.in/health

# Check API docs
curl https://api.travlogue.in/docs

# Check database connection
sudo -u logbook psql -h localhost -U logbook_user -d logbook_prod -c "SELECT 1;"
```

#### 11.3 Useful Commands
```bash
# Restart application
sudo systemctl restart logbook

# Stop application
sudo systemctl stop logbook

# Start application
sudo systemctl start logbook

# Reload Nginx (without downtime)
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep uvicorn
```

---

### Phase 12: Security Hardening

#### 12.1 Additional Security Measures
```bash
# Install fail2ban (brute force protection)
sudo apt install fail2ban -y

# Configure fail2ban for nginx
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/logbook-api-error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/logbook-api-access.log
```

```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status
```

#### 12.2 Set Up Automated Backups
```bash
# Create backup script
sudo nano /usr/local/bin/backup-logbook.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/logbook"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U logbook_user logbook_prod | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Backup env file
cp /var/www/logbook/logbook/.env $BACKUP_DIR/env_backup_$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_backup_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-logbook.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add line:
0 2 * * * /usr/local/bin/backup-logbook.sh >> /var/log/logbook-backup.log 2>&1
```

---

## 🧪 Testing Checklist

### After Deployment
- [ ] Health endpoint: `curl https://api.travlogue.in/health`
- [ ] API docs accessible: `https://api.travlogue.in/docs`
- [ ] Database connection working
- [ ] SSL certificate valid
- [ ] HTTPS redirect working
- [ ] CORS configured correctly
- [ ] Test API endpoints with Bruno
- [ ] Check application logs for errors
- [ ] Verify systemd service is running
- [ ] Test authentication flow (Google OAuth)

---

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
sudo journalctl -u logbook -n 50 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Check permissions
ls -la /var/www/logbook/logbook
```

#### Database Connection Errors
```bash
# Test connection
psql -h localhost -U logbook_user -d logbook_prod

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf
```

#### Nginx 502 Bad Gateway
```bash
# Check if application is running
sudo systemctl status logbook

# Check Nginx error logs
sudo tail -f /var/log/nginx/logbook-api-error.log

# Test upstream connection
curl http://localhost:8000/health
```

#### SSL Certificate Issues
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal -d api.travlogue.in

# Check Nginx SSL config
sudo nginx -t
```

---

## 📊 Performance Optimization

### Uvicorn Worker Configuration
Adjust workers based on CPU cores:
```bash
# In /etc/systemd/system/logbook.service
# Workers = (2 x CPU cores) + 1
ExecStart=/var/www/logbook/logbook/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \  # Adjust based on your server
    --worker-class uvicorn.workers.UvicornWorker
```

### PostgreSQL Tuning
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Adjust based on your RAM:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
```

---

## 📝 Environment Variables Reference

```env
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional with defaults
ENVIRONMENT=production
API_V1_PREFIX=/api/v1
PROJECT_NAME=Logbook API
VERSION=1.0.0
CORS_ORIGINS=["https://travlogue.in"]
```

---

## 🎯 Post-Deployment

### Update Bruno Base URL
```json
{
  "baseUrl": "https://api.travlogue.in/api/v1",
  "accessToken": ""
}
```

### Update Frontend Configuration
```javascript
// config.js or .env.production
VITE_API_BASE_URL=https://api.travlogue.in/api/v1
```

---

## 📚 Useful Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Certbot](https://certbot.eff.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [GitHub CLI](https://cli.github.com/)

---

## ✅ Deployment Complete!

Your Logbook API should now be running at:
- **API Base URL**: `https://api.travlogue.in/api/v1`
- **API Documentation**: `https://api.travlogue.in/docs`
- **Health Check**: `https://api.travlogue.in/health`

Happy deploying! 🚀
