# Content Hub

Personal TikTok analytics + AI agent. Reads exported TikTok Studio data, calculates performance, explains patterns, recommends what to post next.

## Roadmap
1. Setup ✅
2. Import TikTok CSV/Excel exports ✅
3. Analysis: engagement, watch time, views, follower growth ✅
4. AI agent: find patterns, explain performance ✅
5. Recommendations: what to post, improve, test ✅
6. Track recommendations against next videos ✅
7. Dashboard v1 (Streamlit): retired Nov 20, 2026, replaced by v2.
8. Dashboard v2: FastAPI + React rebuild with planning, competitors and trends (step 1 built; rest below)

## Run
```
./run.sh              # dashboard: open http://127.0.0.1:5173 (Ctrl+C stops it)
./run.sh analyze      # text report: views, engagement, followers, viewers
./run.sh recommend    # refresh the advice
./run.sh track        # did the last advice work? (past-7-days export)
```

## Dashboard v2 plan
Decided Nov 20, 2026. Used weekly: upload exports, then say "update my dashboard" in a Claude chat.

**Pages**
1. **Home**: what to post next (incl. hook/retention tips), goal line ("12.0K / 15K, need ~270/week, did X last week"), "did last week's advice work?" card (replaces Track), dances to try, upload exports.
2. **Videos**: table of all posts; click one for its detail page: its Studio numbers vs your usual, drop-off second, traffic source.
3. **Patterns**: what the biggest videos do differently; which videos won followers.
4. **Plan**: 2-week calendar, up to 3 posts a day. Possible dances below, labeled Saved / Trending / Remake / Competitor; drag one onto a day. A day ticks off when a post shows up on that date; flagged if the sound differs from the plan. A dance leaves the list once scheduled.
5. **Competitors**: editable table, 3-5 dance accounts (20K-200K), last ~5 hits each: link, views, likes, comments, shares, caption, sound, format (1-person / 2-person / trend / original). Comparison: "their 2-person videos get 3x views; you post 2-person X%".

Analyze is folded into Videos and Home; Track and Recommendations are gone.

**Data**
- TikTok Studio zips: uploaded as now.
- No crawling (decided Nov 20): nothing navigates, clicks or scrolls TikTok on its own, and no scrapers. Only allowed read: Brian opens a page himself and Claude in Chrome reads that open tab. `scripts/*_read.js` are kept but not run.
- Trending dances: paste a TikTok link + song name on Home's "Dances to try" card.
- Competitor rows: typed in the Competitors page.
- Stored in one SQLite file, `data/hub.db` (git-ignored). Exports stay as zips.
- No scripts feature: ask Claude in chat for script help.

**Tech**
- Same repo: `api/` (FastAPI, imports from `src/`) and `web/` (React + TypeScript + Tailwind + Recharts + dnd-kit).
- `./run.sh` starts both while building; once done, the API serves the built React app. Localhost only.
- Same look as v1: TikTok black/red/cyan tokens, flat cards, color only on data (cyan = good, red = bad), 22px card padding.
- No personal data hardcoded in screens, so a fake-data demo mode can be added later for a portfolio.

**Build order**
1. API endpoints for today's data, then rebuild Home, Videos and Patterns in React. Delete Streamlit. ✅
2. Studio per-post read (Claude in Chrome), the video detail page, hook/retention advice. Step 2 done Nov 20 (days-since-previous-post dropped).
3. Plan calendar (tap a dance, tap a day; up to 3 a day, no set times) + Library tab (one tile per dance you have done, by sound + "dc: @creator", best video shown; "Add to plan"). Saved read done Nov 20 ("Tiktok Dances to Do" Favorites → data/raw/favorites/, ideas table, named by song). Step 3 done.
4. Trending read (adds Trending). Creative Center has no dance or song trends (checked Nov 20, logged in too), so Claude in Chrome reads public tag pages instead: #dancechallenge #1persondance #dance #choreography #viraldance, last 30 days, via `scripts/trending_read.js` → data/raw/trending/ → `trending` table. Home "Dances to try" = swipe card: ✓ adds to Plan, ✕ asks why (saved in `swipes` for the weekly read). Built Nov 20. Since the no-crawling call, new cards come from links pasted on Home.
5. Competitors page (adds Competitor): accounts + their last ~5 hits typed in by hand (link, views, likes, comments, shares, caption, song, format); "their 2-person videos get 3x views" lines; their posts show in Plan's "Dances I want to do". "You post 2-person X%" skipped: your posts have no format yet. Built Nov 20.
6. Inbox + auto-import: iCloud Drive `Content Hub/inbox` + iOS Shortcuts (share a dance link, save an export); a daily launchd job imports new zips and links (short vm.tiktok.com links expanded, one request each). Plain Python, no AI.
7. "You click, Claude reads": a weekly quest (~10 min). The Hub's quest page lists the pages to open (each new post's Studio analytics, 1-2 competitor profiles, a dance hashtag); Brian clicks each link, Claude reads that open tab and saves it into data/hub.db; the step ticks off.
8. Weekly planner + email: fills next week with 1-3 dances a day plus backups per day; emails the plan and last week's results (Gmail). Built Nov 20: `./run.sh plan` fills next week's empty slots (3 a day: your list, ✓ Trending, Saved, Competitor, then remakes not posted in 14 days) + 2 backups a day; the weekly-plan skill ("plan my week") puts the email in a Gmail draft.
9. Learning picker: ranks dances from swipes, reasons and how each posted dance did.
10. Resume polish: fake-data demo mode, tests + CI, write-up with real follower numbers.

## Data
Put TikTok Studio exports in `data/raw/` (git-ignored, personal data):
- `data/raw/year/`: past-365-days export (Overview, Content, Followers, Viewers). Used by `analyze.py`, `patterns.py`, `recommend.py`.
- `data/raw/week/`: past-7-days export. Used by `track.py` to score new videos against the last saved advice (`data/recs/`).
