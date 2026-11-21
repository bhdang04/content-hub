"""Step 4: find what goes with more views, explain it in plain English.
Run: python3 src/patterns.py
Uses Studio per-post data (data/hub.db, ~60 posts, ads left out) when it exists, else the Content
exports (~15 top videos). Small sample either way: every finding is a hint to test, not proof.
Post hour and video length are not checked."""
import json, os, sqlite3
import pandas as pd
from data import videos, fol

def compare(views, mask, label):
    """Median views with vs without mask, as one line. None if either group has < 2 videos."""
    a, b = views[mask], views[~mask]
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = a.median(), b.median()
    r = ma / mb if mb else float("inf")
    size = max(r, 1 / r) if r else float("inf")
    return (f"{label}: {ma:,.0f} median views (n={len(a)}) vs {mb:,.0f} without (n={len(b)}) "
            f"-> {size:.1f}x {'MORE' if r >= 1 else 'FEWER'}{'' if size >= 2 else ' (small gap)'}")

def corr(x, y):
    """Spearman rank correlation without needing scipy."""
    return x.rank().corr(y.rank())

TESTABLE = {"caption_len", "hashtags"}  # you set these directly; rates are outcomes

def bucket(c):
    """Rank correlation -> act on it, test it, or skip it. One rule for recommend.py and the dashboard."""
    if pd.isna(c) or abs(c) < 0.2:
        return "skip"
    return "act" if abs(c) >= 0.4 else "test"

def verdict(col, c):
    """Rank correlation -> what it means, in words (dashboard Patterns page)."""
    b = bucket(c)
    if b == "skip":
        return "No real difference"
    sure = "Clear sign" if b == "act" else "Maybe"
    if col in TESTABLE:
        return f"{sure}: {'more' if c > 0 else 'less'} of this went with more views" + ("" if b == "act" else " (test it)")
    if c > 0:
        return f"{sure}: big videos get more of these. Aim for it."
    return f"{sure}: big videos get fewer (normal: strangers watch)"

def link(x, y):
    """Rank correlation in plain words."""
    c = corr(x, y)
    word = "more views" if c > 0 else "fewer views"
    return f"{c:+.2f} " + (f"higher goes with {word}" if abs(c) >= 0.4 else "no clear link")

# self-check on toy data
_t = compare(pd.Series([10, 10, 1, 1]), pd.Series([True, True, False, False]), "x")
assert "10.0x MORE" in _t and "n=2" in _t, _t
assert compare(pd.Series([1, 2, 3]), pd.Series([True, False, False]), "x") is None
assert link(pd.Series([1, 2, 3]), pd.Series([1, 2, 3])).startswith("+1.00 higher goes with more views")
assert [bucket(x) for x in (0.5, -0.45, 0.3, -0.25, 0.1, float("nan"))] == ["act", "act", "test", "test", "skip", "skip"]
assert verdict("hashtags", 0.3) == "Maybe: more of this went with more views (test it)"
assert verdict("shares_per_1k", -0.5).startswith("Clear sign: big videos get fewer")

def split_followers(post_times, views, gain, days=3):
    """Credit each day's follower gain to videos posted in the `days` days up to it, split by views,
    so near-daily posts don't all claim the same followers. NaN = no follower data for its window."""
    credit = pd.Series(float("nan"), index=post_times.index)
    for day, g in gain.dropna().items():
        near = post_times.index[(post_times <= day) & (post_times > day - pd.Timedelta(days=days))]
        if len(near):
            w = views[near].clip(lower=1)
            credit[near] = credit[near].fillna(0) + g * w / w.sum()
    return credit

_d = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-03-01"])
_c = split_followers(pd.Series(_d), pd.Series([300, 100, 5]), pd.Series([40.0, 0.0], index=pd.to_datetime(["2026-01-02", "2026-01-03"])))
assert list(_c[:2]) == [30.0, 10.0] and pd.isna(_c[2]), _c  # 40 split 3:1 by views; no data for March

def studio_videos(db="data/hub.db"):
    """Studio per-post rows (every public post, real new-follower counts) in the Content-export column names.
    None if there's no Studio data. Ads left out: paid views would make them look like hits."""
    if not os.path.exists(db):
        return None
    con = sqlite3.connect(db)
    try:
        s = pd.read_sql("SELECT * FROM posts WHERE is_ad = 0", con)
    finally:
        con.close()
    if s.empty:
        return None
    # early reads cut captions at 100 chars; take the full one from a Content export when it has the video
    full = videos.set_index(videos["Video link"].str.extract(r"/video/(\d+)")[0])["Video title"]
    s["title"] = s["video_id"].map(full).where(s["title"].str.len() >= 100).fillna(s["title"])
    s = s.sort_values("posted_at").reset_index(drop=True)
    ret = s["retention_json"].map(json.loads)
    return pd.DataFrame({
        "Video title": s["title"],
        "Post time": pd.to_datetime(s["posted_at"], unit="s", utc=True).dt.tz_convert("America/Los_Angeles").dt.tz_localize(None),
        "Total views": s["views"], "Total likes": s["likes"], "Total comments": s["comments"], "Total shares": s["shares"],
        "Total saves": s["saves"], "new_followers": s["new_followers"],
        "kept_3s": ret.map(lambda r: r[3] if len(r) > 3 else None).astype(float),
        "full_watch_rate": s["full_watch_rate"],
        "gap_days": (s["posted_at"].diff() / 86400).round(1),
        "Video link": "https://www.tiktok.com/video/" + s["video_id"],
    })

studio = studio_videos()
STUDIO = studio is not None
v = (studio if STUDIO else videos.sort_values("Post time")).reset_index(drop=True)
views = v["Total views"]
cap = v["Video title"].astype(str)
tags = cap.str.lower().str.findall(r"#\w+")
v["caption_len"] = cap.str.len()
v["hashtags"] = tags.str.len()
for k in ("likes", "comments", "shares") + (("saves",) if STUDIO else ()):
    v[f"{k}_per_1k"] = (v[f"Total {k}"] / views.where(views > 0) * 1000).round(1)
# "days since previous post" only with Studio data: exports list ~25 posts, so their gaps are fake
v["weekend"] = v["Post time"].dt.dayofweek >= 5
if STUDIO:
    v["new_followers_est"] = v["new_followers"]  # Studio's own count
else:
    # shortcut: Content export holds ~15 top videos, so unlisted posts' followers get credited to listed ones
    v["new_followers_est"] = split_followers(v["Post time"], views, fol.set_index("Date")["Followers"].diff()).round(1)
v["followers_per_1k_views"] = (v["new_followers_est"] / views.where(views > 0) * 1000).round(1)

cols = ["caption_len", "hashtags", "likes_per_1k", "comments_per_1k", "shares_per_1k", "followers_per_1k_views"]
if STUDIO:
    v["kept_3s"] = (v["kept_3s"] * 100).round()
    v["full_watch_rate"] = (v["full_watch_rate"] * 100).round(1)
    cols += ["kept_3s", "full_watch_rate", "saves_per_1k", "gap_days"]
    TESTABLE.add("gap_days")
# plain-English names for the dashboard and recommend.py
NAMES = {"caption_len": "characters in the caption", "hashtags": "hashtags", "likes_per_1k": "likes per 1,000 views",
         "comments_per_1k": "comments per 1,000 views", "shares_per_1k": "shares per 1,000 views",
         "followers_per_1k_views": "new followers per 1,000 views",
         "kept_3s": "% still watching at 3s", "full_watch_rate": "% who watched to the end",
         "saves_per_1k": "saves per 1,000 views", "gap_days": "days since the post before"}

TOP_N = 6 if STUDIO else 3  # ~10% of 60 Studio posts; exports hold only ~15
top = views >= views.nlargest(TOP_N).min()

def link_strength(col):
    """Rank correlation with views, or NaN when it points the other way from the top-vs-rest medians
    shown next to it (e.g. "big videos get fewer likes" while the top ones have more): that's no clear sign."""
    c = corr(v[col], views)
    g = v.groupby(top)[col].median()
    return float("nan") if (g[True] - g[False]) * c < 0 else c
# caption without hashtags, @mentions or dance credits ("dc: @x", "tag dc"); all-hashtag captions kept as is
clean = (cap.str.replace(r"(?i)\b(tag\s+)?dc\b:?.*$", "", regex=True).str.replace(r"[#@]\S+", "", regex=True)
         .str.replace("|", "").str.strip().str.replace(r"\s{3,}.*$", "", regex=True))  # drop leftover credit words
v["title"] = clean.where(clean != "", cap).str[:40]

if __name__ == "__main__":
    print(f"== Top {TOP_N} videos vs other {(~top).sum()} (medians) ==" + (" [Studio data]" if STUDIO else " [Content exports]"))
    print(v.groupby(top.map({True: f"top {TOP_N}", False: "rest"}))[cols].median().T.round(1).to_string())

    print("\n== What goes with views (rank correlation, -1..+1) ==")
    for c in cols:
        print(f"{c:24} {link(v[c], views)}")

    print("\n== With vs without ==")
    lines = [compare(views, v["weekend"], "Posted Sat/Sun")]
    for tag in sorted(set(tags.explode().dropna())):
        lines.append(compare(views, tags.apply(lambda t: tag in t), tag))
    print("\n".join(l for l in lines if l) or "Nothing: every group too small.")

    print("\n== Follower conversion (new followers per 1k views) ==")
    print(v[["title", "Post time", "Total views", "new_followers_est", "followers_per_1k_views"]]
          .sort_values("followers_per_1k_views", ascending=False).to_string(index=False))
