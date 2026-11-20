"""Step 5: turn step 4 patterns into what to POST, IMPROVE, TEST.
Run: python3 src/recommend.py
Rules read the numbers each run; nothing is hardcoded to one export."""
import json, os
import pandas as pd
from data import act, fol, END
from patterns import v, views, tags, top, link_strength, NAMES, TESTABLE, bucket, TOP_N

# column -> (what to do if more goes with more views, what to do if less does; None = don't advise)
LEVERS = {
    "caption_len": ("Write longer captions", "Write shorter captions"),
    "hashtags": ("Use more hashtags", "Use fewer hashtags"),
    "likes_per_1k": ("End on a moment people want to like (a big move, a funny face, a loop)", None),
    "comments_per_1k": ("Give people a reason to comment: ask a question in the caption", None),
    "shares_per_1k": ("Make videos people want to send to a friend: tag-a-friend dances, duets, 'you vs me' hooks", None),
    # Studio-only columns; skipped when patterns.py runs on exports
    "kept_3s": ("Hook viewers in the first second: open on your best move, not a slow start", None),
    "full_watch_rate": ("Make it easy to watch to the end: tighter cuts, end on a loop", None),
    # no gap_days lever: posts are almost all <1.5 days apart, too little spread to advise on
}

post, improve, test = [], [], []
med = lambda s: s.median()
top_v, rest_v = v[top].sort_values("Total views", ascending=False), v[~top]

# POST: what already worked, and when
typical_fol = med(v["followers_per_1k_views"])
best_fol = v.nlargest(3, "followers_per_1k_views")
post.append("Make more videos like these. They won you the most new followers for the views they got: "
            + "; ".join(f"'{t.strip()}'" for t in best_fol["title"])
            + f". They brought {best_fol['followers_per_1k_views'].min():g}-{best_fol['followers_per_1k_views'].max():g} "
              f"new followers per 1,000 views; a typical video of yours brings {typical_fol:g}.")
post.append("Do a part 2 or a new take on your biggest hits: " + "; ".join(
    f"'{t.strip()}' ({n:,} views)" for t, n in zip(top_v["title"], top_v["Total views"]))
    + ". Something in these worked: reuse the song, the dance style or the idea.")
hours = act.groupby("Hour")["Active followers"].mean().nlargest(3).index.sort_values()
day = act.groupby(act["Date"].dt.day_name())["Active followers"].mean().idxmax()
# shortcut: activity is one week only; re-check with each new export
at = [f"{h}:00" for h in hours]  # listed, not a range: the busiest hours can be far apart (9, 13, 20)
post.append(f"Post at {', '.join(at[:-1])} or {at[-1]}. That's when most of your followers are on TikTok. "
            f"{day} is their busiest day.")
quiet = (fol["Date"].max() - v["Post time"].max()).days
if quiet > 14:
    # Content export seems capped at 15 videos (top by views?), so newer low-view posts can be missing
    post.insert(0, f"Your newest videos aren't reaching your usual views yet: none made your top {len(v)}, "
                   f"and the newest one that did is {quiet} days old.")

# IMPROVE (strong link) / TEST (weak link)
for col, (more, less) in ((c, l) for c, l in LEVERS.items() if c in v):
    c = link_strength(col)
    b = bucket(c)
    t, r = med(top_v[col]), med(rest_v[col])
    action = more if c > 0 else less
    pc = "%" if NAMES[col].startswith("%") else ""  # "14.1% who watched", not "14.1 % who watched"
    sp = "" if pc else " "
    if b == "act" and action:  # never advise fewer likes/comments/shares: they're outcomes
        improve.append(f"{action}. Your {TOP_N} biggest videos had {t:g}{sp}{NAMES[col]}; your other videos had {r:g}{pc}.")
    elif b == "test" and col in TESTABLE and t != r:  # same median on both sides = nothing to test
        test.append(f"Not sure yet if {NAMES[col]} matters. Your {TOP_N} biggest videos had {t:g}, the others {r:g}. "
                    f"Next 4 videos: make 2 with about {t:g} {NAMES[col]} and 2 with about {r:g}, then compare views.")

if med(top_v["followers_per_1k_views"]) < typical_fol:
    improve.append(f"Your viral videos bring few new followers: {med(top_v['followers_per_1k_views']):g} per 1,000 views, "
                   f"vs {typical_fol:g} on a typical video. Give viewers a reason to follow: make it a series, "
                   f"tease a 'part 2', or say 'follow for more' at the end.")

# hashtags nobody can judge because they never change
always = [t for t, n in tags.explode().value_counts().items() if n >= 0.8 * len(v)]
if always:
    test.append(f"You put {' '.join(always)} on almost every video, so there's no way to tell if it helps. "
                f"Next 4 videos: 2 with it, 2 with more specific tags instead (like the song or dance name).")
wk = med(v.loc[v["weekend"], "Total views"]) / med(v.loc[~v["weekend"], "Total views"])
if 0.5 < wk < 2:
    test.append(f"Weekend vs weekday doesn't clearly matter yet. Post your next 2 on {day} and see if they beat "
                f"{med(views):,.0f} views (a typical video of yours).")

for head, items in (("WHAT TO POST", post), ("WHAT TO FIX", improve), ("WHAT TO TRY", test)):
    print(f"== {head} ==")
    print("\n".join(f"{i}. {s}" for i, s in enumerate(items, 1)) or "Nothing from this data.")
    print()
print(f"Based on {len(v)} of your videos. These are educated guesses from your own numbers: "
      f"try them, then run ./run.sh track after your next export.")

# step 6: save targets so track.py can score the next videos against them
snap = {
    "export_date": str(END.date()),
    "last_post": str(v["Post time"].max().date()),  # exports can lag; track.py counts videos after this as new
    "median_views": float(med(views)),
    "median_followers_per_1k": float(med(v["followers_per_1k_views"])),
    "shares_per_1k_target": float(med(top_v["shares_per_1k"])),
    "caption_len": [float(med(top_v["caption_len"])), float(med(rest_v["caption_len"]))],
    "common_tags": always,
    "recommendations": {"post": post, "improve": improve, "test": test},
}
os.makedirs("data/recs", exist_ok=True)
path = f"data/recs/{snap['export_date']}.json"
with open(path, "w") as fh:
    json.dump(snap, fh, indent=1, ensure_ascii=False)
print(f"Saved targets to {path} for step 6 tracking.")
