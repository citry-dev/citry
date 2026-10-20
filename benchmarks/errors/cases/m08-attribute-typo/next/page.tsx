import Board from "./board";
import { owner, projects, state } from "./data";

// Public setting the browser code may see; the server hands it to the
// client component as a prop.
const API_BASE = "/api";

export default function Home() {
  return (
    <div className="board" title="Board">
      <h1>Projects</h1>
      <p>Owner: {owner.nmae}</p>
      <Board apiBase={API_BASE} projects={projects} initialSaved={state.count} />
      <form role="search">
        <button type="submit">Search</button>
      </form>
    </div>
  );
}
