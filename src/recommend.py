"""Step 5: turn step 4 patterns into what to POST, IMPROVE, TEST.
Run: python3 src/recommend.py
Rules read the numbers each run; nothing is hardcoded to one export."""
import json, os
import pandas as pd
from data import act, fol, END
from patterns import v, views, tags, top, corr

# column -> (plain name, what you can do about it)
LEVERS = {
    "caption_len": ("caption length (chars)", "write captions"),
    "hashtags": ("hashtag count", "use hashtags"),
    "likes_per_1k": ("likes per 1k views", "end on a moment worth liking"),
    "comments_per_1k": ("comments per 1k views", "ask a question in the caption"),
    "shares_per_1k": ("shares per 1k views", "make it worth sending to a friend (tag/duet/'you vs me' hooks)"),
    "days_since_last_post": ("days between posts", "space posts"),
}
TESTABLE = {"caption_len", "hashtags", "days_since_last_post"}  # you set these directly; rates are outcomes

def bucket(c):
    """Rank correlation -> act on it, test it, or skip it."""
    if pd.isna(c) or abs(c) < 0.2:
        return "skip"
    return "act" if abs(c) >= 0.4 else "test"

assert [bucket(x) for x in (0.5, -0.45, 0.3, -0.25, 0.1, float("nan"))] == ["act", "act", "test", "test", "skip", "skip"]

post, improve, test = [], [], []
med = lambda s: s.median()
top_v, rest_v = v[top].sort_values("Total views", ascending=False), v[~top]

# POST: what already worked, and when
best_fol = v.nlargest(3, "followers_per_1k_views")
post.append("More like your best follower-getters: " + "; ".join(
    f"'{r.title.strip()}' ({r.followers_per_1k_views} followers/1k views)" for r in best_fol.itertuples())
    + f". Median video gets {med(v['followers_per_1k_views'])}.")
post.append("New takes on your top-view videos: " + "; ".join(
    f"'{t.strip()}' ({n:,} views)" for t, n in zip(top_v["title"], top_v["Total views"])) + ".")
hours = act.groupby("Hour")["Active followers"].mean().nlargest(3).index.sort_values()
day = act.groupby(act["Date"].dt.day_name())["Active followers"].mean().idxmax()
# shortcut: activity is one week only; re-check with each new export
post.append(f"Post just before your followers peak: {', '.join(f'{h}:00' for h in hours)}. Busiest day: {day}.")
quiet = (fol["Date"].max() - v["Post time"].max()).days
if quiet > 14:
    # Content export seems capped at 15 videos (top by views?), so newer low-view posts can be missing
    post.insert(0, f"None of your newest posts are in this export's top {len(v)}: the newest one listed is {quiet} days old. "
                   f"New posts aren't reaching your usual views yet.")

# IMPROVE (strong link) / TEST (weak link)
for col, (name, action) in LEVERS.items():
    c, b = corr(v[col], views), bucket(corr(v[col], views))
    t, r = med(top_v[col]), med(rest_v[col])
    if b == "act" and (c > 0 or col in TESTABLE):  # never advise fewer likes/comments/shares: they're outcomes
        improve.append(f"{action[0].upper() + action[1:]}: {name} tracks views ({c:+.2f}). Top 3 median {t:g} vs rest {r:g}. Aim for {t:g}+."
                       if c > 0 else f"Lower {name}: more of it goes with fewer views ({c:+.2f}). Top 3 median {t:g} vs rest {r:g}.")
    elif b == "test" and col in TESTABLE and t != r:  # same median on both sides = nothing to test
        test.append(f"{name}: weak link ({c:+.2f}), top 3 median {t:g} vs rest {r:g}. "
                    f"Next 4 posts: 2 near {t:g}, 2 near {r:g}, keep all else the same.")

if med(top_v["followers_per_1k_views"]) < med(v["followers_per_1k_views"]):
    improve.append(f"Your biggest videos convert worst ({med(top_v['followers_per_1k_views'])} vs "
                   f"{med(v['followers_per_1k_views'])} followers/1k views overall). Give viewers a reason to follow: "
                   f"a series, 'part 2', or the format of your best follower-getters.")

# hashtags nobody can judge because they never change
always = [t for t, n in tags.explode().value_counts().items() if n >= 0.8 * len(v)]
if always:
    test.append(f"Hashtags {' '.join(always)} are on almost every video, so their effect is unknown. "
                f"Next 4 posts: 2 with them, 2 with niche tags instead.")
wk = med(v.loc[v["weekend"], "Total views"]) / med(v.loc[~v["weekend"], "Total views"])
if 0.5 < wk < 2:
    test.append(f"Weekend vs weekday: no clear winner ({wk:.1f}x). Post next 2 on {day}, compare to your median "
                f"{med(views):,.0f} views.")

for head, items in (("POST", post), ("IMPROVE", improve), ("TEST", test)):
    print(f"== {head} ==")
    print("\n".join(f"{i}. {s}" for i, s in enumerate(items, 1)) or "Nothing from this data.")
    print()
print(f"Based on {len(v)} videos. Treat as bets to test, not rules. Re-run after each new export.")

# step 6: save targets so track.py can score the next videos against them
snap = {
    "export_date": str(END.date()),
    "last_post": str(v["Post time"].max().date()),  # exports can lag; track.py counts videos after this as new
    "median_views": float(med(views)),
    "median_followers_per_1k": float(med(v["followers_per_1k_views"])),
    "shares_per_1k_target": float(med(top_v["shares_per_1k"])),
    "caption_len": [float(med(top_v["caption_len"])), float(med(rest_v["caption_len"]))],
    "days_since_last_post": [float(med(top_v["days_since_last_post"])), float(med(rest_v["days_since_last_post"]))],
    "common_tags": always,
    "recommendations": {"post": post, "improve": improve, "test": test},
}
os.makedirs("data/recs", exist_ok=True)
path = f"data/recs/{snap['export_date']}.json"
with open(path, "w") as fh:
    json.dump(snap, fh, indent=1, ensure_ascii=False)
print(f"Saved targets to {path} for step 6 tracking.")
