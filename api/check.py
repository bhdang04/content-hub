"""Self-check for the API's safety rules: wrong site name, uploads from other sites, bad files.
Run: ./run.sh check. Only sends uploads that must be refused, so nothing is written to data/raw/."""
import io, sys, warnings, zipfile
from pathlib import Path
warnings.filterwarnings("ignore")  # starlette's TestClient deprecation notice
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from api.main import BASE, app

before = sorted((BASE / "data" / "raw").rglob("*"))
c = TestClient(app, base_url="http://127.0.0.1")
ok = {"X-Content-Hub": "1"}
def zip_with(csv):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(csv, "a")
    return b.getvalue()

cases = [
    ("other site name is refused", c.get("/api/patterns", headers={"Host": "evil.example"}), 400),
    ("upload without the page's header is refused", c.post("/api/upload?range=year&name=a.zip", content=zip_with("Content.csv")), 403),
    ("range outside year/week is refused", c.post("/api/upload?range=../x&name=a.zip", content=zip_with("Content.csv"), headers=ok), 400),
    ("non-zip is refused", c.post("/api/upload?range=year&name=a.zip", content=b"nope", headers=ok), 400),
    ("zip without a TikTok CSV is refused", c.post("/api/upload?range=year&name=a.zip", content=zip_with("x.csv"), headers=ok), 400),
    ("Overview without its date in the name is refused", c.post("/api/upload?range=week&name=Overview.zip", content=zip_with("Overview.csv"), headers=ok), 400),
]
for label, r, want in cases:
    assert r.status_code == want, f"FAIL: {label}: got {r.status_code}, want {want}"
    print(f"ok: {label}")
assert sorted((BASE / "data" / "raw").rglob("*")) == before, "FAIL: a refused upload wrote a file"
print("ok: nothing written to data/raw/")
