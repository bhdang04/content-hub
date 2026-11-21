"""Weekly planner (README v2 step 8): fill next week's empty Plan slots, pick backups, and write the weekly email.
Pure functions; api/main.py feeds them the Plan data. Run it all with ./run.sh plan."""
from datetime import date, timedelta


def next_week(today=None):
    """Next Monday..Sunday as 'YYYY-MM-DD' strings."""
    t = today or date.today()
    mon = t + timedelta(days=7 - t.weekday())
    return [str(mon + timedelta(days=i)) for i in range(7)]


def fill(days, taken, picks, per_day=3, backups=2):
    """taken: {(date, slot): key} already on the calendar (never touched). picks: [{key, label}] best first.
    Each dance is used once in the week. Returns (new slots [(date, slot, key, label)], {date: [pick, ...]})."""
    used = set(taken.values())
    left = [p for p in picks if not (p["key"] in used or used.add(p["key"]))]  # drops repeats too
    new, extra = [], {}
    for d in days:
        for s in range(per_day):
            if (d, s) not in taken and left:
                p = left.pop(0)
                new.append((d, s, p["key"], p["label"]))
    for d in days:  # backups come after every slot is filled, so they never steal a slot's dance
        extra[d], left = left[:backups], left[backups:]
    return new, extra


def email(days, planned, extra, results):
    """Plain text: this week's results, then next week's plan with backups."""
    day = lambda d: date.fromisoformat(d).strftime("%a %b %-d")
    r = results
    out = [f"This week ({day(r['from'])} - {day(r['to'])})"]
    if r["posts"]:
        out += [f"- {r['posts']} posts on {r['days_posted']} of 7 days, {r['views']:,} views, {r['new_followers']:,} new followers",
                f"- Best: \"{r['best_title']}\" with {r['best_views']:,} views"]
    else:
        out.append("- No posts in the Studio data yet. Do the weekly quest, then run this again.")
    out += ["", "Next week"]
    for d in days:
        out.append(f"{day(d)}: " + ("; ".join(x["name"] for x in sorted(planned.get(d, []), key=lambda x: x["slot"])) or "nothing planned"))
        if extra.get(d):
            out.append("  backups: " + "; ".join(p["label"] for p in extra[d]))
    return "\n".join(out)


# self-check
assert next_week(date(2026, 11, 20)) == [f"2026-11-{x}" for x in range(23, 30)]  # Friday -> next Mon..Sun
assert next_week(date(2026, 11, 23))[0] == "2026-11-30"  # on a Monday it plans the week after
_p = [{"key": k, "label": k.upper()} for k in "abcdefgh"]
_new, _extra = fill(["d1", "d2"], {("d1", 1): "b"}, _p, per_day=2, backups=1)
assert _new == [("d1", 0, "a", "A"), ("d2", 0, "c", "C"), ("d2", 1, "d", "D")], _new  # your slot and its dance stay put
assert _extra == {"d1": [_p[4]], "d2": [_p[5]]}, _extra
assert fill(["d1"], {}, _p[:1] * 3, per_day=3)[0] == [("d1", 0, "a", "A")]  # a dance listed twice is used once
