// TikTok hashtag trending reader (README v2 step 4).
// Run by Claude in Chrome (javascript_tool) on a public tag page, e.g. tiktok.com/tag/dancechallenge:
//   paste this file, then: await trendingRead("dancechallenge")
// The tag's list request is signed, so it can't be refetched. Instead this listens to the page's own
// requests while scrolling, keeps posts from the last 30 days, and replaces the page with one JSON
// line per post so get_page_text can read it all in one call. Read-only: no clicks, no writes.
// shortcut: the first batch loads before the listener exists, so it is missed; ok while scrolling finds 30+ recent posts.

async function trendingRead(tag, scrolls = 8, days = 30) {
  const items = {};
  const keep = (text) => { try { for (const i of JSON.parse(text).itemList || []) items[i.id] = i; } catch (e) {} };
  const open = XMLHttpRequest.prototype.open, send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__u = String(u); return open.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function () {
    this.addEventListener("load", () => this.__u.includes("/api/challenge/item_list/") && keep(this.responseText));
    return send.apply(this, arguments);
  };
  const f = window.fetch;
  window.fetch = async (...a) => {
    const r = await f(...a);
    if (String(a[0]?.url || a[0]).includes("/api/challenge/item_list/")) r.clone().text().then(keep);
    return r;
  };
  for (let k = 0; k < scrolls; k++) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise((r) => setTimeout(r, 2500));
  }
  const now = Date.now() / 1000, readAt = Math.floor(now);
  const lines = Object.values(items).filter((i) => now - i.createTime < days * 86400).map((i) => JSON.stringify({
    video_id: i.id, author: i.author?.uniqueId, caption: (i.desc || "").slice(0, 150),
    music_id: i.music?.id, music_title: i.music?.title, music_author: i.music?.authorName,
    views: i.stats?.playCount, likes: i.stats?.diggCount, saves: i.stats?.collectCount,
    posted_at: i.createTime, tag, read_at: readAt,
  }));
  const pre = document.createElement("pre");
  pre.textContent = lines.join("\n");
  document.body.replaceChildren(pre);
  return `${Object.keys(items).length} caught, ${lines.length} from the last ${days} days`;
}
