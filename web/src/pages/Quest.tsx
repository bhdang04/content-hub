import { useEffect, useState } from "react";
import { useApi } from "../api";
import { Card, Loading } from "../ui";

type Quest = { week: string; steps: { step: string; label: string; why: string; url: string; done: boolean; note: string | null }[] };

/** Weekly quest: tap each link; it opens in one "tiktok" tab, Claude reads that tab and the step ticks off.
 * Open this page in Claude's Chrome window, so the TikTok tab lands in the group Claude can read. */
export default function QuestPage({ version }: { version: number }) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 3000); // Claude saves in the background; pick up the ticks
    return () => clearInterval(t);
  }, []);
  const { data: q, error } = useApi<Quest>("quest", version + tick);
  if (!q) return <Loading error={error} />;
  const next = q.steps.find((s) => !s.done);
  const left = q.steps.filter((s) => !s.done).length;

  return (
    <div className="space-y-4 max-w-xl">
      <h1 className="text-3xl font-bold pt-2">Weekly quest</h1>
      <p className="text-muted text-sm">
        Tell Claude "start the weekly quest", then tap each link in order. Wait for the ✓ before the next one.
        No scrolling or clicking on TikTok needed.
      </p>
      <Card title={left ? `${left} left` : "Done for this week ✓"} sub={q.week}>
        <ol className="text-sm">
          {q.steps.map((s, i) => (
            <li key={s.step} className={`flex items-start gap-3 py-2.5 border-b border-grid last:border-0 ${s === next ? "text-text" : "text-muted"}`}>
              <span className={`shrink-0 w-6 text-center ${s.done ? "text-good" : ""}`}>{s.done ? "✓" : i + 1}</span>
              <span className="flex-1 min-w-0">
                {s.done ? <span className="break-words">{s.label}</span>
                  : <a href={s.url} target="tiktok" className={`break-words ${s === next ? "underline text-good" : "hover:underline"}`}>{s.label}</a>}
                <span className="block text-xs text-muted">{s.done ? s.note : s.why}</span>
              </span>
            </li>
          ))}
        </ol>
        {!q.steps.some((s) => s.step.startsWith("studio:")) && !q.steps[0].done &&
          <p className="text-muted text-xs mt-2">Your post analytics links show up after your profile is read.</p>}
      </Card>
    </div>
  );
}
