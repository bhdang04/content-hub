"""Load + clean TikTok Studio zips from data/raw/. Shared by analyze.py and patterns.py."""
import glob, zipfile
import pandas as pd

def load(prefix, name):
    z = glob.glob(f"data/raw/{prefix}*.zip")[0]
    return pd.read_csv(zipfile.ZipFile(z).open(name))

videos = load("Content", "Content.csv")
overview = load("Overview", "Overview.csv")
fol = load("Followers", "FollowerHistory.csv")
viewers = load("Viewers", "Viewers.csv")
act = load("Followers", "FollowerActivity.csv")

ANCHOR_YEAR = 2025  # shortcut: exports have no year; taken from the Overview zip name (2025-11-18)

def add_year(col):
    """'November 18' -> Timestamp. Rows run oldest->newest; walk back from the last row, year-1 when month jumps up."""
    dt = pd.to_datetime(col + f" {ANCHOR_YEAR}", format="%B %d %Y")
    year, out, prev = ANCHOR_YEAR, [], None
    for t in reversed(dt.tolist()):
        if prev is not None and t.month > prev.month:
            year -= 1
        out.append(t.replace(year=year)); prev = t
    return pd.Series(out[::-1], index=col.index)

for d in (overview, fol, viewers):
    d["Date"] = add_year(d["Date"])
act["Date"] = add_year(act["Date"])
# Content is not in date order: take the latest date that is not after the anchor day
videos["Post time"] = pd.to_datetime(videos["Post time"] + f" {ANCHOR_YEAR}", format="%B %d %Y")
videos.loc[videos["Post time"] > "2025-11-18", "Post time"] -= pd.DateOffset(years=1)
fol["Followers"] = fol["Followers"].where(fol["Followers"] > 0).ffill()  # export has 0-follower glitch days
