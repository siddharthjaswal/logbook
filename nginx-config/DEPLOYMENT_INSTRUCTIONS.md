# Nginx Configuration Deployment Instructions

## Problem
Requests to `https://api.travlogue.in/api/v1/auth/google` are timing out because nginx is not properly configured to proxy requests to the FastAPI backend.

## Solution
Deploy the nginx configuration file to your production server.

## Step 1: Find Current Nginx Configuration

On your production server, run these commands to understand the current setup:

```bash
# Find all nginx config files
sudo find /etc/nginx -name "*.conf" -type f

# List sites-enabled
ls -la /etc/nginx/sites-enabled/

# Check main nginx.conf
sudo cat /etc/nginx/nginx.conf | grep include

# Check if there's a default site
sudo cat /etc/nginx/sites-enabled/default 2>/dev/null || echo "No default site"
```

## Step 2: Deploy the Configuration

### Option A: If `/etc/nginx/sites-available/` exists (Debian/Ubuntu style)

```bash
# Copy the configuration file to your server first
# (You can use scp, or copy-paste the content from logbook.conf)

# Create the config file
sudo nano /etc/nginx/sites-available/logbook.conf
# Paste the content from nginx-config/logbook.conf

# Create symlink to enable the site
sudo ln -sf /etc/nginx/sites-available/logbook.conf /etc/nginx/sites-enabled/logbook.conf

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

### Option B: If sites-available doesn't exist (direct conf.d style)

```bash
# Create the config file directly
sudo nano /etc/nginx/conf.d/logbook.conf
# Paste the content from nginx-config/logbook.conf

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

## Step 3: Verify SSL Certificates

Make sure your SSL certificates are in the correct location:

```bash
# Check if Let's Encrypt certificates exist
sudo ls -la /etc/letsencrypt/live/api.travlogue.in/

# If certificates don't exist, you may need to run:
# sudo certbot --nginx -d api.travlogue.in
```

If the SSL certificate paths are different, update the nginx config:
- `ssl_certificate` path
- `ssl_certificate_key` path

## Step 4: Verify Backend is Running

```bash
# Check if FastAPI is running on port 8000
sudo systemctl status logbook

# Test backend locally
curl http://localhost:8000/

# Check what's listening on port 8000
sudo lsof -i :8000
```

## Step 5: Test the Configuration

After deploying and reloading nginx:

```bash
# Test from server
curl -X POST https://api.travlogue.in/api/v1/auth/google \
  -H "Content-Type: application/json" \
  -d '{"idToken":"test"}' \
  -v

# Check nginx access logs
sudo tail -f /var/log/nginx/logbook_access.log

# Check nginx error logs
sudo tail -f /var/log/nginx/logbook_error.log

# Check FastAPI logs
sudo journalctl -u logbook -f
```

## Step 6: Test from Android App

Once nginx is configured and reloaded, try signing in from your Android app again.

## Troubleshooting

### If nginx test fails:
```bash
# Check syntax errors
sudo nginx -t

# View detailed error
sudo journalctl -xe
```

### If still getting 504 timeout:
```bash
# Make sure backend is running
sudo systemctl status logbook

# Check if backend is listening
sudo netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
```

### If getting SSL errors:
```bash
# Renew certificates
sudo certbot renew

# Check certificate expiry
sudo certbot certificates
```

## Quick Deployment Script

```bash
#!/bin/bash
# Save as deploy-nginx.sh

echo "Deploying nginx configuration..."

# Backup existing config if it exists
if [ -f /etc/nginx/sites-enabled/logbook.conf ]; then
    sudo cp /etc/nginx/sites-enabled/logbook.conf /etc/nginx/sites-enabled/logbook.conf.backup.$(date +%Y%m%d_%H%M%S)
fi

# Deploy new config
sudo cp logbook.conf /etc/nginx/sites-available/logbook.conf
sudo ln -sf /etc/nginx/sites-available/logbook.conf /etc/nginx/sites-enabled/logbook.conf

# Test configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration test passed. Reloading nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully!"
    echo ""
    echo "Testing endpoint..."
    curl -I https://api.travlogue.in/api/v1/auth/google
else
    echo "❌ Configuration test failed. Check errors above."
    exit 1
fi
```

Make it executable: `chmod +x deploy-nginx.sh`
Run it: `./deploy-nginx.sh`
