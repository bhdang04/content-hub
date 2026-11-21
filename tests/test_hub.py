"""Tests for the hub, on fake demo data only (never your real data/). Plain asserts, no test library.
Run: ./run.sh test. GitHub runs the same on every push (.github/workflows/test.yml)."""
import os, subprocess, sys, warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "data"
ICLOUD_PLAN = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Content Hub/plan.html"


def snapshot():
    """(path, size, modified time) of every real file the tests must never touch."""
    files = [*REAL.rglob("*"), ICLOUD_PLAN]
    return sorted((str(p), p.stat().st_size, p.stat().st_mtime) for p in files if p.is_file())


before = snapshot()
subprocess.run([sys.executable, str(ROOT / "demo" / "make.py")], check=True, capture_output=True)

os.environ["CONTENT_HUB_DEMO"] = "1"  # must be set before api.main is imported
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")  # starlette's TestClient notice
from fastapi.testclient import TestClient
from api.main import BASE, app
from planner import fill, next_week

assert BASE == ROOT / "demo", BASE
c = TestClient(app, base_url="http://127.0.0.1")
ok = []


def test(name):
    def run(f):
        f()
        ok.append(name)
        print(f"ok: {name}")
    return run


@test("every page loads")
def _():
    for p in ["home", "plan", "videos", "patterns", "posts", "trending", "competitors", "quest", "track", "weekly"]:
        r = c.get(f"/api/{p}")
        assert r.status_code == 200, (p, r.status_code, r.text[:200])


@test("demo fill: next week has 3 a day, 1 of them new, each with a reason")
def _():
    p = c.get("/api/plan").json()
    done = {d["key"] for d in p["dances"]}
    week = next_week()
    planned = [x for x in p["planned"] if x["date"] in week]
    assert len(planned) == 21, len(planned)
    for d in week:
        day = [x for x in planned if x["date"] == d]
        assert sorted(x["slot"] for x in day) == [0, 1, 2], (d, day)
        assert sum(x["key"] not in done for x in day) == 1, (d, [x["name"] for x in day])
    assert all(x["why"] for x in planned), [x["name"] for x in planned if not x["why"]]
    assert len({x["key"] for x in planned}) == 21, "a dance is planned twice in one week"


@test("fill again adds nothing: filled slots are never touched")
def _():
    before = c.get("/api/plan").json()["planned"]
    assert c.post("/api/plan/fill").json()["added"] == 0
    assert c.get("/api/plan").json()["planned"] == before


@test("planner keeps a slot you filled and still gives the day 1 new")
def _():
    new = [{"key": f"n{i}", "label": f"N{i}"} for i in range(9)]
    old = [{"key": f"o{i}", "label": f"O{i}"} for i in range(20)]
    days = ["2026-01-05", "2026-01-06"]
    added, extra = fill(days, {("2026-01-05", 1): "mine"}, new, old)
    assert ("2026-01-05", 1) not in {(d, s) for d, s, *_ in added}
    assert len(added) == 5
    for d in days:
        assert sum(k.startswith("n") for dd, _, k, _ in added if dd == d) == 1, added
        assert len(extra[d]) == 2


move = lambda a, b: c.post("/api/plan/move", json={"from": a, "to": b})


@test("move swaps two dances and moves them back")
def _():
    d = next_week()[0]
    a, b = {"kind": "plan", "date": d, "n": 0}, {"kind": "backup", "date": d, "n": 0}
    key = lambda: {(x["date"], x["slot"]): x["key"] for x in c.get("/api/plan").json()["planned"]}
    start = key()
    assert move(a, b).status_code == 200
    assert key()[(d, 0)] != start[(d, 0)]
    assert move(b, a).status_code == 200
    assert key() == start


@test("move refuses bad spots and empty sources")
def _():
    d = next_week()[0]
    bad = [{"kind": "plan", "date": d, "n": 3}, {"kind": "x; DROP TABLE plan", "date": d, "n": 0},
           {"kind": "plan", "date": "2026-02-31", "n": 0}, {"kind": "plan", "date": d, "n": True}, "nope"]
    for s in bad:
        assert move(s, {"kind": "plan", "date": d, "n": 1}).status_code == 400, s
    assert move({"kind": "plan", "date": "2020-01-01", "n": 0}, {"kind": "plan", "date": d, "n": 1}).status_code == 404


@test("phone plan is written to demo/data, with Learn tags")
def _():
    page = (BASE / "data" / "plan.html").read_text()
    assert "Learn" in page and "Done" in page and "<script" not in page


@test("safety self-check passes")
def _():
    r = subprocess.run([sys.executable, str(ROOT / "api" / "check.py")], capture_output=True, text=True,
                       env={**os.environ, "CONTENT_HUB_DEMO": "1"})
    assert r.returncode == 0, r.stdout + r.stderr


@test("real data/ and the iCloud plan were not touched")
def _():
    assert snapshot() == before, "a test changed your real files"


print(f"\nAll {len(ok)} tests passed.")
