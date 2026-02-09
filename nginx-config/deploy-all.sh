#!/bin/bash
# deploy-all.sh - Deploy Nginx config for both Backend and Frontend

set -e

echo "========================================="
echo "Travlogue Deployment - Nginx"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo ./deploy-all.sh"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect structure
if [ -d /etc/nginx/sites-available ]; then
    echo "📁 Detected Debian/Ubuntu structure"
    # Backend
    cp "$SCRIPT_DIR/logbook.conf" /etc/nginx/sites-available/
    ln -sf /etc/nginx/sites-available/logbook.conf /etc/nginx/sites-enabled/
    # Frontend
    cp "$SCRIPT_DIR/travlogue-web.conf" /etc/nginx/sites-available/
    ln -sf /etc/nginx/sites-available/travlogue-web.conf /etc/nginx/sites-enabled/
else
    echo "📁 Detected conf.d structure"
    cp "$SCRIPT_DIR/logbook.conf" /etc/nginx/conf.d/
    cp "$SCRIPT_DIR/travlogue-web.conf" /etc/nginx/conf.d/
fi

echo "🧪 Testing nginx..."
nginx -t

echo "🔄 Reloading nginx..."
systemctl reload nginx

echo "✅ Done!"
echo "Next: sudo certbot --nginx -d travlogue.in -d api.travlogue.in"
