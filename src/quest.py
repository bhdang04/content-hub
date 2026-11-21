"""Weekly quest (README v2 step 7): the pages Brian opens himself so Claude can read them, and saving what was read.
No TikTok requests here: Claude reads each open tab with scripts/quest_read.js and saves the JSON it returns:
    python3 src/quest.py save <file.json>      (prints what changed; ticks the step on the Quest page)"""
import glob, json, re, sqlite3, subprocess, sys, time, zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

DB = "data/hub.db"
QUEST = Path("data/raw/quest")
TAGS = ["dancechallenge", "1persondance", "dance", "choreography", "viraldance"]  # one per week, in turn
STUDIO = "https://www.tiktok.com/tiktokstudio/analytics/{}?qa_enter_from=analytics"
SCHEMA = "CREATE TABLE IF NOT EXISTS quest (week TEXT, step TEXT, done_at INTEGER, note TEXT, PRIMARY KEY (week, step))"
TRAFFIC = {"For You": "For You", "Search": "Search", "Personal profile": "Personal Profile", "Following": "Follow",
           "Other": "Others", "Sound": "Sound"}  # Studio page label -> the key studio_import.py reads


def week(d=None):
    y, w, _ = (d or date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def me():
    """Your handle, from the newest Content export's video links (so it isn't typed into the code)."""
    for z in sorted(glob.glob("data/raw/**/Content*.zip", recursive=True), reverse=True):
        m = re.search(r"tiktok\.com/@([\w.]+)/video", zipfile.ZipFile(z).read("Content.csv").decode("utf-8-sig"))
        if m:
            return m.group(1)
    raise SystemExit("No Content export yet, so the quest doesn't know your handle.")


def count(x):
    """'12K' / '1.2M' / '9,996' -> int (same as the Competitors page)."""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm]?)", str(x).replace(",", "").strip())
    return round(float(m[1]) * {"": 1, "k": 1e3, "m": 1e6}[m[2].lower()]) if m else None


def seconds(x):
    """'5.56s' / '1m:05s' / '1m 5s' -> 5.56 / 65.0"""
    m = re.fullmatch(r"(?:(\d+)m\W*)?(\d+(?:\.\d+)?)s", (x or "").strip())
    return int(m[1] or 0) * 60 + float(m[2]) if m else None


def latest_profile():
    files = sorted(QUEST.glob("profile-*.json"))
    return json.loads(files[-1].read_text()) if files else None


def migrate(con):
    con.execute(SCHEMA)
    if "read_at" not in {r[1] for r in con.execute("PRAGMA table_info(competitors)")}:  # made before the quest
        con.execute("ALTER TABLE competitors ADD COLUMN read_at INTEGER")


def steps(con):
    """This week's pages, in order, with done flags. Studio steps show once the profile is read."""
    wk = week()
    done = {s: n for s, n in con.execute("SELECT step, note FROM quest WHERE week = ?", (wk,))}
    handle = me()
    out = [{"step": "profile", "label": "Your profile", "why": "finds your new posts and their sounds",
            "url": f"https://www.tiktok.com/@{handle}"}]
    prof = latest_profile()
    if prof and "profile" in done:
        read = {r[0] for r in con.execute("SELECT video_id FROM posts")}
        now = time.time()
        for r in prof["posts"]:
            p = dict(zip(prof["cols"], r))
            # read each post once, after 3 days: most of its views are in by then
            if p["video_id"] not in read and now - p["posted_at"] > 3 * 86400:
                out.append({"step": f"studio:{p['video_id']}", "label": f"Analytics: {p['caption'][:50] or '(no caption)'}",
                            "why": "watch time, retention, traffic", "url": STUDIO.format(p["video_id"])})
    comp = con.execute("SELECT handle FROM competitors ORDER BY COALESCE(read_at, 0), added_at LIMIT 2").fetchall()
    out += [{"step": f"competitor:{h}", "label": f"@{h}", "why": "their top hits this month",
             "url": f"https://www.tiktok.com/@{h}"} for (h,) in comp]
    tag = TAGS[int(wk[-2:]) % len(TAGS)]
    out.append({"step": f"tag:{tag}", "label": f"#{tag}", "why": "trending dances for Home",
                "url": f"https://www.tiktok.com/tag/{tag}"})
    for s in out:
        s["done"] = s["step"] in done
        s["note"] = done.get(s["step"])
    return out


def tick(con, step, note):
    with con:
        con.execute("INSERT OR REPLACE INTO quest VALUES (?, ?, strftime('%s','now'), ?)", (week(), step, note))


def fmt(p):
    """Competitor format from hashtags; None when the caption doesn't say."""
    c = p["caption"].lower()
    if re.search(r"#(2persondance|duo\w*|coupledance)\b", c):
        return "2-person"
    if re.search(r"#(1persondance|solodance)\b", c):
        return "1-person"
    return None


def save(path):
    d = json.loads(Path(path).read_text())
    con = sqlite3.connect(DB)
    migrate(con)
    QUEST.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    posts = [dict(zip(d["cols"], r)) for r in d.get("posts", [])]
    if d["kind"] == "profile":
        handle = re.search(r"tiktok\.com/@([\w.]+)", d["url"])[1]
        if handle == me():
            (QUEST / f"profile-{stamp}.json").write_text(json.dumps(d, ensure_ascii=False))
            tick(con, "profile", f"{len(posts)} posts from the last 14 days")
            return f"Your profile: {len(posts)} recent posts."
        with con:
            if not con.execute("SELECT 1 FROM competitors WHERE handle = ?", (handle,)).fetchone():
                raise SystemExit(f"@{handle} isn't on your Competitors page. Add it there first.")
            con.execute("UPDATE competitors SET followers = COALESCE(?, followers), read_at = strftime('%s','now') WHERE handle = ?",
                        (count(d.get("followers")), handle))
            con.execute("DELETE FROM competitor_posts WHERE handle = ?", (handle,))  # their current top hits replace the old
            con.executemany("INSERT INTO competitor_posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))",
                            [(p["video_id"], handle, p["views"], p["likes"], p["comments"], p["shares"], p["caption"],
                              f"{p['music_title']} · {p['music_author']}", fmt(p)) for p in posts])
        tick(con, f"competitor:{handle}", f"{len(posts)} hits")
        return f"@{handle}: {len(posts)} top hits saved."
    if d["kind"] == "tag":
        tag = re.search(r"/tag/([^/?#]+)", d["url"])[1]
        out = QUEST.parent / "trending" / f"{stamp}-{tag}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps({**p, "tag": tag}, ensure_ascii=False) + "\n" for p in posts))
        tick(con, f"tag:{tag}", f"{len(posts)} posts")
        con.close()
        subprocess.run([sys.executable, "src/studio_import.py"], check=True, capture_output=True)  # loads the newest trending file
        return f"#{tag}: {len(posts)} posts from the last 30 days."
    if d["kind"] == "studio":
        vid = d["video_id"]
        prof = latest_profile()
        p = next((dict(zip(prof["cols"], r)) for r in prof["posts"] if r[0] == vid), None) if prof else None
        if not p:
            raise SystemExit("Read your profile first: it has this post's time and sound.")
        if not d.get("counts") or not d.get("retention"):
            raise SystemExit("The analytics page wasn't fully loaded. Wait a second and read it again.")
        ret = d["retention"]
        if [round(t) for t, _ in ret] != list(range(len(ret))):  # posts table keeps one point per second
            raise SystemExit(f"Retention points aren't one per second ({[t for t, _ in ret[:4]]}...). Needs a code change.")
        views, likes, comments, shares, saves = d["counts"]
        row = {"video_id": vid, "posted_at": p["posted_at"], "title": p["caption"], "length_ms": (p["length_s"] or 0) * 1000,
               "views": views, "likes": likes, "comments": comments, "shares": shares, "saves": saves,
               "avg_watch_s": seconds(d["avg_watch"]), "full_watch_rate": float(d["full_watch"].rstrip("%")) / 100,
               "new_followers": count(d["new_followers"]),
               "traffic": {TRAFFIC.get(k, k): v / 100 for k, v in d["traffic"]},
               "retention": [y for _, y in ret], "search_terms": [[k, v / 100] for k, v in d["search_terms"]],
               "read_at": int(time.time()), "private_status": 0,
               "music_id": p["music_id"], "music_title": p["music_title"], "music_author": p["music_author"]}
        out = QUEST.parent / "studio" / f"{date.today()}-quest.jsonl"
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        tick(con, f"studio:{vid}", f"{views:,} views")
        con.close()
        subprocess.run([sys.executable, "src/studio_import.py"], check=True, capture_output=True)
        return f"Post {vid}: {views:,} views, {row['full_watch_rate']:.0%} watched to the end."
    raise SystemExit(f"Unknown kind: {d['kind']}")


assert count("12K") == 12000 and count("9,996") == 9996 and count("") is None
assert seconds("5.56s") == 5.56 and seconds("1m:05s") == 65 and seconds("") is None
assert fmt({"caption": "x #2persondance #cali"}) == "2-person" and fmt({"caption": "#1persondance"}) == "1-person"
assert fmt({"caption": "#duo #cali"}) == "2-person" and fmt({"caption": "fun dance"}) is None
assert week(date(2026, 11, 20)) == "2026-W47"

if __name__ == "__main__":
    if sys.argv[1:2] != ["save"] or len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(save(sys.argv[2]))
