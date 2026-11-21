import { useState } from "react";
import { type Competitors, send, sendMsg, short, useApi } from "../api";
import { Card, Loading, RecList, Table } from "../ui";

const box = "rounded-lg border border-grid bg-transparent px-3 py-2 text-sm min-w-0";

/** Dance accounts you watch. Everything here is typed in by you from TikTok (no automated reads). */
export default function CompetitorsPage({ version }: { version: number }) {
  const [bump, setBump] = useState(0);
  const { data, error } = useApi<Competitors>("competitors", version + bump);
  const [acc, setAcc] = useState({ handle: "", followers: "" });
  const [msg, setMsg] = useState("");
  if (!data) return <Loading error={error} />;
  const again = () => setBump((b) => b + 1);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold pt-2">Competitors</h1>
      <p className="text-muted text-sm">3-5 dance accounts (20K-200K followers). Open their profile on TikTok and copy their last ~5 hits here. Their posts show up in Plan.</p>

      <Card title="What works for them" sub="Each format against the rest of their posts. Needs 2+ posts on each side.">
        <RecList items={data.compare} dot="bg-good" />
      </Card>

      {data.accounts.map((a) => (
        <Card key={a.handle}>
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <a href={`https://www.tiktok.com/@${a.handle}`} target="_blank" rel="noreferrer" className="font-semibold hover:underline">@{a.handle}</a>
            <span className="text-muted text-sm">{short(a.followers)} followers · {a.posts.length} posts</span>
            <button className="text-muted hover:text-text text-sm ml-auto" aria-label={`Remove @${a.handle} and their posts`}
                    onClick={async () => { if (await send(`competitors/${encodeURIComponent(a.handle)}`, "DELETE")) again(); }}>Remove</button>
          </div>
          {a.posts.length > 0 && (
            <Table rows={a.posts} cols={[
              { head: "Video", cell: (p) => <a href={`https://www.tiktok.com/@${a.handle}/video/${p.video_id}`} target="_blank" rel="noreferrer" className="hover:underline break-words">{p.sound}</a> },
              { head: "Format", cell: (p) => p.format },
              { head: "Views", cell: (p) => short(p.views), right: true },
              { head: "Likes", cell: (p) => short(p.likes), right: true },
              { head: "Comments", cell: (p) => short(p.comments), right: true },
              { head: "Shares", cell: (p) => short(p.shares), right: true },
              { head: "Caption", cell: (p) => <span className="text-muted text-xs break-words">{p.caption}</span> },
              { head: "", cell: (p) => <button aria-label="Remove this post" className="text-muted hover:text-text"
                                               onClick={async () => { if (await send(`competitor_posts/${p.video_id}`, "DELETE")) again(); }}>✕</button> },
            ]} />
          )}
          <AddPost handle={a.handle} formats={data.formats} onAdded={again} />
        </Card>
      ))}

      <Card title="Add an account">
        <form className="flex flex-wrap gap-2"
              onSubmit={async (e) => { e.preventDefault(); const err = await sendMsg("competitors", acc); setMsg(err); if (!err) { setAcc({ handle: "", followers: "" }); again(); } }}>
          <input value={acc.handle} onChange={(e) => setAcc({ ...acc, handle: e.target.value })} placeholder="@handle" aria-label="Handle" maxLength={41} className={`${box} flex-1`} />
          <input value={acc.followers} onChange={(e) => setAcc({ ...acc, followers: e.target.value })} placeholder="Followers, like 45.3K" aria-label="Followers" className={`${box} flex-1`} />
          <button disabled={!acc.handle.trim() || !acc.followers.trim()} className="rounded-lg border border-good text-good px-4 text-sm disabled:opacity-30">Add</button>
        </form>
        {msg && <p className="text-bad-text text-sm mt-2">{msg}</p>}
      </Card>
    </div>
  );
}

const EMPTY = { link: "", views: "", likes: "", comments: "", shares: "", sound: "", caption: "", format: "" };

function AddPost({ handle, formats, onAdded }: { handle: string; formats: string[]; onAdded: () => void }) {
  const [f, setF] = useState(EMPTY);
  const [msg, setMsg] = useState("");
  const set = (k: keyof typeof EMPTY) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <form className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 border-t border-grid pt-4"
          onSubmit={async (e) => { e.preventDefault(); const err = await sendMsg("competitor_posts", f); setMsg(err); if (!err) { setF(EMPTY); onAdded(); } }}>
      <input value={f.link} onChange={set("link")} placeholder={`Link to a @${handle} video`} aria-label="Video link" className={`${box} col-span-2`} />
      <input value={f.sound} onChange={set("sound")} maxLength={200} placeholder="Song name" aria-label="Song name" className={box} />
      <select value={f.format} onChange={set("format")} aria-label="Format" className={`${box} bg-card`}>
        <option value="">Format…</option>
        {formats.map((x) => <option key={x}>{x}</option>)}
      </select>
      {(["views", "likes", "comments", "shares"] as const).map((k) => (
        <input key={k} value={f[k]} onChange={set(k)} placeholder={k[0].toUpperCase() + k.slice(1)} aria-label={k} inputMode="decimal" className={box} />
      ))}
      <input value={f.caption} onChange={set("caption")} maxLength={300} placeholder="Caption (keep the dc: @ part)" aria-label="Caption" className={`${box} col-span-2 sm:col-span-3`} />
      <button disabled={!f.link.trim() || !f.sound.trim() || !f.format} className="rounded-lg border border-good text-good py-2 text-sm disabled:opacity-30">Add post</button>
      {msg && <p className="text-bad-text text-sm col-span-full">{msg}</p>}
    </form>
  );
}
