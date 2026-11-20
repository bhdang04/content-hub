#!/usr/bin/env bash
# Content Hub. Localhost only unless you run "phone"; your data stays on this Mac.
#   ./run.sh              dashboard: API on 127.0.0.1:8000, open http://127.0.0.1:5173 (Ctrl+C stops both)
#   ./run.sh phone        same, plus open it on your phone on the same Wi-Fi (anyone on that Wi-Fi can see it)
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
  ""|phone) ;;
  *) sed -n '2,10p' "$0" | sed 's/^# //'; exit 1 ;;
esac
[ -d web/node_modules ] || (cd web && npm install)
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web
if [ "${1:-}" = phone ]; then
  echo "On your phone (same Wi-Fi): http://$(ipconfig getifaddr en0 || echo '<this Mac IP>'):5173"
  exec npm run dev -- --host 0.0.0.0  # API stays on 127.0.0.1; only Vite listens on Wi-Fi
fi
npm run dev
