#!/bin/bash
# ============================================================================
# Good Bank FastAPI Application - Deploy & Run Script
# ============================================================================
# Usage:
#   Local:      bash deployment_scripts/deploy.sh local
#   Production: bash deployment_scripts/deploy.sh production
#   Auto:       bash deployment_scripts/deploy.sh (detects environment)
# ============================================================================

set -e

ENVIRONMENT="${1:-auto}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================"
echo "  Good Bank FastAPI - Deploy & Run Script"
echo "============================================"
echo ""

cd "$PROJECT_ROOT"

# Check we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo "ERROR: Please run this script from the project root directory."
    echo "Expected to find: requirements.txt and app/ folder"
    exit 1
fi

# Auto-detect environment if not specified
if [ "$ENVIRONMENT" = "auto" ]; then
    # Try to detect if we're on EC2
    if curl -s -m 1 http://169.254.169.254/latest/meta-data/ >/dev/null 2>&1; then
        ENVIRONMENT="production"
        echo "Auto-detected: EC2 instance (production environment)"
    else
        ENVIRONMENT="local"
        echo "Auto-detected: Local environment"
    fi
else
    echo "Environment: $ENVIRONMENT"
fi

# Validate environment
if [ "$ENVIRONMENT" != "local" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "ERROR: Invalid environment '$ENVIRONMENT'. Use 'local' or 'production'."
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

echo ""
echo "Step 1: Configuring environment..."

# Update .env file based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "  - Setting ENVIRONMENT=production"
    sed -i.bak 's/^ENVIRONMENT=.*/ENVIRONMENT=production/' .env
    echo "  - Setting SERVER_HOST=0.0.0.0"
    sed -i.bak 's/^SERVER_HOST=.*/SERVER_HOST=0.0.0.0/' .env
    echo "  - Setting DEBUG_MODE=false"
    sed -i.bak 's/^DEBUG_MODE=.*/DEBUG_MODE=false/' .env
    rm -f .env.bak
else
    echo "  - Setting ENVIRONMENT=local"
    sed -i.bak 's/^ENVIRONMENT=.*/ENVIRONMENT=local/' .env
    echo "  - Setting SERVER_HOST=127.0.0.1"
    sed -i.bak 's/^SERVER_HOST=.*/SERVER_HOST=127.0.0.1/' .env
    echo "  - Setting DEBUG_MODE=true"
    sed -i.bak 's/^DEBUG_MODE=.*/DEBUG_MODE=true/' .env
    rm -f .env.bak
fi

echo ""
echo "Step 2: Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  - Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "  - Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "  - Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "Step 3: Starting application..."

# Stop any existing instance
if [ -f "app.pid" ]; then
    OLD_PID=$(cat app.pid)
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "  - Stopping existing instance (PID: $OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
    rm -f app.pid
fi

# Start the application
HOST=$(grep "^SERVER_HOST=" .env | cut -d '=' -f2)
PORT=$(grep "^SERVER_PORT=" .env | cut -d '=' -f2)
PORT=${PORT:-8000}

echo "  - Starting FastAPI application..."
nohup uvicorn app.main:app --host "$HOST" --port "$PORT" > app.log 2>&1 &
APP_PID=$!
echo $APP_PID > app.pid

# Wait and verify startup
sleep 3
if kill -0 "$APP_PID" 2>/dev/null; then
    echo ""
    echo "============================================"
    echo "  Deployment & Startup Complete!"
    echo "============================================"
    echo ""
    echo "Application Details:"
    echo "  - Environment: $ENVIRONMENT"
    echo "  - PID: $APP_PID"
    echo "  - Host: $HOST"
    echo "  - Port: $PORT"
    echo ""

    if [ "$ENVIRONMENT" = "production" ]; then
        PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
        echo "Access your app at: http://${PUBLIC_IP}:${PORT}"
    else
        echo "Access your app at: http://127.0.0.1:${PORT}"
    fi

    echo ""
    echo "Useful commands:"
    echo "  - View logs:    tail -f app.log"
    echo "  - Stop app:     bash deployment_scripts/manage.sh stop"
    echo "  - Restart app:  bash deployment_scripts/manage.sh restart"
    echo "  - Check status: bash deployment_scripts/manage.sh status"
    echo ""
else
    echo ""
    echo "ERROR: Application failed to start!"
    echo "Check logs: tail -f app.log"
    rm -f app.pid
    exit 1
fi
