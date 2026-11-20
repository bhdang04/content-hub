import { useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type Home, type Post, type Track, num, short, useApi } from "../api";
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
          <Card title="Dances to try" sub="Coming later">
            <p className="text-muted text-sm">Trending dances that fit your style will show here once Trends is built.</p>
          </Card>
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
