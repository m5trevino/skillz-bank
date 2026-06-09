#!/bin/bash
# Session Orchestrator Daemon — MX Linux Autostart
# Works with SysVinit, OpenRC, runit, or any init system.
# Add this script to your desktop autostart or run it manually.

DAEMON="$HOME/.kimi/skills/session-transcript/scripts/session-daemon.py"
PIDFILE="$HOME/.kimi/sessions/.orchestrator.pid"
LOGFILE="$HOME/.kimi/sessions/.orchestrator.log"

start() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Daemon already running (PID $PID)"
            return
        fi
    fi
    echo "Starting session orchestrator daemon..."
    nohup python3 "$DAEMON" --daemon >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "Daemon started (PID $!). Log: $LOGFILE"
}

stop() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        kill "$PID" 2>/dev/null
        rm -f "$PIDFILE"
        echo "Daemon stopped."
    else
        echo "Daemon not running."
    fi
}

status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Daemon running (PID $PID)"
        else
            echo "Daemon not running (stale PID file)"
        fi
    else
        echo "Daemon not running."
    fi
}

case "${1:-start}" in
    start) start ;;
    stop) stop ;;
    restart) stop; sleep 1; start ;;
    status) status ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac
