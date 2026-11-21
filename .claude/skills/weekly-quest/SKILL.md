---
name: weekly-quest
description: Run Content Hub's weekly quest - Brian opens TikTok pages from the Quest tab, Claude reads each open tab and saves it. Use when Brian says "start the weekly quest", "quest", or "weekly read".
---

# Weekly quest

Rule (Brian, Nov 20 2026): Brian clicks, Claude only reads. Never navigate, click, scroll, type or open tabs on TikTok.
Never fetch anything from a TikTok page. One read per page Brian opened.

## Setup
1. `tabs_context_mcp` with `createIfEmpty: true`. Ask Brian to open `http://127.0.0.1:5173/#quest` in that
   Claude window (start `./run.sh` first if the dashboard isn't up). His quest links open in a tab named "tiktok"
   in the same group.
2. Say one line: "Tap step 1."

## Loop
1. Poll `tabs_context_mcp` (with a `computer` wait of ~3s between polls) until a tab's URL matches the next
   unchecked step's page (`/@handle`, `/tiktokstudio/analytics/<id>`, `/tag/<tag>`). Max ~10 polls, then ask.
2. Wait 2s for it to finish loading. Paste `scripts/quest_read.js` with `javascript_tool`, then call one reader:
   - your profile: `hubProfile(14)`
   - a competitor profile: `hubProfile(30, 5)`
   - a tag page: `hubTag(30)`
   - a Studio post analytics page: `hubStudio()`
3. It returns "N chars, K chunks". Read `hubChunk(0)` … `hubChunk(K-1)` (output is cut near 1,000 chars, so
   chunks are 900). Join them exactly, Write to the scratchpad as JSON, run `python3 src/quest.py save <file>`.
4. Relay its one-line result. The Quest page ticks the step within 3s. Go back to 1.
5. If save says the page wasn't loaded, re-read the same tab once. If a profile read returns 0 posts, ask Brian
   to wait for the grid to show, then re-read. Don't ask him to scroll.

## End
All steps ✓: one line with what changed (new posts read, competitor hits, trending posts). Keep it short.
