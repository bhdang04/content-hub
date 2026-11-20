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
export type Patterns = {
  top_count: number;
  other_count: number;
  differences: { what: string; top: number | null; other: number | null; meaning: string }[];
  followers: { title: string; posted: string; views: number; followers_per_1k: number }[];
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
export const num = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 1 });
