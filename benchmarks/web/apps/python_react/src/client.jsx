import React, {createContext, useContext, useEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";

const ProjectContext = createContext(null);
const useProject = () => useContext(ProjectContext);

function ActionForm({action, label, rowId = null, children = null, className = ""}) {
  const {board, submit} = useProject();
  return <form className={className} onSubmit={submit} noValidate>
    <input type="hidden" name="session" value={board.session} readOnly/>
    <input type="hidden" name="operation" value="manual" readOnly/>
    <input type="hidden" name="action" value={action} readOnly/>
    {rowId !== null && <input type="hidden" name="row_id" value={rowId} readOnly/>}
    {children}
    <button type="submit" data-bench-action={rowId === null ? action : `select-${rowId}`}>{label}</button>
  </form>;
}

function LocalDisclosure() {
  const [open, setOpen] = useState(false);
  return <aside id="local-disclosure">
    <button type="button" data-bench-action="disclosure" onClick={() => setOpen(value => !value)} aria-expanded={open}>Local details</button>
    <p id="disclosure-content" hidden={!open}>This disclosure needs no server request.</p>
    <label htmlFor="preserved-input">Local draft</label><input id="preserved-input" defaultValue="Unchanged draft"/>
  </aside>;
}

function ProjectNavbar() {
  const {board} = useProject();
  return <nav id="project-navbar" aria-label="Primary"><a href="#board">Projects</a><span aria-current="page">{board.project.name}</span></nav>;
}

function ProjectSidebar() {
  const {board} = useProject();
  return <aside id="project-sidebar">
    <section aria-labelledby="bookmark-heading"><h2 id="bookmark-heading">Project Bookmarks</h2>
      {board.bookmarks.map(bookmark => <a key={bookmark.id} data-bookmark-id={bookmark.id} data-bookmark-name={bookmark.text} href={bookmark.url}><span className="bookmark-name">{bookmark.text}</span></a>)}
    </section>
    <nav aria-label="Project phases"><h2>Phases</h2><ul>
      {board.phase_groups.map(phase => <li key={phase.id}><a href={`#phase-${phase.id}`}>{phase.title}</a></li>)}
    </ul></nav>
  </aside>;
}

function ProjectHeader() {
  const {board} = useProject();
  return <header className="project-header">
    <p><a href="#project-navbar" aria-label="Projects home">Home</a> / {board.project.name}</p>
    <h1 id="board-title">{board.title}</h1>
    <p><span id="project-start-date">{board.project.start_date}</span> – <span id="project-end-date">{board.project.end_date}</span></p>
    <p>Status: <span id="project-status">{board.project.status}</span>; organization: <span id="project-organization">{board.project.organization}</span></p>
    <p><span id="visible-count">{board.visible_count}</span> visible outputs</p>
  </header>;
}

function ProjectActions() {
  const {board} = useProject();
  return <section aria-label="Project actions">
    <div className="toolbar">
      <ActionForm action="filter" label="Filter"><label htmlFor="query">Filter outputs</label><input key={`query-${board.revision}`} id="query" name="query" defaultValue={board.query}/></ActionForm>
      <ActionForm action="save" label="Save"><label htmlFor="title-input">Project name</label><input key={`title-${board.revision}`} id="title-input" name="title" defaultValue={board.title_input}/></ActionForm>
    </div>
    <p id="form-error" role="alert">{board.error}</p><p id="form-notice" role="status">{board.notice}</p>
    <div className="toolbar"><ActionForm action="insert" label="Insert output"/><ActionForm action="reorder" label="Reverse outputs"/><ActionForm action="remove" label="Remove inserted output"/><ActionForm action="probe" label="Check server"/></div>
  </section>;
}

function ProjectInfo() {
  const {board} = useProject();
  const project = board.project;
  return <section className="project-info"><h2>Project Info</h2>
    <table><tbody>
      <tr><th scope="row">Org</th><td>{project.organization}</td></tr>
      <tr><th scope="row">Duration</th><td>{project.start_date} – {project.end_date}</td></tr>
      <tr><th scope="row">Status</th><td>{project.status}</td></tr>
      <tr><th scope="row">Tags</th><td data-project-tags>{board.project_tags.length ? board.project_tags.join(", ") : "No entries"}</td></tr>
    </tbody></table>
    <section data-project-status-updates><h3>Status updates</h3>{board.status_updates.length ? <ul>{board.status_updates.map((value, index) => <li key={value.id ?? index}>{value.text ?? String(value)}</li>)}</ul> : <p>No entries</p>}</section>
    <section><h3>Team</h3><table><thead><tr><th>Name</th><th>Role</th></tr></thead><tbody>
      {board.roles.map(role => <tr key={role.id} data-role-id={role.id}><td className="user-name">{role.user_name}</td><td className="role-name">{role.name}</td></tr>)}
    </tbody></table></section>
    <section data-project-contacts><h3>Contacts</h3>{board.contacts.length ? <ul>{board.contacts.map((contact, index) => <li key={contact.id ?? index}>{contact.name}</li>)}</ul> : <p>No entries</p>}</section>
  </section>;
}

function Note({note}) {
  return <article data-note-id={note.id}><p className="note-text">{note.text}</p><details><summary>Comments</summary>
    {note.comments.map(comment => <article key={comment.id} data-comment-id={comment.id}><p className="comment-text">{comment.text}</p><small className="comment-author">{comment.author}</small></article>)}
  </details></article>;
}

function ProjectNotes({group}) {
  return <section className="project-notes"><h2>Notes</h2>{group.notes.map(note => <Note key={note.id} note={note}/>)}</section>;
}

function OutputBadge({output}) {
  const missing = output.dependencies.some(dependency => !dependency.completed);
  return <span data-output-badge={output.completed ? "done" : "open"} className="output-badge">{missing ? "Missing dependency" : output.completed ? "Completed" : "In progress"}</span>;
}

function OutputAttachments({output}) {
  return <section className="output-attachments" aria-label="Attachments"><h4>Attachments</h4>{output.attachments.length ? output.attachments.map(attachment =>
    <article key={attachment.id} data-attachment-id={attachment.id} data-attachment-name={attachment.name}><a className="attachment-name" href={attachment.url}>{attachment.name}</a>
      <ul className="attachment-tags">{attachment.tags.map(tag => <li key={tag} data-attachment-tag={tag}>{tag}</li>)}</ul>
    </article>) : <p>No attachments</p>}</section>;
}

function OutputDependency({dependency}) {
  return <article data-dependency-id={dependency.id} data-dependency-title={dependency.title} data-dependency-completed={String(dependency.completed)}><span aria-hidden="true">{dependency.completed ? "✓" : "⚠"}</span> <span className="dependency-title">{dependency.title}</span></article>;
}

function OutputForm({output}) {
  return <ActionForm action="select" label="Select" rowId={output.id} className="output-form">
    <label htmlFor={`description-${output.id}`}>Description</label><textarea id={`description-${output.id}`} data-output-description defaultValue={output.description}/>
    <label><input type="checkbox" data-output-completed defaultChecked={output.completed}/> Completed</label>
  </ActionForm>;
}

function ProjectOutput({output}) {
  const {board} = useProject();
  return <article id={output.element_id} data-row-id={output.id} data-source-id={output.source_id ?? undefined} data-output-expanded="true" data-selected={String(output.id === board.selected)}>
    <header><span className="row-title">{output.title}</span> <span className="row-status">{output.status}</span> <OutputBadge output={output}/></header>
    <OutputForm output={output}/>
    <details open><summary>Output details</summary>
      <section aria-label="Dependencies"><h4>Dependencies</h4>{output.dependencies.length ? output.dependencies.map(dependency => <OutputDependency key={dependency.id} dependency={dependency}/>) : <p>No dependencies</p>}</section>
      <OutputAttachments output={output}/>
    </details>
  </article>;
}

function PhaseGroup({phase}) {
  return <section id={`phase-${phase.id}`} data-phase-id={phase.id} data-phase-expanded="true"><details open><summary><h3 className="phase-title">{phase.title}</h3></summary>
    <div>{phase.outputs.map(output => <ProjectOutput key={output.id} output={output}/>)}</div></details></section>;
}

function ProjectOutputs() {
  const {board} = useProject();
  return <section id="rows" className="project-outputs"><h2>Outputs</h2>{board.phase_groups.map(phase => <PhaseGroup key={phase.id} phase={phase}/>)}</section>;
}

function ProjectTabs() {
  const {board} = useProject();
  const [active, setActive] = useState("outputs");
  const tabs = [
    {id: "project-info", label: "Project Info", content: <ProjectInfo/>},
    ...board.note_tabs.map(group => ({id: group.id, label: group.title, content: <ProjectNotes group={group}/> })),
    {id: "outputs", label: "Outputs", content: <ProjectOutputs/>},
  ];
  return <section id="project-tabs"><div role="tablist">{tabs.map(tab => <button key={tab.id} type="button" role="tab" data-tab-target={tab.id} aria-controls={tab.id} aria-selected={active === tab.id} onClick={() => setActive(tab.id)}>{tab.label}</button>)}</div>
    {tabs.map(tab => <div key={tab.id} id={tab.id} role="tabpanel" data-tab-panel={tab.id} hidden={active !== tab.id}>{tab.content}</div>)}
  </section>;
}

function ProjectPage({board, submit}) {
  return <ProjectContext.Provider value={{board, submit}}><div className="project-shell"><ProjectNavbar/><ProjectSidebar/><main><ProjectHeader/><ProjectActions/><ProjectTabs/></main></div></ProjectContext.Provider>;
}

function App() {
  const [board, setBoard] = useState(null);
  const csrf = useRef("");
  const pending = useRef(0);
  useEffect(() => {
    pending.current += 1;
    fetch("/initial").then(async response => {
      if (!response.ok) throw new Error(`Initial JSON failed: ${response.status}`);
      const data = await response.json();
      csrf.current = data.csrf;
      pending.current -= 1;
      setBoard(data.board);
    }).catch(error => console.error(error));
  }, []);
  useEffect(() => {
    if (!board || pending.current) return;
    window.__citryBench?.ready({session: board.session, operation: board.operation, revision: board.revision,
      pending: pending.current, phase: board.revision === 0 ? "initial" : "update"});
  }, [board]);
  async function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    pending.current += 1;
    try {
      const response = await fetch("/action", {method: "POST", headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf.current}, body: JSON.stringify(values)});
      if (!response.ok) throw new Error(`Action JSON failed: ${response.status}`);
      const data = await response.json();
      pending.current -= 1;
      setBoard(data.board);
    } catch (error) { console.error(error); }
  }
  if (!board) return null;
  return <><LocalDisclosure/><section id="board" data-project-id={board.project.id} data-session={board.session} data-operation={board.operation} data-revision={board.revision}
    data-visible-count={board.visible_count} data-total-count={board.total_count}><ProjectPage board={board} submit={submit}/></section></>;
}

createRoot(document.getElementById("root")).render(<App/>);
