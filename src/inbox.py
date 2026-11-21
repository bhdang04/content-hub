"""Auto-import, no TikTok reads: TikTok Studio export zips from ~/Downloads, and dance links shared from the phone
(iCloud Drive/Content Hub/inbox/links.txt, one link per line, via an iOS Shortcut) become Home swipe cards.
Run from the project root: ./run.sh inbox   (launchd runs it on every change in those folders)"""
import csv, io, os, re, shutil, sqlite3, sys, time, urllib.request, zipfile
from datetime import date
from pathlib import Path

DOWNLOADS = Path(os.environ.get("CONTENT_HUB_DOWNLOADS", Path.home() / "Downloads"))
INBOX = Path(os.environ.get("CONTENT_HUB_INBOX", Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Content Hub/inbox"))

KINDS = {"Content": "Content.csv", "Overview": "Overview.csv", "Followers": "FollowerHistory.csv", "Viewers": "Viewers.csv"}
LINK = re.compile(r"tiktok\.com/@([\w.]{1,40})/video/(\d{5,25})")
SHORT = re.compile(r"https://(?:vm|vt)\.tiktok\.com/\w{5,20}/?|https://www\.tiktok\.com/t/\w{5,20}/?")


def kind_of(body):
    """Which Studio export a zip is (Content/Overview/Followers/Viewers), or None."""
    f = io.BytesIO(body)
    if not zipfile.is_zipfile(f):
        return None
    names = zipfile.ZipFile(f).namelist()
    return next((k for k, c in KINDS.items() if c in names), None)


def out_name(kind, name):
    """Saved file name. Overview keeps TikTok's start date (data.py reads it); others get today's date,
    so old Content exports stay and get merged. None = Overview whose name lost its date."""
    if kind == "Overview":
        m = re.search(r"\d{4}-\d{2}-\d{2}", name)
        return m and f"Overview_{m.group()}_upload.zip"
    return f"{kind}_{date.today()}.zip"


def range_of(body, kind):
    """'year' or 'week' from the number of days inside; None for Content (it has no days: follows its batch)."""
    if kind == "Content":
        return None
    z = zipfile.ZipFile(io.BytesIO(body))
    days = sum(1 for _ in csv.reader(io.TextIOWrapper(z.open(KINDS[kind]), "utf-8-sig"))) - 1
    return "year" if days >= 28 else "week"


def import_exports(raw="data/raw"):
    """Move Studio zips out of Downloads into data/raw/year|week. Returns lines for the log."""
    found = []
    for p in sorted(DOWNLOADS.glob("*.zip"), key=os.path.getmtime):
        if not re.match(r"(Content|Overview|Follower|Viewers)", p.name):  # skip other zips without opening them
            continue
        if time.time() - p.stat().st_mtime > 14 * 86400:  # old downloads were already uploaded by hand; leave them
            continue
        body = p.read_bytes()
        k = kind_of(body)
        if k:
            found.append((p, k, range_of(body, k), p.stat().st_mtime))  # time read now: files move below
    log = []
    for p, k, r, t in found:
        if r is None:  # Content: same range as the export downloaded closest in time, else week (the weekly routine)
            near = min((x for x in found if x[2]), key=lambda x: abs(x[3] - t), default=None)
            r = near[2] if near and abs(near[3] - t) < 1800 else "week"
        name = out_name(k, p.name)
        if not name:
            log.append(f"skipped {p.name}: Overview without its start date in the name")
            continue
        dest = Path(raw) / r / name
        n = 2
        while dest.exists():  # two exports of one kind on one day: keep both, never overwrite
            dest = dest.with_stem(f"{Path(name).stem}_{n}")
            n += 1
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(p, dest)  # keeps the download time: data.py picks the newest export by it
        log.append(f"{p.name} -> {dest}")
    return log


def expand(url):
    """Short phone link -> full link: one request, reads only the redirect target (not the page)."""
    class Stop(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a):
            return None  # don't follow: the Location header is all we need
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    try:
        urllib.request.build_opener(Stop).open(req, timeout=10)
    except urllib.error.HTTPError as e:
        return e.headers.get("Location", "")
    return ""


def import_links(db="data/hub.db"):
    """links.txt lines -> trending rows (tag 'shared') so they show as Home cards. Every line is used up, even a bad one:
    a kept bad short link would hit TikTok again on every run."""
    f = INBOX / "links.txt"
    if not f.exists():
        return []
    lines = [x.strip() for x in f.read_text().splitlines() if x.strip()]
    log = []
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS trending (video_id TEXT, author TEXT, caption TEXT, music_id TEXT, music_title TEXT, music_author TEXT, views TEXT, likes TEXT, saves TEXT, posted_at TEXT, tag TEXT)")
    for line in lines:
        s = SHORT.search(line)
        full = expand(s.group()) if s and not LINK.search(line) else line
        m = LINK.search(full)
        if not m:
            log.append(f"not a TikTok video link, dropped: {line[:80]}")
            continue
        author, vid = m.groups()
        if not con.execute("SELECT 1 FROM trending WHERE video_id = ?", (vid,)).fetchone():
            with con:  # no song name from a shared link; the card shows the video, music_id keeps it its own dance
                con.execute("INSERT INTO trending VALUES (?, ?, '', ?, ?, '', '0', '0', '0', ?, 'shared')",
                            (vid, author, f"link:{vid}", f"Shared dance · @{author}", int(time.time())))
        log.append(f"card added: @{author}/{vid}")
    con.close()
    # shortcut: a link shared during this run could be lost; fine for a phone Shortcut, switch to one file per link if it happens
    f.write_text("")
    return log


if __name__ == "__main__":
    out = import_exports() + import_links()
    stamp = time.strftime("%Y-%m-%d %H:%M")
    with open("data/inbox.log", "a") as log:
        for line in out:
            log.write(f"{stamp} {line}\n")
    print("\n".join(out) or "nothing new")


# self-check (no network, no files)
assert out_name("Overview", "Overview_2026-11-12_1795039149_x.zip") == "Overview_2026-11-12_upload.zip"
assert out_name("Overview", "Overview.zip") is None and out_name("Viewers", "v.zip") == f"Viewers_{date.today()}.zip"
assert SHORT.search("look https://vm.tiktok.com/ZMabc123/ ok") and not SHORT.search("https://evil.com/vm.tiktok.com/x")
assert LINK.search("https://www.tiktok.com/@a.b/video/7312345678901234567").groups() == ("a.b", "7312345678901234567")
