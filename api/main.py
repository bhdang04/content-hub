"""Dashboard API: JSON for the React app in web/. Reads the scripts in src/.
Run from the project root: uvicorn api.main:app --host 127.0.0.1 --port 8000  (or ./run.sh)
Localhost only; your data is not sent anywhere."""
import io, json, os, re, subprocess, sys, threading, zipfile
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
    weeks_left = max((GOAL_DATE - data.END.date()).days / 7, 1)

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

CHOICES = {"caption_len", "hashtags"}  # you decide these; the rest are results

def verdict(col, c):
    """Rank correlation -> what it means, in words."""
    if pd.isna(c) or abs(c) < 0.2:
        return "No real difference"
    sure = "Clear sign" if abs(c) >= 0.4 else "Maybe"
    if col in CHOICES:
        return f"{sure}: {'more' if c > 0 else 'less'} of this went with more views" + ("" if abs(c) >= 0.4 else " (test it)")
    if c > 0:
        return f"{sure}: big videos get more of these. Aim for it."
    return f"{sure}: big videos get fewer (normal: strangers watch)"

@app.get("/api/patterns")
def patterns():
    _, pat = mods()
    v, views = pat.v, pat.v["Total views"]
    g = v.groupby(pat.top)[pat.cols].median()
    f = v.dropna(subset=["followers_per_1k_views"])  # no follower history for posts outside the export range
    return clean({
        "top_count": int(pat.top.sum()), "other_count": int((~pat.top).sum()),
        "differences": [{"what": pat.NAMES[c], "top": g.loc[True, c], "other": g.loc[False, c],
                         "meaning": verdict(c, pat.corr(v[c], views))} for c in pat.cols],
        "followers": rows(pd.DataFrame({"title": f["title"], "posted": day(f["Post time"]), "views": f["Total views"],
                                        "followers_per_1k": f["followers_per_1k_views"]})
                          .sort_values("followers_per_1k", ascending=False)),
    })

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
