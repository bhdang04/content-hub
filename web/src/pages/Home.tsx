import { useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type Home, type Post, type Track, type Trend, num, send, sendMsg, short, useApi } from "../api";
import { Badge, Card, Kpi, Loading, RecList } from "../ui";

const GOOD = "#25f4ee", GRID = "#26262c", MUTED = "#a1a1aa", CARD = "#16161a";
const axis = { stroke: MUTED, tickLine: false, axisLine: false, fontSize: 12 };
const tip = { contentStyle: { background: CARD, border: `1px solid ${GRID}`, borderRadius: 10 }, labelStyle: { color: MUTED } };

// track.py check columns -> plain words
const CHECKS: Record<string, string> = {
  "views>median": "Beat your typical views",
  "shares>=target": "Shared as much as your top videos",
  "followers>median": "Won more followers than usual",
};

export default function HomePage({ version, onUploaded }: { version: number; onUploaded: () => void }) {
  const { data: h, error } = useApi<Home>("home", version);
  if (!h) return <Loading error={error} />;
  const g = h.goal;
  const onPace = g.last_week >= g.per_week_needed;
  const change = h.views_28d_change_pct;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Home</h1>
      <p className="text-muted text-sm">Past-year export: {h.range[0]} to {h.range[1]}</p>

      <Card>
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
          <span className="text-2xl font-bold">{short(g.followers)} / {short(g.goal)}</span>
          <span className="text-muted text-sm">followers by {g.by}</span>
          <span className="text-sm">need ~{Math.ceil(g.per_week_needed)}/week</span>
          <span className="text-sm">did <span className={onPace ? "text-good" : "text-bad-text"}>{num(g.last_week)}</span> last week</span>
        </div>
        <div className="h-2 bg-grid rounded-full mt-3">
          <div className="h-2 bg-good rounded-full" style={{ width: `${Math.min(100, (g.followers / g.goal) * 100)}%` }} />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,2.1fr)_minmax(0,1fr)] gap-4">
        <div className="space-y-4 min-w-0">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Kpi label="Video views (year)" value={short(h.views_year)} sub={`${short(h.views_28d)} in the last 28 days`}
                 badge={change === null ? undefined : <Badge good={change >= 0}>{change >= 0 ? "+" : ""}{change.toFixed(0)}%</Badge>} />
            <Kpi label="Followers" value={short(g.followers)} sub="this year"
                 badge={<Badge good={h.follower_gain_year >= 0}>{h.follower_gain_year >= 0 ? "+" : ""}{num(h.follower_gain_year)}</Badge>} />
            <Kpi label="Typical engagement" value={`${h.typical_engagement_pct.toFixed(1)}%`} sub={`across ${h.videos} videos`} />
          </div>

          <Card title="Weekly video views" sub="Weekly totals">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={h.weekly_views} margin={{ left: -10, right: 8 }}>
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis dataKey="week" {...axis} tickFormatter={(d: string) => d.slice(5)} minTickGap={30} />
                <YAxis {...axis} tickFormatter={short} />
                <Tooltip {...tip} formatter={(v) => [num(Number(v)), "Views"]} labelFormatter={(d) => `Week ending ${d}`} />
                <Area type="monotone" dataKey="views" stroke={GOOD} strokeWidth={2.5} fill={GOOD} fillOpacity={0.12} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="What to post" sub="More of what worked"><RecList items={h.advice.post} dot="bg-good" /></Card>
            <div className="space-y-4">
              <Card title="What to fix" sub="Clear signs from your numbers"><RecList items={h.advice.improve} dot="bg-bad" /></Card>
              <Card title="What to try" sub="Not sure yet: test on your next videos"><RecList items={h.advice.test} dot="bg-muted" /></Card>
            </div>
          </div>

          <OpeningsCard version={version} />
          <TrackCard version={version} />
        </div>

        <div className="space-y-4 min-w-0">
          <Card title="Add new exports" sub="Drop TikTok Studio zips: Content, Overview, Followers, Viewers">
            <Upload onUploaded={onUploaded} />
          </Card>
          <DanceSwipe version={version} />
          <Card title="When your followers are online" sub="Average active followers by day, last 7 days">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={h.follower_activity} margin={{ left: -10 }}>
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis dataKey="day" {...axis} tickFormatter={(d: string) => d.slice(0, 3)} />
                <YAxis {...axis} tickFormatter={short} />
                <Tooltip {...tip} cursor={{ fill: GRID }} formatter={(v) => [num(Number(v)), "Active followers"]} />
                <Bar dataKey="followers" fill={GOOD} radius={[6, 6, 0, 0]} maxBarSize={22} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>
    </div>
  );
}

function TrackCard({ version }: { version: number }) {
  const { data: t, error } = useApi<Track>("track", version);
  const sub = t?.advice_date ? `Videos posted since the advice from ${t.advice_date}, from the past-7-days export.` : "From the past-7-days export.";
  return (
    <Card title="Did last week's advice work?" sub={sub}>
      {!t ? <Loading error={error} />
        : t.message ? <p className="text-muted text-sm">{t.message}</p>
        : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {Object.entries(t.hits ?? {}).map(([k, [hit, all]]) => (
                <div key={k} className="bg-ground rounded-xl p-4">
                  <div className="text-muted text-xs">{CHECKS[k] ?? k}</div>
                  <div className={`text-2xl font-bold mt-1 ${hit * 2 >= all ? "text-good" : "text-bad-text"}`}>{hit} of {all}</div>
                </div>
              ))}
            </div>
            <h3 className="text-sm font-semibold mt-4 mb-1">Tests so far</h3>
            <RecList items={t.tests} dot="bg-muted" />
            {t.still_growing && <p className="text-muted text-xs mt-2">Videos under 7 days old are still collecting views; check again after the next export.</p>}
          </>
        )}
    </Card>
  );
}

function Upload({ onUploaded }: { onUploaded: () => void }) {
  const [range, setRange] = useState<"year" | "week">("year");
  const [files, setFiles] = useState<File[]>([]);
  const [msgs, setMsgs] = useState<{ ok: boolean; text: string }[]>([]);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    const out = [];
    for (const f of files) {
      const r = await fetch(`/api/upload?range=${range}&name=${encodeURIComponent(f.name)}`, { method: "POST", body: f, headers: { "X-Content-Hub": "1" } });
      const body = await r.json().catch(() => ({}));
      out.push(r.ok ? { ok: true, text: `Saved ${f.name} to ${body.saved}.` } : { ok: false, text: body.detail ?? `${f.name}: upload failed.` });
    }
    setMsgs(out);
    setFiles([]);
    setBusy(false);
    if (out.some((m) => m.ok)) onUploaded();
  }

  return (
    <div className="space-y-3 text-sm">
      <div className="flex gap-2" role="radiogroup" aria-label="Export range">
        {(["year", "week"] as const).map((r) => (
          <button key={r} role="radio" aria-checked={range === r} onClick={() => setRange(r)}
                  className={`rounded-lg px-3 py-1.5 ${range === r ? "bg-grid text-text" : "text-muted hover:text-text"}`}>
            {r === "year" ? "Past 365 days" : "Past 7 days"}
          </button>
        ))}
      </div>
      <p className="text-muted text-xs">Past 365 days feeds Home, Videos and Patterns. Past 7 days feeds the advice check.</p>
      <input type="file" accept=".zip" multiple aria-label="TikTok Studio zips"
             onChange={(e) => setFiles([...(e.target.files ?? [])])}
             className="block w-full text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-grid file:px-3 file:py-1.5 file:text-text" />
      <button disabled={!files.length || busy} onClick={save}
              className="w-full rounded-lg bg-bad py-2 font-semibold text-white disabled:opacity-40">
        {busy ? "Saving…" : "Save uploads"}
      </button>
      {msgs.map((m) => <p key={m.text} className={m.ok ? "text-good" : "text-bad-text"}>{m.text}</p>)}
      <p className="text-muted text-xs">Saved on this Mac only, in git-ignored data/raw/.</p>
    </div>
  );
}

/** Best and worst openings from the Studio data. Hidden until Studio data exists. */
function OpeningsCard({ version }: { version: number }) {
  const { data } = useApi<Post[]>("posts", version);
  const ranked = (data ?? []).filter((p) => !p.is_ad && p.kept_3s != null).sort((a, b) => b.kept_3s! - a.kept_3s!);
  if (ranked.length < 6) return null;
  const list = (ps: Post[]) => (
    <ul className="text-sm">
      {ps.map((p) => (
        <li key={p.video_id} className="flex justify-between gap-3 py-1.5 border-b border-grid last:border-0">
          <a href={`#video/${p.video_id}`} className="hover:underline min-w-0 break-words">{p.title || "(no caption)"}</a>
          <span className="text-muted tabular-nums">{Math.round(p.kept_3s! * 100)}%</span>
        </li>
      ))}
    </ul>
  );
  return (
    <Card title="Openings that worked" sub="Share of viewers still watching at 3s. Watch the top ones before you film.">
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="min-w-0"><p className="text-good text-sm mb-1">Best 3</p>{list(ranked.slice(0, 3))}</div>
        <div className="min-w-0"><p className="text-bad-text text-sm mb-1">Worst 3</p>{list(ranked.slice(-3).reverse())}</div>
      </div>
    </Card>
  );
}

// a dance shows if any of its trending videos was posted within this many days (the read keeps 30)
const PERIODS = [{ days: 30, label: "Past month" }, { days: 15, label: "Half month" }, { days: 7, label: "Past week" }, { days: 3, label: "Past 3 days" }];
const REASONS = ["Not my style", "Too hard / too easy", "Don't like the song"]; // "Don't like the song" must match SONG_REASON in api/main.py

/** One trending dance at a time. ✓ adds it to Plan's "Dances I want to do"; ✕ asks why, so the weekly read can learn. */
function DanceSwipe({ version }: { version: number }) {
  const [bump, setBump] = useState(0);
  const { data, error } = useApi<{ cards: Trend[] }>("trending", version + bump);
  const [asking, setAsking] = useState(false);
  const [why, setWhy] = useState("");
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [days, setDays] = useState(30);
  const cards = data?.cards.filter((x) => x.newest_days < days) ?? [];
  const c = cards[0];

  const swipe = async (decision: "accept" | "decline", reason = "") => {
    if (!c || busy) return;
    setBusy(true);
    const ok = await send("swipe", "POST", { key: c.key, name: c.label, video_id: c.video_id, music_id: c.music_id, decision, reason });
    setSaveError(ok ? "" : "Couldn't save that. Is the dashboard still running?");
    if (ok) { setAsking(false); setWhy(""); setBump((b) => b + 1); }
    setBusy(false);
  };

  return (
    <Card title="Dances to try" sub={data ? `Dances you saw trending and pasted below. ${cards.length} left from the ${PERIODS.find((p) => p.days === days)?.label.toLowerCase()}.` : undefined}>
      {!data && <Loading error={error} />}
      {data && (
        <div className="flex flex-wrap gap-2 mb-3" role="group" aria-label="Posted within">
          {PERIODS.map((p) => (
            <button key={p.days} onClick={() => setDays(p.days)} aria-pressed={days === p.days}
                    className={`rounded-full border px-3 py-1 text-xs ${days === p.days ? "border-good text-good" : "border-grid text-muted"}`}>{p.label}</button>
          ))}
        </div>
      )}
      {data && !c && <p className="text-muted text-sm">{data.cards.length ? "None this recent. Try a longer time." : "No new dances. Paste a TikTok link below."}</p>}
      {saveError && <p className="text-bad-text text-sm">{saveError}</p>}
      {c && (
        <div className="flex flex-col items-center gap-2">
          {/* key: a fresh player per card */}
          <iframe key={c.video_id} src={`https://www.tiktok.com/player/v1/${c.video_id}?description=0&music_info=0&rel=0`}
                  title={c.label} allow="autoplay; fullscreen" className="h-[60vh] max-w-full aspect-[9/16] rounded-xl bg-grid" />
          <p className="font-bold text-center break-words">{c.label}</p>
          <p className="text-muted text-xs text-center break-words">{c.credit ? `dc ${c.credit}` : "no dc credit"} · posted by @{c.author} · {c.views ? `${c.days_ago}d ago` : `you added it ${c.days_ago}d ago`}</p>
          {c.views > 0 && <div className="grid grid-cols-3 gap-2 w-full text-center text-sm">
            <div><p className="font-bold">{short(c.views)}</p><p className="text-muted text-xs">views</p></div>
            <div><p className="font-bold">{short(c.saves)}</p><p className="text-muted text-xs">saves ({c.saves_per_1k} per 1K views)</p></div>
            <div><p className="font-bold">{c.videos}</p><p className="text-muted text-xs">{c.videos === 1 ? "video" : "videos"} with this dance</p></div>
          </div>}
          <div className="flex gap-4 mt-1">
            <button onClick={() => setAsking(true)} disabled={busy} aria-label="Decline"
                    className="rounded-full border border-bad-text text-bad-text w-14 h-14 text-2xl disabled:opacity-30">✕</button>
            <button onClick={() => swipe("accept")} disabled={busy} aria-label="Accept: add to Plan"
                    className="rounded-full border border-good text-good w-14 h-14 text-2xl disabled:opacity-30">✓</button>
          </div>
        </div>
      )}
      <AddTrend onAdded={() => setBump((b) => b + 1)} />
      {asking && c && (
        <div role="dialog" aria-modal="true" aria-label="Why not?" onClick={() => setAsking(false)}
             onKeyDown={(e) => e.key === "Escape" && setAsking(false)}
             className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-card rounded-2xl p-5 w-full max-w-sm space-y-2" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold">Why not this one?</h3>
            {REASONS.map((r, i) => (
              <button key={r} autoFocus={i === 0} onClick={() => swipe("decline", r)} disabled={busy}
                      className="w-full text-left rounded-lg border border-grid hover:border-good px-3 py-2 text-sm">{r}</button>
            ))}
            <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (why.trim()) swipe("decline", `Out of my style: ${why.trim()}`); }}>
              <input value={why} onChange={(e) => setWhy(e.target.value)} maxLength={250} placeholder="Out of my style: why?"
                     aria-label="Out of my style: why?" className="flex-1 min-w-0 rounded-lg border border-grid bg-transparent px-3 py-2 text-sm" />
              <button disabled={busy || !why.trim()} className="rounded-lg border border-grid px-3 text-sm disabled:opacity-30">Save</button>
            </form>
            <button onClick={() => setAsking(false)} className="text-muted text-sm w-full pt-1">Cancel</button>
          </div>
        </div>
      )}
    </Card>
  );
}

/** Paste a dance you saw on TikTok; it becomes a card above. No automated reads: you pick what goes in. */
function AddTrend({ onAdded }: { onAdded: () => void }) {
  const [f, setF] = useState({ link: "", song: "", credit: "" });
  const [msg, setMsg] = useState("");
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const box = "w-full rounded-lg border border-grid bg-transparent px-3 py-2 text-sm";
  return (
    <form className="space-y-2 mt-4 border-t border-grid pt-4"
          onSubmit={async (e) => { e.preventDefault(); const err = await sendMsg("trending", f); setMsg(err); if (!err) { setF({ link: "", song: "", credit: "" }); onAdded(); } }}>
      <h3 className="font-semibold text-sm">Add a dance you saw</h3>
      <input value={f.link} onChange={set("link")} placeholder="TikTok link from the browser (tiktok.com/@name/video/...)" aria-label="TikTok link" className={box} />
      <input value={f.song} onChange={set("song")} maxLength={200} placeholder="Song name" aria-label="Song name" className={box} />
      <input value={f.credit} onChange={set("credit")} maxLength={100} placeholder="dc @creator (optional)" aria-label="Dance credit" className={box} />
      <button disabled={!f.link.trim() || !f.song.trim()} className="w-full rounded-lg border border-good text-good py-2 text-sm disabled:opacity-30">Add card</button>
      {msg && <p className="text-bad-text text-sm">{msg}</p>}
    </form>
  );
}
