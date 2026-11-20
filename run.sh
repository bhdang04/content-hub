#!/usr/bin/env bash
# Dashboard v2: API on 127.0.0.1:8000, React dev server on http://127.0.0.1:5173. Ctrl+C stops both.
# Localhost only. Streamlit still works: streamlit run src/dashboard.py
set -e
cd "$(dirname "$0")"
[ -d web/node_modules ] || (cd web && npm install)
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web && npm run dev
