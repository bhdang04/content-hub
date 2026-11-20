import { type Patterns, num, useApi } from "../api";
import { Card, Loading, Table } from "../ui";

const fmt = (n: number | null) => (n === null ? "–" : num(n));

export default function PatternsPage({ version }: { version: number }) {
  const { data: p, error } = useApi<Patterns>("patterns", version);
  if (!p) return <Loading error={error} />;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Patterns</h1>
      <Card title="What your biggest videos do differently"
            sub={`Your ${p.top_count} most-viewed videos vs your other ${p.other_count}. Typical (middle) value for each group.`}>
        <Table rows={p.differences} cols={[
          { head: "What", cell: (r) => r.what },
          { head: `Your ${p.top_count} biggest videos`, right: true, cell: (r) => fmt(r.top) },
          { head: "Your other videos", right: true, cell: (r) => fmt(r.other) },
          { head: "What it means", cell: (r) => r.meaning },
        ]} />
      </Card>
      <Card title="Which videos won you followers"
            sub="New followers in the 3 days after posting, for every 1,000 views. Higher = viewers liked you enough to follow.">
        <Table rows={p.followers} cols={[
          { head: "Video", cell: (r) => r.title },
          { head: "Posted", cell: (r) => r.posted },
          { head: "Views", right: true, cell: (r) => num(r.views) },
          { head: "New followers per 1,000 views", right: true, cell: (r) => fmt(r.followers_per_1k) },
        ]} />
      </Card>
    </div>
  );
}
