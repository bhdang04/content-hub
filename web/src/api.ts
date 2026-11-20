import { useEffect, useState } from "react";

// shapes returned by api/main.py
export type Advice = { post?: string[]; improve?: string[]; test?: string[] };
export type Home = {
  range: [string, string];
  goal: { followers: number; goal: number; by: string; per_week_needed: number; last_week: number };
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
export type Patterns = {
  top_count: number;
  other_count: number;
  differences: { what: string; top: number | null; other: number | null; meaning: string }[];
  followers: { video_id: string; title: string; posted: string; views: number; followers_per_1k: number }[];
};

/** GET /api/<path>. Refetches when `version` changes (after an upload). */
export function useApi<T>(path: string, version = 0) {
  const [state, setState] = useState<{ data?: T; error?: string }>({});
  useEffect(() => {
    let live = true;
    setState({});
    fetch(`/api/${path}`)
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(body.detail ?? `${r.status} ${r.statusText}`);
        return body as T;
      })
      .then((data) => live && setState({ data }))
      .catch((e: Error) => live && setState({ error: e.message }));
    return () => {
      live = false;
    };
  }, [path, version]);
  return state;
}

export const short = (n: number) =>
  Math.abs(n) >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : n.toFixed(0);
/** Time since the previous post, e.g. "9 hours" or "2.5 days". */
export const since = (d: number) => (d < 1 ? `${Math.round(d * 24)} hours` : `${d.toFixed(1)} days`);
export const num = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 1 });
