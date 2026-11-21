---
name: weekly-plan
description: Fill next week's Content Hub plan and put the weekly email (this week's results + next week's plan) in Brian's Gmail as a draft. Use when Brian says "plan my week", "weekly plan", or "weekly email".
---

# Weekly plan + email (README v2 step 8)

Rule: make a Gmail draft only. Never send it; Brian sends it himself.

1. Run `./run.sh plan`. It fills next week's empty Plan slots (1 new dance + 2 refilms a day)
   and 2 backups a day (1 new, 1 refilm), each with its TikTok link, and never
   touches a slot Brian filled. It prints "Added N dances" and then the email text.
   If it fails with "No Studio data yet", tell Brian to do the weekly quest first.
2. Make a Gmail draft with `create_draft`:
   - to: Brian's own Gmail address (the account the Gmail connector uses)
   - subject: `Content Hub: week of <next Monday, e.g. Nov 23>`
   - body: the printed text from "This week" to the end, unchanged
3. Tell Brian in one or two lines: how many dances were added, and that the draft is in Gmail.
   Changes to the week go on the Plan page (http://127.0.0.1:5173/#plan).
