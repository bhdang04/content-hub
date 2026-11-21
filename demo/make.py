"""Build fake demo data in demo/data/ (git-ignored), so anyone can run the dashboard: ./run.sh demo
Made from a seeded random generator only. Never reads data/ (your real exports and hub.db).
Every run wipes demo/data/ and builds it again, ending yesterday so the Plan page has current dates."""
import csv, io, json, os, random, shutil, sys, zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DEMO = Path(__file__).resolve().parent
OUT = DEMO / "data"
R = random.Random(7)  # same fake data every run
END = date.today() - timedelta(days=1)
HANDLE = "demo_dancer"
SOUNDS = [(f"7{100 + i}000000000000000", f"demo sound {i}", f"demo_artist{i}") for i in range(12)]
CHOREOS = [f"@demo.choreo{i}" for i in range(8)]
PULL = {c: 0.5 + R.random() * 2.5 for c in CHOREOS}  # how many followers each choreographer's dances bring


def day(d):
    return f"{d:%B} {d.day}"  # TikTok's export style: "November 3"


def zip_csv(path, files):
    """files: {name: (header, rows)}. Writes a zip of CSVs with a BOM, like TikTok Studio does."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        for name, (header, rows) in files.items():
            buf = io.StringIO()
            buf.write("﻿")
            w = csv.writer(buf, quoting=csv.QUOTE_ALL)
            w.writerow(header)
            w.writerows(rows)
            z.writestr(name, buf.getvalue())


def ts(d, hour):
    """Unix secs for a post on day d at hour (Pacific, roughly: UTC-8)."""
    return int(datetime(d.year, d.month, d.day, hour, R.randrange(60), tzinfo=timezone.utc).timestamp()) + 8 * 3600


def make_posts():
    """~70 posts over the last 150 days, every 1-3 days, posted 7-11pm."""
    posts, d = [], END - timedelta(days=150)
    while d <= END:
        sound, choreo = R.choice(SOUNDS), R.choice(CHOREOS)
        t = ts(d, R.randint(19, 22))
        views = int(R.lognormvariate(9.3, 1.0))
        posts.append({
            "video_id": str((t << 32) | R.getrandbits(32)),  # TikTok IDs start with the post time
            "posted_at": t, "day": d,
            "title": f"{R.choice(['new one', 'learned this', 'part 2', 'fav dance'])} | #dance #fyp | dc: {choreo}",
            "length_ms": R.randint(9000, 25000), "views": views,
            "likes": int(views * R.uniform(0.05, 0.15)), "comments": int(views * R.uniform(0.001, 0.004)),
            "shares": int(views * R.uniform(0.003, 0.02)), "saves": int(views * R.uniform(0.005, 0.02)),
            "avg_watch_s": round(R.uniform(5, 12), 2), "full_watch_rate": round(R.uniform(0.05, 0.3), 4),
            "new_followers": int(views / 1000 * PULL[choreo] * R.uniform(0.5, 1.5)),
            "music_id": sound[0], "music_title": sound[1], "music_author": sound[2],
            "traffic": {"For You": 0.85, "Search": 0.03, "Personal Profile": 0.07, "Follow": 0.03, "Others": 0.02},
            "retention": [1] + [round(0.8 * 0.9 ** i, 2) for i in range(12)],
            "search_terms": [], "private_status": 0, "read_at": ts(END, 12),
        })
        d += timedelta(days=R.randint(1, 3))
    return posts


def export(folder, days, posts):
    """One Studio export: Overview, Followers, Viewers, Content zips covering `days` days up to END."""
    span = [END - timedelta(days=i) for i in range(days - 1, -1, -1)]
    by_day = {}
    for p in posts:
        by_day.setdefault(p["day"], []).append(p)
    base = lambda d: 2000 + (d - span[0]).days * 5  # slow steady views from old videos
    views = {d: base(d) + sum(p["views"] // 3 for p in by_day.get(d, [])) for d in span}
    zip_csv(OUT / "raw" / folder / f"Overview_{span[0]}_demo.zip", {"Overview.csv": (
        ["Date", "Video Views", "Profile Views", "Likes", "Comments", "Shares"],
        [[day(d), views[d], views[d] // 300, views[d] // 12, views[d] // 900, views[d] // 400] for d in span])})
    total, hist = 1000, []
    for d in span:
        new = 2 + sum(p["new_followers"] for p in by_day.get(d, []))
        total += new
        hist.append([day(d), total, new])
    act = [[day(d), h, int(total * (0.3 + 0.4 * (h >= 18)))] for d in span[-7:] for h in range(24)]
    zip_csv(OUT / "raw" / folder / "Followers_demo.zip", {
        "FollowerHistory.csv": (["Date", "Followers", "Difference in followers from previous day"], hist),
        "FollowerActivity.csv": (["Date", "Hour", "Active followers"], act)})
    zip_csv(OUT / "raw" / folder / "Viewers_demo.zip", {"Viewers.csv": (
        ["Date", "Total Viewers", "New Viewers", "Returning Viewers"],
        [[day(d), v * 2 // 3, v // 2, v // 6] for d, v in views.items()])})
    top = sorted((p for p in posts if p["day"] >= span[0]), key=lambda p: -p["views"])[:15]  # exports hold ~15 videos
    zip_csv(OUT / "raw" / folder / "Content_demo.zip", {"Content.csv": (
        ["Time", "Video title", "Video link", "Post time", "Total likes", "Total comments", "Total shares", "Total views"],
        [[day(END), p["title"], f"https://www.tiktok.com/@{HANDLE}/video/{p['video_id']}", day(p["day"]),
          p["likes"], p["comments"], p["shares"], p["views"]] for p in top])})


def jsonl(folder, rows):
    (OUT / "raw" / folder).mkdir(parents=True, exist_ok=True)
    with open(OUT / "raw" / folder / f"{END}.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)


def idea(i, **extra):
    """A dance you haven't done: new sound + new choreographer."""
    t = ts(END - timedelta(days=R.randint(1, 10)), 12)
    return {"video_id": str((t << 32) | R.getrandbits(32)), "author": f"demo_creator{i}",
            "caption": f"try this | #dance | dc: @demo.new{i}", "music_id": f"7900{i:03d}00000000000",
            "music_title": f"new demo sound {i}", "music_author": f"new_artist{i}", **extra}


def main():
    assert OUT.parent == DEMO and OUT.name == "data"  # only ever wipe demo/data
    shutil.rmtree(OUT, ignore_errors=True)
    posts = make_posts()
    export("year", 365, posts)
    export("week", 7, posts)
    jsonl("studio", [{k: v for k, v in p.items() if k != "day"} for p in posts])
    jsonl("favorites", [idea(i, read_at=ts(END, 12)) for i in range(6)])
    jsonl("trending", [idea(i, views=R.randint(20_000, 900_000), likes=R.randint(1000, 50_000), saves=R.randint(100, 5000),
                            posted_at=ts(END - timedelta(days=2), 12), tag="dance") for i in range(6, 14)])
    sys.path.insert(0, str(DEMO.parent / "src"))
    os.chdir(DEMO)  # the importer writes data/hub.db relative to here
    import studio_import
    studio_import.main()
    print(f"Demo data ready in {OUT} ({len(posts)} fake posts, ending {END}).")


if __name__ == "__main__":
    main()
