"use client";

import { useState } from "react";
import { save } from "./actions";
import Card from "./card";
import type { Project } from "./data";
import Status from "./status";

type BoardProps = {
  apiBase: string;
  projects: Project[];
  initialSaved: number;
};

export default function Board({ apiBase, projects, initialSaved }: BoardProps) {
  const [saved, setSaved] = useState(initialSaved);
  const [open, setOpen] = useState(false);
  // Cards are hidden in the browser only; the server list stays the same.
  const [hidden, setHidden] = useState<string[]>([]);

  const toggle = () => setOpen((value) => !value);

  async function add() {
    // The server action returns the stored total, which the counter shows.
    setSaved(await save({ amount: 1 }));
  }

  return (
    <>
      <p>API: {apiBase}</p>
      {projects
        .filter((project) => !hidden.includes(project.title))
        .map((project) => (
          <Card
            key={project.title}
            title={project.title}
            count={project.count}
            tone={project.featured ? "accent" : "plain"}
            footer={(card) => (
              <a href={`#${project.title.toLowerCase()}`}>
                Open {card.title} ({card.count})
              </a>
            )}
            onHide={() => setHidden([...hidden, project.title])}
          />
        ))}
      <p>Saved: {saved}</p>
      <button type="button" onClick={add}>
        Add
      </button>
      <button type="button" aria-expanded={open} onClick={toggle}>
        Details
      </button>
      {open && <p>Details are visible</p>}
      <Status open={open} onClose={() => setOpen(false)} />
    </>
  );
}
