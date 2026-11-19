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

videos = load("Content", "Content.csv")
overview = load("Overview", "Overview.csv")
fol = load("Followers", "FollowerHistory.csv")
viewers = load("Viewers", "Viewers.csv")
act = load("Followers", "FollowerActivity.csv")

# exports have no year. The Overview zip name holds the range START, e.g. Overview_2025-11-18_... covers 2025-11-18..2026-11-17
START = pd.Timestamp(re.search(r"\d{4}-\d{2}-\d{2}", newest("Overview")).group())

def to_date(col):
    """'November 18' -> first such date on/after START (ranges are at most a year)."""
    d = pd.to_datetime(col + f" {START.year}", format="%B %d %Y")  # shortcut: 'February 29' fails in non-leap START years
    return d.where(d >= START, d + pd.DateOffset(years=1))

for name, d in (("Overview", overview), ("Followers", fol), ("Viewers", viewers), ("Followers", act)):
    d["Date"] = to_date(d["Date"])
    assert d["Date"].is_monotonic_increasing, f"{name} zip covers a different date range than the newest Overview zip"
END = overview["Date"].max()

# Content lists every video with views in the range, old ones too. The video ID's top 32 bits are the
# post time (unix secs, UTC); take the year from it, keep TikTok's local day from the 'Post time' text.
id_time = pd.to_datetime(videos["Video link"].str.extract(r"/video/(\d+)")[0].astype("int64") // 2**32, unit="s")
post = pd.to_datetime(videos["Post time"] + " " + id_time.dt.year.astype(str), format="%B %d %Y")
gap = (post - id_time).dt.days
videos["Post time"] = post.where(gap < 180, post - pd.DateOffset(years=1)).where(gap > -180, post + pd.DateOffset(years=1))
fol["Followers"] = fol["Followers"].where(fol["Followers"] > 0).ffill()  # export has 0-follower glitch days
