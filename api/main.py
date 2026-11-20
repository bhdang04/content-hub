"""Dashboard API: JSON for the React app in web/. Reads the scripts in src/.
Run from the project root: uvicorn api.main:app --host 127.0.0.1 --port 8000  (or ./run.sh)
Localhost only; your data is not sent anywhere."""
import io, json, os, re, sqlite3, subprocess, sys, threading, zipfile
from datetime import date
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # the scripts read data/raw/... relative to the project root
sys.path.insert(0, str(ROOT / "src"))

GOAL, GOAL_DATE = 15_000, date(2027, 2, 28)  # follower goal and deadline

app = FastAPI(title="Content Hub API")
# refuse requests addressed to any other site name, so a web page can't reach this API by
# pointing its own domain at 127.0.0.1 (DNS rebinding)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

# ---------- loading ----------
_cache = {}
_lock = threading.Lock()  # requests run in parallel threads; two loads at once break each other's imports

def stamp():
    """Changes whenever an export zip or a src/ script changes, so cached results refresh."""
    files = [*(ROOT / "data" / "raw").rglob("*.zip"), *(ROOT / "src").glob("*.py")]
    return max((p.stat().st_mtime for p in files), default=0)

def cached(key, make):
    with _lock:
        s = stamp()
        if key not in _cache or _cache[key][0] != s:
            _cache[key] = (s, make())
        return _cache[key][1]

def _load():
    os.environ["CONTENT_HUB_RAW"] = "data/raw/year"
    for m in ("data", "patterns"):
        sys.modules.pop(m, None)
    try:
        import data, patterns
        return data, patterns
    except SystemExit as e:  # data.py exits with a plain message when exports are missing
        return None, str(e)

def mods():
    d, p = cached("mods", _load)
    if d is None:
        raise HTTPException(409, p)
    return d, p

def script(name, *args):
    """Run one src/ script as its own process (they print and save at import). Returns (stdout, stderr)."""
    env = {k: v for k, v in os.environ.items() if k != "CONTENT_HUB_RAW"}  # let track.py pick week/
    r = subprocess.run([sys.executable, *(["-c", name] if "\n" in name else [f"src/{name}.py"]), *args],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    return r.stdout, r.stderr

def rows(df):
    """DataFrame -> list of dicts; NaN becomes null (plain json can't hold NaN)."""
    return json.loads(df.to_json(orient="records"))

def clean(obj):
    """numpy numbers -> plain, NaN -> null, so FastAPI can send it."""
    return json.loads(pd.io.json.ujson_dumps(obj))

def day(s):
    return s.dt.strftime("%Y-%m-%d")

def engagement(v):
    views = v["Total views"]
    return (v[["Total likes", "Total comments", "Total shares"]].sum(axis=1) / views.where(views > 0) * 100).round(2)

# ---------- endpoints ----------
@app.get("/api/home")
def home():
    data, pat = mods()
    o = data.overview.set_index("Date")["Video Views"]
    fol = data.fol.set_index("Date")["Followers"]
    last, prev = o.iloc[-28:].sum(), o.iloc[-56:-28].sum()
    now, week = fol.iloc[-1], fol.iloc[-1] - fol.iloc[-8]
    weeks_left = max((GOAL_DATE - date.today()).days / 7, 1)  # from today: an old export mustn't make the pace look easier

    def advice():
        script("recommend")
        files = sorted((ROOT / "data" / "recs").glob("*.json"))
        return json.loads(files[-1].read_text())["recommendations"] if files else {}

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    act = data.act.groupby(data.act["Date"].dt.day_name())["Active followers"].mean().reindex(days).round()
    weekly = o.resample("W").sum()
    return clean({
        "range": [str(o.index.min().date()), str(data.END.date())],
        "goal": {"followers": now, "goal": GOAL, "by": str(GOAL_DATE),
                 "per_week_needed": max(GOAL - now, 0) / weeks_left, "last_week": week},
        "views_year": o.sum(), "views_28d": last, "views_28d_change_pct": (last / prev - 1) * 100 if prev else None,
        "follower_gain_year": fol.iloc[-1] - fol.iloc[0],
        "typical_engagement_pct": engagement(pat.v).median(), "videos": len(pat.v),
        "weekly_views": [{"week": str(d.date()), "views": n} for d, n in weekly.items()],
        "follower_activity": [{"day": d, "followers": n} for d, n in act.items()],
        "advice": cached("advice", advice),
    })

# run track.py in its own process (it needs the week/ export, and data/patterns are loaded once per process)
# and hand back its tables as JSON. exec into our own dict so its variables survive its SystemExit messages.
TRACK = """
import contextlib, io, json, sys
sys.path.insert(0, "src")
g, msg = {"__name__": "__main__"}, None
with contextlib.redirect_stdout(io.StringIO()):
    try:
        exec(compile(open("src/track.py").read(), "src/track.py", "exec"), g)
    except SystemExit as e:
        msg = str(e).strip()
out = {"message": msg, "advice_date": g.get("s", {}).get("export_date"), "export_end": str(g["END"].date()) if "END" in g else None}
if "checks" in g:
    new = g["new"]
    out["videos"] = json.loads(new[["title", "age_days", "Total views"] + g["checks"]].to_json(orient="records"))
    out["hits"] = {c: [int(new[c].sum()), len(new)] for c in g["checks"]}
    out["tests"] = [g["compare"](g["views"], m, label) or f"{label}: not enough videos yet (need 2+ on each side, have {m.sum()}/{(~m).sum()})"
                    for label, m in g["tests"]]
    out["still_growing"] = bool((new["age_days"] < 7).any())
print(json.dumps(out))
"""

@app.get("/api/track")
def track():
    def make():
        out, err = script(TRACK)
        if not out.strip():
            raise HTTPException(500, (err.strip().splitlines() or ["track.py failed"])[-1])
        return json.loads(out)
    return cached("track", make)

@app.get("/api/videos")
def videos():
    _, pat = mods()
    v = pat.v
    t = pd.DataFrame({"title": v["title"], "posted": day(v["Post time"]), "views": v["Total views"],
                      "likes": v["Total likes"], "comments": v["Total comments"], "shares": v["Total shares"],
                      "engagement_pct": engagement(v), "link": v["Video link"]})
    return rows(t.sort_values("views", ascending=False))

@app.get("/api/patterns")
def patterns():
    _, pat = mods()
    v, views = pat.v, pat.v["Total views"]
    g = v.groupby(pat.top)[pat.cols].median()
    f = v.dropna(subset=["followers_per_1k_views"])  # no follower history for posts outside the export range
    return clean({
        "top_count": int(pat.top.sum()), "other_count": int((~pat.top).sum()),
        "differences": [{"what": pat.NAMES[c], "top": g.loc[True, c], "other": g.loc[False, c],
                         "meaning": pat.verdict(c, pat.link_strength(c))} for c in pat.cols],
        "followers": rows(pd.DataFrame({"video_id": f["Video link"].str.extract(r"/video/(\d+)")[0], "title": f["title"], "posted": day(f["Post time"]), "views": f["Total views"],
                                        "followers_per_1k": f["followers_per_1k_views"]})
                          .sort_values("followers_per_1k", ascending=False)),
    })

# ---------- Studio per-post data (data/hub.db, filled by ./run.sh import) ----------
NUMS = ["views", "likes", "comments", "shares", "saves", "avg_watch_s", "full_watch_rate", "kept_3s", "new_followers"]

def drop_second(r):
    """Second where the most viewers left (biggest one-second fall). Matches Studio's 'stopped watching at 0:0X'."""
    if len(r) < 2:
        return None
    return max(range(1, len(r)), key=lambda i: r[i - 1] - r[i])

def studio():
    db = ROOT / "data" / "hub.db"
    if not db.exists():
        raise HTTPException(409, "No Studio data yet. Ask Claude to read Studio, then run ./run.sh import.")
    con = sqlite3.connect(db)
    try:
        df = pd.read_sql("SELECT * FROM posts", con)
    finally:
        con.close()
    df["retention"] = df.pop("retention_json").map(json.loads)
    df["search_terms"] = df.pop("search_terms_json").map(json.loads)
    df["drop_second"] = df["retention"].map(drop_second)
    df["kept_3s"] = df["retention"].map(lambda r: r[3] if len(r) > 3 else None)
    df["posted"] = pd.to_datetime(df["posted_at"], unit="s", utc=True).dt.tz_convert("America/Los_Angeles").dt.strftime("%Y-%m-%d")
    df = df.sort_values("posted_at")
    df["gap_days"] = df["posted_at"].diff() / 86400  # ads count: they're still a post in the feed
    return df.iloc[::-1]

def opening_advice(p, u, usual_len):
    """Plain 'what to do' lines for one video. 5-point cutoff: smaller gaps are mostly chance."""
    k, uk = p.get("kept_3s"), u.get("kept_3s")
    if k is None or uk is None:
        return []
    pc = lambda x: f"{round(x * 100)}%"
    if k >= uk + 0.05:
        out = [f"Strong opening: {pc(k)} still watching at 3s (your usual: {pc(uk)}). Reuse this opening."]
    elif k <= uk - 0.05:
        return [f"Weak opening: only {pc(k)} still watching at 3s (your usual: {pc(uk)}). Start on your best move in the first second."]
    else:
        out = [f"Normal opening ({pc(k)} still watching at 3s)."]
    if p["full_watch_rate"] <= u["full_watch_rate"] - 0.05:
        out.append(f"People stayed for the start but left before the end. Try a shorter cut (your usual length: {round(usual_len)}s).")
    return out

assert opening_advice({"kept_3s": .30, "full_watch_rate": 0}, {"kept_3s": .41, "full_watch_rate": .1}, 15)[0].startswith("Weak")
assert len(opening_advice({"kept_3s": .52, "full_watch_rate": .02}, {"kept_3s": .41, "full_watch_rate": .1}, 15)) == 2
assert opening_advice({"kept_3s": .43, "full_watch_rate": .1}, {"kept_3s": .41, "full_watch_rate": .1}, 15) == ["Normal opening (43% still watching at 3s)."]

@app.get("/api/posts")
def posts():
    df = studio()
    return rows(df[["video_id", "posted", "title", "length_s", "is_ad", "drop_second", "gap_days", *NUMS]])

@app.get("/api/posts/{video_id}")
def post(video_id: str):
    if not video_id.isdigit():
        raise HTTPException(400, "bad video id")
    df = studio()
    hit = df[df["video_id"] == video_id]
    if hit.empty:
        raise HTTPException(404, "That video isn't in the Studio data. Run a new Studio read, then ./run.sh import.")
    p = rows(hit)[0]
    base = df[df["is_ad"] == 0]  # ads get paid traffic; they'd skew "your usual"
    ret = pd.DataFrame(base["retention"].tolist())  # one column per second; shorter videos leave gaps
    p["usual"] = clean(base[NUMS].median().to_dict())
    p["usual_retention"] = clean(ret.median().iloc[:len(p["retention"])].round(3).tolist())
    p["usual_from"] = len(base)
    p["advice"] = opening_advice(p, p["usual"], base["length_s"].median())
    return p

# ---------- Plan: 2-week calendar + dance shortlist (plan, shortlist tables in data/hub.db) ----------
SCHEMAS = [
    "CREATE TABLE IF NOT EXISTS plan (date TEXT, slot INTEGER, dance_key TEXT, dance_name TEXT, PRIMARY KEY (date, slot))",
    "CREATE TABLE IF NOT EXISTS shortlist (dance_key TEXT PRIMARY KEY, label TEXT, added_at INTEGER)",
]

def plan_db():
    con = sqlite3.connect(ROOT / "data" / "hub.db")
    for q in SCHEMAS:
        con.execute(q)
    return con

def plan_write(sql, args):
    con = plan_db()
    try:
        with con:
            con.execute(sql, args)
    finally:
        con.close()
    return {"ok": True}

@app.get("/api/plan")
def plan():
    from dances import dances
    df = studio()  # 409s with a plain message when there's no Studio data
    days = [str(d.date()) for d in pd.date_range(pd.Timestamp.now(tz="America/Los_Angeles").date(), periods=14)]
    con = plan_db()
    try:
        planned = pd.read_sql("SELECT date, slot, dance_key AS key, dance_name AS name FROM plan WHERE date >= ?", con, params=[days[0]])
        short = pd.read_sql("SELECT dance_key AS key, label FROM shortlist ORDER BY added_at", con)
    finally:
        con.close()
    posted = df["posted"].value_counts()
    d = dances(df[df["is_ad"] == 0]) if "music_id" in df else pd.DataFrame(columns=["key"])  # an ad isn't a dance
    return clean({
        "days": [{"date": x, "posted": int(posted.get(x, 0))} for x in days],
        "planned": rows(planned),
        "shortlist": rows(short.assign(planned=short["key"].isin(planned["key"]))),
        "dances": rows(d.sort_values("best_views", ascending=False)),
    })

# trust boundary: the page sends these, so check them before they reach the database
def _slot(day: str, slot: int):
    try:
        ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", day)) and date.fromisoformat(day) and 0 <= slot <= 2
    except ValueError:  # 2026-02-31
        ok = False
    if not ok:
        raise HTTPException(400, "bad day or slot")

async def _dance(request: Request):
    body = await request.json()
    key, name = body.get("key"), body.get("name")
    if not (isinstance(key, str) and isinstance(name, str) and 0 < len(key) <= 100 and 0 < len(name) <= 200):
        raise HTTPException(400, "bad dance")
    return key, name

@app.put("/api/plan/{day}/{slot}")
async def plan_put(day: str, slot: int, request: Request):
    _slot(day, slot)
    return plan_write("INSERT OR REPLACE INTO plan VALUES (?, ?, ?, ?)", (day, slot, *await _dance(request)))

@app.delete("/api/plan/{day}/{slot}")
def plan_delete(day: str, slot: int):
    _slot(day, slot)
    return plan_write("DELETE FROM plan WHERE date = ? AND slot = ?", (day, slot))

@app.post("/api/shortlist")
async def shortlist_add(request: Request):
    key, name = await _dance(request)
    return plan_write("INSERT OR IGNORE INTO shortlist VALUES (?, ?, strftime('%s','now'))", (key, name))

@app.delete("/api/shortlist")
async def shortlist_remove(request: Request):
    key, _ = await _dance(request)
    return plan_write("DELETE FROM shortlist WHERE dance_key = ?", (key,))

# ---------- upload ----------
KINDS = {"Content": "Content.csv", "Overview": "Overview.csv", "Followers": "FollowerHistory.csv", "Viewers": "Viewers.csv"}
MAX_BYTES = 200 * 1024 * 1024

@app.post("/api/upload")
async def upload(request: Request, range: str, name: str = ""):
    """Body = the raw zip bytes. Never uses the uploaded file name as a path."""
    # other sites can't add custom headers without a CORS OK we never give, so this blocks cross-site uploads
    if request.headers.get("x-content-hub") != "1":
        raise HTTPException(403, "Upload from the Content Hub page only.")
    if range not in ("year", "week"):
        raise HTTPException(400, "range must be year or week")
    body = await request.body()
    if len(body) > MAX_BYTES:
        raise HTTPException(413, f"{name}: too big for a TikTok Studio export.")
    f = io.BytesIO(body)
    kind = None
    if zipfile.is_zipfile(f):
        names = zipfile.ZipFile(f).namelist()
        kind = next((k for k, csv in KINDS.items() if csv in names), None)
    if kind is None:
        raise HTTPException(400, f"{name}: not a TikTok Studio export (no Content/Overview/FollowerHistory/Viewers CSV inside).")
    if kind == "Overview":
        m = re.search(r"\d{4}-\d{2}-\d{2}", name)
        if not m:  # data.py reads the range start from this date
            raise HTTPException(400, f"{name}: keep TikTok's file name, it holds the start date (Overview_2026-11-12_...).")
        out_name = f"Overview_{m.group()}_upload.zip"
    else:
        out_name = f"{kind}_{date.today()}.zip"  # dated, so old Content exports stay and get merged
    out = ROOT / "data" / "raw" / range
    out.mkdir(parents=True, exist_ok=True)
    (out / out_name).write_bytes(body)
    return {"saved": f"data/raw/{range}/{out_name}"}
