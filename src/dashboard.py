"""Step 7: local dashboard for analyze / patterns / recommend / track, plus export upload.
Run from the project root: streamlit run src/dashboard.py
Runs on localhost only; your data is not sent anywhere."""
import os, re, subprocess, sys, zipfile
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # the scripts read data/raw/... relative to the project root
sys.path.insert(0, str(ROOT / "src"))

KINDS = {"Content": "Content.csv", "Overview": "Overview.csv", "Followers": "FollowerHistory.csv", "Viewers": "Viewers.csv"}

def zip_kind(f):
    """Which TikTok Studio export this is, judged by the CSV inside. None if it isn't one."""
    if not zipfile.is_zipfile(f):
        return None
    names = zipfile.ZipFile(f).namelist()
    return next((k for k, csv in KINDS.items() if csv in names), None)

def save(up, folder):
    """Save one uploaded zip into data/raw/<folder>/. Returns an error message, or None if saved.
    Never uses the uploaded file name as a path."""
    kind = zip_kind(up)
    if kind is None:
        return f"{up.name}: not a TikTok Studio export (no Content/Overview/FollowerHistory/Viewers CSV inside)."
    if kind == "Overview":
        m = re.search(r"\d{4}-\d{2}-\d{2}", up.name)
        if not m:  # data.py reads the range start from this date
            return f"{up.name}: keep TikTok's file name, it holds the start date (Overview_2026-11-12_...)."
        name = f"Overview_{m.group()}_upload.zip"
    else:
        name = f"{kind}_{date.today()}.zip"  # dated, so old Content exports stay and get merged
    out = ROOT / "data" / "raw" / folder
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_bytes(up.getvalue())
    return None

def stamp():
    """Changes whenever a zip under data/raw/ changes, so cached results refresh."""
    return max((p.stat().st_mtime for p in (ROOT / "data" / "raw").rglob("*.zip")), default=0)

@st.cache_resource
def load(raw, _stamp):
    """Fresh import of data + patterns for one export folder. Returns (data, patterns) or (None, error)."""
    os.environ["CONTENT_HUB_RAW"] = raw
    for m in ("data", "patterns"):
        sys.modules.pop(m, None)
    try:
        import data, patterns
        return data, patterns
    except SystemExit as e:
        return None, str(e)

@st.cache_data
def run(script, _stamp):
    """Text output of one of the step scripts, run as its own process."""
    env = {k: v for k, v in os.environ.items() if k != "CONTENT_HUB_RAW"}  # let track.py pick week/
    r = subprocess.run([sys.executable, f"src/{script}.py"], capture_output=True, text=True, env=env, cwd=ROOT)
    return r.stdout + (f"\n{r.stderr.strip().splitlines()[-1]}" if r.returncode else "")

st.set_page_config(page_title="Content Hub", layout="wide")
st.title("Content Hub")

with st.sidebar:
    st.header("Upload exports")
    folder = st.radio("Export range", ["year", "week"],
                      format_func={"year": "Past 365 days", "week": "Past 7 days"}.get,
                      help="Year feeds Analyze, Patterns and Recommendations. Week feeds Track.")
    ups = st.file_uploader("TikTok Studio zips (Content, Overview, Followers, Viewers)", type="zip",
                           accept_multiple_files=True)
    if ups and st.button("Save uploads", type="primary"):
        errors = [e for e in (save(u, folder) for u in ups) if e]
        st.session_state["upload_msg"] = errors or [f"Saved {len(ups)} file(s) to data/raw/{folder}/."]
        st.rerun()
    for msg in st.session_state.pop("upload_msg", []):
        (st.success if msg.startswith("Saved") else st.error)(msg)
    st.caption("Files are saved on this Mac only, in git-ignored data/raw/.")

s = stamp()
data, pat = load("data/raw/year", s)
if data is None:
    st.error(pat)
    st.stop()

v = pat.v
views = v["Total views"]
eng = (v[["Total likes", "Total comments", "Total shares"]].sum(axis=1) / views.where(views > 0) * 100).round(2)
tab_a, tab_p, tab_r, tab_t = st.tabs(["Analyze", "Patterns", "Recommendations", "Track"])

with tab_a:
    o = data.overview.set_index("Date")
    fol = data.fol.set_index("Date")["Followers"]
    st.caption(f"Past-year export: {o.index.min():%b %d, %Y} to {data.END:%b %d, %Y}")
    c = st.columns(4)
    c[0].metric("Video views", f"{o['Video Views'].sum():,.0f}")
    c[1].metric("Followers", f"{fol.iloc[-1]:,.0f}", f"{fol.iloc[-1] - fol.iloc[0]:+,.0f} in range")
    c[2].metric("Median engagement", f"{eng.median():.1f}%", help="(likes + comments + shares) / views")
    c[3].metric("Videos tracked", len(v), help="Merged from every Content export; each holds ~15 top videos.")
    st.subheader("Weekly video views")
    st.line_chart(o["Video Views"].resample("W").sum(), y_label="views")
    left, right = st.columns(2)
    left.subheader("Followers")
    left.line_chart(fol, y_label="followers")
    right.subheader("New vs returning viewers (weekly)")
    right.area_chart(data.viewers.set_index("Date")[["New Viewers", "Returning Viewers"]].resample("W").sum())
    st.subheader("Videos")
    st.dataframe(v[["title", "Post time", "Total views", "Total likes", "Total comments", "Total shares"]]
                 .assign(**{"Engagement %": eng}).sort_values("Total views", ascending=False),
                 hide_index=True, use_container_width=True)
    with st.expander("Full text report (analyze.py)"):
        st.code(run("analyze", s), language=None)

CHOICES = {"caption_len", "hashtags", "days_since_last_post"}  # you decide these; the rest are results

def verdict(col, c):
    """Rank correlation -> what it means, in words."""
    if pd.isna(c) or abs(c) < 0.2:
        return "No real difference"
    sure = "Clear sign" if abs(c) >= 0.4 else "Maybe"
    if col in CHOICES:
        return f"{sure}: {'more' if c > 0 else 'less'} of this went with more views" + ("" if abs(c) >= 0.4 else " (test it)")
    if c > 0:
        return f"{sure}: your big videos get more of these. Aim for it."
    return f"{sure}: your big videos get fewer of these. Normal: viral views come from strangers."

with tab_p:
    st.subheader("What your biggest videos do differently")
    st.caption(f"Your 3 most-viewed videos compared with your other {(~pat.top).sum()}. "
               "Typical (middle) value for each group.")
    groups = v.groupby(pat.top)[pat.cols].median()
    st.dataframe(pd.DataFrame({
        "What": [pat.NAMES[c] for c in pat.cols],
        "Your 3 biggest videos": [f"{groups.loc[True, c]:g}" for c in pat.cols],
        "Your other videos": [f"{groups.loc[False, c]:g}" for c in pat.cols],
        "What it means": [verdict(c, pat.corr(v[c], views)) for c in pat.cols],
    }), hide_index=True, use_container_width=True)
    st.subheader("Which videos won you followers")
    st.caption("New followers in the 3 days after posting, for every 1,000 views. Higher = viewers liked you enough to follow.")
    st.dataframe(v[["title", "Post time", "Total views", "followers_per_1k_views"]]
                 .rename(columns={"title": "Video", "Post time": "Posted", "Total views": "Views",
                                  "followers_per_1k_views": "New followers per 1,000 views"})
                 .sort_values("New followers per 1,000 views", ascending=False), hide_index=True, use_container_width=True)
    with st.expander("Details (raw numbers)"):
        st.code(run("patterns", s), language=None)

with tab_r:
    st.caption(f"Built from {len(v)} of your videos. Try these on your next posts, then check the Track tab.")
    st.markdown(re.sub(r"^== (.+) ==$", r"### \1", run("recommend", s), flags=re.M))

with tab_t:
    st.caption("Scores videos from the past-7-days export against the last saved advice.")
    st.code(run("track", s), language=None)
