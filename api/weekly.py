"""Weekly planner (README v2 step 8): fill next week's empty Plan slots + backups, then print the weekly email text.
Run: ./run.sh plan. Works without the dashboard running. The weekly-plan skill puts the text in a Gmail draft."""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")  # starlette's TestClient deprecation notice
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app, base_url="http://127.0.0.1")
r = c.post("/api/plan/fill")
if r.status_code != 200:
    raise SystemExit(f"Couldn't fill the plan: {r.json().get('detail', r.status_code)}")
print(f"Added {r.json()['added']} dances to next week.\n")
print(c.get("/api/weekly").json()["text"])
