# Content Hub

Personal TikTok analytics + AI agent. Reads exported TikTok Studio data, calculates performance, explains patterns, recommends what to post next.

## Roadmap
1. Setup ✅
2. Import TikTok CSV/Excel exports
3. Analysis: engagement, watch time, views, follower growth
4. AI agent: find patterns, explain performance
5. Recommendations: what to post, improve, test
6. Track recommendations against next videos
7. Later: content planning, scripts, competitor research, trends

## Data
Put TikTok Studio exports in `data/raw/` (git-ignored, personal data):
- `data/raw/year/`: past-365-days export (Overview, Content, Followers, Viewers). Used by `analyze.py`, `patterns.py`, `recommend.py`.
- `data/raw/week/`: past-7-days export. Used by `track.py` to score new videos against the last saved advice (`data/recs/`).
