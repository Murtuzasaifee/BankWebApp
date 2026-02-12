#!/bin/bash
# ============================================================================
# Good Bank FastAPI Application - Management Script
# ============================================================================
# Usage: bash manage.sh {start|stop|restart|status|logs}
# ============================================================================

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/app.log"
VENV_DIR="$APP_DIR/venv"
HOST="0.0.0.0"
PORT="8000"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Application is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    echo "Starting Good Bank FastAPI Application..."
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"
    nohup uvicorn app.main:app --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Application started successfully (PID: $(cat "$PID_FILE"))"
        PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
        echo "Access at: http://${PUBLIC_IP}:${PORT}"
    else
        echo "ERROR: Application failed to start. Check logs:"
        echo "  tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "PID file not found. Trying to find process..."
        PID=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)
        if [ -n "$PID" ]; then
            echo "Found process PID: $PID. Stopping..."
            kill "$PID"
            echo "Application stopped."
        else
            echo "Application is not running."
        fi
        return 0
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping application (PID: $PID)..."
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Application stopped."
    else
        echo "Process not running. Cleaning up PID file."
        rm -f "$PID_FILE"
    fi
}

restart() {
    echo "Restarting application..."
    stop
    sleep 2
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Application is RUNNING (PID: $(cat "$PID_FILE"))"
        PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
        echo "Access at: http://${PUBLIC_IP}:${PORT}"
    else
        echo "Application is STOPPED"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "Showing logs (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
