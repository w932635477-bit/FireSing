#!/bin/bash
# GPU SSH tunnel manager with auto-reconnection via autossh.
# Usage: ./gpu-tunnel.sh [start|stop|status]
#
# Keeps a persistent SSH tunnel to the AutoDL GPU server.
# autossh monitors the connection and reconnects on failure.

TUNNEL_PORT=8001
REMOTE_HOST="connect.westb.seetacloud.com"
REMOTE_PORT=11311
PID_FILE="/tmp/firesing_gpu_tunnel.pid"
LOG_FILE="/tmp/firesing_gpu_tunnel.log"

# Read password from environment or use default
SSH_PASS="${GPU_SSH_PASS:-I+5NyK0aOvwa}"

start_tunnel() {
    if is_running; then
        echo "Tunnel already running (PID $(cat $PID_FILE))"
        return 0
    fi

    echo "Starting GPU SSH tunnel..."
    echo "$(date): Starting tunnel" > "$LOG_FILE"

    # Kill any stale tunnel processes on the port
    lsof -ti :$TUNNEL_PORT 2>/dev/null | xargs kill 2>/dev/null

    # Use autossh for persistent connection with auto-reconnect
    export AUTOSSH_POLL=60          # Check every 60s
    export AUTOSSH_GATETIME=0       # Don't wait before first connect
    export AUTOSSH_PORT=0           # Disable port forwarding check (use ServerAliveInterval instead)

    AUTOSSH_PIDFILE="$PID_FILE" \
    sshpass -p "$SSH_PASS" autossh -M 0 \
        -p $REMOTE_PORT \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=5 \
        -o TCPKeepAlive=yes \
        -o ExitOnForwardFailure=yes \
        -o ConnectTimeout=10 \
        -f -N \
        -L ${TUNNEL_PORT}:localhost:${TUNNEL_PORT} \
        root@${REMOTE_HOST}

    sleep 2
    if is_running; then
        echo "Tunnel started (PID $(cat $PID_FILE))"
        echo "GPU server available at http://localhost:${TUNNEL_PORT}"
    else
        echo "ERROR: Tunnel failed to start. Check $LOG_FILE"
        return 1
    fi
}

stop_tunnel() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        # Kill autossh and its child ssh process
        kill -TERM "$PID" 2>/dev/null
        # Also kill any process listening on the tunnel port
        lsof -ti :$TUNNEL_PORT 2>/dev/null | xargs kill 2>/dev/null
        rm -f "$PID_FILE"
        echo "Tunnel stopped"
    else
        echo "No tunnel PID file found"
        # Try to clean up any leftover processes
        lsof -ti :$TUNNEL_PORT 2>/dev/null | xargs kill 2>/dev/null
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
        rm -f "$PID_FILE"
    fi
    return 1
}

status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "Tunnel running (PID $PID)"
        # Quick health check
        if curl -s -m 3 "http://localhost:${TUNNEL_PORT}/health" > /dev/null 2>&1; then
            echo "GPU server: ONLINE"
            curl -s "http://localhost:${TUNNEL_PORT}/health" 2>/dev/null | python3 -m json.tool 2>/dev/null || true
        else
            echo "GPU server: OFFLINE (tunnel up but server not responding)"
        fi
    else
        echo "Tunnel not running"
    fi
}

case "${1:-start}" in
    start)  start_tunnel ;;
    stop)   stop_tunnel ;;
    status) status ;;
    restart) stop_tunnel; sleep 1; start_tunnel ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Manages the SSH tunnel to AutoDL GPU server."
        echo "Set GPU_SSH_PASS env var to override the default password."
        exit 1
        ;;
esac
