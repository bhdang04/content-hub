import { useState } from "react";
import { type Post, type Video, num, since, useApi } from "../api";
import { Card, Loading, Table } from "../ui";

export default function VideosPage({ version }: { version: number }) {
  const { data, error } = useApi<Video[]>("videos", version);
  const studio = useApi<Post[]>("posts", version);
  const [sort, setSort] = useState({ key: "views", desc: true });
  if (!data) return <Loading error={error} />;
  const pct = (x: number | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);

  const k = sort.key as keyof Video;
  const rows = [...data].sort((a, b) => {
    const x = a[k] ?? -Infinity, y = b[k] ?? -Infinity;
    return (x < y ? -1 : x > y ? 1 : 0) * (sort.desc ? -1 : 1);
  });
  const onSort = (key: string) => setSort((s) => ({ key, desc: s.key === key ? !s.desc : true }));

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Videos</h1>
      <Card title="Latest posts (TikTok Studio)"
            sub={studio.data ? `${studio.data.length} posts, newest first. Click one for how viewers watched it.` : studio.error ?? "Loading…"}>
        {studio.data && (
          <Table rows={studio.data} cols={[
            { head: "Video", cell: (p) => <a href={`#video/${p.video_id}`} className="hover:underline">{p.title || "(no caption)"}{p.is_ad ? " (ad)" : ""}</a> },
            { head: "Posted", cell: (p) => p.posted },
            { head: "Since last post", right: true, cell: (p) => (p.gap_days == null ? "–" : since(p.gap_days)) },
            { head: "Views", right: true, cell: (p) => num(p.views) },
            { head: "Still watching at 3s", right: true, cell: (p) => pct(p.kept_3s) },
            { head: "Watched to the end", right: true, cell: (p) => pct(p.full_watch_rate) },
            { head: "New followers", right: true, cell: (p) => (p.new_followers == null ? "–" : num(p.new_followers)) },
          ]} />
        )}
      </Card>
      <Card title="Your videos" sub={`${data.length} videos, merged from every Content export (each holds ~15 top videos). Click a column to sort.`}>
        <Table rows={rows} sort={sort} onSort={onSort} cols={[
          { head: "Video", key: "title", cell: (v) => <a href={v.link} target="_blank" rel="noreferrer" className="hover:underline">{v.title}</a> },
          { head: "Posted", key: "posted", cell: (v) => v.posted },
          { head: "Views", key: "views", right: true, cell: (v) => num(v.views) },
          { head: "Likes", key: "likes", right: true, cell: (v) => num(v.likes) },
          { head: "Comments", key: "comments", right: true, cell: (v) => num(v.comments) },
          { head: "Shares", key: "shares", right: true, cell: (v) => num(v.shares) },
          { head: "Engagement %", key: "engagement_pct", right: true, cell: (v) => v.engagement_pct?.toFixed(1) ?? "–" },
        ]} />
      </Card>
    </div>
  );
}
