"""Step 6: score videos posted since the last saved recommendations against their targets.
Reads data/raw/week/ (past-week export). Advice comes from recommend.py on data/raw/year/.
Exports have no post hour, so timing advice can't be checked."""
import glob, json, os
os.environ.setdefault("CONTENT_HUB_RAW", "data/raw/week")  # must run before data is imported
from data import END
from patterns import v, tags, compare

snaps = sorted(p for p in glob.glob("data/recs/*.json") if os.path.basename(p)[:10] < str(END.date()))
if not snaps:
    raise SystemExit(f"No saved recommendations from before this export ({END.date()}). "
                     "Run recommend.py now; track.py works once a newer export is in data/raw/.")
s = json.load(open(snaps[-1]))
new = v[v["Post time"] > s["last_post"]].copy()
print(f"Recommendations from {s['export_date']} (last video seen {s['last_post']}), "
      f"export ending {END.date()}: {len(new)} new videos.")
print("Advice given then:")
for head, items in s["recommendations"].items():
    print("".join(f"  [{head}] {x}\n" for x in items), end="")
if new.empty:
    raise SystemExit("\nNothing to score yet: no videos posted since then.")

new["age_days"] = (END - new["Post time"]).dt.days
new["views>median"] = new["Total views"] > s["median_views"]
new["shares>=target"] = new["shares_per_1k"] >= s["shares_per_1k_target"]
new["followers>median"] = new["followers_per_1k_views"] > s["median_followers_per_1k"]
checks = ["views>median", "shares>=target", "followers>median"]
print(f"\n== New videos vs targets (median views {s['median_views']:,.0f}, shares/1k {s['shares_per_1k_target']}, "
      f"followers/1k {s['median_followers_per_1k']}) ==")
print(new[["title", "age_days", "Total views", "shares_per_1k", "followers_per_1k_views"] + checks].to_string(index=False))
print("Hit rate: " + ", ".join(f"{c} {new[c].sum()}/{len(new)}" for c in checks))
if (new["age_days"] < 7).any():
    print("Note: videos under 7 days old are still collecting views; re-check next export.")

print("\n== Test results (median views among new videos) ==")
views = new["Total views"]
tests = []
for col, unit in (("caption_len", "chars"), ("days_since_last_post", "days gap")):
    hi, lo = s[col]
    tests.append((f"{col} near {hi:g} {unit} (vs near {lo:g})", (new[col] - hi).abs() < (new[col] - lo).abs()))
if s["common_tags"]:
    tests.append((f"Using {' '.join(s['common_tags'])}", tags.loc[new.index].apply(lambda t: set(s["common_tags"]) <= set(t))))
tests.append(("Posted Sat/Sun", new["weekend"]))
for label, mask in tests:
    print(compare(views, mask, label) or f"{label}: not enough videos yet (need 2+ on each side, have {mask.sum()}/{(~mask).sum()})")
