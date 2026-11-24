import { type DragEvent, useState } from "react";
import { motion } from "framer-motion";
import { type Plan, send, useApi } from "../api";
import { Badge, Card, Loading, Overlay, TikTok } from "../ui";

type Pick = { key: string; label: string };
// a calendar spot: a day's slot (plan) or a day's backup; n = slot or backup rank
type Spot = { kind: "plan" | "backup"; date: string; n: number };
// step 9 picker's one-line reason under a planned dance
// on the calendar it's shortened (full sentence on hover); wording comes from src/picker.py
const why = (w: string | null) => w && <span className="block text-muted mt-0.5" title={w}>{shortWhy(w)}</span>;
const shortWhy = (w: string) => {
  const m = w.match(/^Brings \+(\d+) followers a take \(you usually get \+(\d+)\)/);
  return m ? `+${m[1]} followers a take (usual +${m[2]})` : w.startsWith("Last take got") ? "Fewer followers last time: rest it" : w;
};

/** 2-week calendar, up to 3 dances a day (no set times: you post 7-11pm). Tap a dance below, then a day. */
export default function PlanPage({ version }: { version: number }) {
  const [bump, setBump] = useState(0); // refetch after each change
  const { data: p, error } = useApi<Plan>("plan", version + bump);
  const [picked, setPicked] = useState<Pick | null>(null);
  const [saveError, setSaveError] = useState("");
  const [at_, setAt] = useState(0); // which "want" video the player shows
  const [moving, setMoving] = useState<(Spot & { name: string }) | null>(null); // dance being dragged or tap-moved
  const [preview, setPreview] = useState<{ video_id: string; name: string; why?: string | null } | null>(null); // planned dance's reference video
  if (!p) return <Loading error={error} />;

  const write = async (path: string, method: string, body?: object) => {
    const ok = await send(path, method, body);
    setSaveError(ok ? "" : "Couldn't save that. Is the dashboard still running?");
    if (ok) { setPicked(null); setBump((b) => b + 1); }
  };
  const move = (to: Spot) => {
    if (!moving) return;
    const { name: _, ...from } = moving;
    setMoving(null);
    write("plan/move", "POST", { from, to });
  };
  // drag on a computer; the ↕ button then a tap does the same on a phone
  const drag = (s: Spot & { name: string }) => ({
    draggable: true,
    onDragStart: (e: DragEvent) => { e.dataTransfer.setData("text/plain", s.name); setTimeout(() => setMoving(s)); }, // later: Chrome drops the drag if the page re-renders during dragstart
  });
  const dropOn = (to: Spot) => ({
    onDragOver: (e: DragEvent) => e.preventDefault(),
    onDrop: (e: DragEvent) => { e.preventDefault(); move(to); },
  });
  const moveBtn = (s: Spot & { name: string }) => (
    <button aria-label={`Move ${s.name}`} title="Move (or drag it)" className="text-muted hover:text-text"
            onClick={() => { setPicked(null); setMoving(moving?.date === s.date && moving.kind === s.kind && moving.n === s.n ? null : s); }}>↕</button>
  );
  const at = (date: string, slot: number) => p.planned.find((x) => x.date === date && x.slot === slot);
  const fmtDay = (d: string) => new Date(`${d}T12:00`).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const best = new Map(p.dances.map((d) => [d.key, d]));
  // new dance = learn it first; done = a refilm of one you've posted
  const tag = (key: string) => best.has(key)
    ? <span className="block text-muted">Done {best.get(key)!.times}x</span>
    : <span className="block mt-0.5"><Badge good>Learn</Badge></span>;
  // shortlist holds both lists: dances you've done (added on Library) and new ones (+ Add in the player)
  const saved = new Set(p.shortlist.map((s) => s.key));
  const fromLibrary = p.shortlist.filter((s) => !s.planned && best.has(s.key));
  const added = p.shortlist.filter((s) => !s.planned && !s.checked && !best.has(s.key)); // ticked off on Home = done, even before the export shows it
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
  // one id per dance on the calendar (2nd copy of a dance gets #1), so a moved dance springs to its new spot
  const seen = new Map<string, number>();
  const flyId = (key: string) => { const k = seen.get(key) ?? 0; seen.set(key, k + 1); return `${key}#${k}`; };
  const spring = { type: "spring", stiffness: 500, damping: 35 } as const;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Plan</h1>
      <p className="text-muted text-sm">
        {moving ? <>Moving <b className="text-text">{moving.name}</b>: tap any spot or backup. A dance already there swaps places. <button className="underline" onClick={() => setMoving(null)}>Cancel</button></>
          : picked ? <>Placing <b className="text-text">{picked.label}</b>: tap an empty spot on a day. <button className="underline" onClick={() => setPicked(null)}>Cancel</button></>
                : "Tap a dance below, then tap an empty spot on a day. Up to 3 a day, posted 7-11pm. Drag a dance (or tap ↕) to move it."}
      </p>
      {saveError && <p className="text-bad-text text-sm">{saveError}</p>}

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {p.days.map((d) => (
          <motion.div key={d.date} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: p.days.indexOf(d) * 0.03 }} className="neon-card rounded-xl p-3 min-w-0">
            <div className="flex justify-between text-sm">
              <span className="font-bold">{fmtDay(d.date)}</span>
              {d.posted > 0 && <span className="text-good" title={`${d.posted} posted`}>✓ {d.posted}</span>}
            </div>
            <div className="space-y-1.5 mt-2">
              {[0, 1, 2].map((slot) => {
                const x = at(d.date, slot);
                const spot: Spot = { kind: "plan", date: d.date, n: slot };
                return x ? (
                  <motion.div key={slot} layoutId={flyId(x.key)} transition={spring}>
                  <div {...drag({ ...spot, name: x.name })} {...dropOn(spot)}
                       className={`text-xs rounded-lg bg-grid p-2 flex justify-between gap-1 cursor-grab ${moving ? "outline outline-1 outline-good" : ""}`}>
                    {moving
                      ? <button className="min-w-0 break-words text-left" onClick={() => move(spot)}>{x.name}{tag(x.key)}</button>
                      : x.video_id
                      ? <button className="min-w-0 break-words text-left hover:text-good" title="Watch it" onClick={() => setPreview({ video_id: x.video_id!, name: x.name, why: x.why })}>▶ {x.name}{tag(x.key)}{why(x.why)}</button>
                      : <span className="min-w-0 break-words">{x.name}{tag(x.key)}{why(x.why)}</span>}
                    <span className="flex flex-col gap-1">{moveBtn({ ...spot, name: x.name })}
                    <button aria-label={`Remove ${x.name}`} className="text-muted hover:text-text" onClick={() => write(`plan/${d.date}/${slot}`, "DELETE")}>✕</button></span>
                  </div>
                  </motion.div>
                ) : (
                  <button key={slot} disabled={!picked && !moving} {...dropOn(spot)}
                          onClick={() => moving ? move(spot) : write(`plan/${d.date}/${slot}`, "PUT", { key: picked!.key, name: picked!.label })}
                          className={`w-full text-left text-xs rounded-lg p-2 border border-dashed ${picked || moving ? "border-good text-text" : "border-grid text-muted"}`}>
                    {moving ? "move here" : picked ? "place here" : "empty"}
                  </button>
                );
              })}
            </div>
            {(() => {
              const bs = p.backups.filter((b) => b.date === d.date);
              const end: Spot = { kind: "backup", date: d.date, n: Math.max(-1, ...bs.map((b) => b.rank)) + 1 }; // add after the last backup
              if (!bs.length && !moving) return null;
              return (
                <div className="text-muted text-xs mt-2 space-y-1">
                  <p>Backups:</p>
                  {bs.map((b) => {
                    const spot: Spot = { kind: "backup", date: d.date, n: b.rank };
                    return (
                      <motion.div key={b.key} layoutId={flyId(b.key)} transition={spring}>
                      <div {...drag({ ...spot, name: b.name })} {...dropOn(spot)} className="flex justify-between gap-1 cursor-grab">
                        {moving
                          ? <button className="min-w-0 text-left break-words text-text" onClick={() => move(spot)}>{b.name}{tag(b.key)}</button>
                          : b.video_id
                          ? <button title={b.why ?? undefined} className="min-w-0 text-left break-words hover:text-good" onClick={() => setPreview({ video_id: b.video_id!, name: b.name, why: b.why })}>▶ {b.name}{tag(b.key)}</button>
                          : <span className="min-w-0 break-words">{b.name}{tag(b.key)}</span>}
                        {moveBtn({ ...spot, name: b.name })}
                      </div>
                      </motion.div>
                    );
                  })}
                  {moving && end.n <= 9 && (
                    <button {...dropOn(end)} onClick={() => move(end)} className="w-full text-left rounded-lg p-1.5 border border-dashed border-good text-text">add as backup</button>
                  )}
                </div>
              );
            })()}
          </motion.div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4 items-start">
        <Card title="Dances I want to do"
              sub={`Dances you ✓ on Home, your saved Favorites, then competitors' posts, by song. ${doneCount ? `${doneCount} you've already posted are left out (they're in Library).` : ""}`}>
          {p.ideas.length === 0 && <p className="text-muted text-sm">Nothing yet. ✓ dances on Home, or add posts on the Competitors page.</p>}
          {cur && (
            <div className="flex flex-col items-center gap-2">
              {/* key: a new iframe per video so each one loads fresh */}
              <TikTok key={cur.video_id} src={`https://www.tiktok.com/player/v1/${cur.video_id}?description=0&music_info=0&rel=0`}
                      title={cur.label} allow="autoplay; fullscreen" className="h-[60vh] max-w-full aspect-[9/16] rounded-xl bg-grid" />
              <p className="text-sm text-center break-words">{cur.label}</p>
              <p className="text-muted text-xs text-center break-words">{cur.source} · {cur.credit ? `dc ${cur.credit}` : `posted by @${cur.author}`}</p>
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
          {p.ideas.length > 0 && !cur && <p className="text-muted text-sm">Every dance here is added or on a day.</p>}
          <h3 className="font-bold text-sm mt-4">Added ({added.length})</h3>
          {added.length === 0 && <p className="text-muted text-sm">Tap "+ Add" on a video to save it here. Then tap it and a day.</p>}
          <ul className="text-sm">{added.map(row)}</ul>
        </Card>
        <Card title="From your library" sub="Dances you added on the Library tab. They leave this list once placed on a day.">
          {fromLibrary.length === 0 && <p className="text-muted text-sm">Nothing yet. Open <a href="#library" className="underline">Library</a> and tap "+ Add to plan".</p>}
          <ul className="text-sm">{fromLibrary.map(row)}</ul>
        </Card>
      </div>

      <Overlay open={!!preview} onClose={() => setPreview(null)} label={preview?.name} className="flex-col gap-3">
        {preview && <>
          <TikTok key={preview.video_id} src={`https://www.tiktok.com/player/v1/${preview.video_id}?description=0&music_info=0&rel=0&autoplay=1`}
                  title={preview.name} allow="autoplay; fullscreen" className="h-[80vh] max-w-full aspect-[9/16] rounded-xl bg-grid" onClick={(e) => e.stopPropagation()} />
          <p className="text-sm text-center break-words max-w-md">{preview.name}</p>
          {preview.why && <p className="text-muted text-xs text-center max-w-md">{preview.why}</p>}
          <button autoFocus className="rounded-full border border-grid px-4 py-2" onClick={() => setPreview(null)}>Close</button>
        </>}
      </Overlay>
    </div>
  );
}
