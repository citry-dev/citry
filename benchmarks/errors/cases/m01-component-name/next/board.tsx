"use client";

import { useState } from "react";
import { save } from "./actions";
import Card from "./card";
import type { Project } from "./data";

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
          <Crad
            key={project.title}
            title={project.title}
            count={project.count}
            footer={
              <a href={`#${project.title.toLowerCase()}`}>
                Open {project.title}
              </a>
            }
            onHide={() => setHidden([...hidden, project.title])}
          />
        ))}
      <p>Saved: {saved}</p>
      <button type="button" onClick={add}>
        Add
      </button>
      <button type="button" onClick={toggle}>
        Details
      </button>
      {open && <p>Details are visible</p>}
    </>
  );
}
