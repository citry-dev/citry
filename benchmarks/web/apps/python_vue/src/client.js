import {createApp, defineComponent, h, inject, nextTick, onMounted, provide, ref} from "vue";

const ProjectContext = Symbol("project");
const context = () => inject(ProjectContext);

const ActionForm = defineComponent({
  props: {action: String, label: String, rowId: {default: null}, className: {type: String, default: ""}},
  setup(props, {slots}) {
    const project = context();
    return () => h("form", {class: props.className, onSubmit: project.submit, novalidate: true}, [
      h("input", {type: "hidden", name: "session", value: project.board.value.session}),
      h("input", {type: "hidden", name: "operation", value: "manual"}),
      h("input", {type: "hidden", name: "action", value: props.action}),
      ...(props.rowId === null ? [] : [h("input", {type: "hidden", name: "row_id", value: props.rowId})]),
      slots.default?.(),
      h("button", {type: "submit", "data-bench-action": props.rowId === null ? props.action : `select-${props.rowId}`}, props.label),
    ]);
  },
});

const LocalDisclosure = defineComponent({setup() {
  const open = ref(false);
  return () => h("aside", {id: "local-disclosure"}, [
    h("button", {type: "button", "data-bench-action": "disclosure", "aria-expanded": open.value,
      onClick: () => { open.value = !open.value; }}, "Local details"),
    h("p", {id: "disclosure-content", hidden: !open.value}, "This disclosure needs no server request."),
    h("label", {for: "preserved-input"}, "Local draft"), h("input", {id: "preserved-input", value: "Unchanged draft"}),
  ]);
}});

const ProjectNavbar = defineComponent({setup() {
  const {board} = context();
  return () => h("nav", {id: "project-navbar", "aria-label": "Primary"}, [
    h("a", {href: "#board"}, "Projects"), h("span", {"aria-current": "page"}, board.value.project.name),
  ]);
}});

const ProjectSidebar = defineComponent({setup() {
  const {board} = context();
  return () => h("aside", {id: "project-sidebar"}, [
    h("section", {"aria-labelledby": "bookmark-heading"}, [h("h2", {id: "bookmark-heading"}, "Project Bookmarks"),
      ...board.value.bookmarks.map(bookmark => h("a", {key: bookmark.id, "data-bookmark-id": bookmark.id, "data-bookmark-name": bookmark.text, href: bookmark.url}, h("span", {class: "bookmark-name"}, bookmark.text)))]),
    h("nav", {"aria-label": "Project phases"}, [h("h2", "Phases"), h("ul", board.value.phase_groups.map(phase =>
      h("li", {key: phase.id}, h("a", {href: `#phase-${phase.id}`}, phase.title))))]),
  ]);
}});

const ProjectHeader = defineComponent({setup() {
  const {board} = context();
  return () => h("header", {class: "project-header"}, [
    h("p", [h("a", {href: "#project-navbar", "aria-label": "Projects home"}, "Home"), ` / ${board.value.project.name}`]),
    h("h1", {id: "board-title"}, board.value.title),
    h("p", [h("span", {id: "project-start-date"}, board.value.project.start_date), " – ", h("span", {id: "project-end-date"}, board.value.project.end_date)]),
    h("p", ["Status: ", h("span", {id: "project-status"}, board.value.project.status), "; organization: ", h("span", {id: "project-organization"}, board.value.project.organization)]),
    h("p", [h("span", {id: "visible-count"}, board.value.visible_count), " visible outputs"]),
  ]);
}});

const ProjectActions = defineComponent({setup() {
  const {board} = context();
  const action = (name, label, children) => h(ActionForm, {action: name, label}, children ? {default: children} : undefined);
  return () => h("section", {"aria-label": "Project actions"}, [
    h("div", {class: "toolbar"}, [
      action("filter", "Filter", () => [h("label", {for: "query"}, "Filter outputs"), h("input", {key: `query-${board.value.revision}`, id: "query", name: "query", value: board.value.query})]),
      action("save", "Save", () => [h("label", {for: "title-input"}, "Project name"), h("input", {key: `title-${board.value.revision}`, id: "title-input", name: "title", value: board.value.title_input})]),
    ]),
    h("p", {id: "form-error", role: "alert"}, board.value.error), h("p", {id: "form-notice", role: "status"}, board.value.notice),
    h("div", {class: "toolbar"}, [action("insert", "Insert output"), action("reorder", "Reverse outputs"), action("remove", "Remove inserted output"), action("probe", "Check server")]),
  ]);
}});

const ProjectInfo = defineComponent({setup() {
  const {board} = context();
  return () => {
    const value = board.value;
    const project = value.project;
    return h("section", {class: "project-info"}, [h("h2", "Project Info"),
      h("table", h("tbody", [
        h("tr", [h("th", {scope: "row"}, "Org"), h("td", project.organization)]),
        h("tr", [h("th", {scope: "row"}, "Duration"), h("td", `${project.start_date} – ${project.end_date}`)]),
        h("tr", [h("th", {scope: "row"}, "Status"), h("td", project.status)]),
        h("tr", [h("th", {scope: "row"}, "Tags"), h("td", {"data-project-tags": ""}, value.project_tags.length ? value.project_tags.join(", ") : "No entries")]),
      ])),
      h("section", {"data-project-status-updates": ""}, [h("h3", "Status updates"), value.status_updates.length ? h("ul", value.status_updates.map((item, index) => h("li", {key: item.id ?? index}, item.text ?? String(item)))) : h("p", "No entries")]),
      h("section", [h("h3", "Team"), h("table", [h("thead", h("tr", [h("th", "Name"), h("th", "Role")])), h("tbody", value.roles.map(role => h("tr", {key: role.id, "data-role-id": role.id}, [h("td", {class: "user-name"}, role.user_name), h("td", {class: "role-name"}, role.name)])))])]),
      h("section", {"data-project-contacts": ""}, [h("h3", "Contacts"), value.contacts.length ? h("ul", value.contacts.map((item, index) => h("li", {key: item.id ?? index}, item.name))) : h("p", "No entries")]),
    ]);
  };
}});

const Note = defineComponent({props: {note: Object}, setup(props) {
  return () => h("article", {"data-note-id": props.note.id}, [h("p", {class: "note-text"}, props.note.text),
    h("details", [h("summary", "Comments"), ...props.note.comments.map(comment => h("article", {key: comment.id, "data-comment-id": comment.id}, [h("p", {class: "comment-text"}, comment.text), h("small", {class: "comment-author"}, comment.author)]))])]);
}});

const ProjectNotes = defineComponent({props: {group: Object}, setup(props) {
  return () => h("section", {class: "project-notes"}, [h("h2", "Notes"), ...props.group.notes.map(note => h(Note, {key: note.id, note}))]);
}});

const OutputBadge = defineComponent({props: {output: Object}, setup(props) {
  return () => {
    const missing = props.output.dependencies.some(dependency => !dependency.completed);
    return h("span", {"data-output-badge": props.output.completed ? "done" : "open", class: "output-badge"}, missing ? "Missing dependency" : props.output.completed ? "Completed" : "In progress");
  };
}});

const OutputAttachments = defineComponent({props: {output: Object}, setup(props) {
  return () => h("section", {class: "output-attachments", "aria-label": "Attachments"}, [
    h("h4", "Attachments"),
    ...(props.output.attachments.length ? props.output.attachments.map(attachment =>
      h("article", {key: attachment.id, "data-attachment-id": attachment.id, "data-attachment-name": attachment.name}, [
        h("a", {href: attachment.url, class: "attachment-name"}, attachment.name),
        h("ul", {class: "attachment-tags"}, attachment.tags.map(tag => h("li", {key: tag, "data-attachment-tag": tag}, tag))),
      ])) : [h("p", "No attachments")]),
  ]);
}});

const OutputDependency = defineComponent({props: {dependency: Object}, setup(props) {
  return () => h("article", {"data-dependency-id": props.dependency.id, "data-dependency-title": props.dependency.title, "data-dependency-completed": String(props.dependency.completed)}, [
    h("span", {"aria-hidden": "true"}, props.dependency.completed ? "✓" : "⚠"), " ",
    h("span", {class: "dependency-title"}, props.dependency.title),
  ]);
}});

const OutputForm = defineComponent({props: {output: Object}, setup(props) {
  return () => h(ActionForm, {action: "select", label: "Select", rowId: props.output.id, className: "output-form"}, {default: () => [
    h("label", {for: `description-${props.output.id}`}, "Description"), h("textarea", {id: `description-${props.output.id}`, "data-output-description": "", value: props.output.description}),
    h("label", [h("input", {type: "checkbox", "data-output-completed": "", checked: props.output.completed}), " Completed"]),
  ]});
}});

const ProjectOutput = defineComponent({props: {output: Object}, setup(props) {
  const {board} = context();
  return () => h("article", {id: props.output.element_id, "data-row-id": props.output.id, "data-source-id": props.output.source_id ?? undefined, "data-output-expanded": "true", "data-selected": String(props.output.id === board.value.selected)}, [
    h("header", [h("span", {class: "row-title"}, props.output.title), h("span", {class: "row-status"}, props.output.status), h(OutputBadge, {output: props.output})]),
    h(OutputForm, {output: props.output}),
    h("details", {open: true}, [
      h("summary", "Output details"),
      h("section", {"aria-label": "Dependencies"}, [
        h("h4", "Dependencies"),
        ...(props.output.dependencies.length ? props.output.dependencies.map(dependency => h(OutputDependency, {key: dependency.id, dependency})) : [h("p", "No dependencies")]),
      ]),
      h(OutputAttachments, {output: props.output}),
    ]),
  ]);
}});

const PhaseGroup = defineComponent({props: {phase: Object}, setup(props) {
  return () => h("section", {id: `phase-${props.phase.id}`, "data-phase-id": props.phase.id, "data-phase-expanded": "true"}, h("details", {open: true}, [
    h("summary", h("h3", {class: "phase-title"}, props.phase.title)), h("div", props.phase.outputs.map(output => h(ProjectOutput, {key: output.id, output}))),
  ]));
}});

const ProjectOutputs = defineComponent({setup() {
  const {board} = context();
  return () => h("section", {id: "rows", class: "project-outputs"}, [h("h2", "Outputs"), ...board.value.phase_groups.map(phase => h(PhaseGroup, {key: phase.id, phase}))]);
}});

const ProjectTabs = defineComponent({setup() {
  const {board} = context();
  const active = ref("outputs");
  return () => {
    const tabs = [
      {id: "project-info", label: "Project Info", content: () => h(ProjectInfo)},
      ...board.value.note_tabs.map(group => ({id: group.id, label: group.title, content: () => h(ProjectNotes, {group})})),
      {id: "outputs", label: "Outputs", content: () => h(ProjectOutputs)},
    ];
    return h("section", {id: "project-tabs"}, [
      h("div", {role: "tablist"}, tabs.map(tab => h("button", {key: tab.id, type: "button", role: "tab", "data-tab-target": tab.id,
        "aria-controls": tab.id, "aria-selected": active.value === tab.id, onClick: () => { active.value = tab.id; }}, tab.label))),
      ...tabs.map(tab => h("div", {key: tab.id, id: tab.id, role: "tabpanel", "data-tab-panel": tab.id, hidden: active.value !== tab.id}, tab.content())),
    ]);
  };
}});

const ProjectPage = defineComponent({props: {board: Object, submit: Function}, setup(props) {
  provide(ProjectContext, {board: {get value() { return props.board; }}, submit: props.submit});
  return () => h("div", {class: "project-shell"}, [h(ProjectNavbar), h(ProjectSidebar), h("main", [h(ProjectHeader), h(ProjectActions), h(ProjectTabs)])]);
}});

createApp({setup() {
  const board = ref(null);
  let csrf = "";
  let pending = 0;
  async function ready() {
    await nextTick();
    if (!board.value || pending) return;
    const value = board.value;
    window.__citryBench?.ready({session: value.session, operation: value.operation, revision: value.revision,
      pending, phase: value.revision === 0 ? "initial" : "update"});
  }
  onMounted(async () => {
    pending += 1;
    try {
      const response = await fetch("/initial");
      if (!response.ok) throw new Error(`Initial JSON failed: ${response.status}`);
      const data = await response.json();
      csrf = data.csrf;
      pending -= 1;
      board.value = data.board;
      await ready();
    } catch (error) { console.error(error); }
  });
  async function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    pending += 1;
    try {
      const response = await fetch("/action", {method: "POST", headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf}, body: JSON.stringify(values)});
      if (!response.ok) throw new Error(`Action JSON failed: ${response.status}`);
      const data = await response.json();
      pending -= 1;
      board.value = data.board;
      await ready();
    } catch (error) { console.error(error); }
  }
  return () => board.value ? [h(LocalDisclosure), h("section", {id: "board", "data-project-id": board.value.project.id, "data-session": board.value.session, "data-operation": board.value.operation,
    "data-revision": board.value.revision, "data-visible-count": board.value.visible_count, "data-total-count": board.value.total_count},
    h(ProjectPage, {board: board.value, submit}))] : null;
}}).mount("#root");
