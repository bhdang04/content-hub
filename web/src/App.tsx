import { useEffect, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
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
    <MotionConfig reducedMotion="user">
    <div className="md:flex min-h-screen">
      <nav className="md:w-52 shrink-0 p-4 md:p-6 flex md:flex-col gap-1 items-center md:items-stretch md:sticky md:top-0 md:self-start md:h-screen md:overflow-y-auto">
        <div className="glitch text-xl font-bold mr-4 md:mr-0 md:mb-4">Content Hub</div>
        {(Object.keys(PAGES) as Page[]).map((p) => {
          const on = video ? p === "videos" : page === p;
          return (
            <a key={p} href={`#${p}`} className={`relative rounded-lg px-3 py-2 text-sm transition-colors ${on ? "text-text" : "text-muted hover:text-text"}`}>
              {/* the highlight slides from the old tab to the new one */}
              {on && <motion.span layoutId="nav-pill" transition={{ type: "spring", stiffness: 400, damping: 32 }}
                                  className="absolute inset-0 rounded-lg neon-card border-l-2 !border-l-good" />}
              <span className="relative">{PAGES[p]}</span>
            </a>
          );
        })}
      </nav>
      <main className="flex-1 min-w-0 px-4 pb-10 md:p-8 max-w-[1400px]">
        <AnimatePresence mode="wait">
        <motion.div key={video ?? page} initial={{ opacity: 0, y: 12, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    exit={{ opacity: 0, y: -8, filter: "blur(4px)" }} transition={{ duration: 0.25 }}>
        {video && <VideoPage id={video} version={version} />}
        {!video && page === "home" && <HomePage version={version} onUploaded={() => setVersion((v) => v + 1)} />}
        {!video && page === "videos" && <VideosPage version={version} />}
        {!video && page === "patterns" && <PatternsPage version={version} />}
        {!video && page === "plan" && <PlanPage version={version} />}
        {!video && page === "library" && <LibraryPage version={version} />}
        {!video && page === "competitors" && <CompetitorsPage version={version} />}
        {!video && page === "quest" && <QuestPage version={version} />}
        </motion.div>
        </AnimatePresence>
      </main>
    </div>
    </MotionConfig>
  );
}
