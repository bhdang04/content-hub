"""Group Studio posts into dances: same sound + same "dc: @creator" = same dance.
A caption with no dc: handle counts as the sound's general dance."""
import re

import pandas as pd

# the credit runs from "dc:" to the next | # ( ) or line end, e.g. "dc: @Jackson Diep" or "dc: @Roma @swegi"
DC = re.compile(r"(?i)\bdc\s*:?\s*(@[^|#()\n]+)")


def credit(caption):
    m = DC.search(caption or "")
    return " ".join(m.group(1).split()) if m else ""


def dance_key(music_id, caption):
    return f"{music_id}|{credit(caption).lower()}"


def dance_name(title, author, caption):
    """Readable name: "son original · Rmx2Rmx, dc @OL". Sound titles are often a generic "original sound"
    in any language, so the uploader is always added."""
    t = title or "unknown sound"
    if author and author not in t:
        t = f"{t} · {author}"
    c = credit(caption)
    return f"{t}, dc {c}" if c else t


def label(caption):
    """Caption text before the hashtags/credits: what you called the video ("rich girl")."""
    return re.split(r"[#|]|\bdc\b", caption or "", flags=re.I)[0].strip()


def dances(posts):
    """One row per dance from Studio posts (needs music_id): times done, best post, last posted."""
    p = posts.dropna(subset=["music_id"]).copy()
    p["key"] = [dance_key(m, c) for m, c in zip(p["music_id"], p["title"])]
    p["name"] = [dance_name(t, a, c) for t, a, c in zip(p["music_title"], p["music_author"], p["title"])]
    best = p.sort_values("views", ascending=False).drop_duplicates("key").set_index("key")
    g = p.groupby("key").agg(times=("video_id", "size"), last_posted=("posted_at", "max"))
    best["label"] = [label(c) or n for c, n in zip(best["title"], best["name"])]  # best video's caption names the dance
    out = g.join(best[["label", "name", "video_id", "views"]].rename(columns={"video_id": "best_video_id", "views": "best_views"}))
    return out.reset_index().sort_values(["times", "best_views"], ascending=False)


# self-check: dc: handle splits one sound into separate dances; no handle = general dance
assert dance_key("1", "no hands dc: @Swegi #fyp") == "1|@swegi"
assert dance_key("1", "no hands DC @river.noviin") == "1|@river.noviin"
assert dance_key("1", "x (dc: @Roma)") == "1|@roma"
assert dance_key("1", "x | dc: @Jackson Diep | 🕺: @Zay ") == "1|@jackson diep"
assert dance_key("1", "no hands tag dc") == dance_key("1", "HE DID IT AGAIN @Roma") == "1|"
assert dance_name("son original", "Rmx2Rmx", "x dc: @OL ") == "son original · Rmx2Rmx, dc @OL"
assert dance_name("original sound - swegi", "swegi", "") == "original sound - swegi"
assert label("rich girl | #1persondance | dc: @OL") == "rich girl" and label("#fyp") == ""
_d = dances(pd.DataFrame({"video_id": ["a", "b", "c"], "music_id": ["1", "1", "1"], "posted_at": [1, 2, 3],
                          "title": ["dc: @x", "dc: @x", "hi"], "views": [5, 9, 1],
                          "music_title": ["No Hands"] * 3, "music_author": ["s"] * 3}))
assert _d.set_index("key").loc["1|@x", ["times", "best_video_id", "label"]].tolist() == [2, "b", "No Hands, dc @x"], _d
