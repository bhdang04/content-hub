import { type ComponentProps, type ReactNode, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, animate, motion, useReducedMotion } from "framer-motion";

const rise = { initial: { opacity: 0, y: 18 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-40px" },
               transition: { type: "spring", stiffness: 260, damping: 26 } } as const;

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
    <motion.section {...rise} className={`neon-card rounded-2xl p-[22px] ${className}`}>
      {title && <h2 className="font-semibold">{title}</h2>}
      {sub && <p className="text-muted text-sm mt-1 mb-3">{sub}</p>}
      {children}
    </motion.section>
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
    <motion.div {...rise} whileHover={{ y: -4 }} className="neon-card rounded-2xl p-[22px]">
      <div className="text-muted text-sm">{label}</div>
      <div className="text-4xl font-bold tracking-tight mt-1"><CountUp value={value} /></div>
      <div className="text-muted text-xs mt-1 flex flex-wrap items-center gap-2">{badge}{sub}</div>
    </motion.div>
  );
}

/** "1.5M", "10.5%", "3,452": the number counts up from 0, the rest stays. Anything else shows as is. */
function CountUp({ value }: { value: string }) {
  const m = value.match(/^([\d,]*\.?\d+)(.*)$/);
  const end = m ? Number(m[1].replace(/,/g, "")) : 0;
  const dec = m?.[1].split(".")[1]?.length ?? 0;
  const still = useReducedMotion();
  const [n, setN] = useState(m && !still ? 0 : end);
  useEffect(() => {
    if (!m || still) return setN(end);
    const a = animate(0, end, { duration: 1.2, ease: "easeOut", onUpdate: setN });
    return () => a.stop();
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!m) return <>{value}</>;
  const txt = m[1].includes(",") ? Math.round(n).toLocaleString("en-US") : n.toFixed(dec);
  return <>{txt}{m[2]}</>;
}

/** Full-screen popup, drawn at the page root (a parent's transform would otherwise trap a fixed box). */
export function Overlay({ open, onClose, children, className = "", label }: { open: boolean; onClose: () => void; children: ReactNode; className?: string; label?: string }) {
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div role="dialog" aria-modal="true" aria-label={label} onClick={onClose}
                    onKeyDown={(e) => e.key === "Escape" && onClose()}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className={`fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 ${className}`}>
          {children}
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
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

/** `small`: a shimmer bar inside a card, instead of a whole-page placeholder. */
export function Loading({ error, small }: { error?: string; small?: boolean }) {
  if (error) return small ? <p className="text-bad-text text-sm">{error}</p> : <Card title="Couldn't load this" sub={error} />;
  if (small) return <div className="shimmer h-16 rounded-xl" aria-label="Loading" />;
  return (
    <div className="space-y-4 pt-2" aria-label="Loading">
      <div className="shimmer h-9 w-48 rounded-lg" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">{[0, 1, 2].map((i) => <div key={i} className="shimmer h-28 rounded-2xl" />)}</div>
      <div className="shimmer h-64 rounded-2xl" />
    </div>
  );
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
