import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type PostDetail, num, since, useApi } from "../api";
import { Badge, Card, Kpi, Loading } from "../ui";

const GOOD = "#25f4ee", GRID = "#26262c", MUTED = "#a1a1aa", CARD = "#16161a";
const axis = { stroke: MUTED, tickLine: false, axisLine: false, fontSize: 12 };
const tip = { contentStyle: { background: CARD, border: `1px solid ${GRID}`, borderRadius: 10 }, labelStyle: { color: MUTED } };
const pct = (x: number | null | undefined) => (x == null ? "–" : `${Math.round(x * 100)}%`);

/** One video's Studio numbers next to your usual (middle value of your other posts, ads left out). */
export default function VideoPage({ id, version }: { id: string; version: number }) {
  const { data: p, error } = useApi<PostDetail>(`posts/${id}`, version);
  if (!p) return <Loading error={error} />;
  const u = p.usual;

  const vs = (mine: number | null, usual: number | null) =>
    mine == null || usual == null ? undefined : <Badge good={mine >= usual}>{mine >= usual ? "above usual" : "below usual"}</Badge>;
  const tiles: [string, string, string, number | null, number | null][] = [
    ["Views", num(p.views), num(u.views), p.views, u.views],
    ["Still watching at 3s", pct(p.kept_3s), pct(u.kept_3s), p.kept_3s, u.kept_3s],
    ["Average watch", `${p.avg_watch_s.toFixed(1)}s`, `${u.avg_watch_s.toFixed(1)}s`, p.avg_watch_s, u.avg_watch_s],
    ["Watched to the end", pct(p.full_watch_rate), pct(u.full_watch_rate), p.full_watch_rate, u.full_watch_rate],
    ["Saves", num(p.saves), num(u.saves), p.saves, u.saves],
    ["New followers", p.new_followers == null ? "–" : num(p.new_followers), num(u.new_followers ?? 0), p.new_followers, u.new_followers],
  ];

  const curve = p.retention.map((v, s) => ({ s, mine: Math.round(v * 100), usual: p.usual_retention[s] == null ? null : Math.round(p.usual_retention[s] * 100) }));
  const traffic: [string, number | null][] = [
    ["For You", p.pct_for_you], ["Search", p.pct_search], ["Your profile", p.pct_profile],
    ["Following", p.pct_following], ["Other", p.pct_other],
  ];

  return (
    <div className="space-y-4">
      <a href="#videos" className="text-muted text-sm hover:text-text">← All videos</a>
      <div>
        <h1 className="text-2xl font-bold break-words">{p.title || "(no caption)"}</h1>
        <p className="text-muted text-sm mt-1">
          Posted {p.posted} ·{p.gap_days == null ? "" : ` ${since(p.gap_days)} after your last post ·`} {Math.round(p.length_s)}s long ·{" "}
          <a className="hover:underline" target="_blank" rel="noreferrer"
             href={`https://www.tiktok.com/tiktokstudio/analytics/${p.video_id}?qa_enter_from=analytics`}>open in TikTok Studio</a>
        </p>
        {p.is_ad === 1 && <p className="text-sm mt-2">Paid/sponsored post: its views came from ads, so it's left out of "your usual".</p>}
      </div>

      {p.advice.length > 0 && (
        <Card title="What to do">
          <ul className="text-sm space-y-1.5">{p.advice.map((a) => <li key={a}>{a}</li>)}</ul>
        </Card>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {tiles.map(([label, value, usual, mine, base]) => (
          <Kpi key={label} label={label} value={value} sub={`Usual: ${usual}`} badge={value === usual ? undefined : vs(mine, base)} />
        ))}
      </div>

      <Card title="When viewers left"
            sub={p.retention.length ? "Cyan line = this video, grey = your usual." : "No watch data for this video yet."}>
        <div className="h-64">
          <ResponsiveContainer>
            <LineChart data={curve} margin={{ left: -10, right: 10 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="s" {...axis} tickFormatter={(s: number) => `${s}s`} />
              <YAxis {...axis} domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
              <Tooltip {...tip} labelFormatter={(s) => `At ${s}s`}
                       formatter={(v, k) => [`${v}%`, k === "mine" ? "This video" : "Your usual"]} />
              <Line dataKey="usual" stroke={MUTED} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
              <Line dataKey="mine" stroke={GOOD} strokeWidth={2.5} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card title="Where viewers found it">
          {traffic.map(([name, v]) => (
            <div key={name} className="py-1.5 text-sm">
              <div className="flex justify-between"><span>{name}</span><span className="tabular-nums">{pct(v)}</span></div>
              <div className="h-1.5 rounded bg-grid mt-1"><div className="h-full rounded bg-good" style={{ width: pct(v ?? 0) }} /></div>
            </div>
          ))}
        </Card>
        <Card title="What people searched to find it">
          {p.search_terms.length ? (
            <ul className="text-sm">
              {p.search_terms.map(([q, v]) => (
                <li key={q} className="flex justify-between py-1.5 border-b border-grid last:border-0">
                  <span>{q}</span><span className="text-muted tabular-nums">{pct(v)}</span>
                </li>
              ))}
            </ul>
          ) : <p className="text-muted text-sm">No search views yet.</p>}
        </Card>
      </div>
      <p className="text-muted text-xs">"Usual" = the middle value across your {p.usual_from} Studio posts (ads left out).</p>
    </div>
  );
}
