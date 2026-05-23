#!/usr/bin/env bash
# Start QMUN Hub in the background. Survives terminal close.
# Logs go to logs/streamlit.log. Stop with ./scripts/stop.sh.
set -e
cd "$(dirname "$0")/.."

PID_FILE=".qmun-hub.pid"
LOG_FILE="logs/streamlit.log"
mkdir -p logs

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Already running (PID $(cat "$PID_FILE")). http://localhost:8501"
    exit 0
fi

source .venv/bin/activate
nohup arch -arm64 .venv/bin/python3 -m streamlit run app.py \
    --server.headless true \
    >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "Started (PID $!). http://localhost:8501"
echo "Logs:  tail -f $LOG_FILE"
echo "Stop:  ./scripts/stop.sh"
