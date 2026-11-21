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
  const [at_, setAt] = useState(0); // which "want" video the player shows
  if (!p) return <Loading error={error} />;

  const write = async (path: string, method: string, body?: object) => {
    const ok = await send(path, method, body);
    setSaveError(ok ? "" : "Couldn't save that. Is the dashboard still running?");
    if (ok) { setPicked(null); setBump((b) => b + 1); }
  };
  const at = (date: string, slot: number) => p.planned.find((x) => x.date === date && x.slot === slot);
  const fmtDay = (d: string) => new Date(`${d}T12:00`).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const best = new Map(p.dances.map((d) => [d.key, d]));
  // shortlist holds both lists: dances you've done (added on Library) and new ones (+ Add in the player)
  const saved = new Set(p.shortlist.map((s) => s.key));
  const fromLibrary = p.shortlist.filter((s) => !s.planned && best.has(s.key));
  const added = p.shortlist.filter((s) => !s.planned && !best.has(s.key));
  const want = p.ideas.filter((i) => !i.done && !i.planned && !saved.has(i.key));
  const n = Math.min(at_, want.length - 1); // the list shrinks after each Add
  const cur = want[n];
  const row = (s: { key: string; label: string }) => (
    <li key={s.key} className={`border-b border-grid last:border-0 flex items-start gap-2 rounded ${picked?.key === s.key ? "bg-grid" : ""}`}>
      <button onClick={() => setPicked(picked?.key === s.key ? null : s)} className="flex-1 min-w-0 text-left py-2 px-1 hover:text-good">
        <span className="break-words">{s.label}</span>
        {best.get(s.key) && <span className="block text-muted text-xs">Done {best.get(s.key)!.times}x</span>}
      </button>
      <button aria-label={`Remove ${s.label} from the list`} className="text-muted hover:text-text py-2 px-1"
              onClick={() => write("shortlist", "DELETE", { key: s.key, name: s.label })}>✕</button>
    </li>
  );
  const doneCount = p.ideas.filter((i) => i.done).length;

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
        <Card title="Dances I want to do"
              sub={`Dances you ✓ on Home, then your "Tiktok Dances to Do" Favorites, by song. ${doneCount ? `${doneCount} you've already posted are left out (they're in Library).` : ""}`}>
          {p.ideas.length === 0 && <p className="text-muted text-sm">Not read yet. Ask Claude to read your Favorites, then run ./run.sh import.</p>}
          {cur && (
            <div className="flex flex-col items-center gap-2">
              {/* key: a new iframe per video so each one loads fresh */}
              <iframe key={cur.video_id} src={`https://www.tiktok.com/player/v1/${cur.video_id}?description=0&music_info=0&rel=0`}
                      title={cur.label} allow="autoplay; fullscreen" className="h-[60vh] max-w-full aspect-[9/16] rounded-xl bg-grid" />
              <p className="text-sm text-center break-words">{cur.label}</p>
              <p className="text-muted text-xs text-center break-words">{cur.credit ? `dc ${cur.credit}` : `posted by @${cur.author}`}</p>
              <div className="flex items-center gap-3">
                <button onClick={() => setAt(n - 1)} disabled={n === 0} aria-label="Previous video"
                        className="rounded-full border border-grid px-4 py-2 disabled:opacity-30">‹ Back</button>
                <button onClick={() => write("shortlist", "POST", { key: cur.key, name: cur.label })}
                        className="rounded-full border border-good text-good px-4 py-2">+ Add</button>
                <button onClick={() => setAt(n + 1)} disabled={n === want.length - 1} aria-label="Next video"
                        className="rounded-full border border-grid px-4 py-2 disabled:opacity-30">Next ›</button>
              </div>
              <span className="text-muted text-xs tabular-nums">{n + 1} / {want.length}</span>
            </div>
          )}
          {p.ideas.length > 0 && !cur && <p className="text-muted text-sm">Every Favorite is added or on a day.</p>}
          <h3 className="font-bold text-sm mt-4">Added ({added.length})</h3>
          {added.length === 0 && <p className="text-muted text-sm">Tap "+ Add" on a video to save it here. Then tap it and a day.</p>}
          <ul className="text-sm">{added.map(row)}</ul>
        </Card>
        <Card title="From your library" sub="Dances you added on the Library tab. They leave this list once placed on a day.">
          {fromLibrary.length === 0 && <p className="text-muted text-sm">Nothing yet. Open <a href="#library" className="underline">Library</a> and tap "+ Add to plan".</p>}
          <ul className="text-sm">{fromLibrary.map(row)}</ul>
        </Card>
      </div>

    </div>
  );
}
