#!/bin/bash

# Helper script to run CodeForge with HTTPS support
set -e

# Default values
PORT=${PORT:-8000}
HTTPS_PORT=${HTTPS_PORT:-443}
DOMAIN=${DOMAIN:-localhost}
SESSION_SECRET_KEY=${SESSION_SECRET_KEY:-"your-session-secret"}

echo "🚀 CodeForge HTTPS Runner"
echo "========================"

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --domain DOMAIN     Set domain name (default: localhost)"
    echo "  --email EMAIL       Email for Let's Encrypt registration"
    echo "  --http              Run HTTP only (port $PORT)"
    echo "  --https             Run HTTPS only (requires certificates)"
    echo "  --local-ssl         Generate and use local self-signed certificates"
    echo "  --letsencrypt       Setup Let's Encrypt certificates"
    echo "  --help              Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  DOMAIN              Domain name"
    echo "  EMAIL               Email for Let's Encrypt"
    echo "  SESSION_SECRET_KEY  Session secret key"
    echo "  PORT                HTTP port (default: 8000)"
    echo "  HTTPS_PORT          HTTPS port (default: 443)"
    echo ""
    echo "Examples:"
    echo "  $0 --http                                    # HTTP only"
    echo "  $0 --local-ssl                              # Generate local SSL and run HTTPS"
    echo "  $0 --domain example.com --email me@example.com --letsencrypt  # Setup Let's Encrypt"
    echo "  DOMAIN=example.com $0 --https               # Run with existing Let's Encrypt certs"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --http)
            MODE="http"
            shift
            ;;
        --https)
            MODE="https"
            shift
            ;;
        --local-ssl)
            MODE="local-ssl"
            shift
            ;;
        --letsencrypt)
            MODE="letsencrypt"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Export environment variables
export DOMAIN="$DOMAIN"
export SESSION_SECRET_KEY="$SESSION_SECRET_KEY"

case "${MODE:-auto}" in
    "http")
        echo "🌐 Starting HTTP server on port $PORT"
        cd src
        uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
        ;;
    
    "local-ssl")
        echo "🔐 Generating local SSL certificates..."
        ./scripts/generate_ssl_certs.sh
        echo "🌐 Starting HTTPS server with local certificates on port 8443"
        cd src
        uvicorn main:app --host 0.0.0.0 --port 8443 --reload
        ;;
    
    "letsencrypt")
        if [ -z "$EMAIL" ]; then
            echo "❌ Email is required for Let's Encrypt setup"
            echo "Usage: $0 --domain $DOMAIN --email your@email.com --letsencrypt"
            exit 1
        fi
        echo "🔐 Setting up Let's Encrypt for domain: $DOMAIN"
        export EMAIL="$EMAIL"
        ./scripts/setup_letsencrypt.sh
        ;;
    
    "https")
        # Check for Let's Encrypt certificates first
        LETSENCRYPT_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        LETSENCRYPT_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
        LOCAL_CERT="src/ssl/server.crt"
        LOCAL_KEY="src/ssl/server.key"
        
        if [ -f "$LETSENCRYPT_CERT" ] && [ -f "$LETSENCRYPT_KEY" ]; then
            echo "🔐 Starting HTTPS server with Let's Encrypt certificates"
            echo "🌐 Domain: $DOMAIN"
            echo "📋 Note: This requires sudo to bind to port 443"
            cd src
            sudo uvicorn main:app --host 0.0.0.0 --port "$HTTPS_PORT" \
                --ssl-certfile "$LETSENCRYPT_CERT" \
                --ssl-keyfile "$LETSENCRYPT_KEY"
        elif [ -f "$LOCAL_CERT" ] && [ -f "$LOCAL_KEY" ]; then
            echo "🔐 Starting HTTPS server with local certificates on port 8443"
            cd src
            uvicorn main:app --host 0.0.0.0 --port 8443 \
                --ssl-certfile "$LOCAL_CERT" \
                --ssl-keyfile "$LOCAL_KEY"
        else
            echo "❌ No SSL certificates found!"
            echo "Available options:"
            echo "  $0 --local-ssl     # Generate local self-signed certificates"
            echo "  $0 --letsencrypt   # Setup Let's Encrypt (requires domain and email)"
            exit 1
        fi
        ;;
    
    "auto"|*)
        # Auto-detect best configuration
        LETSENCRYPT_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        LOCAL_CERT="src/ssl/server.crt"
        
        if [ "$DOMAIN" != "localhost" ] && [ -f "$LETSENCRYPT_CERT" ]; then
            echo "🔐 Auto-detected Let's Encrypt certificates"
            echo "📋 Note: This requires sudo to bind to port 443"
            cd src
            sudo uvicorn main:app --host 0.0.0.0 --port "$HTTPS_PORT"
        elif [ -f "$LOCAL_CERT" ]; then
            echo "🔐 Auto-detected local SSL certificates"
            cd src
            uvicorn main:app --host 0.0.0.0 --port 8443
        else
            echo "🌐 No SSL certificates found, starting HTTP server"
            cd src
            uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
        fi
        ;;
esac

