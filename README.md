# Content Hub

Personal TikTok analytics + AI agent. Reads exported TikTok Studio data, calculates performance, explains patterns, recommends what to post next.

## Roadmap
1. Setup ✅
2. Import TikTok CSV/Excel exports ✅
3. Analysis: engagement, watch time, views, follower growth ✅
4. AI agent: find patterns, explain performance ✅
5. Recommendations: what to post, improve, test ✅
6. Track recommendations against next videos ✅
7. Dashboard: `streamlit run src/dashboard.py` (local only). Tabs for analyze, patterns, recommendations, track; sidebar upload for exports.
8. Later: content planning, scripts, competitor research, trends (plan below, not built)

## Step 8 plan
Build one part at a time, in this order. Each part is one script in `src/`, run on real data, with an assert self-check.

**Before starting**
- Content exports are capped at 15 videos (out of 400-600), even for the 7-day range. They seem to be the most-viewed in the range, not the newest. Options:
  - **Chosen:** keep every weekly Content zip under a dated name (e.g. `Content_2026-11-18.zip`) and merge them in `data.py` by video link, keeping the newest stats. This builds a full list from now on.
  - Recent videos the export misses, plus extra stats: use Claude in Chrome on your TikTok Studio pages to save per-video stats (views, likes, comments, shares, avg watch time, watched full video %) to `data/raw/studio_<date>.csv`, with the same video-link column so `data.py` can merge it. This also adds the watch time that step 3 couldn't get.
  - Older videos (optional): profile-grid screenshots (about 40), read once into `data/raw/`. That gives views in post order only, with no dates, captions or likes.
- Commit the step 6 fixes.

**8a. Content planning: `src/plan.py`**
- Input: the newest advice in `data/recs/`.
- Output: a 2-week posting calendar, `data/plans/<date>.csv` (git-ignored). One row per post: date, time slot, idea type (remake of a top video / follower-getter format / test), caption length target, hashtag set.
- Spreads the A/B tests across posts so each side gets 2+ videos.
- `track.py` later matches posted videos to plan rows by date and reports whether the plan was followed.
- No new dependency.

**8b. Scripts: `src/scripts.py`**
- Input: plan rows plus your top videos' captions.
- Output: `data/plans/<date>_scripts.md`, with a hook line, a shot list and a caption per planned post.
- Decision needed: templates (no AI, nothing leaves your machine) or the Claude API (better writing; needs the `anthropic` package, an API key, and a change to the "no outside services" rule for captions).

**8c. Competitor research: `src/competitors.py`**
- TikTok has no free API for other accounts' stats, and scraping breaks its terms.
- Plan: you fill `data/competitors.csv` by hand (handle, video link, views, likes, comments, shares, caption). Post dates come from the video ID, as they do now.
- Reuses the `patterns.py` functions to compare their share rate, caption length and hashtags against yours. Output: what they do that you don't.
- Decision needed: a manual CSV, the TikTok Research API (academics only, needs approval) or a paid third-party API.

**8d. Trends: `src/trends.py`**
- Source: TikTok Creative Center (trending sounds and hashtags). It has no stable public API.
- Plan: once a week, paste the top sounds and hashtags into `data/trends.csv` (date, type, name, rank).
- Flags trends that fit your niche (dance) and that are rising week on week. `plan.py` then adds them as idea slots.
- Decision needed: the same choice as in 8c, manual or an API.

## Data
Put TikTok Studio exports in `data/raw/` (git-ignored, personal data):
- `data/raw/year/`: past-365-days export (Overview, Content, Followers, Viewers). Used by `analyze.py`, `patterns.py`, `recommend.py`.
- `data/raw/week/`: past-7-days export. Used by `track.py` to score new videos against the last saved advice (`data/recs/`).
