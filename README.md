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
- Weekly "update my dashboard" chat; Claude in Chrome reads:
  - Studio per-post pages: every post once, then the last ~10 each week. Views, likes, comments, shares, saves, play time, avg watch time, watched full %, new followers, drop-off second, traffic source. Not the hourly chart.
  - TikTok Creative Center trends.
  - The "Dance ideas" Favorites collection.
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
2. Studio per-post read (Claude in Chrome), the video detail page, hook/retention advice. (Read + `./run.sh import` + detail page done Nov 20; advice + days-since-previous-post left.)
3. Plan calendar (tap a dance, tap a day; up to 3 a day, no set times) + Library tab (one tile per dance you have done, by sound + "dc: @creator", best video shown; "Add to plan"). Done Nov 20; Saved read ("Tiktok Dances to Do" Favorites) left.
4. Creative Center read (adds Trending).
5. Competitors page (adds Competitor).

## Data
Put TikTok Studio exports in `data/raw/` (git-ignored, personal data):
- `data/raw/year/`: past-365-days export (Overview, Content, Followers, Viewers). Used by `analyze.py`, `patterns.py`, `recommend.py`.
- `data/raw/week/`: past-7-days export. Used by `track.py` to score new videos against the last saved advice (`data/recs/`).
