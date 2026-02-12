#!/bin/bash
# Good Bank Chat Application Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs]

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="app.py"
LOG_FILE="$APP_DIR/app.log"
PID_FILE="$APP_DIR/app.pid"

get_public_ip() {
    curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_PUBLIC_IP"
}

start_app() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  App is already running (PID: $PID)"
            return 1
        fi
    fi
    
    echo "🚀 Starting Good Bank Chat Application..."
    cd "$APP_DIR"
    source venv/bin/activate
    nohup python "$APP_NAME" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ App started successfully (PID: $(cat $PID_FILE))"
        echo "🌐 Access at: http://$(get_public_ip):8000"
    else
        echo "❌ Failed to start app. Check logs: tail -50 $LOG_FILE"
        return 1
    fi
}

stop_app() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 Stopping Good Bank Chat Application (PID: $PID)..."
            kill $PID
            rm -f "$PID_FILE"
            echo "✅ App stopped"
            return 0
        fi
    fi
    
    # Try to find and kill by name
    PIDS=$(pgrep -f "python.*$APP_NAME" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "🛑 Stopping Good Bank Chat Application..."
        pkill -f "python.*$APP_NAME"
        rm -f "$PID_FILE"
        echo "✅ App stopped"
    else
        echo "⚠️  App is not running"
    fi
}

status_app() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ App is running (PID: $PID)"
            echo "🌐 URL: http://$(get_public_ip):8000"
            return 0
        fi
    fi
    
    PIDS=$(pgrep -f "python.*$APP_NAME" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "✅ App is running (PID: $PIDS)"
        echo "🌐 URL: http://$(get_public_ip):8000"
    else
        echo "❌ App is not running"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Showing last 50 lines of logs..."
        echo "   (Press Ctrl+C to exit)"
        echo "=========================================="
        tail -50f "$LOG_FILE"
    else
        echo "❌ No log file found at: $LOG_FILE"
    fi
}

case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        sleep 2
        start_app
        ;;
    status)
        status_app
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Good Bank Chat Application Manager"
        echo "============================"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  status  - Check if app is running"
        echo "  logs    - View application logs"
        echo ""
        ;;
esac
