"""Weekly planner (README v2 step 8): fill next week's empty Plan slots, pick backups, and write the weekly email.
Each day: 1 new dance to learn + refilms of old dances (Brian learns 1-2 new a day, mostly refilms).
Pure functions; api/main.py feeds them the Plan data. Run it all with ./run.sh plan."""
from datetime import date, timedelta


def next_week(today=None):
    """Next Monday..Sunday as 'YYYY-MM-DD' strings."""
    t = today or date.today()
    mon = t + timedelta(days=7 - t.weekday())
    return [str(mon + timedelta(days=i)) for i in range(7)]


def fill(days, taken, new, old, per_day=3, new_per_day=1):
    """taken: {(date, slot): key} already on the calendar (never touched). new / old: [{key, label}] best first.
    A day gets new_per_day new dances (counting new ones already placed), the rest old. Each dance once a week.
    Returns (new slots [(date, slot, key, label)], {date: [1 new backup, 1 old backup]})."""
    used, new_keys = set(taken.values()), {p["key"] for p in new}
    new, old = list(new), list(old)

    def take(lst):
        while lst:
            p = lst.pop(0)
            if p["key"] not in used:
                used.add(p["key"])
                return p

    added = []
    for d in days:
        want_new = new_per_day - sum(k in new_keys for (dd, _), k in taken.items() if dd == d)
        for s in range(per_day):
            if (d, s) in taken:
                continue
            p = (want_new > 0 and take(new)) or take(old) or take(new)  # run out of one kind: use the other
            want_new -= p is not None and p["key"] in new_keys
            if p:
                added.append((d, s, p["key"], p["label"]))
    extra = {d: [p for p in (take(new), take(old)) if p] for d in days}  # after the slots, so they never steal one
    return added, extra


def email(days, planned, results, old_keys):
    """Short plain text: this week's results + how much of next week is planned. The dances themselves
    (with a play button each) are on the Plan page."""
    day = lambda d: date.fromisoformat(d).strftime("%a %b %-d")
    r = results
    out = [f"This week ({day(r['from'])} - {day(r['to'])})"]
    if r["posts"]:
        out += [f"- {r['posts']} posts on {r['days_posted']} of 7 days, {r['views']:,} views, {r['new_followers']:,} new followers",
                f"- Best: \"{r['best_title']}\" with {r['best_views']:,} views"]
    else:
        out.append("- No posts in the Studio data yet. Do the weekly quest, then run this again.")
    keys = [x["key"] for x in planned if x["date"] in days]
    refilms = sum(k in old_keys for k in keys)
    out.append(f"Next week: {len(keys)} dances planned ({len(keys) - refilms} new, {refilms} refilms). "
               "Tap any of them on the Plan page to watch it.")
    return "\n".join(out)


# self-check
assert next_week(date(2026, 11, 20)) == [f"2026-11-{x}" for x in range(23, 30)]  # Friday -> next Mon..Sun
assert next_week(date(2026, 11, 23))[0] == "2026-11-30"  # on a Monday it plans the week after
_n = [{"key": k, "label": k} for k in "abcd"]
_o = [{"key": k, "label": k} for k in "wxyz"]
_add, _ex = fill(["d1", "d2"], {("d2", 0): "b"}, _n, _o, per_day=2)
assert _add == [("d1", 0, "a", "a"), ("d1", 1, "w", "w"), ("d2", 1, "x", "x")], _add  # d2 already has a new one (b)
assert _ex == {"d1": [_n[2], _o[2]], "d2": [_n[3], _o[3]]}, _ex
assert fill(["d1"], {}, [], _o[:1] + _o[:1], per_day=3)[0] == [("d1", 0, "w", "w")]  # out of both: slots stay empty
assert email(["2026-11-23"], [{"date": "2026-11-23", "key": "w"}, {"date": "2026-11-30", "key": "a"}],
             {"from": "2026-11-16", "to": "2026-11-22", "posts": 0}, {"w"}).endswith("1 dances planned (0 new, 1 refilms). Tap any of them on the Plan page to watch it.")
