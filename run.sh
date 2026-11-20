#!/usr/bin/env bash
# Content Hub. Localhost only; your data stays on this Mac.
#   ./run.sh              dashboard: API on 127.0.0.1:8000, open http://127.0.0.1:5173 (Ctrl+C stops both)
#   ./run.sh plan [1-3]   2-week posting calendar, videos per day (default 2)
#   ./run.sh analyze      text report: views, engagement, followers, viewers
#   ./run.sh recommend    refresh the advice (what to post, fix, try)
#   ./run.sh track        did the last advice work? (uses the past-7-days export)
#   ./run.sh check        self-check the dashboard's safety rules (writes nothing)
#   ./run.sh import       load Studio per-post reads (data/raw/studio/) into data/hub.db
set -e
cd "$(dirname "$0")"
case "${1:-}" in
  plan|analyze|recommend|track) exec python3 "src/$1.py" "${@:2}" ;;
  check) exec python3 api/check.py ;;
  import) exec python3 src/studio_import.py ;;
  "") ;;
  *) sed -n '2,9p' "$0" | sed 's/^# //'; exit 1 ;;
esac
[ -d web/node_modules ] || (cd web && npm install)
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web && npm run dev
