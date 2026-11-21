"""Learning picker (README v2 step 9): rank dances by what brought Brian new followers before.
Refilms: followers per take vs your usual; a dance whose last take did worse than the one before is "tired".
New dances: choreographer and sound track record (2+ of your posts each, else it's luck), the video's own views,
your ✓ / ✕ swipes. Each dance gets a score (1 = usual) and one plain reason line."""
import math

import pandas as pd

BIG_VIEWS = 100_000  # a new dance's video above this counts as proven


def rank(posts, ideas, refilms, liked, not_my_style, views):
    """posts: your non-ad posts with columns key, credit, music_id, new_followers, posted_at.
    ideas: [{key, credit, author, video_id}] new dances. refilms: keys of dances you've posted.
    liked: keys you ✓'d. not_my_style: lowercased dc credits / @authors you ✕'d as "Not my style".
    views: {video_id: views}. Returns {key: {"score", "why", "tired"}}."""
    p = posts.dropna(subset=["new_followers"])
    usual = max(p["new_followers"].median(), 1) if len(p) else 1
    track = lambda col: {k: g.median() / usual for k, g in p.groupby(col)["new_followers"] if len(g) >= 2 and k}
    by_credit, by_sound = track("credit"), track("music_id")
    out = {}

    for key in refilms:
        takes = p[p["key"] == key].sort_values("posted_at")["new_followers"]
        if takes.empty:
            continue
        m = takes.median()
        tired = len(takes) >= 2 and takes.iloc[-1] < takes.iloc[-2]
        why = (f"Last take got +{takes.iloc[-1]:.0f} followers, less than the one before. Give it a rest." if tired
               else f"Brings +{m:.0f} followers a take (you usually get +{usual:.0f}).")
        out[key] = {"score": m / usual * (0.5 if tired else 1), "why": why, "tired": bool(tired)}

    for i in ideas:
        who = (i["credit"] or f"@{i['author']}").lower()
        factors = []  # (multiplier, reason)
        if i["credit"] in by_credit:
            r = by_credit[i["credit"]]
            factors.append((r, f"{i['credit']} dances bring you {r:.1f}x your usual followers."))
        sound = i["key"].split("|")[0]
        if sound in by_sound:
            r = by_sound[sound]
            factors.append((r, f"This sound brought you {r:.1f}x your usual followers."))
        v = views.get(i["video_id"]) or 0
        if v >= BIG_VIEWS:
            factors.append((1.5, f"{v / 1000:.0f}K views for @{i['author']}."))
        if i["key"] in liked:
            factors.append((1.5, "You ✓'d it on Home."))
        if who in not_my_style:
            factors.append((0.5, f"You said \"Not my style\" to a {who} dance."))
        score = math.prod(f for f, _ in factors)
        why = max(factors, key=lambda f: abs(math.log(f[0])))[1] if factors else "New: no track record yet."
        out[i["key"]] = {"score": score, "why": why, "tired": False}
    return out


# self-check
_posts = pd.DataFrame({"key": ["s1|@ol", "s1|@ol", "s2|", "s3|@x", "s3|@x"], "credit": ["@ol", "@ol", "", "@x", "@x"],
                       "music_id": ["s1", "s1", "s2", "s3", "s3"], "new_followers": [40, 20, 10, 10, 2],
                       "posted_at": [1, 2, 3, 4, 5]})
_r = rank(_posts, [{"key": "s9|@ol", "credit": "@ol", "author": "a", "video_id": "v"},
                   {"key": "s8|", "credit": "", "author": "b", "video_id": "w"},
                   {"key": "s7|", "credit": "", "author": "c", "video_id": "z"}],
          ["s1|@ol", "s3|@x"], {"s8|"}, {"@c"}, {"w": 200_000})
assert _r["s1|@ol"]["tired"] and _r["s1|@ol"]["score"] == 30 / 10 * 0.5, _r  # 40 then 20: tired
assert _r["s3|@x"]["tired"] and "rest" in _r["s3|@x"]["why"]
assert _r["s9|@ol"]["score"] == 3 and "@ol dances" in _r["s9|@ol"]["why"], _r["s9|@ol"]  # @ol median 30 / usual 10
assert _r["s8|"]["score"] == 1.5 * 1.5 and _r["s7|"]["score"] == 0.5 and "Not my style" in _r["s7|"]["why"]
