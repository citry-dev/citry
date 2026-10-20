import Board from "./board";
import { owner, projects, state } from "./data";

// Public setting the browser code may see; the server hands it to the
// client component as a prop.
const API_BASE = "/api";

export default function Home() {
  return (
    <div className="board" title="Board">
      <h1>Projects</h1>
      <p>Owner: {owner.name}</p>
      <Board apiBase={API_BASE} projects={projects.map((project) => ({ ...project, count: String(project.count) }))} initialSaved={state.count} />
      <form role="search">
        <button type="submit">Search</button>
      </form>
    </div>
  );
}
