"""Load Studio per-post reads (data/raw/studio/*.jsonl, written by scripts/studio_read.js) into
the `posts` table of data/hub.db. Upsert by video_id; files load oldest-first so newer reads win.
Private posts are skipped. Usage: ./run.sh import"""
import glob, json, sqlite3

DB = "data/hub.db"

SCHEMA = """CREATE TABLE IF NOT EXISTS posts (
  video_id TEXT PRIMARY KEY, posted_at INTEGER, title TEXT, length_s REAL,
  views INTEGER, likes INTEGER, comments INTEGER, shares INTEGER, saves INTEGER,
  avg_watch_s REAL, full_watch_rate REAL, new_followers INTEGER,
  pct_for_you REAL, pct_search REAL, pct_profile REAL, pct_following REAL, pct_other REAL,
  retention_json TEXT, search_terms_json TEXT,
  is_ad INTEGER, read_at INTEGER, music_id TEXT, music_title TEXT, music_author TEXT)"""

COLS = ["video_id", "posted_at", "title", "length_s", "views", "likes", "comments", "shares", "saves",
        "avg_watch_s", "full_watch_rate", "new_followers", "pct_for_you", "pct_search", "pct_profile",
        "pct_following", "pct_other", "retention_json", "search_terms_json", "is_ad", "read_at",
        "music_id", "music_title", "music_author"]


def row(r):
    t = r.get("traffic", {})
    return {
        **{k: r.get(k) for k in ["video_id", "posted_at", "title", "views", "likes", "comments", "shares",
                                 "saves", "avg_watch_s", "full_watch_rate", "new_followers", "read_at",
                                 "music_id", "music_title", "music_author"]},
        "length_s": r["length_ms"] / 1000 if r.get("length_ms") else None,
        "pct_for_you": t.get("For You"), "pct_search": t.get("Search"),
        "pct_profile": t.get("Personal Profile"), "pct_following": t.get("Follow"),
        "pct_other": t.get("Others"),
        "retention_json": json.dumps(r.get("retention", [])),
        "search_terms_json": json.dumps(r.get("search_terms", []), ensure_ascii=False),
        # shortcut: paid/promoted posts show up as mostly "Others" traffic; switch to a real flag if Studio exposes one
        "is_ad": int((t.get("Others") or 0) > 0.5),
    }


def favorites(con):
    """Newest data/raw/favorites/*.jsonl (the "Tiktok Dances to Do" collection) replaces the ideas table:
    the collection's current state, so videos you un-saved drop out."""
    files = sorted(glob.glob("data/raw/favorites/*.jsonl"))
    if not files:
        return
    rows = [json.loads(l) for l in open(files[-1], encoding="utf-8")]
    cols = ["video_id", "author", "caption", "music_id", "music_title", "music_author", "read_at"]
    with con:
        con.execute("DROP TABLE IF EXISTS ideas")
        con.execute(f"CREATE TABLE ideas ({', '.join(c + ' TEXT' for c in cols)})")
        con.executemany(f"INSERT INTO ideas VALUES ({','.join('?' * len(cols))})", [[r.get(c) for c in cols] for r in rows])
    print(f"Imported {len(rows)} saved dances from {files[-1]}.")


def main():
    files = sorted(glob.glob("data/raw/studio/*.jsonl"))
    if not files:
        raise SystemExit("No data/raw/studio/*.jsonl yet. Ask Claude to read Studio first.")
    rows, skipped = {}, 0
    for f in files:
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r.get("error") or r.get("private_status", 0) != 0:
                skipped += 1
                continue
            rows[r["video_id"]] = row(r)
    con = sqlite3.connect(DB)
    with con:
        con.execute(SCHEMA)
        have = {r[1] for r in con.execute("PRAGMA table_info(posts)")}
        for c in ("music_id", "music_title", "music_author"):  # tables made before sounds were read
            if c not in have:
                con.execute(f"ALTER TABLE posts ADD COLUMN {c} TEXT")
        con.executemany(
            f"INSERT OR REPLACE INTO posts ({','.join(COLS)}) VALUES ({','.join(':' + c for c in COLS)})",
            rows.values())
    favorites(con)
    total, ads = con.execute("SELECT COUNT(*), SUM(is_ad) FROM posts").fetchone()
    assert total >= len(rows)
    print(f"Imported {len(rows)} posts from {len(files)} file(s), skipped {skipped} private/error. "
          f"Table now has {total} posts ({ads} ad).")


if __name__ == "__main__":
    main()
