"""Step 7: local dashboard for analyze / patterns / recommend / track, plus export upload.
Run from the project root: streamlit run src/dashboard.py
Runs on localhost only; your data is not sent anywhere."""
import html, json, os, re, subprocess, sys, zipfile
from datetime import date
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # the scripts read data/raw/... relative to the project root
sys.path.insert(0, str(ROOT / "src"))

# palette: TikTok black + cyan + red. Color goes on data only: cyan/blue = the numbers and good news, red = bad news.
CARD, GRID, MUTED, RED, CYAN, BLUE = "#16161A", "#26262C", "#A1A1AA", "#FE2C55", "#25F4EE", "#2D9CF0"

CSS = f"""<style>
.block-container {{padding-top: 2rem; max-width: 1400px;}}
/* the innermost bordered container holding a .card marker becomes a rounded card */
[data-testid="stVerticalBlockBorderWrapper"]:has(.card):not(:has([data-testid="stVerticalBlockBorderWrapper"] .card)) {{
  background: {CARD}; border: none !important; border-radius: 16px; padding: 6px 22px 22px;}}  /* top is short: Streamlit adds 16px above the title */
.card-title {{font-weight: 600; font-size: 1rem; margin-bottom: .25rem;}}
.card-sub {{color: {MUTED}; font-size: .85rem; margin-bottom: .5rem;}}
.kpi {{background: {CARD}; border-radius: 16px; padding: 18px 22px; min-height: 118px;}}
.kpi-label {{color: {MUTED}; font-size: .9rem;}}
.kpi-value {{font-size: 2.6rem; font-weight: 700; line-height: 1.15; letter-spacing: -.02em;}}
.kpi-sub {{color: {MUTED}; font-size: .8rem; display: flex; gap: 8px; align-items: center;}}
.pill {{background: {CARD}; border-radius: 14px; padding: 12px 16px; margin-bottom: 12px;
  display: flex; justify-content: space-between; align-items: center;}}
.pill-label {{color: {MUTED}; font-size: .85rem;}}
.pill-value {{font-weight: 600; font-size: 1.15rem;}}
.badge {{border-radius: 10px; padding: 2px 10px; font-size: .8rem; font-weight: 600; white-space: nowrap;}}
[data-testid="stSidebarNav"]::before {{content: "Content Hub"; display: block; font-size: 1.35rem; font-weight: 700;
  padding: 0 0 1rem 1.5rem;}}
.badge-up {{background: rgba(37,244,238,.15); color: {CYAN};}}
.badge-down {{background: rgba(254,44,85,.18); color: #FF6B86;}}
.rec {{display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid {GRID}; line-height: 1.45;}}
.rec:last-child {{border-bottom: none;}}
.dot {{flex: 0 0 10px; height: 10px; border-radius: 50%; margin-top: 7px;}}
</style>"""

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
    """Changes whenever an export zip or a src/ script changes, so cached results refresh."""
    files = [*(ROOT / "data" / "raw").rglob("*.zip"), *(ROOT / "src").glob("*.py")]
    return max((p.stat().st_mtime for p in files), default=0)

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
def run(script, _stamp, *args):
    """Text output of one of the step scripts, run as its own process."""
    env = {k: v for k, v in os.environ.items() if k != "CONTENT_HUB_RAW"}  # let track.py pick week/
    r = subprocess.run([sys.executable, f"src/{script}.py", *args], capture_output=True, text=True, env=env, cwd=ROOT)
    return r.stdout + (f"\n{r.stderr.strip().splitlines()[-1]}" if r.returncode else "")

def recs(_stamp):
    """Latest advice as lists: {'post': [...], 'improve': [...], 'test': [...]}. Runs recommend.py first."""
    run("recommend", _stamp)
    files = sorted((ROOT / "data" / "recs").glob("*.json"))
    return json.loads(files[-1].read_text())["recommendations"] if files else {}

# ---------- small view helpers ----------
def card(title=None, sub=None):
    c = st.container(border=True)
    c.markdown('<span class="card"></span>' + (f'<div class="card-title">{title}</div>' if title else "")
               + (f'<div class="card-sub">{sub}</div>' if sub else ""), unsafe_allow_html=True)
    return c

def short(n):
    for div, suf in ((1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:.1f}{suf}"
    return f"{n:,.0f}"

def kpi(label, value, sub, badge=None, up=True):
    b = f'<span class="badge badge-{"up" if up else "down"}">{badge}</span>' if badge else ""
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{b}{sub}</div></div>', unsafe_allow_html=True)

def pill(label, value, badge=None, up=True):
    b = f'<span class="badge badge-{"up" if up else "down"}">{badge}</span>' if badge else ""
    st.markdown(f'<div class="pill"><div><div class="pill-label">{label}</div><div class="pill-value">{value}</div></div>{b}</div>',
                unsafe_allow_html=True)

def rec_list(items, color):
    if not items:
        st.markdown(f'<div class="card-sub">Nothing from this data yet.</div>', unsafe_allow_html=True)
    st.markdown("".join(f'<div class="rec"><span class="dot" style="background:{color}"></span><span>{html.escape(t)}</span></div>'
                        for t in items), unsafe_allow_html=True)

def style(chart, height=260):
    return (chart.properties(height=height, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(gridColor=GRID, labelColor=MUTED, titleColor=MUTED, domain=False, ticks=False, labelPadding=8)
            .configure_legend(labelColor=MUTED, titleColor=MUTED, orient="bottom"))

def glow(color):
    """Vertical fade: color at the top, transparent at the bottom."""
    return alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                        stops=[alt.GradientStop(color=color + "00", offset=0), alt.GradientStop(color=color + "88", offset=1)])

def area(df, x, y, color, fmt=",.0f"):
    return style(alt.Chart(df).mark_area(interpolate="monotone", line={"color": color, "strokeWidth": 2.5}, color=glow(color))
                 .encode(x=alt.X(f"{x}:T", title=None), y=alt.Y(f"{y}:Q", title=None, axis=alt.Axis(format="~s")),
                         tooltip=[alt.Tooltip(f"{x}:T", title="Week"), alt.Tooltip(f"{y}:Q", format=fmt)]))

def show(chart):
    st.altair_chart(chart, use_container_width=True, theme=None)

# ---------- pages ----------
def home():
    o = data.overview.set_index("Date")
    fol = data.fol.set_index("Date")["Followers"]
    last, prev = o["Video Views"].iloc[-28:].sum(), o["Video Views"].iloc[-56:-28].sum()
    change = (last / prev - 1) * 100 if prev else 0
    st.title("Home")
    st.caption(f"Past-year export: {o.index.min():%b %d, %Y} to {data.END:%b %d, %Y}")

    left, right = st.columns([2.1, 1], gap="medium")
    with left:
        k1, k2, k3 = st.columns([1, 1, 1.05])
        with k1:
            kpi("Video views (year)", short(o["Video Views"].sum()), f"{short(last)} in the last 28 days")
        with k2:
            gain = fol.iloc[-1] - fol.iloc[0]
            kpi("Followers", short(fol.iloc[-1]), "this year", f"{gain:+,.0f}", gain >= 0)
        with k3:
            pill("Views, last 28 days vs the 28 before", short(last), f"{change:+.0f}%", change >= 0)
            pill("Typical engagement", f"{eng.median():.1f}%", f"{len(v)} videos")
        with card("Weekly video views", "Smoothed weekly totals"):
            show(area(o["Video Views"].resample("W").sum().reset_index(), "Date", "Video Views", CYAN))
        a, b = st.columns(2, gap="medium")
        r = recs(s)
        with a, card("Ideas for your next videos", "What's worked for you"):
            rec_list(r.get("post", []), CYAN)
        with b, card("What to improve", "Fixes first, then things to test"):
            rec_list(r.get("improve", []), RED)
            rec_list(r.get("test", []), MUTED)

    with right:
        with card("Add new exports", "Drop TikTok Studio zips: Content, Overview, Followers, Viewers"):
            upload_box()
        with card("Dances to try", "Coming later"):
            st.markdown('<div class="card-sub">Trending dances that fit your style will show here once the '
                        'Trends feature (roadmap step 8d) is built.</div>', unsafe_allow_html=True)
        with card("When your followers are online", "Average active followers by day, last 7 days"):
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            d = data.act.groupby(data.act["Date"].dt.day_name())["Active followers"].mean().reindex(days).reset_index()
            d["Day"] = d["Date"].str[:3]
            bars = alt.Chart(d).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=22,
                                         color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                                                            stops=[alt.GradientStop(color=BLUE, offset=0),
                                                                   alt.GradientStop(color=CYAN, offset=1)])
                                         ).encode(x=alt.X("Day:N", sort=[x[:3] for x in days], title=None,
                                                          axis=alt.Axis(labelAngle=0)),
                                                  y=alt.Y("Active followers:Q", title=None, axis=alt.Axis(format="~s")),
                                                  tooltip=["Date", alt.Tooltip("Active followers:Q", format=",.0f")])
            show(style(bars, 300))

def upload_box():
    folder = st.radio("Export range", ["year", "week"], horizontal=True,
                      format_func={"year": "Past 365 days", "week": "Past 7 days"}.get,
                      help="Year feeds Home, Analyze, Patterns and Recommendations. Week feeds Track.")
    ups = st.file_uploader("TikTok Studio zips", type="zip", accept_multiple_files=True, label_visibility="collapsed")
    if ups and st.button("Save uploads", type="primary", use_container_width=True):
        errors = [e for e in (save(u, folder) for u in ups) if e]
        st.session_state["upload_msg"] = errors or [f"Saved {len(ups)} file(s) to data/raw/{folder}/."]
        st.rerun()
    for msg in st.session_state.pop("upload_msg", []):
        (st.success if msg.startswith("Saved") else st.error)(msg)
    st.caption("Saved on this Mac only, in git-ignored data/raw/.")

def analyze():
    o = data.overview.set_index("Date")
    fol = data.fol.set_index("Date")["Followers"]
    st.title("Analyze")
    c = st.columns(4)
    c[0].metric("Video views", f"{o['Video Views'].sum():,.0f}")
    c[1].metric("Followers", f"{fol.iloc[-1]:,.0f}", f"{fol.iloc[-1] - fol.iloc[0]:+,.0f} in range")
    c[2].metric("Typical engagement", f"{eng.median():.1f}%", help="(likes + comments + shares) / views")
    c[3].metric("Videos tracked", len(v), help="Merged from every Content export; each holds ~15 top videos.")
    a, b = st.columns([2, 1], gap="medium")
    with a, card("Followers over time"):
        show(area(fol.reset_index(), "Date", "Followers", CYAN))
    with b, card("New vs returning viewers", "Whole year"):
        vw = data.viewers[["New Viewers", "Returning Viewers"]].sum().reset_index()
        vw.columns = ["Type", "Viewers"]
        donut = alt.Chart(vw).mark_arc(innerRadius=70, cornerRadius=4).encode(
            theta="Viewers:Q", color=alt.Color("Type:N", scale=alt.Scale(range=[CYAN, BLUE]), title=None),
            tooltip=["Type", alt.Tooltip("Viewers:Q", format=",.0f")])
        show(style(donut))
    with card("Your videos", "Biggest first"):
        st.dataframe(v[["title", "Post time", "Total views", "Total likes", "Total comments", "Total shares"]]
                     .assign(**{"Post time": v["Post time"].dt.date, "Engagement %": eng})
                     .rename(columns={"title": "Video", "Post time": "Posted", "Total views": "Views",
                                      "Total likes": "Likes", "Total comments": "Comments", "Total shares": "Shares"})
                     .sort_values("Views", ascending=False), hide_index=True, use_container_width=True)
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
        return f"{sure}: big videos get more of these. Aim for it."
    return f"{sure}: big videos get fewer (normal: strangers watch)"

def patterns_page():
    st.title("Patterns")
    with card("What your biggest videos do differently",
              f"Your 3 most-viewed videos vs your other {(~pat.top).sum()}. Typical (middle) value for each group."):
        groups = v.groupby(pat.top)[pat.cols].median()
        st.dataframe(pd.DataFrame({
            "What": [pat.NAMES[c] for c in pat.cols],
            "Your 3 biggest videos": [f"{groups.loc[True, c]:g}" for c in pat.cols],
            "Your other videos": [f"{groups.loc[False, c]:g}" for c in pat.cols],
            "What it means": [verdict(c, pat.corr(v[c], views)) for c in pat.cols],
        }), hide_index=True, use_container_width=True)
    with card("Which videos won you followers",
              "New followers in the 3 days after posting, for every 1,000 views. Higher = viewers liked you enough to follow."):
        f = v.dropna(subset=["followers_per_1k_views"])  # no follower history for posts outside the export range
        st.dataframe(pd.DataFrame({"Video": f["title"], "Posted": f["Post time"].dt.date, "Views": f["Total views"],
                                   "New followers per 1,000 views": f["followers_per_1k_views"]})
                     .sort_values("New followers per 1,000 views", ascending=False),
                     hide_index=True, use_container_width=True, height=36 * (len(f) + 1) + 3)
    with st.expander("Details (raw numbers)"):
        st.code(run("patterns", s), language=None)

def recommendations():
    st.title("Recommendations")
    st.caption(f"Built from {len(v)} of your videos. Try these on your next posts, then check Track.")
    r = recs(s)
    for key, title, sub, color in (("post", "What to post", "More of what worked", CYAN),
                                   ("improve", "What to fix", "Clear signs from your numbers", RED),
                                   ("test", "What to try", "Not sure yet: test on your next 4 videos", MUTED)):
        with card(title, sub):
            rec_list(r.get(key, []), color)

def plan():
    st.title("Plan")
    n = st.radio("Videos per day", [1, 2, 3], index=1, horizontal=True)
    recs(s)  # plan.py reads the advice recommend.py saves
    # date in the cache key so a new day makes a new plan; files are per videos-a-day, so switching n can't show the wrong one
    out = run("plan", s, str(n), str(date.today()))
    files = sorted((ROOT / "data" / "plans").glob(f"*_{n}-a-day.csv"))
    with card("Next 2 weeks", "One row per video. Times are PST."):
        if files:
            st.dataframe(pd.read_csv(files[-1]), hide_index=True, use_container_width=True)
        else:
            st.error(out)
    with card("Notes"):
        st.code(out.split("\n\n")[0], language=None)

def track():
    st.title("Track")
    with card("Did the advice work?", "Videos from the past-7-days export, scored against the last saved advice."):
        st.code(run("track", s), language=None)

# ---------- app ----------
st.set_page_config(page_title="Content Hub", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
s = stamp()
data, pat = load("data/raw/year", s)
if data is None:
    st.error(pat)
    with card("Add exports"):
        upload_box()
    st.stop()
v = pat.v
views = v["Total views"]
eng = (v[["Total likes", "Total comments", "Total shares"]].sum(axis=1) / views.where(views > 0) * 100).round(2)

st.navigation([st.Page(home, title="Home", icon=":material/home:", default=True),
               st.Page(analyze, title="Analyze", icon=":material/monitoring:"),
               st.Page(patterns_page, title="Patterns", icon=":material/insights:", url_path="patterns"),
               st.Page(recommendations, title="Recommendations", icon=":material/lightbulb:"),
               st.Page(plan, title="Plan", icon=":material/calendar_month:"),
               st.Page(track, title="Track", icon=":material/fact_check:")]).run()
