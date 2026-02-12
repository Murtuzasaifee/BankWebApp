#!/bin/bash
# ============================================================================
# Good Bank FastAPI Application - Quick Deploy Script for EC2
# ============================================================================
# Usage: bash deploy.sh
# Run this script from the project root directory on your EC2 instance.
# ============================================================================

set -e

echo "============================================"
echo "  Good Bank FastAPI - Deployment Script"
echo "============================================"

# Check we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo "ERROR: Please run this script from the project root directory."
    echo "Expected to find: requirements.txt and app/ folder"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Update SERVER_HOST for EC2 (bind to all interfaces)
if grep -q "SERVER_HOST=127.0.0.1" .env; then
    echo "Updating SERVER_HOST to 0.0.0.0 for EC2 deployment..."
    sed -i 's/SERVER_HOST=127.0.0.1/SERVER_HOST=0.0.0.0/' .env
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or use the management script:"
echo "  bash deployment_scripts/manage.sh start"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
echo "Access your app at: http://${PUBLIC_IP}:8000"
echo ""
