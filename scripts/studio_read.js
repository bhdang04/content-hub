// TikTok Studio per-post reader (README v2 step 2).
// Run by Claude in Chrome (javascript_tool) inside a signed-in TikTok Studio post analytics tab:
//   paste this file, then: await studioRead(["<video id>", ...])
// It reuses the page's own insight request (same cookies and params), asks only for the fields
// the posts table keeps, waits ~1s between posts, and replaces the page with one JSON line per post
// so get_page_text can read it all in one call. Read-only: GET requests only.

const TYPES = [
  "video_info", "item_search_terms", "video_traffic_source_percent_realtime",
  "video_retention_rate_realtime", "video_total_duration_realtime",
  "video_per_duration_realtime", "video_finish_rate_realtime", "video_new_followers",
];

function insightUrl(id) {
  const tpl = performance.getEntriesByType("resource").map(e => e.name)
    .find(n => n.includes("/aweme/v2/data/insight/") && n.includes("type_requests="));
  if (!tpl) throw new Error("open a post's analytics page in Studio first");
  const u = new URL(tpl);
  u.searchParams.set("type_requests", JSON.stringify(TYPES.map(t => ({ insigh_type: t, aweme_id: id }))));
  return u.toString();
}

function pick(id, r) {
  const v = r.video_info || {}, s = v.statistics || {};
  const val = k => r[k]?.value?.value;
  const ret = r.video_retention_rate_realtime?.value?.list || [];
  // Points are 1 per second; keep plain values unless TikTok ever changes the step.
  const perSecond = ret.every((p, i) => Number(p.timestamp) === i * 1000);
  return {
    video_id: id,
    posted_at: v.create_time,
    private_status: v.status?.private_status,  // 0 = public; non-zero = private/friends (import skips)
    title: (v.desc || "").slice(0, 100),
    length_ms: v.video?.duration,
    views: s.play_count, likes: s.digg_count, comments: s.comment_count,
    shares: s.share_count, saves: s.collect_count,
    avg_watch_s: val("video_per_duration_realtime"),
    full_watch_rate: val("video_finish_rate_realtime"),
    total_play_s: val("video_total_duration_realtime"),
    new_followers: r.video_new_followers?.value,
    traffic: Object.fromEntries((val("video_traffic_source_percent_realtime") || []).map(x => [x.key, x.value])),
    retention: perSecond ? ret.map(p => p.value) : ret.map(p => [Number(p.timestamp) / 1000, p.value]),
    search_terms: (r.item_search_terms?.value || []).map(x => [x.key, x.value]),
    read_at: Math.floor(Date.now() / 1000),
  };
}

async function studioRead(ids, gapMs = 1000) {
  const urls = ids.map(insightUrl);  // build all first so the template survives the page swap
  const lines = [];
  for (let i = 0; i < ids.length; i++) {
    try {
      const r = await fetch(urls[i], { credentials: "include" }).then(x => x.json());
      if (r.status_code !== 0) throw new Error(`status_code ${r.status_code} ${r.status_msg || ""}`);
      lines.push(JSON.stringify(pick(ids[i], r)));
    } catch (e) {
      lines.push(JSON.stringify({ video_id: ids[i], error: String(e) }));
    }
    if (i < ids.length - 1) await new Promise(ok => setTimeout(ok, gapMs));
  }
  const pre = document.createElement("pre");
  pre.textContent = lines.join("\n");
  document.body.replaceChildren(pre);
  return `${lines.length} posts, ${lines.filter(l => l.includes('"error"')).length} errors`;
}
