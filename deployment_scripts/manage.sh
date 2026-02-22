#!/bin/bash
# ============================================================================
# Banking Web Application with FastAPI - Management Script
# ============================================================================
# Usage: bash deployment_scripts/manage.sh {start|stop|restart|status|logs}
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/app.log"
VENV_DIR="$APP_DIR/venv"
ENV_FILE="$APP_DIR/.env"

# Get app name from .env if available
APP_NAME="Banking App"
if [ -f "$ENV_FILE" ]; then
    APP_NAME=$(grep "^APP_NAME=" "$ENV_FILE" | cut -d '=' -f2 || echo "Banking App")
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get configuration from .env
get_config() {
    if [ -f "$ENV_FILE" ]; then
        HOST=$(grep "^SERVER_HOST=" "$ENV_FILE" | cut -d '=' -f2)
        PORT=$(grep "^SERVER_PORT=" "$ENV_FILE" | cut -d '=' -f2)
        ENV=$(grep "^ENVIRONMENT=" "$ENV_FILE" | cut -d '=' -f2)
        HOST=${HOST:-0.0.0.0}
        PORT=${PORT:-8000}
        ENV=${ENV:-local}
    else
        HOST="0.0.0.0"
        PORT="8000"
        ENV="unknown"
    fi
    
    # Failsafe: if running in production but using localhost, force 0.0.0.0
    if [ "$ENV" = "production" ] && [ "$HOST" = "127.0.0.1" ]; then
        HOST="0.0.0.0"
    fi
}

# Get public or local IP
get_access_url() {
    get_config
    if [ "$ENV" = "production" ]; then
        PUBLIC_IP=$(curl -s -m 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
        echo "http://${PUBLIC_IP}:${PORT}"
    else
        echo "http://127.0.0.1:${PORT}"
    fi
}

start() {
    echo "Starting $APP_NAME FastAPI Application..."

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}Application is already running (PID: $PID)${NC}"
            echo "Access at: $(get_access_url)"
            return 0
        else
            echo "Removing stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi

    # Check for .env file
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}ERROR: .env file not found!${NC}"
        echo "Please copy .env.example to .env and configure it."
        return 1
    fi

    # Check for virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}ERROR: Virtual environment not found!${NC}"
        echo "Please run: bash deployment_scripts/deploy.sh"
        return 1
    fi

    # Start application
    cd "$APP_DIR"
    get_config
    source "$VENV_DIR/bin/activate"

    echo "  - Host: $HOST"
    echo "  - Port: $PORT"
    echo "  - Environment: $ENV"

    nohup uvicorn app.main:app --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
    APP_PID=$!
    echo $APP_PID > "$PID_FILE"

    # Verify startup
    sleep 2
    if kill -0 "$APP_PID" 2>/dev/null; then
        echo -e "${GREEN}Application started successfully (PID: $APP_PID)${NC}"
        echo "Access at: $(get_access_url)"
        echo ""
        echo "Tip: View logs with: bash $0 logs"
    else
        echo -e "${RED}ERROR: Application failed to start${NC}"
        echo "Check logs: tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    echo "Stopping $APP_NAME FastAPI Application..."

    # Try PID file first
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "  - Stopping process (PID: $PID)..."
            kill "$PID"

            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                echo "  - Force stopping..."
                kill -9 "$PID" 2>/dev/null || true
            fi

            rm -f "$PID_FILE"
            echo -e "${GREEN}Application stopped${NC}"
            return 0
        else
            echo "Process not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    fi

    # Try to find and kill any running uvicorn process
    PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "  - Found running process(es): $PIDS"
        echo "$PIDS" | xargs kill 2>/dev/null || true
        
        # Wait a moment for graceful shutdown
        sleep 3
        
        # Force kill any remaining processes
        REMAINING_PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || true)
        if [ -n "$REMAINING_PIDS" ]; then
            echo "  - Force stopping remaining process(es)..."
            echo "$REMAINING_PIDS" | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        
        echo -e "${GREEN}Application stopped${NC}"
    else
        echo -e "${YELLOW}Application is not running${NC}"
    fi
}

restart() {
    echo "Restarting $APP_NAME FastAPI Application..."
    stop
    sleep 3
    start
}

status() {
    get_config
    echo "$APP_NAME FastAPI Application Status"
    echo "======================================"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "Status:      ${GREEN}RUNNING${NC}"
            echo "PID:         $PID"
            echo "Environment: $ENV"
            echo "Host:        $HOST"
            echo "Port:        $PORT"
            echo "Access URL:  $(get_access_url)"
            echo ""
            echo "Uptime:"
            ps -p "$PID" -o etime= | sed 's/^/  /'
            return 0
        fi
    fi

    # Check for any running uvicorn process
    PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo -e "Status:      ${YELLOW}RUNNING (no PID file)${NC}"
        echo "PID(s):      $PIDS"
        echo ""
        echo "Tip: Run 'stop' then 'start' to fix PID file"
    else
        echo -e "Status:      ${RED}STOPPED${NC}"
    fi
}

logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}No log file found at $LOG_FILE${NC}"
        return 1
    fi

    if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
        echo "Following logs (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        echo "Showing last 50 lines of logs..."
        tail -n 50 "$LOG_FILE"
        echo ""
        echo "Tip: Use '$0 logs follow' to follow logs in real-time"
    fi
}

# Main command dispatcher
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    *)
        echo "$APP_NAME - Management Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  status  - Show application status"
        echo "  logs    - Show recent logs"
        echo "  logs -f - Follow logs in real-time"
        echo ""
        exit 1
        ;;
esac
