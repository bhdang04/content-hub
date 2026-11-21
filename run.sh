#!/usr/bin/env bash
# Content Hub. Localhost only unless you run "phone"; your data stays on this Mac.
#   ./run.sh              dashboard: API on 127.0.0.1:8000, open http://127.0.0.1:5173 (Ctrl+C stops both)
#   ./run.sh demo         dashboard on fake data (demo/data/), never opens your real data/
#   ./run.sh phone        same, plus open it on your phone on the same Wi-Fi (anyone on that Wi-Fi can see it)
#   ./run.sh analyze      text report: views, engagement, followers, viewers
#   ./run.sh recommend    refresh the advice (what to post, fix, try)
#   ./run.sh track        did the last advice work? (uses the past-7-days export)
#   ./run.sh plan         fill next week's empty Plan slots + backups, print the weekly email text
#   ./run.sh check        self-check the dashboard's safety rules (writes nothing)
#   ./run.sh test         run the tests on fake demo data (never touches your real data/)
#   ./run.sh import       load Studio per-post reads (data/raw/studio/) into data/hub.db
#   ./run.sh inbox        import new Studio zips from ~/Downloads + phone links (iCloud Content Hub/inbox)
#   ./run.sh inbox-on     run "inbox" by itself whenever those folders change (inbox-off stops it)
set -e
cd "$(dirname "$0")"
case "${1:-}" in
  analyze|recommend|track) exec python3 "src/$1.py" "${@:2}" ;;
  check) exec python3 api/check.py ;;
  test) exec python3 tests/test_hub.py ;;
  plan) exec python3 api/weekly.py ;;
  import) exec python3 src/studio_import.py ;;
  inbox) exec python3 src/inbox.py ;;
  inbox-on|inbox-off)
    PLIST=~/Library/LaunchAgents/com.contenthub.inbox.plist
    INBOX=~/"Library/Mobile Documents/com~apple~CloudDocs/Content Hub/inbox"
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    if [ "$1" = inbox-off ]; then rm -f "$PLIST"; echo "Auto-import off."; exit 0; fi
    mkdir -p "$INBOX"
    cat > "$PLIST" <<PLIST_END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.contenthub.inbox</string>
  <key>ProgramArguments</key><array><string>$(command -v python3)</string><string>src/inbox.py</string></array>
  <key>WorkingDirectory</key><string>$PWD</string>
  <key>WatchPaths</key><array><string>$HOME/Downloads</string><string>$INBOX</string></array>
  <key>StartInterval</key><integer>86400</integer>
  <key>StandardErrorPath</key><string>$PWD/data/inbox.err</string>
</dict></plist>
PLIST_END
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
    echo "Auto-import on. Log: data/inbox.log, errors: data/inbox.err"; exit 0 ;;
  demo) python3 demo/make.py; export CONTENT_HUB_DEMO=1 VITE_DEMO=1 ;;  # VITE_DEMO: pages show a box for fake videos
  ""|phone) ;;
  *) sed -n '2,14p' "$0" | sed 's/^# //'; exit 1 ;;
esac
[ -d web/node_modules ] || (cd web && npm install)
# an API already on :8000 would serve the page instead (e.g. your real data during a demo), so stop
if lsof -ti tcp:8000 -sTCP:LISTEN >/dev/null; then echo "Port 8000 is busy: another dashboard is running. Stop it (Ctrl+C there), then try again."; exit 1; fi
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web
if [ "${1:-}" = phone ]; then
  echo "On your phone (same Wi-Fi): http://$(ipconfig getifaddr en0 || echo '<this Mac IP>'):5173"
  exec npm run dev -- --host 0.0.0.0  # API stays on 127.0.0.1; only Vite listens on Wi-Fi
fi
npm run dev
