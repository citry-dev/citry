import type { CSSProperties } from "react";
import Image from "next/image";
import Link from "next/link";
import Board from "./board";
import BoardProvider from "./board-context";
import { owner, projects, state } from "./data";
import Search from "./search";

// Public setting the browser code may see; the server hands it to the
// client component as a prop.
const API_BASE = "/api";

// The heading's color, which globals.css reads as the CSS variable --accent.
const ACCENT = "rgb(0, 0, 255)";

export default async function Home({ searchParams }: PageProps<"/">) {
  // The search form submits back to this page with its text in `q`.
  const { q } = await searchParams;
  return (
    <div className="board" id="board" title="Board" style={{ "--accent": ACCENT } as CSSProperties}>
      <h1>Projects</h1>
      <p>Owned by {owner.name}</p>
      <Image src="/avatar.svg" alt={owner.name} width={32} height={32} />
      <p>Owner: {owner.name}</p>
      <p>Projects: {projects.length}</p>
      <BoardProvider>
        <Board apiBase={API_BASE} projects={projects} initialSaved={state.count} />
      </BoardProvider>
      <Search />
      {q && <p>Searched: {q}</p>}
      <nav>
        <Link href="/about">About</Link> <Link href="/projects/1">Project 1</Link>
      </nav>
    </div>
  );
}
