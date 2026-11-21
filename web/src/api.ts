import { useEffect, useState } from "react";

// shapes returned by api/main.py
export type Advice = { post?: string[]; improve?: string[]; test?: string[] };
export type Home = {
  range: [string, string];
  followers: number;
  views_year: number;
  views_28d: number;
  views_28d_change_pct: number | null;
  follower_gain_year: number;
  typical_engagement_pct: number;
  videos: number;
  weekly_views: { week: string; views: number }[];
  follower_activity: { day: string; followers: number }[];
  advice: Advice;
};
export type Track = {
  message: string | null;
  advice_date: string | null;
  export_end: string | null;
  hits?: Record<string, [number, number]>;
  tests?: string[];
  still_growing?: boolean;
};
export type Video = {
  title: string; posted: string; views: number; likes: number; comments: number; shares: number;
  engagement_pct: number | null; link: string;
};
// Studio per-post data (data/hub.db)
type PostNums = {
  views: number; likes: number; comments: number; shares: number; saves: number;
  avg_watch_s: number; full_watch_rate: number; kept_3s: number | null; new_followers: number | null;
};
export type Post = PostNums & {
  video_id: string; posted: string; title: string; length_s: number; is_ad: number; drop_second: number | null; gap_days: number | null;
};
export type PostDetail = Post & {
  pct_for_you: number | null; pct_search: number | null; pct_profile: number | null;
  pct_following: number | null; pct_other: number | null;
  retention: number[]; search_terms: [string, number][];
  usual: PostNums; usual_retention: number[]; usual_from: number; advice: string[];
};
export type Dance = {
  key: string; label: string; name: string; times: number; best_video_id: string; best_views: number; last_posted: number;
};
export type Plan = {
  days: { date: string; posted: number }[];
  planned: { date: string; slot: number; key: string; name: string; video_id: string | null; why: string | null }[];
  backups: { date: string; rank: number; key: string; name: string; video_id: string | null; why: string | null }[]; // weekly planner's spare dances per day (./run.sh plan)
  shortlist: { key: string; label: string; planned: boolean }[];
  // "Tiktok Dances to Do" Favorites, named by song; done = times you've posted the same dance
  ideas: { key: string; label: string; credit: string; video_id: string; author: string; done: number; planned: boolean; source: "Trending" | "Saved" | "Competitor" }[];
  dances: Dance[]; // best views first
};
/** POST JSON; returns the API's error text ("" when saved), so forms can show why it was refused. */
export const sendMsg = (path: string, body: object) =>
  fetch(`/api/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
    .then(async (r) => (r.ok ? "" : ((await r.json().catch(() => ({}))).detail ?? `${r.status}`)), () => "Couldn't save. Is the dashboard still running?");
/** Write to the plan/shortlist tables. Returns false when the API refuses or is down. */
export const send = (path: string, method: string, body?: object) =>
  fetch(`/api/${path}`, { method, headers: { "Content-Type": "application/json" }, body: body && JSON.stringify(body) })
    .then((r) => r.ok, () => false);
export type Trend = {
  key: string; label: string; credit: string; video_id: string; music_id: string; author: string;
  views: number; likes: number; saves: number; saves_per_1k: number; days_ago: number; videos: number; total: number; newest_days: number;
};
export type CompetitorPost = {
  video_id: string; handle: string; views: number; likes: number; comments: number; shares: number; caption: string; sound: string; format: string;
};
export type Competitors = {
  accounts: { handle: string; followers: number; posts: CompetitorPost[] }[];
  formats: string[];
  compare: string[]; // plain sentences, e.g. "Their 2-person videos get 3.0x the views of their other videos (4 vs 6 posts)."
};
export type Patterns = {
  top_count: number;
  other_count: number;
  differences: { what: string; top: number | null; other: number | null; meaning: string }[];
  followers: { video_id: string; title: string; posted: string; views: number; followers_per_1k: number }[];
};

/** GET /api/<path>. Refetches when `version` changes (after an upload or a save), keeping the old data on
 * screen meanwhile so the page doesn't blank out and jump to the top. A new `path` starts empty. */
export function useApi<T>(path: string, version = 0) {
  const [state, setState] = useState<{ path?: string; data?: T; error?: string }>({});
  useEffect(() => {
    let live = true;
    fetch(`/api/${path}`)
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(body.detail ?? `${r.status} ${r.statusText}`);
        return body as T;
      })
      .then((data) => live && setState({ path, data }))
      .catch((e: Error) => live && setState({ path, error: e.message }));
    return () => {
      live = false;
    };
  }, [path, version]);
  return state.path === path ? state : {};
}

export const short = (n: number) =>
  Math.abs(n) >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : n.toFixed(0);
/** Time since the previous post, e.g. "9 hours" or "2.5 days". */
export const since = (d: number) => (d < 1 ? `${Math.round(d * 24)} hours` : `${d.toFixed(1)} days`);
export const num = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 1 });
