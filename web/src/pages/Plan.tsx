import { useState } from "react";
import { type Plan, send, useApi } from "../api";
import { Card, Loading } from "../ui";

type Pick = { key: string; label: string };

/** 2-week calendar, up to 3 dances a day (no set times: you post 7-11pm). Tap a dance below, then a day. */
export default function PlanPage({ version }: { version: number }) {
  const [bump, setBump] = useState(0); // refetch after each change
  const { data: p, error } = useApi<Plan>("plan", version + bump);
  const [picked, setPicked] = useState<Pick | null>(null);
  const [saveError, setSaveError] = useState("");
  if (!p) return <Loading error={error} />;

  const write = async (path: string, method: string, body?: object) => {
    const ok = await send(path, method, body);
    setSaveError(ok ? "" : "Couldn't save that. Is the dashboard still running?");
    if (ok) { setPicked(null); setBump((b) => b + 1); }
  };
  const at = (date: string, slot: number) => p.planned.find((x) => x.date === date && x.slot === slot);
  const fmtDay = (d: string) => new Date(`${d}T12:00`).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const best = new Map(p.dances.map((d) => [d.key, d]));
  const fromLibrary = p.shortlist.filter((s) => !s.planned);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Plan</h1>
      <p className="text-muted text-sm">
        {picked ? <>Placing <b className="text-text">{picked.label}</b>: tap an empty spot on a day. <button className="underline" onClick={() => setPicked(null)}>Cancel</button></>
                : "Tap a dance below, then tap an empty spot on a day. Up to 3 a day, posted 7-11pm."}
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
              {[0, 1, 2].map((slot) => {
                const x = at(d.date, slot);
                return x ? (
                  <div key={slot} className="text-xs rounded-lg bg-grid p-2 flex justify-between gap-1">
                    <span className="min-w-0 break-words">{x.name}</span>
                    <button aria-label={`Remove ${x.name}`} className="text-muted hover:text-text" onClick={() => write(`plan/${d.date}/${slot}`, "DELETE")}>✕</button>
                  </div>
                ) : (
                  <button key={slot} disabled={!picked} onClick={() => write(`plan/${d.date}/${slot}`, "PUT", { key: picked!.key, name: picked!.label })}
                          className={`w-full text-left text-xs rounded-lg p-2 border border-dashed ${picked ? "border-good text-text" : "border-grid text-muted"}`}>
                    {picked ? "place here" : "empty"}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Dances I want to do" sub='From your "Tiktok Dances to Do" Favorites.'>
          <p className="text-muted text-sm">Coming next: Claude reads that collection.</p>
        </Card>
        <Card title="From your library" sub="Dances you added on the Library tab. They leave this list once placed on a day.">
          {fromLibrary.length === 0 && <p className="text-muted text-sm">Nothing yet. Open <a href="#library" className="underline">Library</a> and tap "+ Add to plan".</p>}
          <ul className="text-sm">
            {fromLibrary.map((s) => (
              <li key={s.key} className={`border-b border-grid last:border-0 flex items-start gap-2 rounded ${picked?.key === s.key ? "bg-grid" : ""}`}>
                <button onClick={() => setPicked(picked?.key === s.key ? null : s)} className="flex-1 min-w-0 text-left py-2 px-1 hover:text-good">
                  <span className="break-words">{s.label}</span>
                  {best.get(s.key) && <span className="block text-muted text-xs">Done {best.get(s.key)!.times}x</span>}
                </button>
                <button aria-label={`Remove ${s.label} from the list`} className="text-muted hover:text-text py-2 px-1"
                        onClick={() => write("shortlist", "DELETE", { key: s.key, name: s.label })}>✕</button>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
