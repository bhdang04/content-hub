import { useState } from "react";
import { type Dance, type Plan, num, useApi } from "../api";
import { Card, Loading } from "../ui";

const GROUPS: [string, string, (d: Dance) => boolean][] = [
  ["Repeatable (4x+)", "Dances you've posted 4 or more times.", (d) => d.times >= 4],
  ["Done 1-3x", "Dances you've posted a few times. Biggest views first: good ones to remake.", (d) => d.times < 4],
];

/** 2-week posting calendar. Tap a dance, then tap an empty slot to place it. */
export default function PlanPage({ version }: { version: number }) {
  const [bump, setBump] = useState(0); // refetch after each change
  const { data: p, error } = useApi<Plan>("plan", version + bump);
  const [picked, setPicked] = useState<Dance | null>(null);
  const [saveError, setSaveError] = useState("");
  if (!p) return <Loading error={error} />;

  const save = async (date: string, slot: number, method: "PUT" | "DELETE") => {
    setSaveError("");
    const r = await fetch(`/api/plan/${date}/${slot}`, {
      method, headers: { "Content-Type": "application/json" },
      body: method === "PUT" ? JSON.stringify({ key: picked!.key, name: picked!.label }) : undefined,
    }).catch(() => null);
    if (!r?.ok) return setSaveError("Couldn't save that. Is the dashboard still running?");
    setPicked(null);
    setBump((b) => b + 1);
  };
  const at = (date: string, slot: number) => p.planned.find((x) => x.date === date && x.slot === slot);
  const fmtDay = (d: string) => new Date(`${d}T12:00`).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const hour = (h: number) => `${h % 12 || 12}${h < 12 ? "am" : "pm"}`;
  const open = p.dances.filter((d) => !d.planned);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Plan</h1>
      <p className="text-muted text-sm">
        {picked ? <>Placing <b className="text-text">{picked.label}</b>: tap an empty slot. <button className="underline" onClick={() => setPicked(null)}>Cancel</button></>
                : "Tap a dance below, then tap an empty slot. Times = when most of your followers are on TikTok."}
      </p>
      {saveError && <p className="text-bad-text text-sm">{saveError}</p>}

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {p.days.map((d) => (
          <div key={d.date} className="bg-card rounded-xl p-3 min-w-0">
            <div className="flex justify-between text-sm">
              <span className="font-bold">{fmtDay(d.date)}</span>
              {d.posted > 0 && <span className="text-good" title={`${d.posted} posted`}>✓ {d.posted}</span>}
            </div>
            <div className="space-y-1.5 mt-2">
              {p.hours.map((h, slot) => {
                const x = at(d.date, slot);
                return x ? (
                  <div key={slot} className="text-xs rounded-lg bg-grid p-2 flex justify-between gap-1">
                    <span className="min-w-0 break-words"><span className="text-muted">{hour(h)}</span> {x.name}</span>
                    <button aria-label={`Remove ${x.name}`} className="text-muted hover:text-text" onClick={() => save(d.date, slot, "DELETE")}>✕</button>
                  </div>
                ) : (
                  <button key={slot} disabled={!picked} onClick={() => save(d.date, slot, "PUT")}
                          className={`w-full text-left text-xs rounded-lg p-2 border border-dashed ${picked ? "border-good text-text" : "border-grid text-muted"}`}>
                    {hour(h)} {picked ? "· place here" : "· empty"}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {p.dances.length === 0 && (
        <Card title="Possible dances"><p className="text-muted text-sm">No sounds read yet. Ask Claude to read Studio, then run ./run.sh import.</p></Card>
      )}
      <div className="grid md:grid-cols-3 gap-4">
        {GROUPS.map(([title, sub, test]) => (
          <Card key={title} title={title} sub={sub}>
            <ul className="text-sm">
              {open.filter(test).map((d) => (
                <li key={d.key} className={`border-b border-grid last:border-0 flex items-start gap-2 rounded ${picked?.key === d.key ? "bg-grid" : ""}`}>
                  <button onClick={() => setPicked(picked?.key === d.key ? null : d)} className="flex-1 min-w-0 text-left py-2 px-1 hover:text-good">
                    <span className="break-words">{d.label}</span>
                    <span className="block text-muted text-xs break-words">{d.name}</span>
                    <span className="block text-muted text-xs">{d.times}x · best {num(d.best_views)} views</span>
                  </button>
                  <a href={`#video/${d.best_video_id}`} className="text-muted text-xs underline py-2 px-1 shrink-0">see it</a>
                </li>
              ))}
            </ul>
          </Card>
        ))}
        <Card title="Haven't done" sub="From your Saved dances collection.">
          <p className="text-muted text-sm">Coming next: Claude reads your "Dance ideas" Favorites.</p>
        </Card>
      </div>
    </div>
  );
}
