import { useState } from "react";
import { type Video, num, useApi } from "../api";
import { Card, Loading, Table } from "../ui";

export default function VideosPage({ version }: { version: number }) {
  const { data, error } = useApi<Video[]>("videos", version);
  const [sort, setSort] = useState({ key: "views", desc: true });
  if (!data) return <Loading error={error} />;

  const k = sort.key as keyof Video;
  const rows = [...data].sort((a, b) => {
    const x = a[k] ?? -Infinity, y = b[k] ?? -Infinity;
    return (x < y ? -1 : x > y ? 1 : 0) * (sort.desc ? -1 : 1);
  });
  const onSort = (key: string) => setSort((s) => ({ key, desc: s.key === key ? !s.desc : true }));

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Videos</h1>
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
