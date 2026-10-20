#!/usr/bin/env bash
# One command demo: starts the bridge in the background, then opens a vendor chat.
# Agent replies print right below your messages. Ctrl+C to quit (stops the server too).
cd "$(dirname "$0")/.." || exit 1
[ -f .env ] || cp .env.example .env

PORT=${PORT:-8000}
if curl -s "localhost:$PORT/health" >/dev/null 2>&1; then
  echo "A server is already running on port $PORT; using it."
  echo "(Its replies print in the terminal where it was started.)"
else
  uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level warning &
  SERVER=$!
  trap 'kill $SERVER 2>/dev/null' EXIT
  for i in $(seq 1 20); do curl -s "localhost:$PORT/health" >/dev/null 2>&1 && break; sleep 0.5; done
fi

echo
echo "Chatting as a vendor. Try: hi | LINK SHARMA42 | stock | add 10 OIL1 | price RICE5 499 | YES | when is my payout"
echo
SIM_URL="http://localhost:$PORT/webhook" python scripts/simulate.py
