"""Step 8a: 2-week posting calendar from the newest advice in data/recs/.
Run: python3 src/plan.py [videos_per_day]   (1-3, default 2)
Writes data/plans/<start>_<n>-a-day.csv, one row per video."""
import glob, json, os, sys
import pandas as pd
from data import act
from patterns import NAMES

per_day = int(sys.argv[1]) if len(sys.argv) > 1 else 2
assert 1 <= per_day <= 3, "videos per day: 1, 2 or 3"
found = sorted(glob.glob("data/recs/*.json"))
if not found:
    raise SystemExit("No advice yet. Run python3 src/recommend.py first.")
s = json.load(open(found[-1]))
tests_txt = " ".join(s["recommendations"]["test"])

# busiest follower hours, at least 2 hours apart so your own videos don't compete
# shortcut: assumes FollowerActivity hours are PST (your zone); unverified, re-check if peaks look off
hours = []
for h in act.groupby("Hour")["Active followers"].mean().sort_values(ascending=False).index:
    if all(abs(h - x) >= 2 for x in hours):
        hours.append(h)
    if len(hours) == per_day:
        break
hours.sort()

IDEAS = ["Remake a top hit: part 2, or the same song or dance style",
         "Follower-getter: like your best follow-earning videos; end with 'follow for part 2'"]
tag_test = bool(s["common_tags"])
cap_test = NAMES["caption_len"] in tests_txt
cap_hi, cap_lo = s["caption_len"]
start = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)

rows = []
for i in range(14 * per_day):
    day = start + pd.Timedelta(days=i // per_day)
    tests = []
    if tag_test:
        tags = " ".join(s["common_tags"]) if (i // 2) % 2 == 0 else "song or dance name tags (no " + " ".join(s["common_tags"]) + ")"
        tests.append("hashtags")
    else:
        tags = "your usual tags"
    if cap_test:  # idea flips every post, tags every 2, caption every 4: no test lines up with another
        cap = f"about {cap_hi if (i // 4) % 2 == 0 else cap_lo:g}"
        tests.append("caption length")
    else:
        cap = f"about {cap_hi:g} (like your top videos)"
    rows.append({"date": day.date(), "day": day.day_name(), "time (PST)": f"{hours[i % per_day]}:00",
                 "idea": IDEAS[i % 2],
                 "caption chars": cap, "hashtags": tags, "testing": ", ".join(tests) or "-"})
plan = pd.DataFrame(rows)
assert pd.crosstab(plan["idea"], plan["hashtags"]).min().min() >= 2, "hashtag test mixed up with idea type"

# each test side needs 2+ videos to compare (track.py rule)
if tag_test:
    assert plan["hashtags"].str.startswith("song").value_counts().min() >= 2
if cap_test:
    assert plan["caption chars"].value_counts().min() >= 2

print(f"Plan from advice dated {s['export_date']}: {len(plan)} videos, {per_day} a day, "
      f"{start.date()} to {plan['date'].iloc[-1]}.")
print("Monday vs other days needs no planning: you post every day, so Track can compare them.\n")
print(plan.to_string(index=False))

os.makedirs("data/plans", exist_ok=True)
path = f"data/plans/{start.date()}_{per_day}-a-day.csv"
plan.to_csv(path, index=False)
print(f"\nSaved to {path}")
