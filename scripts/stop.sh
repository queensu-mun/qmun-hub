#!/usr/bin/env bash
cd "$(dirname "$0")/.."

PID_FILE=".qmun-hub.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Not running (no PID file)."
    exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm "$PID_FILE"
    echo "Stopped (PID $PID)."
else
    echo "Already stopped (stale PID $PID)."
    rm "$PID_FILE"
fi
