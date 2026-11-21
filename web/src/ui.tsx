import type { ComponentProps, ReactNode } from "react";

/** TikTok's player. In demo mode (./run.sh demo) the video IDs are fake, so show a box instead of a dead player. */
export function TikTok(props: ComponentProps<"iframe">) {
  if (import.meta.env.VITE_DEMO !== "1") return <iframe {...props} />;
  return (
    <div className={`${props.className} grid place-items-center text-muted text-sm`} onClick={props.onClick}>
      Demo video
    </div>
  );
}

export function Card({ title, sub, children, className = "" }: { title?: string; sub?: string; children?: ReactNode; className?: string }) {
  return (
    <section className={`bg-card rounded-2xl p-[22px] ${className}`}>
      {title && <h2 className="font-semibold">{title}</h2>}
      {sub && <p className="text-muted text-sm mt-1 mb-3">{sub}</p>}
      {children}
    </section>
  );
}

export function Badge({ children, good }: { children: ReactNode; good: boolean }) {
  return (
    <span className={`rounded-lg px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${good ? "bg-good/15 text-good" : "bg-bad/20 text-bad-text"}`}>
      {children}
    </span>
  );
}

export function Kpi({ label, value, sub, badge }: { label: string; value: string; sub: string; badge?: ReactNode }) {
  return (
    <div className="bg-card rounded-2xl p-[22px]">
      <div className="text-muted text-sm">{label}</div>
      <div className="text-4xl font-bold tracking-tight mt-1">{value}</div>
      <div className="text-muted text-xs mt-1 flex flex-wrap items-center gap-2">{badge}{sub}</div>
    </div>
  );
}

/** One bullet list of advice. `dot` is a Tailwind bg class: bg-good, bg-bad or bg-muted. */
export function RecList({ items, dot }: { items?: string[]; dot: string }) {
  if (!items?.length) return <p className="text-muted text-sm">Nothing from this data yet.</p>;
  return (
    <ul>
      {items.map((t) => (
        <li key={t} className="flex gap-3 py-2.5 border-b border-grid last:border-0 leading-relaxed text-sm">
          <span className={`${dot} shrink-0 size-2.5 rounded-full mt-1.5`} />
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

export function Loading({ error }: { error?: string }) {
  return error ? <Card title="Couldn't load this" sub={error} /> : <p className="text-muted">Loading…</p>;
}

/** Plain table. Columns: [header, cell renderer, right-align?]. Click a header to sort when `sort` is given. */
export function Table<T>({ rows, cols, sort, onSort }: {
  rows: T[];
  cols: { head: string; cell: (r: T) => ReactNode; right?: boolean; key?: string }[];
  sort?: { key: string; desc: boolean };
  onSort?: (key: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-left">
            {cols.map((c) => (
              <th key={c.head} className={`font-normal py-2 pr-4 ${c.right ? "text-right" : ""}`}>
                {c.key && onSort ? (
                  <button className="hover:text-text" onClick={() => onSort(c.key!)}>
                    {c.head}{sort?.key === c.key ? (sort.desc ? " ↓" : " ↑") : ""}
                  </button>
                ) : c.head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-grid">
              {cols.map((c) => (
                <td key={c.head} className={`py-2 pr-4 ${c.right ? "text-right tabular-nums" : ""}`}>{c.cell(r)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
