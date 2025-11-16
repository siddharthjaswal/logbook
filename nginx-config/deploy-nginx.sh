#!/bin/bash
# Nginx Configuration Deployment Script for Logbook API

set -e  # Exit on error

echo "========================================="
echo "Logbook API - Nginx Deployment"
echo "========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo ./deploy-nginx.sh"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/logbook.conf"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: logbook.conf not found in $SCRIPT_DIR"
    exit 1
fi

echo "📋 Config file found: $CONFIG_FILE"
echo ""

# Detect nginx directory structure
if [ -d /etc/nginx/sites-available ]; then
    echo "📁 Detected Debian/Ubuntu nginx structure (sites-available/sites-enabled)"
    NGINX_AVAILABLE="/etc/nginx/sites-available/logbook.conf"
    NGINX_ENABLED="/etc/nginx/sites-enabled/logbook.conf"
    USE_SYMLINK=true
elif [ -d /etc/nginx/conf.d ]; then
    echo "📁 Detected RHEL/CentOS nginx structure (conf.d)"
    NGINX_CONF="/etc/nginx/conf.d/logbook.conf"
    USE_SYMLINK=false
else
    echo "❌ Error: Could not detect nginx directory structure"
    exit 1
fi

echo ""

# Backup existing configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ "$USE_SYMLINK" = true ]; then
    if [ -f "$NGINX_AVAILABLE" ]; then
        echo "💾 Backing up existing configuration..."
        cp "$NGINX_AVAILABLE" "${NGINX_AVAILABLE}.backup.${TIMESTAMP}"
        echo "   Backup: ${NGINX_AVAILABLE}.backup.${TIMESTAMP}"
    fi

    # Copy new configuration
    echo "📝 Deploying new configuration..."
    cp "$CONFIG_FILE" "$NGINX_AVAILABLE"

    # Remove old symlink if exists
    rm -f "$NGINX_ENABLED"

    # Create new symlink
    ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
    echo "   Deployed: $NGINX_AVAILABLE"
    echo "   Enabled: $NGINX_ENABLED"
else
    if [ -f "$NGINX_CONF" ]; then
        echo "💾 Backing up existing configuration..."
        cp "$NGINX_CONF" "${NGINX_CONF}.backup.${TIMESTAMP}"
        echo "   Backup: ${NGINX_CONF}.backup.${TIMESTAMP}"
    fi

    # Copy new configuration
    echo "📝 Deploying new configuration..."
    cp "$CONFIG_FILE" "$NGINX_CONF"
    echo "   Deployed: $NGINX_CONF"
fi

echo ""

# Check if SSL certificates exist
echo "🔐 Checking SSL certificates..."
if [ -f /etc/letsencrypt/live/api.travlogue.in/fullchain.pem ]; then
    echo "   ✅ SSL certificates found"
else
    echo "   ⚠️  WARNING: SSL certificates not found at /etc/letsencrypt/live/api.travlogue.in/"
    echo "   You may need to run: certbot --nginx -d api.travlogue.in"
    echo "   Or update the certificate paths in the nginx config"
fi

echo ""

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Nginx configuration test FAILED!"
    echo "   Please check the errors above and fix the configuration."
    echo "   Your old configuration has been backed up."
    exit 1
fi

echo ""
echo "✅ Nginx configuration test PASSED!"
echo ""

# Ask for confirmation before reloading
read -p "Reload nginx now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Reloading nginx..."
    systemctl reload nginx

    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================="
        echo "✅ Deployment successful!"
        echo "========================================="
        echo ""
        echo "Next steps:"
        echo "1. Check nginx logs: sudo tail -f /var/log/nginx/logbook_access.log"
        echo "2. Check backend logs: sudo journalctl -u logbook -f"
        echo "3. Test endpoint: curl -I https://api.travlogue.in/api/v1/auth/google"
        echo "4. Try signing in from your Android app"
        echo ""
    else
        echo "❌ Failed to reload nginx"
        exit 1
    fi
else
    echo "⏸️  Nginx NOT reloaded. Run 'sudo systemctl reload nginx' manually when ready."
fi
