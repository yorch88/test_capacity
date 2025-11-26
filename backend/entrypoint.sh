#!/bin/sh
set -e

echo "[entrypoint] Running init_admin..."
python -m app.init_admin || echo "[entrypoint] init_admin failed (continuing anyway)."

echo "[entrypoint] Starting uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
