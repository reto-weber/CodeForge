#!/bin/bash

# Script to setup Let's Encrypt SSL certificates for CodeForge
set -e

# Configuration
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"

echo "🔐 Setting up Let's Encrypt SSL certificates for CodeForge"

# Check if domain is provided
if [ -z "$DOMAIN" ]; then
    echo "❌ Error: DOMAIN environment variable is required"
    echo "Usage: DOMAIN=yourdomain.com EMAIL=your@email.com ./scripts/setup_letsencrypt.sh"
    exit 1
fi

# Check if email is provided
if [ -z "$EMAIL" ]; then
    echo "❌ Error: EMAIL environment variable is required"
    echo "Usage: DOMAIN=yourdomain.com EMAIL=your@email.com ./scripts/setup_letsencrypt.sh"
    exit 1
fi

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    
    # Detect OS and install certbot
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y certbot
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S certbot
    else
        echo "❌ Unsupported package manager. Please install certbot manually."
        echo "Visit: https://certbot.eff.org/instructions"
        exit 1
    fi
else
    echo "✅ certbot is already installed"
fi

# Stop any running FastAPI server on port 80 or 443
echo "🛑 Stopping any running web servers..."
sudo pkill -f "uvicorn.*main:app" || true

# Use certbot standalone mode to get certificates
echo "🔒 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

# Check if certificates were created successfully
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
    echo "✅ Let's Encrypt certificates obtained successfully!"
    echo "📜 Certificate: $CERT_PATH"
    echo "🔑 Private key: $KEY_PATH"
    
    # Set up automatic renewal
    echo "⚙️  Setting up automatic certificate renewal..."
    
    # Create renewal script
    sudo tee /etc/cron.d/certbot-renew > /dev/null <<EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx || pkill -HUP -f 'uvicorn.*main:app' || true"
EOF
    
    echo "🔄 Automatic renewal configured (runs twice daily)"
    
    echo ""
    echo "🚀 Setup complete! You can now start your FastAPI server:"
    echo "   export DOMAIN=$DOMAIN"
    echo "   export SESSION_SECRET_KEY=\"your-session-secret\""
    echo "   sudo $(which python3) src/main.py"
    echo ""
    echo "   Or with uvicorn directly:"
    echo "   sudo uvicorn main:app --host 0.0.0.0 --port 443 --ssl-certfile $CERT_PATH --ssl-keyfile $KEY_PATH"
    echo ""
    echo "📝 Note: You need sudo to bind to port 443"
    echo "🌐 Your site will be available at: https://$DOMAIN"
    
else
    echo "❌ Failed to obtain Let's Encrypt certificates"
    echo "Please check the error messages above and try again"
    exit 1
fi

