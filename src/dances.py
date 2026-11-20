"""Group Studio posts into dances: same sound + same "dc: @creator" = same dance.
A caption with no dc: handle counts as the sound's general dance."""
import re

import pandas as pd

# the credit runs from "dc:" to the next | # ( ) or line end, e.g. "dc: @Jackson Diep" or "dc: @Roma @swegi"
DC = re.compile(r"(?i)\bdc\s*:?\s*(@[^|#()\n]+)")


ME = re.compile(r"(?i)\bdc\s*:?\s*(me|us)\b")  # "dc: me" = the poster made the dance


def credit(caption, author=None):
    m = DC.search(caption or "")
    if m:
        return " ".join(m.group(1).split())
    return f"@{author}" if author and ME.search(caption or "") else ""


def dance_key(music_id, caption, author=None):
    return f"{music_id}|{credit(caption, author).lower()}"


def song(title, author):
    """Song name for a sound: "Booty Wurk · Niana Guerrero". Generic sounds stay "original sound · jada"."""
    t = title or "unknown sound"
    return f"{t} · {author}" if author and author not in t else t


def dance_name(title, author, caption):
    """Readable name: "son original · Rmx2Rmx, dc @OL". Sound titles are often a generic "original sound"
    in any language, so the uploader is always added."""
    t = song(title, author)
    c = credit(caption)
    return f"{t}, dc {c}" if c else t


def dances(posts):
    """One row per dance from Studio posts (needs music_id): times done, best post, last posted."""
    p = posts.dropna(subset=["music_id"]).copy()
    p["key"] = [dance_key(m, c) for m, c in zip(p["music_id"], p["title"])]
    p["name"] = [dance_name(t, a, c) for t, a, c in zip(p["music_title"], p["music_author"], p["title"])]
    best = p.sort_values("views", ascending=False).drop_duplicates("key").set_index("key")
    g = p.groupby("key").agg(times=("video_id", "size"), last_posted=("posted_at", "max"))
    best["label"] = best["name"]  # named by song + dc credit, same as Favorites
    out = g.join(best[["label", "name", "video_id", "views"]].rename(columns={"video_id": "best_video_id", "views": "best_views"}))
    return out.reset_index().sort_values(["times", "best_views"], ascending=False)


# self-check: dc: handle splits one sound into separate dances; no handle = general dance
assert dance_key("1", "no hands dc: @Swegi #fyp") == "1|@swegi"
assert dance_key("1", "no hands DC @river.noviin") == "1|@river.noviin"
assert dance_key("1", "x (dc: @Roma)") == "1|@roma"
assert dance_key("1", "x | dc: @Jackson Diep | 🕺: @Zay ") == "1|@jackson diep"
assert dance_key("1", "Dc:me #dance", "lz.zb") == "1|@lz.zb" and dance_key("1", "DC: ME 💓", "big") == "1|@big"
assert dance_key("1", "dc : 🙌🏼🪩 #csws", "x") == "1|"
assert song("Booty Wurk", "Niana Guerrero") == "Booty Wurk · Niana Guerrero"
assert dance_key("1", "no hands tag dc") == dance_key("1", "HE DID IT AGAIN @Roma") == "1|"
assert dance_name("son original", "Rmx2Rmx", "x dc: @OL ") == "son original · Rmx2Rmx, dc @OL"
assert dance_name("original sound - swegi", "swegi", "") == "original sound - swegi"
_d = dances(pd.DataFrame({"video_id": ["a", "b", "c"], "music_id": ["1", "1", "1"], "posted_at": [1, 2, 3],
                          "title": ["dc: @x", "dc: @x", "hi"], "views": [5, 9, 1],
                          "music_title": ["No Hands"] * 3, "music_author": ["s"] * 3}))
assert _d.set_index("key").loc["1|@x", ["times", "best_video_id", "label"]].tolist() == [2, "b", "No Hands, dc @x"], _d
