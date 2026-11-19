"""Step 4: find what goes with more views, explain it in plain English.
Run: python3 src/patterns.py
Small sample (15 videos): every finding is a hint to test, not proof.
Exports have no post hour or video length, so those are not checked."""
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

v = videos.sort_values("Post time").reset_index(drop=True)
views = v["Total views"]
cap = v["Video title"].astype(str)
tags = cap.str.lower().str.findall(r"#\w+")
v["caption_len"] = cap.str.len()
v["hashtags"] = tags.str.len()
for k in ("likes", "comments", "shares"):
    v[f"{k}_per_1k"] = (v[f"Total {k}"] / views.where(views > 0) * 1000).round(1)
v["days_since_last_post"] = v["Post time"].diff().dt.days
v["weekend"] = v["Post time"].dt.dayofweek >= 5
# shortcut: posts < 3 days apart share the window, so their gain is double-counted; fine for spotting outliers
gain = fol.set_index("Date")["Followers"].diff()
v["followers_3d"] = [gain.loc[d:d + pd.Timedelta(days=2)].sum() for d in v["Post time"]]
v["followers_per_1k_views"] = (v["followers_3d"] / views.where(views > 0) * 1000).round(1)

cols = ["caption_len", "hashtags", "likes_per_1k", "comments_per_1k", "shares_per_1k",
        "days_since_last_post", "followers_per_1k_views"]

top = views >= views.nlargest(3).min()
v["title"] = cap.str[:40]

if __name__ == "__main__":
    print(f"== Top 3 videos vs other {(~top).sum()} (medians) ==")
    print(v.groupby(top.map({True: "top 3", False: "rest"}))[cols].median().T.round(1).to_string())

    print("\n== What goes with views (rank correlation, -1..+1) ==")
    for c in cols:
        print(f"{c:24} {link(v[c], views)}")

    print("\n== With vs without ==")
    lines = [compare(views, v["weekend"], "Posted Sat/Sun")]
    for tag in sorted(set(tags.explode().dropna())):
        lines.append(compare(views, tags.apply(lambda t: tag in t), tag))
    print("\n".join(l for l in lines if l) or "Nothing: every group too small.")

    print("\n== Follower conversion (followers gained in 3 days after post, per 1k views) ==")
    print(v[["title", "Post time", "Total views", "followers_3d", "followers_per_1k_views"]]
          .sort_values("followers_per_1k_views", ascending=False).to_string(index=False))
