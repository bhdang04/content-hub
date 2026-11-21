// TikTok competitor reader (README v2 step 5).
// Run by Claude in Chrome (javascript_tool) on a competitor's public profile, e.g. tiktok.com/@maxlvjacob:
//   paste this file, then: await competitorRead("maxlvjacob")
// Follower count comes from a fresh fetch of the profile (the copy inside the open tab has zeros); the newest
// post IDs from the video links on the page, sorted by ID so an old pinned post drops out; stats/sound/caption
// from each post's public page, ~1s apart. The page also links other people's videos (yours showed up), so
// posts by anyone but `handle` are skipped. Replaces the page with one JSON line per post so get_page_text can
// read it all. Read-only: GET requests only.

const DATA = /<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)<\/script>/;
const scope = (html) => JSON.parse(html.match(DATA)[1])["__DEFAULT_SCOPE__"];

async function competitorRead(handle, n = 15) {
  if (location.pathname !== `/@${handle}`) throw new Error(`open tiktok.com/@${handle} first`);
  const user = scope(await fetch(`/@${handle}`).then((r) => r.text()))["webapp.user-detail"].userInfo;
  const ids = [...new Set([...document.querySelectorAll('a[href*="/video/"]')].map((a) => a.pathname.split("/").pop()))]
    .sort((a, b) => (BigInt(b) > BigInt(a) ? 1 : -1));
  const lines = [], readAt = Math.floor(Date.now() / 1000);
  let skipped = 0;
  for (const id of ids) {
    if (lines.length >= n) break;
    try {
      const i = scope(await fetch(`/@${handle}/video/${id}`).then((r) => r.text()))["webapp.video-detail"].itemInfo.itemStruct;
      if (i.author?.uniqueId !== handle) { skipped++; continue; }
      lines.push(JSON.stringify({
        handle, followers: user.stats.followerCount, video_id: id, caption: (i.desc || "").slice(0, 150),
        music_id: i.music?.id, music_title: i.music?.title, music_author: i.music?.authorName,
        views: +i.stats.playCount, likes: +i.stats.diggCount, comments: +i.stats.commentCount,
        shares: +i.stats.shareCount, saves: +i.stats.collectCount, posted_at: +i.createTime, read_at: readAt,
      }));
    } catch (e) { lines.push(JSON.stringify({ handle, video_id: id, error: String(e).slice(0, 80) })); }
    await new Promise((r) => setTimeout(r, 1000));
  }
  const pre = document.createElement("pre");
  pre.textContent = lines.join("\n");
  document.body.replaceChildren(pre);
  return `${handle}: ${lines.length} posts, ${skipped} by other people skipped`;
}
