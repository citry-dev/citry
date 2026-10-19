// The Node adapters use the same frozen source data and state transitions as
// the Python adapters.  This module deliberately contains no framework code;
// Next and Nuxt call it from their own server entry points.
import source from "../generated/data.mjs";

export const CANONICAL_OUTPUT_COUNT = 14;
export const SUPPORTED_COUNTS = [14, 140, 1400];
export const FILTER_QUERY = "Lorem ipsum 12";
export const PHASE_TYPES = ["PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4", "PHASE_5"];

const boards = new Map();

function canonicalState(count) {
  if (!SUPPORTED_COUNTS.includes(count)) throw new Error("count must be 14, 140 or 1400 outputs");
  const scale = count / CANONICAL_OUTPUT_COUNT;
  const templates = new Map(source.phase_templates.map(item => [item.pk, item.fields]));
  const phasesByType = new Map(
    source.phases.map(item => [templates.get(item.fields.phase_template).type, item.pk]),
  );
  const phaseOrder = PHASE_TYPES.map(type => phasesByType.get(type));
  const phaseTitles = Object.fromEntries(
    PHASE_TYPES.map(type => [phasesByType.get(type), source.phase_titles[type]]),
  );
  const outputsBySource = new Map(source.outputs.map(item => [item[0].pk, item[0]]));
  const outputsByPhase = new Map(
    phaseOrder.map(phaseId => [
      phaseId,
      source.outputs.filter(item => item[0].fields.phase === phaseId),
    ]),
  );
  const ordered = [];
  for (const phaseId of phaseOrder) {
    for (let replica = 0; replica < scale; replica += 1) {
      for (const item of outputsByPhase.get(phaseId)) ordered.push([replica, item]);
    }
  }
  const outputIds = new Map(
    ordered.map(([replica, item], index) => [`${replica}:${item[0].pk}`, index + 1]),
  );
  const rows = [];
  let attachmentId = 1;
  ordered.forEach(([replica, item], index) => {
    const [output, attachments, dependencies] = item;
    const fields = output.fields;
    const rowAttachments = attachments.map(([attachment, tags]) => ({
      id: attachmentId++,
      name: attachment.fields.text,
      url: attachment.fields.url,
      tags: tags.map(String),
    }));
    const rowDependencies = dependencies.map(([dependency]) => {
      const dependencyFields = outputsBySource.get(dependency.pk).fields;
      return {
        id: outputIds.get(`${replica}:${dependency.pk}`),
        title: dependencyFields.name,
        completed: Boolean(dependencyFields.completed),
      };
    });
    rows.push({
      id: index + 1,
      source_id: output.pk,
      title: fields.name,
      status: fields.completed ? "done" : "open",
      completed: Boolean(fields.completed),
      description: fields.description,
      phase_id: fields.phase,
      attachments: rowAttachments,
      dependencies: rowDependencies,
    });
  });

  const users = new Map(source.users.map(item => [item.pk, item.fields]));
  const noteTabs = [];
  let noteId = 1;
  let commentId = 1;
  for (let tabNumber = 1; tabNumber <= 3; tabNumber += 1) {
    const notes = [];
    for (let replica = 0; replica < scale; replica += 1) {
      for (const note of source[`notes_${tabNumber}`]) {
        const comments = (source[`comments_by_notes_${tabNumber}`][String(note.pk)] || []).map(comment => {
          const fields = comment.fields;
          const user = users.get(fields.modified_by) || source.users[0].fields;
          return {
            id: commentId++,
            text: fields.text ?? fields.notes ?? "",
            author: user.name,
          };
        });
        notes.push({id: noteId++, text: note.fields.text, comments});
      }
    }
    noteTabs.push({id: `notes-${tabNumber}`, title: `Notes ${tabNumber}`, notes});
  }

  const roles = [];
  let roleId = 1;
  for (let replica = 0; replica < scale; replica += 1) {
    for (const role of source.roles_with_users) {
      const fields = role.fields;
      roles.push({id: roleId++, name: fields.name, user_name: users.get(fields.user).name});
    }
  }
  const projectFields = source.project.fields;
  const organizations = new Map(source.organizations.map(item => [item.pk, item.fields]));
  const project = {
    id: source.project.pk,
    name: projectFields.name,
    status: projectFields.status,
    start_date: projectFields.start_date,
    end_date: projectFields.end_date,
    organization: organizations.get(projectFields.organization).name,
  };
  return {
    rows,
    project,
    phase_order: phaseOrder,
    phase_titles: phaseTitles,
    note_tabs: noteTabs,
    roles,
    bookmarks: Array.from({length: scale}, (_, replica) => ({
      id: replica + 1,
      text: "Test bookmark",
      url: "/bookmarks/9/create",
    })),
    contacts: [...source.contacts],
    status_updates: [...source.status_updates],
    project_tags: [...source.project_tags],
  };
}

function validateSession(session) {
  if (!session || session.length > 128 || !/^[A-Za-z0-9_-]+$/.test(session)) {
    throw new Error("session must contain 1 to 128 letters, digits, underscores or hyphens");
  }
}

export function reset(session, count) {
  validateSession(session);
  const state = canonicalState(count);
  boards.set(session, {
    session,
    ...state,
    revision: 0,
    operation: "initial",
    title: state.project.name,
    title_input: state.project.name,
    query: "",
    selected: 0,
    error: "",
    notice: "",
    next_id: count + 1,
    inserted: 0,
  });
}

export function ensure(session, count) {
  if (!boards.has(session)) reset(session, count);
}

function getBoard(session) {
  const board = boards.get(session);
  if (!board) throw new Error("Board session does not exist");
  return board;
}

export function snapshot(session) {
  const board = getBoard(session);
  const visible = board.rows
    .filter(row => board.query.toLocaleLowerCase().length === 0 || row.title.toLocaleLowerCase().includes(board.query.toLocaleLowerCase()))
    .map(row => ({
      ...row,
      element_id: `row-${row.id}`,
      select_action: `select-${row.id}`,
      selected: row.id === board.selected,
    }));
  const grouped = new Map(board.phase_order.map(phaseId => [phaseId, []]));
  for (const row of visible) grouped.get(row.phase_id).push(row);
  const result = {
    ...board,
    rows: visible,
    phase_groups: board.phase_order.map(phaseId => ({
      id: phaseId,
      title: board.phase_titles[String(phaseId)],
      outputs: grouped.get(phaseId),
    })),
    visible_count: visible.length,
    total_count: board.rows.length,
  };
  delete result.phase_order;
  delete result.phase_titles;
  return result;
}

export function browserSnapshot(value) {
  const result = {...value};
  delete result.rows;
  return result;
}

export function apply(session, data) {
  const board = getBoard(session);
  if (!data.operation || data.operation.length > 128) throw new Error("operation must contain 1 to 128 characters");
  if (data.action === "select") {
    const rowId = Number.parseInt(data.row_id || "0", 10);
    if (!board.rows.some(row => row.id === rowId)) throw new Error("selected output does not exist");
    board.selected = rowId;
  } else if (data.action === "filter") {
    board.query = data.query || "";
  } else if (data.action === "save") {
    board.title_input = data.title || "";
    const title = board.title_input.trim();
    board.error = title.length < 3 || title.length > 80 ? "Use between 3 and 80 characters." : "";
    board.notice = board.error ? "" : "Saved on server.";
    if (!board.error) {
      board.title = title;
      board.project.name = title;
    }
  } else if (data.action === "insert") {
    const phaseId = board.phase_order.at(-1);
    const row = {
      id: board.next_id++,
      source_id: null,
      title: `New output ${String(board.next_id - 1).padStart(4, "0")}`,
      status: "open",
      completed: false,
      description: "",
      phase_id: phaseId,
      attachments: [],
      dependencies: [],
    };
    board.rows.push(row);
    board.inserted = row.id;
  } else if (data.action === "remove") {
    if (!board.inserted) throw new Error("insert an output before removing it");
    board.rows = board.rows.filter(row => row.id !== board.inserted);
    board.inserted = 0;
  } else if (data.action === "reorder") {
    board.rows.reverse();
    board.phase_order.reverse();
  } else if (data.action !== "probe") {
    throw new Error("unknown board action");
  }
  board.revision += 1;
  board.operation = data.operation;
  return snapshot(session);
}

export function csrfFor(session) {
  return `bench-csrf-${session}`;
}
