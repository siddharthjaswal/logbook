# Nginx Configuration for Logbook API

## Problem Identified

The Android app authentication was failing with timeout errors because **nginx was not configured to proxy `/api/v1/auth/google` requests to the FastAPI backend**.

### Symptoms
- Android app times out after 30 seconds when trying to authenticate
- `curl` requests to `https://api.travlogue.in/api/v1/auth/google` timeout
- NO requests appear in nginx access logs
- Backend is running correctly (port 8000)
- Root endpoint `https://api.travlogue.in/` works fine

### Root Cause
The file `/etc/nginx/sites-enabled/logbook.conf` doesn't exist on the production server, meaning nginx has no configuration to route API requests to the FastAPI backend.

## Solution

This directory contains the complete nginx configuration needed to fix the issue.

## Files

### 1. `logbook.conf`
The nginx configuration file that:
- Redirects HTTP to HTTPS
- Proxies all requests to FastAPI backend on port 8000
- Sets up proper SSL/TLS
- Configures appropriate timeouts (60s)
- Adds security headers
- Sets up logging

### 2. `deploy-nginx.sh` ⭐ Recommended
Automated deployment script that:
- Detects your nginx directory structure automatically
- Backs up existing configuration
- Deploys new configuration
- Checks SSL certificates
- Tests configuration before applying
- Reloads nginx safely

**Usage:**
```bash
# Copy the entire nginx-config directory to your server
scp -r nginx-config/ sid@api.travlogue.in:~/

# SSH into your server
ssh sid@api.travlogue.in

# Run the deployment script
cd ~/nginx-config
sudo ./deploy-nginx.sh
```

### 3. `DEPLOYMENT_INSTRUCTIONS.md`
Detailed manual deployment instructions for those who prefer step-by-step commands or need to troubleshoot.

## Quick Start

**Option 1: Automated (Recommended)**
```bash
sudo ./deploy-nginx.sh
```

**Option 2: Manual**
```bash
# Copy config file
sudo cp logbook.conf /etc/nginx/sites-available/logbook.conf

# Enable the site
sudo ln -sf /etc/nginx/sites-available/logbook.conf /etc/nginx/sites-enabled/logbook.conf

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## After Deployment

1. **Verify nginx is routing requests:**
   ```bash
   sudo tail -f /var/log/nginx/logbook_access.log
   ```

2. **Test the endpoint:**
   ```bash
   curl -X POST https://api.travlogue.in/api/v1/auth/google \
     -H "Content-Type: application/json" \
     -d '{"idToken":"test"}' \
     -v
   ```
   You should get a 400 error (invalid token) instead of timeout - this means nginx is working!

3. **Try signing in from Android app** - Authentication should now work

## Configuration Details

### Backend Connection
```nginx
upstream logbook_backend {
    server 127.0.0.1:8000;
}
```
Connects to your FastAPI application running on localhost:8000

### SSL Certificates
```nginx
ssl_certificate /etc/letsencrypt/live/api.travlogue.in/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.travlogue.in/privkey.pem;
```
Uses Let's Encrypt certificates. If your certificates are in a different location, update these paths.

### Timeouts
```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```
Set to 60 seconds to handle Google OAuth verification (which can take a few seconds).

## Troubleshooting

### If deployment fails

1. **Check nginx syntax:**
   ```bash
   sudo nginx -t
   ```

2. **Check backend is running:**
   ```bash
   sudo systemctl status logbook
   curl http://localhost:8000/
   ```

3. **Check SSL certificates:**
   ```bash
   sudo ls -la /etc/letsencrypt/live/api.travlogue.in/
   ```

4. **View nginx error logs:**
   ```bash
   sudo tail -50 /var/log/nginx/error.log
   ```

### If still getting timeouts after deployment

1. **Check if nginx reloaded:**
   ```bash
   sudo systemctl status nginx
   ```

2. **Check if requests are reaching nginx:**
   ```bash
   sudo tail -f /var/log/nginx/logbook_access.log
   ```
   You should see POST requests to /api/v1/auth/google

3. **Check if backend is receiving requests:**
   ```bash
   sudo journalctl -u logbook -f
   ```
   You should see log messages about Google authentication

## Need Help?

Refer to `DEPLOYMENT_INSTRUCTIONS.md` for detailed manual deployment steps and additional troubleshooting.
