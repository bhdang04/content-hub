import { useState } from "react";
import { type Patterns, num, useApi } from "../api";
import { Card, Loading, Table, TikTok } from "../ui";

const fmt = (n: number | null) => (n === null ? "–" : num(n));

export default function PatternsPage({ version }: { version: number }) {
  const { data: p, error } = useApi<Patterns>("patterns", version);
  const [shown, setShown] = useState(6);
  if (!p) return <Loading error={error} />;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Patterns</h1>
      <Card title="What your biggest videos do differently"
            sub={`Your ${p.top_count} most-viewed videos vs your other ${p.other_count}. Typical (middle) value for each group.`}>
        <Table rows={p.differences} cols={[
          { head: "What", cell: (r) => r.what },
          { head: `Your ${p.top_count} biggest videos`, right: true, cell: (r) => fmt(r.top) },
          { head: "Your other videos", right: true, cell: (r) => fmt(r.other) },
          { head: "What it means", cell: (r) => r.meaning },
        ]} />
      </Card>
      <Card title="Which videos won you followers"
            sub="New followers for every 1,000 views, best first. Higher = viewers liked you enough to follow.">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {p.followers.slice(0, shown).map((r) => (
            <div key={r.video_id} className="min-w-0">
              {/* TikTok's own player: the browser loads the public video from TikTok; no stats are sent */}
              <TikTok src={`https://www.tiktok.com/player/v1/${r.video_id}?description=0&music_info=0&rel=0`}
                      title={r.title} loading="lazy" allow="fullscreen" className="w-full aspect-[9/16] rounded-lg bg-grid" />
              <p className="text-lg font-bold mt-2 tabular-nums">{fmt(r.followers_per_1k)} <span className="text-muted text-xs font-normal">followers per 1,000 views</span></p>
              <a href={`#video/${r.video_id}`} className="text-sm hover:underline block truncate">{r.title || "(no caption)"}</a>
              <p className="text-muted text-xs">{num(r.views)} views · {r.posted}</p>
            </div>
          ))}
        </div>
        {shown < p.followers.length && (
          <button onClick={() => setShown(shown + 6)} className="mt-4 text-sm text-muted hover:text-text">
            Show 6 more ({p.followers.length - shown} left)
          </button>
        )}
      </Card>
    </div>
  );
}
