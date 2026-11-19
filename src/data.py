"""Load + clean TikTok Studio zips from data/raw/. Shared by analyze.py and patterns.py."""
import glob, os, re, zipfile
import pandas as pd

# past-year export drives analysis + recommendations; track.py switches this to data/raw/week
RAW = os.environ.get("CONTENT_HUB_RAW", "data/raw/year")

def newest(prefix):
    # several exports of one kind: Overview names sort by date; others carry no date, so replace them
    found = sorted(glob.glob(f"{RAW}/{prefix}*.zip"))
    if not found:
        raise SystemExit(f"No {prefix}*.zip in {RAW}/. Export it from TikTok Studio and put it there.")
    return found[-1]

def load(prefix, name):
    return pd.read_csv(zipfile.ZipFile(newest(prefix)).open(name))

def all_videos():
    """Each Content export holds only ~15 top videos, so merge every Content zip under data/raw/
    (keep old ones, e.g. week/Content_2026-11-18.zip). One row per video, stats from the newest file."""
    zips = sorted(glob.glob("data/raw/**/Content*.zip", recursive=True), key=os.path.getmtime)
    if not zips:
        raise SystemExit("No Content*.zip under data/raw/. Export it from TikTok Studio and put it there.")
    # shortcut: newest = latest file modified time (download time); breaks if old zips get re-downloaded/touched
    df = pd.concat([pd.read_csv(zipfile.ZipFile(z).open("Content.csv")) for z in zips], ignore_index=True)
    out = df.drop_duplicates("Video link", keep="last").reset_index(drop=True)
    assert out["Video link"].is_unique and len(out) <= len(df)
    return out

videos = all_videos()
overview = load("Overview", "Overview.csv")
fol = load("Followers", "FollowerHistory.csv")
viewers = load("Viewers", "Viewers.csv")
act = load("Followers", "FollowerActivity.csv")

# exports have no year. The Overview zip name holds the range START, e.g. Overview_2025-11-18_... covers 2025-11-18..2026-11-17
START = pd.Timestamp(re.search(r"\d{4}-\d{2}-\d{2}", newest("Overview")).group())
OV_END = START + pd.Timedelta(days=len(overview) - 1)  # Overview has one row per day

def to_date(col):
    """'November 18' -> Timestamp. Files can end a few days off the Overview (exported another day;
    FollowerActivity is always the last 7 days), so: last row = that day nearest OV_END, then walk
    back to the first row, year-1 each time the month jumps up."""
    md = pd.to_datetime(col + " 2000", format="%B %d %Y")  # 2000 is a leap year, so 'February 29' parses
    last = md.iloc[-1]
    year = min((OV_END.year + k for k in (-1, 0, 1)), key=lambda y: abs(last.replace(year=y) - OV_END))
    out, prev = [], None
    for t in reversed(md.tolist()):
        if prev is not None and t.month > prev.month:
            year -= 1
        out.append(t.replace(year=year)); prev = t  # shortcut: Feb 29 in a non-leap year raises; fix if it ever happens
    return pd.Series(out[::-1], index=col.index)

for name, d in (("Overview", overview), ("Followers", fol), ("Viewers", viewers), ("Followers", act)):
    d["Date"] = to_date(d["Date"])
    off = abs((d["Date"].max() - OV_END).days)
    assert off <= 7, f"{name} zip ends {off} days from the Overview zip: export them at the same time"
END = max(d["Date"].max() for d in (overview, fol, viewers))  # newest day any file covers

# Content lists every video with views in the range, old ones too. The video ID's top 32 bits are the
# post time (unix secs, UTC); take the year from it, keep TikTok's local day from the 'Post time' text.
id_time = pd.to_datetime(videos["Video link"].str.extract(r"/video/(\d+)")[0].astype("int64") // 2**32, unit="s")
post = pd.to_datetime(videos["Post time"] + " " + id_time.dt.year.astype(str), format="%B %d %Y")
gap = (post - id_time).dt.days
videos["Post time"] = post.where(gap < 180, post - pd.DateOffset(years=1)).where(gap > -180, post + pd.DateOffset(years=1))
fol["Followers"] = fol["Followers"].where(fol["Followers"] > 0).ffill()  # export has 0-follower glitch days
