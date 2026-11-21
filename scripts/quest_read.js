// Weekly quest reader (README v2 step 7). Brian opens the page himself; Claude in Chrome pastes this file
// with javascript_tool and calls ONE reader. Read-only: no clicks, no scrolling, no requests, no page changes.
// It reads what the open page already shows or holds in memory, keeps the result in window.__hub,
// and returns its length; read it back with hubChunk(0), hubChunk(1), ... (javascript_tool output is capped).
//   hubProfile(sinceDays, top)  any profile (yours or a competitor): follower count + posts from the last
//                               sinceDays days; top > 0 keeps only the top N by views (a competitor's hits)
//   hubTag(sinceDays)           a tag page (tiktok.com/tag/<tag>): posts on screen from the last sinceDays days
//   hubStudio()                 a Studio post analytics page: watch time, traffic, search terms, retention
// Posts come back as rows in the order of `cols`, to fit through the output cap.
// var, not const: the file gets pasted again on every page, and const can't be declared twice.

function hubPosts() {
  const seen = new Map();
  const scan = (v, depth) => {
    if (!v || typeof v !== "object" || depth > 6) return;
    if (Array.isArray(v)) { for (const x of v.slice(0, 300)) scan(x, depth + 1); return; }
    if (typeof v.id === "string" && /^\d{15,25}$/.test(v.id) && v.music && v.stats) { seen.set(v.id, v); return; }
    for (const k of Object.keys(v).slice(0, 60)) {
      if (k[0] !== "_" && k !== "return" && k !== "child" && k !== "sibling") try { scan(v[k], depth + 1); } catch (e) {}
    }
  };
  for (const el of document.querySelectorAll('[data-e2e$="-item"], [data-e2e$="-item-list"]')) {
    const k = Object.keys(el).find((k) => k.startsWith("__reactFiber"));
    for (let f = k && el[k], d = 0; f && d < 12; d++, f = f.return) scan(f.memoizedProps, 0);
  }
  return [...seen.values()].map((i) => [
    i.id, i.author?.uniqueId ?? i.author, Number(i.createTime), (i.desc || "").trim(), i.video?.duration,
    i.stats.playCount, i.stats.diggCount, i.stats.commentCount, i.stats.shareCount, Number(i.stats.collectCount) || 0,
    i.music.id, i.music.title, i.music.authorName,
  ]);
}
var cols = ["video_id", "author", "posted_at", "caption", "length_s", "views", "likes", "comments", "shares", "saves",
              "music_id", "music_title", "music_author"];

function hubRecent(sinceDays, top = 0) {
  const cut = Date.now() / 1000 - sinceDays * 86400;
  const rows = hubPosts().filter((r) => r[2] >= cut);
  return top ? rows.sort((a, b) => b[5] - a[5]).slice(0, top) : rows.sort((a, b) => b[2] - a[2]);
}

function hubSave(obj) {
  window.__hub = JSON.stringify(obj);
  return `${window.__hub.length} chars, ${Math.ceil(window.__hub.length / 900)} chunks`;
}

var hubChunk = (i) => window.__hub.slice(i * 900, (i + 1) * 900);  // the tool cuts output near 1,000 chars

function hubProfile(sinceDays = 14, top = 0) {
  const followers = document.querySelector('[data-e2e="followers-count"]')?.textContent;
  return hubSave({ kind: "profile", url: location.href, followers, cols, posts: hubRecent(sinceDays, top) });
}

function hubTag(sinceDays = 30) {
  return hubSave({ kind: "tag", url: location.href, cols, posts: hubRecent(sinceDays) });
}

function hubStudio() {
  const t = document.body.innerText;
  const after = (label) => t.split(label + "\n")[1]?.split("\n")[0];
  // label/percent pairs between two headings, e.g. "For You\n55.2%"
  const pairs = (from, to) => {
    const part = t.split(from + "\n")[1]?.split(to)[0] ?? "";
    const out = [], lines = part.split("\n").map((x) => x.trim()).filter(Boolean);
    for (let i = 0; i + 1 < lines.length; i += 2) if (/%$/.test(lines[i + 1])) out.push([lines[i], parseFloat(lines[i + 1].replace("<", ""))]);
    return out;
  };
  // the charts are canvas; their points sit in the chart component's props
  const charts = [];
  for (const c of document.querySelectorAll("canvas")) {
    let el = c, data = null;
    for (let up = 0; up < 8 && el && !data; up++, el = el.parentElement) {
      const k = Object.keys(el).find((k) => k.startsWith("__reactFiber"));
      for (let f = k && el[k], d = 0; f && d < 15 && !data; d++, f = f.return) {
        const p = f.memoizedProps?.data;
        if (Array.isArray(p) && p.length > 1 && p[0] && "x" in p[0]) data = p;
      }
    }
    if (data) charts.push(data);
  }
  const ret = charts.find((d) => d[0].x === "0");  // retention: x = ms from start, y = share still watching
  // exact views, likes, comments, shares, saves: the 5 numbers under "Posted on" (profile counts are rounded)
  const n = t.match(/Posted on [^\n]+\n([\d,]+)\n([\d,]+)\n([\d,]+)\n([\d,]+)\n([\d,]+)\n/);
  return hubSave({
    kind: "studio", video_id: location.pathname.match(/(\d{15,25})/)?.[1],
    counts: n ? n.slice(1).map((x) => Number(x.replace(/,/g, ""))) : null,
    avg_watch: after("Average watch time"), full_watch: after("Watched full video"), new_followers: after("New followers"),
    traffic: pairs("Traffic source", "Search queries"), search_terms: pairs("Search queries", "\nBack\n"),
    retention: ret ? ret.map((p) => [Number(p.x) / 1000, p.y]) : [],
  });
}
