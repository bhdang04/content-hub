import { useState } from "react";
import { type Plan, num, send, useApi } from "../api";
import { Card, Loading, TikTok } from "../ui";

/** Every dance you've done, shown by its best video (most views). "Add to plan" puts it on the Plan page. */
export default function LibraryPage({ version }: { version: number }) {
  const [bump, setBump] = useState(0);
  const { data: p, error } = useApi<Plan>("plan", version + bump);
  const [shown, setShown] = useState(9);
  const [saveError, setSaveError] = useState("");
  if (!p) return <Loading error={error} />;
  const inPlan = new Set(p.shortlist.map((s) => s.key));

  const toggle = async (key: string, label: string) => {
    const ok = await send("shortlist", inPlan.has(key) ? "DELETE" : "POST", { key, name: label });
    setSaveError(ok ? "" : "Couldn't save that. Is the dashboard still running?");
    if (ok) setBump((b) => b + 1);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Library</h1>
      {saveError && <p className="text-bad-text text-sm">{saveError}</p>}
      <Card title={`${p.dances.length} dances you've done`}
            sub="Same sound + same dc: credit = one dance. Each shows its best video. Most views first.">
        {p.dances.length === 0 && <p className="text-muted text-sm">No sounds read yet. Ask Claude to read Studio, then run ./run.sh import.</p>}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {p.dances.slice(0, shown).map((d) => (
            <div key={d.key} className="min-w-0">
              {/* TikTok's own player: the browser loads the public video from TikTok; no stats are sent */}
              <TikTok src={`https://www.tiktok.com/player/v1/${d.best_video_id}?description=0&music_info=0&rel=0`}
                      title={d.label} loading="lazy" allow="fullscreen" className="w-full aspect-[9/16] rounded-lg bg-grid" />
              <a href={`#video/${d.best_video_id}`} className="font-bold mt-2 block break-words hover:underline">{d.label}</a>
              <p className="text-muted text-xs">Done {d.times}x · best {num(d.best_views)} views</p>
              <button onClick={() => toggle(d.key, d.label)}
                      className={`mt-2 w-full text-sm rounded-lg py-1.5 border ${inPlan.has(d.key) ? "border-good text-good" : "border-grid hover:border-good"}`}>
                {inPlan.has(d.key) ? "✓ In plan (tap to remove)" : "+ Add to plan"}
              </button>
            </div>
          ))}
        </div>
        {shown < p.dances.length && (
          <button onClick={() => setShown(shown + 9)} className="mt-4 text-sm text-muted hover:text-text">
            Show 9 more ({p.dances.length - shown} left)
          </button>
        )}
      </Card>
    </div>
  );
}
