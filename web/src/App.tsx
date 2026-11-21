import { useEffect, useState } from "react";
import HomePage from "./pages/Home";
import VideosPage from "./pages/Videos";
import PatternsPage from "./pages/Patterns";
import VideoPage from "./pages/Video";
import PlanPage from "./pages/Plan";
import LibraryPage from "./pages/Library";
import CompetitorsPage from "./pages/Competitors";
import QuestPage from "./pages/Quest";

const PAGES = { home: "Home", plan: "Plan", library: "Library", competitors: "Competitors", quest: "Quest", videos: "Videos", patterns: "Patterns" } as const;
type Page = keyof typeof PAGES;
const fromHash = (): Page => (location.hash.slice(1) in PAGES ? (location.hash.slice(1) as Page) : "home");
const videoId = () => location.hash.match(/^#video\/(\d+)$/)?.[1]; // #video/<id> = one video's detail page

export default function App() {
  const [page, setPage] = useState<Page>(fromHash);
  const [video, setVideo] = useState(videoId);
  const [version, setVersion] = useState(0); // bumps after an upload so every page refetches
  useEffect(() => {
    const on = () => { setPage(fromHash()); setVideo(videoId()); scrollTo(0, 0); };
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);

  return (
    <div className="md:flex min-h-screen">
      <nav className="md:w-52 shrink-0 p-4 md:p-6 flex md:flex-col gap-1 items-center md:items-stretch">
        <div className="text-xl font-bold mr-4 md:mr-0 md:mb-4">Content Hub</div>
        {(Object.keys(PAGES) as Page[]).map((p) => (
          <a key={p} href={`#${p}`}
             className={`rounded-lg px-3 py-2 text-sm ${(video ? p === "videos" : page === p) ? "bg-card text-text" : "text-muted hover:text-text"}`}>
            {PAGES[p]}
          </a>
        ))}
      </nav>
      <main className="flex-1 min-w-0 px-4 pb-10 md:p-8 max-w-[1400px]">
        {video && <VideoPage id={video} version={version} />}
        {!video && page === "home" && <HomePage version={version} onUploaded={() => setVersion((v) => v + 1)} />}
        {!video && page === "videos" && <VideosPage version={version} />}
        {!video && page === "patterns" && <PatternsPage version={version} />}
        {!video && page === "plan" && <PlanPage version={version} />}
        {!video && page === "library" && <LibraryPage version={version} />}
        {!video && page === "competitors" && <CompetitorsPage version={version} />}
        {!video && page === "quest" && <QuestPage version={version} />}
      </main>
    </div>
  );
}
